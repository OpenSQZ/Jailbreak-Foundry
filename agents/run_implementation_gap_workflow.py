#!/usr/bin/env python3
"""
Claude Code-driven workflow for generating implementation gap notes and refining an attack.

Steps:
1) Call Claude Code to write implementation_gap_notes.md for a paper/attack.
2) Call Claude Code again to refine the generated attack implementation file only.
"""

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Add parent directory to path to allow 'agents' to be a package
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.utils.agent_utils import validate_environment


@dataclass
class ImplementationGapWorkflowConfig:
    """Configuration for implementation gap + refinement workflow."""

    arxiv_id: str
    attack_name: str
    repo_root: Path
    claude_bin: str = "claude"
    claude_flags: list = None
    claude_model: Optional[str] = None
    prompt_flag: Optional[str] = "-p"
    prompt_stdin: bool = False
    permission_mode: Optional[str] = "acceptEdits"
    dangerously_skip_permissions: bool = False
    force: bool = False
    run_test: bool = True
    max_refine_attempts: int = 3
    use_extra_agent: bool = False

    def __post_init__(self):
        if self.claude_flags is None:
            self.claude_flags = []


class ImplementationGapWorkflow:
    """Orchestrates gap-note generation and strict refinement via Claude Code."""

    def __init__(self, config: ImplementationGapWorkflowConfig):
        self.config = config
        self.repo_root = config.repo_root
        self.paper_dir = self.repo_root / "attacks_paper_info" / self.config.arxiv_id
        self.impl_plan_file = self.paper_dir / f"{self.config.arxiv_id}_implementation_plan.md"

        # Set up extra_agent mode paths and naming
        if self.config.use_extra_agent:
            self.extra_agent_dir = self.paper_dir / "extra_agent"
            self.gap_notes_file = self.extra_agent_dir / "implementation_gap_notes.md"
            self.attack_name = self._normalize_attack_name(self.config.attack_name, suffix="_improved")
            self.attack_file = (
                self.repo_root / "src" / "jbfoundry" / "attacks" / "generated"
                / f"{self.attack_name}_improved.py"
            )
            self.test_script = 'scripts/comprehensive_tests/attack' / f"test_{self.config.attack_name.replace('_gen', '')}_improved_comprehensive.sh"
            self.source_test_script = 'scripts/comprehensive_tests/attack' / f"test_{self.config.attack_name.replace('_gen', '')}_comprehensive.sh"
            self.gap_prompt_file = self.extra_agent_dir / f"{self.config.arxiv_id}_gap_prompt.md"
            self.refine_prompt_file = self.extra_agent_dir / f"{self.config.arxiv_id}_refine_prompt.md"
        else:
            self.gap_notes_file = self.paper_dir / "implementation_gap_notes.md"
            self.attack_name = self._normalize_attack_name(self.config.attack_name)
            self.attack_file = (
                self.repo_root / "src" / "jbfoundry" / "attacks" / "generated" / f"{self.attack_name}.py"
            )
            self.test_script = self.paper_dir / f"test_{self.attack_name.replace('_gen', '')}_comprehensive.sh"
            self.gap_prompt_file = self.paper_dir / f"{self.config.arxiv_id}_gap_prompt.md"
            self.refine_prompt_file = self.paper_dir / f"{self.config.arxiv_id}_refine_prompt.md"

        self.log_dir = self.repo_root / "logs" / "implementation_gap_workflow" / self.config.arxiv_id
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Validate environment - in extra_agent mode, check original file instead of improved one
        if self.config.use_extra_agent:
            original_attack = self.config.attack_name
            if not original_attack.endswith("_gen"):
                original_attack = f"{original_attack}_gen"
            original_attack_file = (
                self.repo_root / "src" / "jbfoundry" / "attacks" / "generated" / f"{original_attack}.py"
            )
            validate_environment(self.config.claude_bin, [self.impl_plan_file, original_attack_file])
        else:
            validate_environment(self.config.claude_bin, [self.impl_plan_file, self.attack_file])

    def _normalize_attack_name(self, attack_name: str, suffix: str = "") -> str:
        name = attack_name.strip()
        if not name:
            raise ValueError("attack_name must be non-empty")
        if not name.endswith("_gen"):
            name = f"{name}_gen"
        # Add suffix (e.g., "_improved") before the file extension, after "_gen"
        if suffix:
            name = name.replace("_gen", f"_gen{suffix}")
        return name

    def _relative_to_repo(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.repo_root))
        except ValueError:
            return str(path)

    def _setup_extra_agent_folder(self) -> None:
        """Create extra_agent folder and copy test script with updated attack name."""
        if not self.config.use_extra_agent:
            return

        # Create extra_agent directory
        self.extra_agent_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Created extra_agent folder: {self.extra_agent_dir}")

        # Copy original attack file to improved location
        original_attack = self.config.attack_name
        if not original_attack.endswith("_gen"):
            original_attack = f"{original_attack}_gen"
        original_attack_file = (
            self.repo_root / "src" / "jbfoundry" / "attacks" / "generated" / f"{original_attack}.py"
        )

        if original_attack_file.exists():
            if not self.attack_file.exists() or self.config.force:
                import shutil
                shutil.copy2(original_attack_file, self.attack_file)
                print(f"📄 Copied original attack file: {original_attack_file.name} → {self.attack_file.name}")
            else:
                print(f"ℹ️  Improved attack file already exists: {self.attack_file}")
        else:
            print(f"⚠️  Warning: Original attack file not found: {original_attack_file}")

        # Copy and update test script
        if self.source_test_script.exists():
            test_content = self.source_test_script.read_text()
            # Replace attack name in the script (e.g., "air_gen" -> "air_gen_improved")
            test_content = test_content.replace(
                f'ATTACK_NAME="{original_attack}"',
                f'ATTACK_NAME="{self.attack_name}"'
            )
            self.test_script.write_text(test_content)
            print(f"📋 Copied and updated test script: {self.test_script}")
        else:
            print(f"⚠️  Warning: Source test script not found: {self.source_test_script}")

    def _write_gap_prompt(self) -> None:
        """Write prompt instructing Claude Code to generate implementation gap notes."""
        gap_output = self._relative_to_repo(self.gap_notes_file)
        impl_plan = self._relative_to_repo(self.impl_plan_file)
        attack_file = self._relative_to_repo(self.attack_file)
        paper_dir = self._relative_to_repo(self.paper_dir)

        prompt = f"""You are Claude Code operating inside this repository.

Goal: Create implementation gap notes that explain why ASR may be lower than the paper.

Required inputs to read:
- Implementation plan: `{impl_plan}`
- Reference implementation files under `{paper_dir}/` (use them as the gold standard)
- Current generated attack: `{attack_file}`

Write/overwrite the file `{gap_output}` with markdown that mirrors the style of
`attacks_paper_info/2510.08859/implementation_gap_notes.md`.

Format requirements:
- Start with: "## Differences Likely Causing the ASR Gap"
- Each gap should include: What the paper does / What your version does / Why this matters / Files
- Keep items concise, actionable, and rooted in concrete code differences

Rules:
- Do NOT edit any files other than `{gap_output}`
- Do NOT run any code or tests
- If the reference repo conflicts with the paper, treat the repo as the source of truth

At the end, print a brief summary and list the files you wrote.
"""
        self.gap_prompt_file.write_text(prompt)

    def _write_refine_prompt(self, attempt_index: int) -> None:
        """Write prompt instructing Claude Code to refine the attack file only."""
        gap_notes = self._relative_to_repo(self.gap_notes_file)
        impl_plan = self._relative_to_repo(self.impl_plan_file)
        attack_file = self._relative_to_repo(self.attack_file)
        test_script = self._relative_to_repo(self.test_script)
        model_constraints = (
            "Available models (must not invent or align to your own runtime): "
            "llama-2-7b-chat, llama-3-8b-instruct, gpt-3.5-turbo, gpt-4-0613, "
            "gpt-5.1, gpt-4o, claude-3-5-sonnet-20241022, "
            "claude-3-7-sonnet-20250219, qwen3-14b."
        )
        provider_constraints = (
            "Provider/model mapping (must match src/jbfoundry/runners/test_comprehensive.py): "
            "llama-2-7b-chat->openai, llama-3-8b-instruct->openai, "
            "gpt-3.5-turbo->openai, gpt-4-0613->openai, gpt-5.1->openai, "
            "gpt-4o->openai, claude-3-5-sonnet-20241022->wenwen, "
            "claude-3-7-sonnet-20250219->wenwen, qwen3-14b->infini."
        )
        api_base_constraints = (
            "Allowed api_base values: "
            "http://10.210.22.10:30254/v1 (llama-2-7b-chat), "
            "http://10.210.22.10:30253/v1 (llama-3-8b-instruct). "
            "Other providers should not set api_base unless already present."
        )

        prompt = f"""You are Claude Code operating inside this repository.

Goal: Refine the attack implementation to close the gaps documented in `{gap_notes}`.
This is refinement attempt #{attempt_index}.

Strict rules:
- You MUST follow the framework contract and the implementation plan exactly.
- You MUST only edit `{attack_file}` and `{test_script}`. No other files may be changed.
- Do NOT read or modify other generated/manual attacks.
- Do NOT run any code or tests.

Framework files to read before editing:
- `src/jbfoundry/attacks/base.py`
- `src/jbfoundry/attacks/factory.py`
- `src/jbfoundry/llm/litellm.py`
- `src/jbfoundry/runners/universal_attack.py`

Primary sources:
- Implementation plan: `{impl_plan}`
- Gap notes: `{gap_notes}`

Model constraints:
- {model_constraints}
- {provider_constraints}
- {api_base_constraints}
- If you touch `{test_script}`, you may only use the models above and must not change them
  to match your own runtime model.

Deliverable:
- Update `{attack_file}` to match the plan and reference implementation gaps.
- If needed, update `{test_script}` to align with paper-critical parameters and framework rules.
- Preserve the framework API, naming rules, and parameters.
- If a gap cannot be addressed within `{attack_file}`, explain why in comments inside the file.

At the end, print a brief summary and list the files you changed.
"""
        self.refine_prompt_file.write_text(prompt)

    def _run_claude(self, prompt_file: Path, log_file: Path) -> None:
        """Run Claude Code with a prompt file and capture logs."""
        prompt_text = prompt_file.read_text()

        cmd = [self.config.claude_bin]
        if self.config.claude_model:
            cmd.extend(["--model", self.config.claude_model])
        if self.config.permission_mode:
            cmd.extend(["--permission-mode", self.config.permission_mode])
        if self.config.dangerously_skip_permissions:
            cmd.append("--dangerously-skip-permissions")
        if self.config.claude_flags:
            cmd.extend(self.config.claude_flags)

        input_text = None
        if self.config.prompt_stdin or not self.config.prompt_flag:
            input_text = prompt_text
        else:
            cmd.extend([self.config.prompt_flag, prompt_text])

        process = subprocess.Popen(
            cmd,
            cwd=self.repo_root,
            stdin=subprocess.PIPE if input_text is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )

        with log_file.open("w") as log_handle:
            log_handle.write(f"COMMAND: {' '.join(cmd)}\n\nOUTPUT:\n")
            if input_text is not None and process.stdin:
                process.stdin.write(input_text)
                process.stdin.close()

            if process.stdout:
                for line in process.stdout:
                    print(line, end="")
                    log_handle.write(line)

        returncode = process.wait()
        with log_file.open("a") as log_handle:
            log_handle.write(f"\n\nRETURN_CODE: {returncode}\n")
        if returncode != 0:
            print(f"❌ Claude Code failed. See log: {log_file}")
            sys.exit(1)

    def run(self) -> None:
        """Execute gap-note generation and refinement passes."""
        # Set up extra_agent folder structure if needed
        self._setup_extra_agent_folder()

        if self.gap_notes_file.exists() and not self.config.force:
            print(f"ℹ️  Gap notes already exist: {self.gap_notes_file}")
            print("    Use --force to overwrite")
        else:
            self._write_gap_prompt()
            gap_log = self.log_dir / "gap-pass.txt"
            print("🧠 Running Claude Code for implementation gap notes...")
            self._run_claude(self.gap_prompt_file, gap_log)

        for attempt_index in range(1, self.config.max_refine_attempts + 1):
            self._write_refine_prompt(attempt_index)
            refine_log = self.log_dir / f"refine-pass-{attempt_index}.txt"
            print("🧠 Running Claude Code for attack refinement...")
            self._run_claude(self.refine_prompt_file, refine_log)

            if not self.config.run_test:
                break

            if not self.test_script.exists():
                print(f"❌ Test script not found: {self.test_script}")
                sys.exit(1)
            print(f"🧪 Running test script: {self.test_script}")
            result = subprocess.run(
                ["bash", str(self.test_script)],
                cwd=self.repo_root,
                text=True,
            )
            if result.returncode == 0:
                break

            print(f"❌ Test script failed (attempt {attempt_index})")
            if attempt_index == self.config.max_refine_attempts:
                sys.exit(1)

        print("✅ Workflow completed")
        print(f"   Gap notes: {self.gap_notes_file}")
        print(f"   Attack file: {self.attack_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate implementation gap notes and refine a generated attack with Claude Code."
    )
    parser.add_argument("arxiv_id", help="ArXiv paper ID (e.g., 2510.08859)")
    parser.add_argument("attack_name", help="Attack name (with or without _gen suffix)")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Repository root directory (default: auto-detect)",
    )
    parser.add_argument(
        "--claude-bin",
        default=os.environ.get("CLAUDE_CODE_BIN", "claude"),
        help="Claude Code CLI binary (default: claude or CLAUDE_CODE_BIN)",
    )
    parser.add_argument(
        "--claude-flags",
        default=os.environ.get("CLAUDE_CODE_FLAGS", ""),
        help="Additional Claude CLI flags (space-separated or CLAUDE_CODE_FLAGS)",
    )
    parser.add_argument(
        "--claude-model",
        default=os.environ.get("CLAUDE_CODE_MODEL"),
        help="Claude model name (optional, or CLAUDE_CODE_MODEL)",
    )
    parser.add_argument(
        "--prompt-flag",
        default=os.environ.get("CLAUDE_CODE_PROMPT_FLAG", "-p"),
        help="Prompt flag for Claude CLI (default: -p). Use empty string to disable.",
    )
    parser.add_argument(
        "--prompt-stdin",
        action="store_true",
        help="Send prompt via stdin instead of using the prompt flag",
    )
    parser.add_argument(
        "--permission-mode",
        default=os.environ.get("CLAUDE_PERMISSION_MODE", "acceptEdits"),
        help="Claude permission mode (default: acceptEdits or CLAUDE_PERMISSION_MODE)",
    )
    parser.add_argument(
        "--dangerously-skip-permissions",
        action="store_true",
        help="Bypass all Claude permission checks",
    )
    parser.add_argument(
        "--skip-test",
        action="store_true",
        help="Skip running the paper test script after refinement",
    )
    parser.add_argument(
        "--max-refine-attempts",
        type=int,
        default=int(os.environ.get("MAX_REFINE_ATTEMPTS", "3")),
        help="Max refine/test attempts before failing (default: 3)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing implementation_gap_notes.md if present",
    )
    parser.add_argument(
        "--extra-agent",
        action="store_true",
        help="Use extra_agent mode: create extra_agent folder, use _improved suffix",
    )

    args = parser.parse_args()

    prompt_flag = args.prompt_flag.strip() if args.prompt_flag is not None else None
    if prompt_flag == "":
        prompt_flag = None

    config = ImplementationGapWorkflowConfig(
        arxiv_id=args.arxiv_id,
        attack_name=args.attack_name,
        repo_root=args.repo_root,
        claude_bin=args.claude_bin,
        claude_flags=args.claude_flags.split() if args.claude_flags else [],
        claude_model=args.claude_model,
        prompt_flag=prompt_flag,
        prompt_stdin=args.prompt_stdin,
        permission_mode=args.permission_mode,
        dangerously_skip_permissions=args.dangerously_skip_permissions,
        force=args.force,
        run_test=not args.skip_test,
        max_refine_attempts=args.max_refine_attempts,
        use_extra_agent=args.extra_agent,
    )

    workflow = ImplementationGapWorkflow(config)
    workflow.run()


if __name__ == "__main__":
    main()
