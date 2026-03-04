#!/usr/bin/env python3
"""
Generic checkpoint/resume system for workflow.

Philosophy: Save minimal state (iteration, step_name, attack_name) to checkpoint.json.
Resume from the EXACT point of failure by loading from checkpoint file.
No log file parsing - checkpoint file is the single source of truth.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional


class CheckpointManager:
    """
    Manages workflow checkpoints using a single checkpoint.json file.

    Key principle: Save minimal state after each step completion.
    Checkpoint file is the single source of truth for resume state.
    """

    def __init__(self, checkpoint_dir: Path):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory containing step logs
        """
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_file = checkpoint_dir / "checkpoint.json"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def save_checkpoint(
        self,
        iteration: int,
        step_name: str,
        attack_name: Optional[str] = None
    ) -> None:
        """
        Save minimal checkpoint state to file.

        Args:
            iteration: Current iteration number
            step_name: Current step name (e.g., "attack", "auditor")
            attack_name: Attack name (if available)
        """
        checkpoint_data = {
            "iteration": iteration,
            "step_name": step_name,
            "attack_name": attack_name
        }
        with open(self.checkpoint_file, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)

    def get_last_checkpoint(self) -> Optional[Dict[str, Any]]:
        """
        Get last completed step from checkpoint file.

        The checkpoint indicates the last COMPLETED step, not the next step to run.

        Returns:
            Dict with {iteration, step_name, attack_name} of last completed step,
            or None if no checkpoint exists (fresh start)
        """
        if not self.checkpoint_file.exists():
            return None

        try:
            with open(self.checkpoint_file, 'r') as f:
                data = json.load(f)
                return data
        except (json.JSONDecodeError, KeyError):
            return None

    def clear(self) -> None:
        """Clear checkpoint indication (workflow completed successfully)."""
        # Remove checkpoint file
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()

        # Create completion marker
        completion_marker = self.checkpoint_dir / ".completed"
        completion_marker.touch()
