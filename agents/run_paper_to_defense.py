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
  %(prog)s 2501.01830 --defense-model opus --audit-model gpt-5.1
  %(prog)s 2501.01830 --cursor-agent-bin /path/to/cursor-agent

Environment Variables:
  MAX_LOOPS            Maximum number of iterations (default: 5)
  CURSOR_AGENT_BIN     Path to cursor-agent binary (default: cursor-agent)
  CURSOR_AGENT_FLAGS   Additional flags for cursor-agent
  DEFENSE_MODEL        Model for defense implementation (default: sonnet-4.5)
  PLANNER_MODEL        Model for implementation planning (default: gpt-5.1)
  AUDIT_MODEL          Model for auditing (default: gpt-5.1)
  USE_PROXYCHAINS      Whether to use proxychains4 (default: true)
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
        "--cursor-agent-bin",
        default=os.environ.get("CURSOR_AGENT_BIN", "cursor-agent"),
        help="Path to cursor-agent binary (default: cursor-agent)"
    )

    parser.add_argument(
        "--cursor-agent-flags",
        default=os.environ.get("CURSOR_AGENT_FLAGS", ""),
        help="Additional flags for cursor-agent (space-separated)"
    )

    parser.add_argument(
        "--defense-model",
        default=os.environ.get("DEFENSE_MODEL", "sonnet-4.5"),
        help="Model for defense implementation (default: sonnet-4.5)"
    )

    parser.add_argument(
        "--planner-model",
        default=os.environ.get("PLANNER_MODEL", "gemini-3-pro"),
        help="Model for implementation planning (default: gemini-3-pro)"
    )

    parser.add_argument(
        "--audit-model",
        default=os.environ.get("AUDIT_MODEL", "gpt-5.1-codex-max"),
        help="Model for auditing (default: gpt-5.1-codex-max)"
    )

    parser.add_argument(
        "--no-proxychains",
        action="store_true",
        help="Disable proxychains4 (enabled by default)"
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
        cursor_agent_bin=args.cursor_agent_bin,
        cursor_agent_flags=args.cursor_agent_flags.split() if args.cursor_agent_flags else [],
        defense_model=args.defense_model,
        planner_model=args.planner_model,
        audit_model=args.audit_model,
        use_proxychains=not args.no_proxychains
    )

    print("=" * 60)
    print("PAPER-TO-DEFENSE WORKFLOW CONFIGURATION")
    print("=" * 60)
    print(f"Paper ID:        {config.arxiv_id}")
    print(f"Repo Root:       {config.repo_root}")
    print(f"Max Loops:       {config.max_loops}")
    print(f"Defense Model:   {config.defense_model}")
    print(f"Planner Model:   {config.planner_model}")
    print(f"Audit Model:     {config.audit_model}")
    print(f"Cursor Binary:   {config.cursor_agent_bin}")
    print(f"Use Proxychains: {config.use_proxychains}")
    if config.cursor_agent_flags:
        print(f"Extra Flags:     {' '.join(config.cursor_agent_flags)}")
    print("=" * 60)
    print()

    workflow = PaperToDefenseWorkflow(config)
    workflow.run()


if __name__ == "__main__":
    main()
