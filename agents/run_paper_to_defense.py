#!/usr/bin/env python3
"""
Main entry point for paper-to-defense workflow.
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.workflows.defense import PaperToDefenseWorkflow, DefenseWorkflowConfig


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run paper-to-defense implementation and auditing workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 2501.01830
  %(prog)s 2501.01830 --max-loops 5
  %(prog)s 2501.01830 --defense-model gpt-5.5 --audit-model gpt-5.5

Environment Variables:
  MAX_LOOPS              Maximum number of iterations (default: 5)
  PAPER_SOURCE           Paper source for planning: pdf or ocr (default: pdf)
  PLANNER_AGENT          Agent backend for planning (default: codex)
  DEFENSE_AGENT          Agent backend for defense implementation (default: codex)
  AUDIT_AGENT            Agent backend for auditing (default: codex)
  DEFENSE_MODEL          Model for defense implementation (default: gpt-5.5)
  PLANNER_MODEL          Model for implementation planning (default: gpt-5.5)
  AUDIT_MODEL            Model for auditing (default: gpt-5.5)
  CLAUDE_CODE_BIN        Path to Claude Code binary (default: claude)
  CLAUDE_CODE_FLAGS      Additional flags for Claude Code CLI
  CODEX_BIN              Path to Codex binary (default: codex)
  CODEX_FLAGS            Additional flags for Codex CLI
        """
    )

    parser.add_argument(
        "arxiv_id",
        help="ArXiv paper ID (e.g., 2501.01830)"
    )

    parser.add_argument(
        "--max-loops",
        type=int,
        default=int(os.environ.get("MAX_LOOPS", "5")),
        help="Maximum number of iterations (default: 5 or MAX_LOOPS env var)"
    )

    parser.add_argument(
        "--planner-agent",
        default=os.environ.get("PLANNER_AGENT", "codex"),
        help="Agent backend for planning (default: codex)"
    )

    parser.add_argument(
        "--defense-agent",
        default=os.environ.get("DEFENSE_AGENT", "codex"),
        help="Agent backend for defense implementation (default: codex)"
    )

    parser.add_argument(
        "--audit-agent",
        default=os.environ.get("AUDIT_AGENT", "codex"),
        help="Agent backend for auditing (default: codex)"
    )

    parser.add_argument(
        "--planner-model",
        default=os.environ.get("PLANNER_MODEL", "gpt-5.5"),
        help="Model for implementation planning (default: gpt-5.5)"
    )
    
    parser.add_argument(
        "--defense-model",
        default=os.environ.get("DEFENSE_MODEL", "gpt-5.5"),
        help="Model for defense implementation (default: gpt-5.5)"
    )

    parser.add_argument(
        "--audit-model",
        default=os.environ.get("AUDIT_MODEL", "gpt-5.5"),
        help="Model for auditing (default: gpt-5.5)"
    )
    parser.add_argument(
        "--paper-source",
        choices=["pdf", "ocr"],
        default=os.environ.get("PAPER_SOURCE", "pdf"),
        help="Planner paper source: pdf skips OCR; ocr creates/uses paper markdown (default: pdf)"
    )

    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).parent.parent,
        help="Repository root directory (default: auto-detect)"
    )

    args = parser.parse_args()

    config = DefenseWorkflowConfig(
        arxiv_id=args.arxiv_id,
        repo_root=args.repo_root,
        max_loops=args.max_loops,
        planner_agent=args.planner_agent,
        defense_agent=args.defense_agent,
        audit_agent=args.audit_agent,
        defense_model=args.defense_model,
        planner_model=args.planner_model,
        audit_model=args.audit_model,
        paper_source=args.paper_source,
    )

    print("=" * 60)
    print("PAPER-TO-DEFENSE WORKFLOW CONFIGURATION")
    print("=" * 60)
    print(f"Paper ID:        {config.arxiv_id}")
    print(f"Repo Root:       {config.repo_root}")
    print(f"Max Loops:       {config.max_loops}")
    print(f"Planner:         {config.planner_agent} / {config.planner_model}")
    print(f"Paper Source:    {config.paper_source}")
    print(f"Defense:         {config.defense_agent} / {config.defense_model}")
    print(f"Audit:           {config.audit_agent} / {config.audit_model}")
    print("=" * 60)
    print()

    workflow = PaperToDefenseWorkflow(config)
    workflow.run()


if __name__ == "__main__":
    main()
