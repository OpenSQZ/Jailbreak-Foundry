"""
Cost tracking for LLM usage across attacks.

This module provides thread-safe cost tracking for monitoring token usage
across all LLM calls during an attack, including both attack generation
and victim model queries.
"""

import threading
from typing import Dict, Any, Optional
from collections import defaultdict


class CostTracker:
    """
    Thread-safe tracker for LLM usage costs across an entire attack.

    Tracks token usage by model name and provides aggregated statistics.
    Designed to be passed to LLM instances and accumulate usage from
    all query calls during an attack lifecycle.
    """

    def __init__(self):
        """Initialize empty cost tracker with thread-safe data structures."""
        # Use defaultdict to automatically initialize model entries
        self._costs = defaultdict(lambda: {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "reasoning_tokens": 0,
            "query_count": 0
        })
        self._lock = threading.Lock()

    def add_usage(self, model_name: str, usage: Dict[str, int]) -> None:
        """
        Add token usage for a specific model in a thread-safe manner.

        Args:
            model_name: Name/identifier of the model
            usage: Dictionary containing token counts with keys:
                - prompt_tokens: Input tokens
                - completion_tokens: Output tokens
                - total_tokens: Total tokens
                - reasoning_tokens: Reasoning tokens (optional)
        """
        with self._lock:
            model_costs = self._costs[model_name]
            model_costs["prompt_tokens"] += usage.get("prompt_tokens", 0)
            model_costs["completion_tokens"] += usage.get("completion_tokens", 0)
            model_costs["total_tokens"] += usage.get("total_tokens", 0)
            model_costs["reasoning_tokens"] += usage.get("reasoning_tokens", 0)
            model_costs["query_count"] += 1

    def get_model_costs(self, model_name: str) -> Dict[str, int]:
        """
        Get cost breakdown for a specific model.

        Args:
            model_name: Name of the model to get costs for

        Returns:
            Dictionary with token counts and query count for the model
        """
        with self._lock:
            return dict(self._costs[model_name])

    def get_all_model_costs(self) -> Dict[str, Dict[str, int]]:
        """
        Get cost breakdown for all models.

        Returns:
            Dictionary mapping model names to their cost breakdowns
        """
        with self._lock:
            return {model: dict(costs) for model, costs in self._costs.items()}

    def get_total_costs(self) -> Dict[str, int]:
        """
        Get aggregated costs across all models.

        Returns:
            Dictionary with total token counts and total query count
        """
        with self._lock:
            totals = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
                "reasoning_tokens": 0,
                "query_count": 0,
                "model_count": len(self._costs)
            }

            for model_costs in self._costs.values():
                totals["prompt_tokens"] += model_costs["prompt_tokens"]
                totals["completion_tokens"] += model_costs["completion_tokens"]
                totals["total_tokens"] += model_costs["total_tokens"]
                totals["reasoning_tokens"] += model_costs["reasoning_tokens"]
                totals["query_count"] += model_costs["query_count"]

            return totals

    def get_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive cost summary including per-model and total costs.

        Returns:
            Dictionary with complete cost breakdown:
            - by_model: Per-model cost breakdowns
            - totals: Aggregated costs across all models
        """
        return {
            "by_model": self.get_all_model_costs(),
            "totals": self.get_total_costs()
        }

    def reset(self) -> None:
        """Reset all tracked costs to zero."""
        with self._lock:
            self._costs.clear()

    def __str__(self) -> str:
        """String representation showing total costs."""
        totals = self.get_total_costs()
        return (f"CostTracker(models={totals['model_count']}, "
                f"queries={totals['query_count']}, "
                f"total_tokens={totals['total_tokens']})")