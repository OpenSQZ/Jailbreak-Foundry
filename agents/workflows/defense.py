#!/usr/bin/env python3
"""
Workflow orchestrator for paper-to-defense implementation and auditing.
"""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from agents.utils.agent_utils import AgentResult, CursorAgentRunner, validate_environment
from agents.utils.checkpoint import CheckpointManager


@dataclass
class DefenseWorkflowConfig:
    """Configuration for the defense workflow."""
    arxiv_id: str
    repo_root: Path
    max_loops: int = 10
    cursor_agent_bin: str = "cursor-agent"
    cursor_agent_flags: list = None
    defense_model: str = "sonnet-4.5"
    planner_model: str = "gpt-5.1"
    audit_model: str = "gpt-5.1"
    use_proxychains: bool = True

    def __post_init__(self):
        if self.cursor_agent_flags is None:
            self.cursor_agent_flags = []


class PaperToDefenseWorkflow:
    """Orchestrates the paper-to-defense implementation and auditing workflow."""

    def __init__(self, config: DefenseWorkflowConfig):
        self.config = config
        self.repo_root = config.repo_root

        # Setup paths
        self.paper_dir = self.repo_root / "defense_paper_info" / self.config.arxiv_id
        self.paper_pdf_file = self.paper_dir / f"{self.config.arxiv_id}.pdf"
        self.paper_md_file = self.paper_dir / f"{self.config.arxiv_id}.md"
        self.impl_plan_md_file = self.paper_dir / f"{self.config.arxiv_id}_implementation_plan.md"
        self.current_source_md_file = self.paper_md_file
        self._update_current_source_path()
        playbook_dir = self.repo_root / "agents/playbooks/defense"
        self.planner_playbook = playbook_dir / "defense_planner.md"
        self.defense_playbook = playbook_dir / "defense_implementation.md"
        self.audit_playbook = playbook_dir / "defense_auditor.md"
        self.log_dir = self.repo_root / "logs/defense_auditor" / config.arxiv_id

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Initialize checkpoint manager
        self.checkpoint = CheckpointManager(self.log_dir)

        # Initialize agent runner
        self.agent_runner = CursorAgentRunner(
            cursor_agent_bin=config.cursor_agent_bin,
            cursor_agent_flags=config.cursor_agent_flags,
            repo_root=self.repo_root
        )

        # Validate environment
        validate_environment(
            config.cursor_agent_bin,
            [self.planner_playbook, self.defense_playbook, self.audit_playbook]
        )

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
        """
        pdf_exists = self.paper_pdf_file.exists()
        md_exists = self.paper_md_file.exists()
        impl_plan_exists = self.impl_plan_md_file.exists()

        if impl_plan_exists:
            print("✅ Implementation plan already exists; skipping paper markdown requirement")
            print(f"   Plan: {self.impl_plan_md_file}")
            self._update_current_source_path()
            return

        if pdf_exists and md_exists:
            print("✅ Paper assets already processed")
            print(f"   PDF: {self.paper_pdf_file}")
            print(f"   paper markdown: {self.paper_md_file}")
            self._update_current_source_path()
            return

        print("📥 Paper assets missing, running preprocessor...")

        cmd = [
            "python",
            "agents/utils/paper_preprocessor.py",
            "--arxiv-id", self.config.arxiv_id,
            "--service-account", "vertex_credentials.json",
            "--output-root", "defense_paper_info"
        ]

        print(f"🔧 Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            cwd=self.repo_root,
            capture_output=False,
            text=True
        )

        if result.returncode != 0:
            print("❌ Paper preprocessing failed!")
            sys.exit(1)

        pdf_exists = self.paper_pdf_file.exists()
        md_exists = self.paper_md_file.exists()
        if not pdf_exists or not md_exists:
            print("❌ Preprocessing completed but files not found:")
            print(f"   PDF exists: {pdf_exists}")
            print(f"   MD exists:  {md_exists}")
            sys.exit(1)

        print("✅ Paper processed successfully")
        print(f"   PDF: {self.paper_pdf_file}")
        print(f"   MD:  {self.paper_md_file}")
        self._update_current_source_path()

    def check_audit_verdict_exists(self) -> Optional[str]:
        """
        Check if an audit verdict file exists and what it says.
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
        if "100% Fidelity" in content:
            print("✅ Previous audit shows 100% fidelity")
            return "100%"

        return None

    def run_defense_implementation(self, iteration: int, is_refinement: bool = False) -> AgentResult:
        """Run defense implementation agent."""
        print(f"\n{'='*60}")
        print(f"🛡️ DEFENSE IMPLEMENTATION PASS (Iteration {iteration})")
        print(f"   Mode: {'Refinement (Mode 2)' if is_refinement else 'Initial (Mode 1)'}")
        print(f"{'='*60}")

        self._update_current_source_path()

        with open(self.defense_playbook, 'r') as f:
            playbook_content = f.read()

        context = {
            "arxiv_id": self.config.arxiv_id,
            "iteration": iteration,
            "mode": "refinement" if is_refinement else "initial",
            "source_markdown": self._relative_to_repo(self.current_source_md_file),
            "implementation_plan": self._relative_to_repo(self.impl_plan_md_file)
        }

        extra_instructions = f"""
At the end of your implementation, output a JSON result block:

```json
{{
  "status": "success",
  "result": {{
    "defense_name": "the_defense_name_gen",
    "implementation_file": "src/jbfoundry/defenses/generated/defense_name_gen.py",
    "test_script": "scripts/comprehensive_tests/defense/test_defense_name_gen_comprehensive.sh",
    "completed": true
  }}
}}
```
"""

        prompt = self.agent_runner.build_prompt(
            f"defense-implementation-iter-{iteration}",
            playbook_content,
            context,
            extra_instructions
        )

        log_file = self.log_dir / f"defense-pass-{iteration}.txt"
        result = self.agent_runner.run(
            prompt,
            model=self.config.defense_model,
            log_file=log_file,
            use_proxychains=self.config.use_proxychains
        )

        return result

    def run_defense_planner(self, iteration: int, is_refinement: bool = False) -> AgentResult:
        """Run defense planning agent."""
        print(f"\n{'='*60}")
        print(f"🧭 DEFENSE PLANNING PASS (Iteration {iteration})")
        print(f"   Mode: {'Refinement (Mode 2)' if is_refinement else 'Initial (Mode 1)'}")
        print(f"{'='*60}")

        self._update_current_source_path()

        if not self.paper_md_file.exists():
            raise FileNotFoundError(f"Paper markdown missing: {self.paper_md_file}")

        with open(self.planner_playbook, 'r') as f:
            playbook_content = f.read()

        context = {
            "arxiv_id": self.config.arxiv_id,
            "iteration": iteration,
            "mode": "refinement" if is_refinement else "initial",
            "paper_markdown": self._relative_to_repo(self.current_source_md_file),
            "implementation_plan_output": self._relative_to_repo(self.impl_plan_md_file),
            "paper_assets_dir": self._relative_to_repo(self.paper_dir),
            "audit_verdict": self._relative_to_repo(
                self.paper_dir / "Implementation_verdict.md"
            )
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

        prompt = self.agent_runner.build_prompt(
            f"defense-planning-iter-{iteration}",
            playbook_content,
            context,
            extra_instructions
        )

        log_file = self.log_dir / f"planner-pass-{iteration}.txt"
        result = self.agent_runner.run(
            prompt,
            model=self.config.planner_model,
            log_file=log_file,
            use_proxychains=self.config.use_proxychains
        )

        if result.success:
            try:
                self.paper_md_file.unlink()
                print(f"🗑️  Removed paper markdown after planning: {self.paper_md_file}")
            except FileNotFoundError:
                pass
            except OSError as exc:
                print(f"⚠️  Failed to remove paper markdown {self.paper_md_file}: {exc}")

        return result

    def extract_impl_plan_from_result(self, result: AgentResult) -> str:
        """Extract implementation plan path from planner result JSON."""
        if not result.metadata.get("result_data"):
            raise ValueError("Planner agent did not return structured JSON result. Check logs.")

        result_data = result.metadata["result_data"].get("result", {}) or {}
        plan_path = result_data.get("implementation_plan_file")

        if not plan_path:
            raise ValueError(f"JSON result missing 'implementation_plan_file' field. \n{result.metadata['result_data']}")

        print(f"✅ Implementation plan path from JSON: {plan_path}")
        return plan_path

    def run_audit(self, iteration: int, defense_name: str) -> AgentResult:
        """Run audit agent."""
        print(f"\n{'='*60}")
        print(f"🔍 DEFENSE AUDIT PASS (Iteration {iteration})")
        print(f"   Defense: {defense_name}")
        print(f"{'='*60}")

        self._update_current_source_path()

        with open(self.audit_playbook, 'r') as f:
            playbook_content = f.read()

        context = {
            "arxiv_id": self.config.arxiv_id,
            "defense_name": defense_name,
            "source_markdown": self._relative_to_repo(self.current_source_md_file),
            "implementation_file": f"src/jbfoundry/defenses/generated/{defense_name}.py",
            "iteration": iteration
        }

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

        prompt = self.agent_runner.build_prompt(
            f"defense-audit-iter-{iteration}",
            playbook_content,
            context,
            extra_instructions
        )

        log_file = self.log_dir / f"auditor-pass-{iteration}.txt"
        result = self.agent_runner.run(
            prompt,
            model=self.config.audit_model,
            log_file=log_file,
            use_proxychains=self.config.use_proxychains
        )

        return result

    def extract_coverage_from_result(self, result: AgentResult) -> int:
        """Extract coverage percentage from audit result JSON."""
        if not result.metadata.get("result_data"):
            raise ValueError("Audit agent did not return structured JSON result. Check logs.")

        result_data = result.metadata["result_data"].get("result", {}) or {}
        coverage = result_data.get("coverage_percentage")

        if coverage is None:
            raise ValueError(f"JSON result missing 'coverage_percentage' field. \n{result.metadata['result_data']}")

        print(f"📊 Coverage from JSON: {coverage}%")
        return int(coverage)

    def extract_defense_name_from_result(self, result: AgentResult) -> str:
        """Extract defense name from implementation result JSON."""
        if not result.metadata.get("result_data"):
            raise ValueError("Agent did not return structured JSON result. Check logs.")

        result_data = result.metadata["result_data"].get("result", {}) or {}
        defense_name = result_data.get("defense_name")

        if not defense_name:
            raise ValueError(f"JSON result missing 'defense_name' field. \n{result.metadata['result_data']}")

        print(f"✅ Defense name from JSON: {defense_name}")
        return defense_name

    def run(self) -> None:
        """Execute the main workflow loop."""
        print(f"\n{'='*60}")
        print("🚀 PAPER-TO-DEFENSE WORKFLOW")
        print(f"   Paper: {self.config.arxiv_id}")
        print(f"   Max iterations: {self.config.max_loops}")
        print(f"{'='*60}\n")

        print("📄 Step 0: Checking paper processing status...")
        self.check_and_process_paper()
        print()

        verdict_status = self.check_audit_verdict_exists()
        is_refinement = verdict_status == "NOT_100%"

        if verdict_status == "100%":
            print("✅ Previous audit shows 100% fidelity. Nothing to do.")
            self.checkpoint.clear()
            sys.exit(0)

        last_checkpoint = self.checkpoint.get_last_checkpoint()
        if last_checkpoint:
            print("📂 Found checkpoint (last completed step):")
            print(f"   Iteration: {last_checkpoint['iteration']}")
            print(f"   Completed step: {last_checkpoint['step_name']}")
            defense_name = last_checkpoint.get('defense_name')
            if defense_name:
                print(f"   Defense: {defense_name}")
            print("   Will skip completed steps and resume from next step")
            print()
            iteration = last_checkpoint['iteration']
            last_checkpoint_step = last_checkpoint['step_name']
        else:
            print("ℹ️  No checkpoint found, starting from beginning\n")
            iteration = 1
            defense_name = None
            last_checkpoint_step = None

        skipping = (last_checkpoint_step is not None)
        coverage = 0

        while iteration <= self.config.max_loops:
            print(f"\n{'#'*60}")
            print(f"# ITERATION {iteration}")
            print(f"{'#'*60}\n")

            if skipping:
                if last_checkpoint_step == "planner":
                    skipping = False
            else:
                if self.impl_plan_md_file.exists():
                    print("🧭 Implementation plan already exists; skipping planner pass")
                    self.checkpoint.save_checkpoint(iteration, "planner", defense_name)
                else:
                    plan_result = self.run_defense_planner(iteration, is_refinement)
                    if not plan_result.success:
                        print(f"❌ Implementation planning failed: {plan_result.error}")
                        sys.exit(1)

                    try:
                        self.extract_impl_plan_from_result(plan_result)
                        self.checkpoint.save_checkpoint(iteration, "planner", defense_name)
                    except ValueError as e:
                        print(f"❌ Failed to extract implementation plan path: {e}")
                        sys.exit(1)

            if skipping:
                if last_checkpoint_step == "defense":
                    skipping = False
            else:
                impl_result = self.run_defense_implementation(iteration, is_refinement)
                if not impl_result.success:
                    print(f"❌ Defense implementation failed: {impl_result.error}")
                    sys.exit(1)

                try:
                    defense_name = self.extract_defense_name_from_result(impl_result)
                    self.checkpoint.save_checkpoint(iteration, "defense", defense_name)
                except ValueError as e:
                    print(f"❌ Failed to extract defense name: {e}")
                    sys.exit(1)

            if skipping:
                if last_checkpoint_step == "auditor":
                    skipping = False
            else:
                audit_result = self.run_audit(iteration, defense_name)

                if not audit_result.success:
                    print(f"❌ Audit failed: {audit_result.error}")
                    sys.exit(1)

                try:
                    coverage = self.extract_coverage_from_result(audit_result)
                    self.checkpoint.save_checkpoint(iteration, "auditor", defense_name)
                except ValueError as e:
                    print(f"❌ Failed to extract coverage: {e}")
                    sys.exit(1)

            print(f"\n{'='*60}")
            print(f"📊 ITERATION {iteration} RESULTS")
            print(f"   Coverage: {coverage}%")
            print(f"{'='*60}\n")

            if coverage >= 100:
                print("✅ Target coverage achieved (100%)!")
                print(f"   Defense: {defense_name}")
                print(f"   Implementation: src/jbfoundry/defenses/generated/{defense_name}.py")
                self.checkpoint.clear()
                sys.exit(0)

            print(f"🔁 Coverage {coverage}% < 100%. Continuing to next iteration...")
            is_refinement = True
            iteration += 1

        print(f"\n❌ Reached maximum iterations ({self.config.max_loops}) without achieving 100% coverage")
        print(f"   Final coverage: {coverage}%")
        print(f"   Defense: {defense_name}")
        sys.exit(1)
