#!/usr/bin/env python3
"""
Workflow orchestrator for paper-to-attack implementation and auditing.

This module handles all flow control logic, determining when to run which agent
and passing structured results between agents.
"""

import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from agents.utils.agent_utils import AgentResult, create_agent_runner, find_in_json, validate_environment
from agents.utils.checkpoint import CheckpointManager


@dataclass
class AttackWorkflowConfig:
    """Configuration for the attack workflow."""
    arxiv_id: str
    repo_root: Path
    max_loops: int = 10
    planner_agent: str = "codex"
    attack_agent: str = "codex"
    audit_agent: str = "codex"
    attack_model: str = "gpt-5.5"
    planner_model: str = "gpt-5.5"
    audit_model: str = "gpt-5.5"
    paper_source: str = "pdf"  # "pdf" skips OCR; "ocr" creates/uses paper markdown
    per_query_timeout: int = 0  # Maximum time (seconds) per attack query (0 = no timeout)


def _compute_resume_state(
    checkpoint: Optional[Dict[str, Any]],
) -> Tuple[int, Optional[str], Optional[str]]:
    """
    Compute (iteration, last_completed_step, attack_name) from a checkpoint record.

    The checkpoint stores the *last completed* step. If that step is "auditor",
    the iteration is already fully processed and we advance to the next iteration.
    """
    if not checkpoint:
        return 1, None, None

    iteration = int(checkpoint["iteration"])
    last_step = checkpoint.get("step_name")
    attack_name = checkpoint.get("attack_name")

    if last_step == "auditor":
        return iteration + 1, None, attack_name

    return iteration, last_step, attack_name


