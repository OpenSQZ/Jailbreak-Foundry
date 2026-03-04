#!/usr/bin/env python3
"""Test that CostTracker works correctly with ThreadPoolExecutor and monkey-patch."""

import sys
sys.path.insert(0, '/root/jbfoundry/src')

# Import the framework which applies the monkey-patch
import jbfoundry
from jbfoundry.cost_tracker import CostTracker

from contextvars import ContextVar
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Create a context variable for cost tracker (simulating attack context)
cost_tracker_var = ContextVar('cost_tracker', default=None)

def simulate_llm_call(model_name: str, call_id: int):
    """Simulate an LLM call that tracks costs."""
    # Get cost tracker from context (like LLMLiteLLM.query does)
    tracker = cost_tracker_var.get()

    if tracker is None:
        return f"Call {call_id}: No tracker in context!"

    # Simulate some token usage
    usage = {
        "prompt_tokens": random.randint(10, 100),
        "completion_tokens": random.randint(50, 200),
        "total_tokens": 0,  # Will be calculated
        "reasoning_tokens": random.randint(0, 50)
    }
    usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

    # Add to tracker (thread-safe)
    tracker.add_usage(model_name, usage)

    return f"Call {call_id}: Added {usage['total_tokens']} tokens"

def test_cost_tracker_with_threads():
    """Test CostTracker with monkey-patched ThreadPoolExecutor."""
    # Create a cost tracker
    tracker = CostTracker()

    # Set it in context
    cost_tracker_var.set(tracker)

    print(f"Initial tracker: {tracker}")

    # Simulate parallel LLM calls (like llm_virus does)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []

        # Submit 20 tasks across 3 different models
        for i in range(20):
            model = f"model_{i % 3}"
            futures.append(executor.submit(simulate_llm_call, model, i))

        print("\nSimulating parallel LLM calls:")
        for future in as_completed(futures):
            result = future.result()
            print(f"  {result}")
            if "No tracker" in result:
                print("  ❌ FAILED: Context was not propagated!")
                return False

    # Check final costs
    print(f"\nFinal tracker: {tracker}")
    print(f"\nCost summary:")
    summary = tracker.get_summary()

    for model, costs in summary["by_model"].items():
        print(f"  {model}: {costs['query_count']} calls, {costs['total_tokens']} tokens")

    print(f"\nTotal: {summary['totals']['query_count']} calls, {summary['totals']['total_tokens']} tokens")

    # Verify all calls were tracked
    if summary['totals']['query_count'] == 20:
        print("\n✅ All 20 calls were tracked successfully!")
        return True
    else:
        print(f"\n❌ Only {summary['totals']['query_count']} out of 20 calls were tracked!")
        return False

if __name__ == "__main__":
    print("=== Testing CostTracker with Monkey-Patched ThreadPoolExecutor ===\n")
    success = test_cost_tracker_with_threads()

    if success:
        print("\n✅ Cost tracking works correctly with multi-threading!")
        sys.exit(0)
    else:
        print("\n❌ Cost tracking failed in multi-threaded environment!")
        sys.exit(1)
