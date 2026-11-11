#!/usr/bin/env python3
"""
Main entry point for paper-to-attack workflow.

This script orchestrates the full workflow from paper to attack implementation
with iterative refinement based on audit feedback.

Usage:
    python agents/run_paper_to_attack.py <arxiv_id> [options]

Example:
    python agents/run_paper_to_attack.py 2501.01830
    python agents/run_paper_to_attack.py 2501.01830 --max-loops 5
"""

import argparse
import os
import sys
from pathlib import Path

# Add parent directory to path to allow 'agents' to be a package
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.utils.paper_preprocessor import _load_dotenv
from agents.workflows.attack import PaperToAttackWorkflow, AttackWorkflowConfig

_load_dotenv(Path(__file__).resolve().parent.parent / ".env")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run paper-to-attack implementation and auditing workflow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s 2501.01830
  %(prog)s 2501.01830 --max-loops 5
  %(prog)s 2501.01830 --attack-model gpt-5.6-sol-high

Environment Variables:
  MAX_LOOPS              Maximum number of iterations (default: 5)
  PAPER_SOURCE           Paper source for planning: pdf or ocr (default: pdf)
  PLANNER_AGENT          Agent backend for planning (default: cursor)
  ATTACK_AGENT           Agent backend for attack implementation (default: cursor)
  AUDIT_AGENT            Agent backend for auditing (default: cursor)
  ATTACK_MODEL           Model for attack implementation (default: gpt-5.3-codex-high)
  PLANNER_MODEL          Model for implementation planning (default: gpt-5.3-codex-high)
  AUDIT_MODEL            Model for auditing (default: gpt-5.3-codex-high)
  CURSOR_API_KEY         Cursor CLI auth (read from .env if not exported)
  CURSOR_AGENT_BIN       Path to Cursor CLI binary (default: cursor-agent)
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
        default=os.environ.get("PLANNER_AGENT", "cursor"),
        help="Agent backend for planning (default: cursor)"
    )

    parser.add_argument(
        "--attack-agent",
        default=os.environ.get("ATTACK_AGENT", "cursor"),
        help="Agent backend for attack implementation (default: cursor)"
    )

    parser.add_argument(
        "--audit-agent",
        default=os.environ.get("AUDIT_AGENT", "cursor"),
        help="Agent backend for auditing (default: cursor)"
    )

    parser.add_argument(
        "--planner-model",
        default=os.environ.get("PLANNER_MODEL", "gpt-5.3-codex-high"),
        help="Model for implementation planning (default: gpt-5.3-codex-high)"
    )

    parser.add_argument(
        "--attack-model",
        default=os.environ.get("ATTACK_MODEL", "gpt-5.3-codex-high"),
        help="Model for attack implementation (default: gpt-5.3-codex-high)"
    )

    parser.add_argument(
        "--audit-model",
        default=os.environ.get("AUDIT_MODEL", "gpt-5.3-codex-high"),
        help="Model for auditing (default: gpt-5.3-codex-high)"
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

    parser.add_argument(
        "--per-query-timeout",
        type=int,
        default=int(os.environ.get("PER_QUERY_TIMEOUT", "0")),
        help="Maximum time (in seconds) per attack query during test execution (default: 0 - no timeout). "
             "NOTE: Not recommended for implementation phase. Timeouts should be applied during testing, not implementation."
    )

    args = parser.parse_args()

    # Build configuration
    config = AttackWorkflowConfig(
        arxiv_id=args.arxiv_id,
        repo_root=args.repo_root,
        max_loops=args.max_loops,
        planner_agent=args.planner_agent,
        attack_agent=args.attack_agent,
        audit_agent=args.audit_agent,
        attack_model=args.attack_model,
        planner_model=args.planner_model,
        audit_model=args.audit_model,
        paper_source=args.paper_source,
        per_query_timeout=args.per_query_timeout
    )

    # Print configuration
    print("="*60)
    print("PAPER-TO-ATTACK WORKFLOW CONFIGURATION")
    print("="*60)
    print(f"Paper ID:        {config.arxiv_id}")
    print(f"Repo Root:       {config.repo_root}")
    print(f"Max Loops:       {config.max_loops}")
    print(f"Planner:         {config.planner_agent} / {config.planner_model}")
    print(f"Paper Source:    {config.paper_source}")
    print(f"Attack:          {config.attack_agent} / {config.attack_model}")
    print(f"Audit:           {config.audit_agent} / {config.audit_model}")
    if config.per_query_timeout > 0:
        print(f"Query Timeout:   {config.per_query_timeout}s")
    print("="*60)
    print()

    # Create and run workflow
    workflow = PaperToAttackWorkflow(config)
    workflow.run()


if __name__ == "__main__":
    main()