class PaperToAttackWorkflow:
    """Orchestrates the paper-to-attack implementation and auditing workflow."""

    def __init__(self, config: AttackWorkflowConfig):
        """
        Initialize workflow.

        Args:
            config: Workflow configuration
        """
        if config.paper_source not in {"pdf", "ocr"}:
            raise ValueError("paper_source must be 'pdf' or 'ocr'")

        self.config = config
        self.repo_root = config.repo_root

        self.paper_dir = self.repo_root / "attacks_paper_info" / self.config.arxiv_id

        # Common paths for all variants
        self.paper_pdf_file = self.paper_dir / f"{self.config.arxiv_id}.pdf"
        self.paper_md_file = self.paper_dir / f"{self.config.arxiv_id}.md"
        self.impl_plan_md_file = self.paper_dir / f"{self.config.arxiv_id}_implementation_plan.md"
        self.experiment_setup_file = self.paper_dir / "experiment_setup.yaml"
        self.current_source_md_file = self.paper_md_file
        self._update_current_source_path()

        playbook_dir = self.repo_root / "agents/playbooks/attack"
        self.planner_playbook = playbook_dir / "attack_planner.md"
        self.attack_playbook = playbook_dir / "attack_implementation.md"
        self.audit_playbook = playbook_dir / "attack_auditor.md"

        self.log_dir = self.repo_root / ".agent_runs" / "attack" / config.arxiv_id

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize checkpoint manager
        self.checkpoint = CheckpointManager(self.log_dir)

        # Initialize agent runners
        self.planner_runner = create_agent_runner(config.planner_agent, self.repo_root)
        self.attack_runner = create_agent_runner(config.attack_agent, self.repo_root)
        self.audit_runner = create_agent_runner(config.audit_agent, self.repo_root)

        # Validate environment
        seen_bins = set()
        for runner in [self.planner_runner, self.attack_runner, self.audit_runner]:
            if runner.bin_path not in seen_bins:
                validate_environment(runner.bin_path, [])
                seen_bins.add(runner.bin_path)
        for playbook in [self.planner_playbook, self.attack_playbook, self.audit_playbook]:
            if not playbook.exists():
                print(f"❌ Missing required file: {playbook}", file=sys.stderr)
                sys.exit(1)

    def _update_current_source_path(self) -> None:
        """Update pointer to current source document (paper or implementation plan)."""
        if self.impl_plan_md_file.exists():
            self.current_source_md_file = self.impl_plan_md_file
        else:
            self.current_source_md_file = self.paper_md_file

    def _relative_to_repo(self, path: Path) -> str:
        """Return a repository-relative string for a path."""
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)

    def check_and_process_paper(self) -> None:
        """
        Ensure the paper assets exist, reprocessing if needed.

        This checks for paper assets in attacks_paper_info/{arxiv_id}/.

        If requirements are missing, runs paper_preprocessor.py to download
        the PDF and optionally create OCR markdown.

        Raises:
            SystemExit: If preprocessing fails
        """
        pdf_exists = self.paper_pdf_file.exists()
        md_exists = self.paper_md_file.exists()
        impl_plan_exists = self.impl_plan_md_file.exists()

        if impl_plan_exists:
            print("✅ Implementation plan already exists; skipping paper source requirement")
            print(f"   Plan: {self.impl_plan_md_file}")
            self._update_current_source_path()
            return

        requires_ocr = self.config.paper_source == "ocr"

        if pdf_exists and (md_exists or not requires_ocr):
            print(f"✅ Paper assets already processed")
            print(f"   PDF: {self.paper_pdf_file}")
            if md_exists:
                print(f"   paper markdown: {self.paper_md_file}")
            self._update_current_source_path()
            return

        print(f"📥 Paper assets missing, running preprocessor...")

        cmd = [
            "python",
            "agents/utils/paper_preprocessor.py",
            "--arxiv-id", self.config.arxiv_id
        ]
        if not requires_ocr:
            cmd.append("--skip-ocr")

        print(f"🔧 Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=False,
            text=True
        )

        if result.returncode != 0:
            if result.returncode == 4:
                print(f"⚠️  Paper rejected by eligibility triage (not a CPU-runnable black-box text-only jailbreak)")
                sys.exit(4)
            print(f"❌ Paper preprocessing failed!")
            sys.exit(1)

        pdf_exists = self.paper_pdf_file.exists()
        md_exists = self.paper_md_file.exists()
        if not pdf_exists or (requires_ocr and not md_exists):
            print(f"❌ Preprocessing completed but files not found:")
            print(f"   PDF exists: {pdf_exists}")
            print(f"   MD exists:  {md_exists}")
            sys.exit(1)

        print(f"✅ Paper processed successfully")
        print(f"   PDF: {self.paper_pdf_file}")
        if md_exists:
            print(f"   MD:  {self.paper_md_file}")
        self._update_current_source_path()

    def extract_experiment_setup(self) -> None:
        """
        Extract experiment setup (datasets, models, judge) from paper PDF.

        Runs agents/utils/experiment_setup_extractor.py to analyze the paper
        and extract evaluation configuration used in the original paper.

        This is a one-time step that creates experiment_setup.yaml if it doesn't exist.

        Raises:
            SystemExit: If extraction fails
        """
        if self.experiment_setup_file.exists():
            print(f"✅ Experiment setup already extracted")
            print(f"   File: {self.experiment_setup_file}")
            return

        print(f"📊 Experiment setup not found, running extractor...")

        # Check if PDF exists
        if not self.paper_pdf_file.exists():
            print(f"❌ Paper PDF not found: {self.paper_pdf_file}")
            print(f"   Run check_and_process_paper() first")
            sys.exit(1)

        # Run experiment setup extractor
        cmd = [
            "python",
            "agents/utils/experiment_setup_extractor.py",
            "--arxiv-id", self.config.arxiv_id,
            "--pdf-path", str(self.paper_pdf_file),
            "--output", str(self.experiment_setup_file)
        ]

        print(f"🔧 Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=False,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ Experiment setup extraction failed!")
            sys.exit(1)

        # Verify file was created
        if not self.experiment_setup_file.exists():
            print(f"❌ Extraction completed but file not found: {self.experiment_setup_file}")
            sys.exit(1)

        print(f"✅ Experiment setup extracted successfully")
        print(f"   File: {self.experiment_setup_file}")

    def check_audit_verdict_exists(self) -> Optional[str]:
        """
        Check if an audit verdict file exists and what it says.

        Returns:
            "100%" if 100% fidelity achieved
            "NOT_100%" if verdict exists but not 100%
            None if no verdict exists
        """
        verdict_file = self.paper_dir / "Implementation_verdict.md"

        if not verdict_file.exists():
            print("📋 No audit verdict found")
            return None

        with open(verdict_file, 'r') as f:
            content = f.read()

        if "Not 100% Fidelity" in content:
            print("⚠️  Previous audit shows issues to fix")
            return "NOT_100%"
        elif "100% Fidelity" in content:
            print("✅ Previous audit shows 100% fidelity")
            return "100%"

        return None

    def run_attack_implementation(self, iteration: int, is_refinement: bool = False) -> AgentResult:
        """
        Run attack implementation agent.

        Args:
            iteration: Current iteration number
            is_refinement: Whether this is a refinement pass (Mode 2)

        Returns:
            AgentResult from the agent
        """
        print(f"\n{'='*60}")
        print(f"🔨 ATTACK IMPLEMENTATION PASS (Iteration {iteration})")
        print(f"   Mode: {'Refinement (Mode 2)' if is_refinement else 'Initial (Mode 1)'}")
        print(f"{'='*60}")

        # Always use latest blueprint path
        self._update_current_source_path()

        # Load playbook
        with open(self.attack_playbook, 'r') as f:
            playbook_content = f.read()

        # Build context
        context = {
            "arxiv_id": self.config.arxiv_id,
            "iteration": iteration,
            "mode": "refinement" if is_refinement else "initial",
            "source_markdown": self._relative_to_repo(self.current_source_md_file),
            "implementation_plan": self._relative_to_repo(self.impl_plan_md_file)
        }

        # Build extra instructions
        timeout_instruction = ""
        if self.config.per_query_timeout > 0:
            timeout_instruction = f"""

TIMEOUT CONSTRAINTS (LEGACY - should not be used during implementation):
- When running attack configs, add --per-query-timeout {self.config.per_query_timeout}
- If you encounter "ATTACK TIMEOUT ERROR" or "timeout exceeded":
  * DO NOT try to fix or optimize the code
  * This is a FATAL error indicating the algorithm is too slow
  * Immediately report failure with status: "failure" and error details
  * Do not continue attempting to fix the implementation
"""

        extra_instructions = f"""
At the end of your implementation, output a JSON result block:

```json
{{
  "status": "success",
  "result": {{
    "attack_name": "the_attack_name_gen",
    "implementation_file": "src/jbfoundry/attacks/generated/attack_name_gen.py",
    "attack_config": "scripts/attack_configs/attack_name_gen.yaml",
    "completed": true
  }}
}}
```

If the implementation fails (including timeout errors), report:
```json
{{
  "status": "failure",
  "error": "description of the error"
}}
```{timeout_instruction}
"""

        # Build prompt
        prompt = self.attack_runner.build_prompt(
            f"attack-implementation-iter-{iteration}",
            playbook_content,
            context,
            extra_instructions
        )

        # Run agent
        log_file = self.log_dir / f"attack-pass-{iteration}.txt"
        result = self.attack_runner.run(
            prompt,
            model=self.config.attack_model,
            log_file=log_file,
        )

        return result

    def run_attack_planner(self, iteration: int) -> AgentResult:
        """
        Run attack planning agent to produce detailed implementation instructions.

        Args:
            iteration: Current iteration number

        Returns:
            AgentResult from the agent
        """
        print(f"\n{'='*60}")
        print(f"🧭 IMPLEMENTATION PLANNING PASS (Iteration {iteration})")
        print(f"{'='*60}")

        paper_md = self.paper_md_file if self.paper_md_file.exists() else None
        if not self.paper_pdf_file.exists():
            raise FileNotFoundError(f"Paper PDF missing: {self.paper_pdf_file}")

        # Load playbook
        with open(self.planner_playbook, 'r') as f:
            playbook_content = f.read()

        context = {
            "arxiv_id": self.config.arxiv_id,
            "iteration": iteration,
            "paper_markdown": self._relative_to_repo(paper_md) if paper_md else "",
            "paper_pdf": self._relative_to_repo(self.paper_pdf_file),
            "paper_source": self._relative_to_repo(paper_md) if paper_md else self._relative_to_repo(self.paper_pdf_file),
            "implementation_plan_output": self._relative_to_repo(self.impl_plan_md_file),
            "paper_assets_dir": self._relative_to_repo(self.paper_dir)
        }

        extra_instructions = f"""
At the end of your planning, output a JSON result block:

```json
{{
  "status": "success",
  "result": {{
    "implementation_plan_file": "{self._relative_to_repo(self.impl_plan_md_file)}",
    "completed": true
  }}
}}
```
"""

        prompt = self.planner_runner.build_prompt(
            f"attack-planning-iter-{iteration}",
            playbook_content,
            context,
            extra_instructions
        )

        log_file = self.log_dir / f"planner-pass-{iteration}.txt"
        result = self.planner_runner.run(
            prompt,
            model=self.config.planner_model,
            log_file=log_file,
        )

        return result

    def extract_impl_plan_from_result(self, result: AgentResult) -> str:
        """
        Extract implementation plan path from planner result JSON.

        Args:
            result: AgentResult from planning pass

        Returns:
            Path to implementation plan file
        """
        if not result.metadata.get("result_data"):
            raise ValueError("Planner agent did not return structured JSON result. Check logs.")

        raw = result.metadata["result_data"]
        plan_path = find_in_json(raw, "implementation_plan_file")

        if not plan_path:
            raise ValueError(f"JSON result missing 'implementation_plan_file' field. \n{raw}")

        print(f"✅ Implementation plan path from JSON: {plan_path}")
        return plan_path

    def run_audit(self, iteration: int, attack_name: str) -> AgentResult:
        """
        Run audit agent.

        Args:
            iteration: Current iteration number
            attack_name: Name of the attack to audit

        Returns:
            AgentResult from the agent
        """
        print(f"\n{'='*60}")
        print(f"🔍 AUDIT PASS (Iteration {iteration})")
        print(f"   Attack: {attack_name}")
        print(f"{'='*60}")

        # Always use latest blueprint path
        self._update_current_source_path()

        # Load playbook
        with open(self.audit_playbook, 'r') as f:
            playbook_content = f.read()

        # Build context
        context = {
            "arxiv_id": self.config.arxiv_id,
            "attack_name": attack_name,
            "source_markdown": self._relative_to_repo(self.current_source_md_file),
            "implementation_file": f"src/jbfoundry/attacks/generated/{attack_name}.py",
            "iteration": iteration
        }

        # Build extra instructions
        extra_instructions = """
At the end of your audit, output a JSON result block:

```json
{
  "status": "success",
  "result": {
    "verdict": "100% Fidelity" or "Not 100% Fidelity",
    "coverage_percentage": 95,
    "total_components": 20,
    "covered_components": 19,
    "major_issues": 3,
    "completed": true
  }
}
```
"""

        # Build prompt
        prompt = self.audit_runner.build_prompt(
            f"audit-iter-{iteration}",
            playbook_content,
            context,
            extra_instructions
        )

        # Run agent
        log_file = self.log_dir / f"auditor-pass-{iteration}.txt"
        result = self.audit_runner.run(
            prompt,
            model=self.config.audit_model,
            log_file=log_file,
        )

        return result

    def extract_coverage_from_result(self, result: AgentResult) -> int:
        """
        Extract coverage percentage from audit result JSON.

        Args:
            result: AgentResult from audit

        Returns:
            Coverage percentage

        Raises:
            ValueError: If JSON result is missing or invalid
        """
        # Require structured JSON result
        if not result.metadata.get("result_data"):
            raise ValueError("Audit agent did not return structured JSON result. Check logs.")

        raw = result.metadata["result_data"]
        coverage = find_in_json(raw, "coverage_percentage")

        if coverage is None:
            raise ValueError(f"JSON result missing 'coverage_percentage' field. \n{raw}")

        print(f"📊 Coverage from JSON: {coverage}%")
        return int(coverage)

    def extract_attack_name_from_result(self, result: AgentResult) -> str:
        """
        Extract attack name from implementation result JSON.

        Args:
            result: AgentResult from implementation

        Returns:
            Attack name

        Raises:
            ValueError: If JSON result is missing or invalid
        """
        # Require structured JSON result
        if not result.metadata.get("result_data"):
            raise ValueError("Agent did not return structured JSON result. Check logs.")

        raw = result.metadata["result_data"]
        attack_name = find_in_json(raw, "attack_name")

        if not attack_name:
            raise ValueError(f"JSON result missing 'attack_name' field. \n{raw}")

        print(f"✅ Attack name from JSON: {attack_name}")
        return attack_name

    def write_metadata_file(self, attack_name: str, iteration: int, result: AgentResult) -> None:
        """
        Write stable metadata file with attack information.

        This creates a JSON file that can be reliably read by backend without parsing agent output.

        Args:
            attack_name: Name of the generated attack
            iteration: Current iteration number
            result: AgentResult containing structured data

        The metadata file is saved at attacks_paper_info/{arxiv_id}/metadata.json.
        """
        raw = result.metadata.get("result_data", {})

        # Build paths
        implementation_file = find_in_json(raw, "implementation_file") or f"src/jbfoundry/attacks/generated/{attack_name}.py"
        attack_config = find_in_json(raw, "attack_config") or f"scripts/attack_configs/{attack_name}.yaml"
        metadata = {
            "attack_name": attack_name,
            "arxiv_id": self.config.arxiv_id,
            "implementation_file": implementation_file,
            "attack_config": attack_config,
            "iteration": iteration,
            "generated_at": datetime.now().isoformat(),
            "repo_root": str(self.repo_root),
            "paper_dir": str(self.paper_dir)
        }

        metadata_file = self.paper_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Metadata file written: {metadata_file}")
        print(f"   Attack name: {attack_name}")
        print(f"   Implementation: {implementation_file}")
        print(f"   Attack config: {attack_config}")

    def run(self) -> None:
        """Execute the main workflow loop."""
        print(f"\n{'='*60}")
        print(f"🚀 PAPER-TO-ATTACK WORKFLOW")
        print(f"   Paper: {self.config.arxiv_id}")
        print(f"   Max iterations: {self.config.max_loops}")
        print(f"{'='*60}\n")

        # Step 0: Ensure paper is processed
        print("📄 Step 0: Checking paper processing status...")
        self.check_and_process_paper()
        print()

        # # Step 0.5: Extract experiment setup from paper
        # print("📊 Step 0.5: Extracting experiment setup...")
        # self.extract_experiment_setup()
        # print()

        # Check if we're in refinement mode
        verdict_status = self.check_audit_verdict_exists()
        is_refinement = verdict_status == "NOT_100%"

        if verdict_status == "100%":
            print("✅ Previous audit shows 100% fidelity. Nothing to do.")
            self.checkpoint.clear()
            sys.exit(0)

        # Check for last checkpoint (last completed step)
        last_checkpoint = self.checkpoint.get_last_checkpoint()
        if last_checkpoint:
            print(f"📂 Found checkpoint (last completed step):")
            print(f"   Iteration: {last_checkpoint['iteration']}")
            print(f"   Completed step: {last_checkpoint['step_name']}")
            ck_attack_name = last_checkpoint.get("attack_name")
            if ck_attack_name:
                print(f"   Attack: {ck_attack_name}")
            print()
        else:
            print("ℹ️  No checkpoint found, starting from beginning\n")

        iteration, last_checkpoint_step, attack_name = _compute_resume_state(last_checkpoint)

        # Planning is a one-time step; run only if the plan is missing or the last checkpoint
        # indicates we stopped right after planning.
        if not self.impl_plan_md_file.exists():
            plan_result = self.run_attack_planner(iteration)
            if not plan_result.success:
                print(f"❌ Implementation planning failed: {plan_result.error}")
                sys.exit(1)

            try:
                self.extract_impl_plan_from_result(plan_result)
            except ValueError as e:
                print(f"❌ Failed to extract implementation plan path: {e}")
                sys.exit(1)

            # Only remove paper markdown after plan is confirmed written
            try:
                self.paper_md_file.unlink()
                print(f"🗑️  Removed paper markdown after planning: {self.paper_md_file}")
            except FileNotFoundError:
                pass
            except OSError as exc:
                print(f"⚠️  Failed to remove paper markdown {self.paper_md_file}: {exc}")

        # Initialize control variables
        coverage = 0

        while iteration <= self.config.max_loops:
            print(f"\n{'#'*60}")
            print(f"# ITERATION {iteration}")
            print(f"{'#'*60}\n")

            # Step 1: Attack implementation (skip if checkpoint says attack already done)
            if last_checkpoint_step != "attack":
                impl_result = self.run_attack_implementation(iteration, is_refinement)

                # Check for timeout errors in JSON result and output text
                error_msg = impl_result.error or ""
                output_text = impl_result.output_text or ""
                result_data = impl_result.metadata.get("result_data") or {}
                result_status = result_data.get("status", "")
                result_error = result_data.get("error", "")

                # Check for timeout indicators (text-based only)
                is_timeout = False

                if "ATTACK TIMEOUT ERROR" in error_msg.upper():
                    is_timeout = True
                elif "ATTACK TIMEOUT ERROR" in output_text.upper():
                    is_timeout = True
                elif "ATTACK TIMEOUT ERROR" in str(result_error).upper():
                    is_timeout = True
                elif "TIMEOUT EXCEEDED" in error_msg.upper():
                    is_timeout = True
                elif "TIMEOUT EXCEEDED" in output_text.upper():
                    is_timeout = True
                elif "TIMEOUT EXCEEDED" in str(result_error).upper():
                    is_timeout = True

                if is_timeout:
                    print(f"\n{'='*60}")
                    print(f"⏱️  ATTACK IMPLEMENTATION TIMEOUT DETECTED")
                    print(f"{'='*60}")
                    print(f"\nThe attack implementation is taking too long per query.")
                    print(f"This indicates the implementation needs optimization.")
                    if self.config.per_query_timeout > 0:
                        print(f"\nTimeout limit: {self.config.per_query_timeout} seconds per query")
                    print(f"\nStopping workflow. Please review and optimize:")
                    print(f"  - Reduce computational complexity")
                    print(f"  - Use more efficient algorithms")
                    print(f"  - Minimize API calls")
                    print(f"  - Cache expensive computations")
                    print(f"{'='*60}\n")
                    sys.exit(3)  # Exit with code 3 for timeout

                # Check for other failures
                if not impl_result.success or result_status == "failure":
                    if result_status == "failure":
                        print(f"❌ Attack implementation failed (JSON status): {result_error}")
                    else:
                        print(f"❌ Attack implementation failed: {impl_result.error}")
                    sys.exit(1)

                try:
                    attack_name = self.extract_attack_name_from_result(impl_result)
                    # Write stable metadata file immediately
                    self.write_metadata_file(attack_name, iteration, impl_result)
                    self.checkpoint.save_checkpoint(iteration, "attack", attack_name)
                except ValueError as e:
                    print(f"❌ Failed to extract attack name: {e}")
                    sys.exit(1)

            # Step 2: Audit (skip if checkpoint says auditor already done)
            if last_checkpoint_step != "auditor":
                audit_result = self.run_audit(iteration, attack_name)

                if not audit_result.success:
                    print(f"❌ Audit failed: {audit_result.error}")
                    sys.exit(1)

                try:
                    coverage = self.extract_coverage_from_result(audit_result)
                    self.checkpoint.save_checkpoint(iteration, "auditor", attack_name)
                except ValueError as e:
                    print(f"❌ Failed to extract coverage: {e}")
                    sys.exit(1)

            print(f"\n{'='*60}")
            print(f"📊 ITERATION {iteration} RESULTS")
            print(f"   Coverage: {coverage}%")
            print(f"{'='*60}\n")

            # Check if we're done
            if coverage >= 100:
                print("✅ Target coverage achieved (100%)!")
                print(f"   Attack: {attack_name}")
                print(f"   Implementation: src/jbfoundry/attacks/generated/{attack_name}.py")
                self.checkpoint.clear()
                sys.exit(0)

            # Continue to next iteration in refinement mode
            print(f"🔁 Coverage {coverage}% < 100%. Continuing to next iteration...")
            is_refinement = True  # All subsequent iterations are refinements
            iteration += 1
            # Planner is not rerun in refinements; carry forward existing plan
            last_checkpoint_step = None

        print(f"\n❌ Reached maximum iterations ({self.config.max_loops}) without achieving 100% coverage")
        print(f"   Final coverage: {coverage}%")
        print(f"   Attack: {attack_name}")
        sys.exit(1)
