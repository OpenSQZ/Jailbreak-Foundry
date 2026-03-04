#!/usr/bin/env python3
"""
Universal JBFoundry Attack Script with Modular Architecture

This script provides a unified interface for running various jailbreak attacks
using the modular attack system with auto-discovery capabilities.
"""

import os
import sys
import json
import random
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import jbfoundry as jbf
from jbfoundry.utils.logging import configure_logging

logger = logging.getLogger(__name__)

# Try to import the modern attack system
try:
    from jbfoundry.attacks.registry import registry
    from jbfoundry.attacks.factory import AttackFactory
    create_attack = AttackFactory.create_attack
    MODERN_SYSTEM_AVAILABLE = True
except ImportError as e:
    MODERN_SYSTEM_AVAILABLE = False
    logger.warning(f"Modern attack system not available: {e}")


def create_argument_parser():
    """Create context-aware argument parser that only loads relevant attack parameters."""
    try:
        from jbfoundry.runners.utils.dynamic_args_parser import parse_args_with_context
        # Use the new context-aware parsing system
        return parse_args_with_context()
    except ImportError as e:
        logger.error(f"Failed to import context-aware parser: {e}")
        exit(1)




def setup_attack(args, attack_name=None):
    """Set up a specific attack using modular system."""
    target_attack = attack_name or args.attack_name
    
    if not target_attack:
        raise ValueError("No attack specified")
    
    # Try modern system first
    if MODERN_SYSTEM_AVAILABLE:
        try:
            attack = create_attack(target_attack, args=args)
            
            # Get attack metadata
            attack_class = registry.get_attack(target_attack)
            config = attack_class.get_config()
            
            attack_meta = {
                "name": target_attack,
                "paper": config.get("paper", "Unknown"),
                "system": "modern",
                "config": config
            }
            
            return attack, attack_meta
            
        except ValueError as e:
            logger.error(f"Attack {target_attack} not found in modern system: {e}")
    
    # Attack not found in modern system
    available_attacks = []
    if MODERN_SYSTEM_AVAILABLE:
        available_attacks.extend(list(registry._attack_metadata.keys()))
    
    raise ValueError(f"Unknown attack: {target_attack}. Available: {available_attacks}")


def setup_model(args):
    """Set up the model based on provider."""
    from jbfoundry.llm.litellm import LLMLiteLLM

    try:
        return LLMLiteLLM.from_config(
            model_name=args.model,
            provider=args.provider,
            api_key=args.api_key,
            api_base=args.api_base,
        )
    except Exception as e:
        raise ValueError(f"Failed to set up model for provider {args.provider}: {e}")


def setup_evaluator(args):
    """Set up the evaluator with automatic dataset-specific detection."""
    from jbfoundry.evaluation import LLMChatEvaluator

    dataset_name = args.dataset.lower()

    # GSM8K dataset detection (exact matches)
    if dataset_name in ['gsm8k', 'gsm8k-evil']:
        try:
            evaluator = jbf.JailbreakEvaluator.from_preset("GSM8K-Hybrid")
            evaluation_info = {
                "method": "GSM8K-Hybrid",
                "model": "Auto-detected for GSM8K",
                "provider": "pattern_matching_with_llm_fallback",
                "criteria": ["numerical_correctness", "refusal_detection"],
                "dataset_type": "gsm8k",
                "dataset_variant": dataset_name
            }
            logger.debug(f"Auto-detected GSM8K dataset ({dataset_name}): using GSM8K-Hybrid evaluator")
            return evaluator, evaluation_info
        except (ValueError, ImportError) as e:
            logger.warning(f"GSM8K evaluator not available ({e}), falling back to generic evaluator")
    
    # WMDP dataset detection (starts with 'wmdp-')
    elif dataset_name.startswith('wmdp-'):
        # Extract WMDP domain (bio, chem, cyber)
        wmdp_domain = dataset_name.split('-')[1] if '-' in dataset_name else 'generic'
        
        try:
            evaluator = jbf.JailbreakEvaluator.from_preset("WMDP-Hybrid")
            evaluation_info = {
                "method": "WMDP-Hybrid",
                "model": "Auto-detected for WMDP",
                "provider": "domain_specific_evaluation",
                "criteria": ["domain_correctness", "refusal_detection"],
                "dataset_type": "wmdp",
                "dataset_variant": dataset_name,
                "wmdp_domain": wmdp_domain
            }
            logger.debug(f"Auto-detected WMDP dataset ({dataset_name}): using WMDP-Hybrid evaluator")
            return evaluator, evaluation_info
        except (ValueError, ImportError) as e:
            logger.warning(f"WMDP evaluator not available ({e}), falling back to generic evaluator")
    
    # Fall back to generic jailbreak evaluation for other datasets
    eval_provider = getattr(args, 'eval_provider', 'openai')
    eval_model = getattr(args, 'eval_model', 'gpt-4o')

    # Create unified LLM evaluator that works with any provider
    evaluator = LLMChatEvaluator(
        model_name=eval_model,
        provider=eval_provider
    )

    evaluation_info = {
        "method": "LLMChat",
        "model": eval_model,
        "provider": eval_provider,
        "criteria": ["harmfulness", "instruction_following"],
        "dataset_type": "generic"
    }

    logger.info(f"Using LLM evaluator ({eval_provider}/{eval_model}) for dataset: {dataset_name}")

    return evaluator, evaluation_info


def load_dataset(args):
    """Load the dataset for evaluation."""
    # Determine dataset name to load
    dataset_name = "jbb-harmful" if args.dataset == "harmful" else args.dataset
    
    # Load dataset
    try:
        dataset = jbf.read_dataset(dataset_name)
    except:
        raise ValueError(f"Unknown dataset: {args.dataset}")
    
    # Apply sampling if needed (only if not using all samples)
    if not args.all_samples and args.samples and args.samples < len(dataset):
        dataset = dataset.sample(args.samples, args.seed)
    
    return dataset


def get_results_file_path(args, attack_meta):
    """Get the standardized results file path."""
    if hasattr(args, 'output') and args.output:
        return args.output
    
    attack_name = attack_meta.get("name", "unknown")
    output_file = f"{args.output_dir}/results_{attack_name}.json"
    
    return output_file


def load_existing_results(output_file, retry_invalid=True, retry_failed=False):
    """Load existing results if the file exists.

    Args:
        output_file: Path to the results file
        retry_invalid: Whether to retry queries with jailbroken=None (default: True)
        retry_failed: Whether to retry queries with jailbroken=False (default: False)
    """
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r') as f:
                data = json.load(f)
                results = data.get("results", [])

                # Count query states
                success_count = sum(1 for r in results if r["jailbroken"] is True)
                failed_count = sum(1 for r in results if r["jailbroken"] is False)
                invalid_count = sum(1 for r in results if r["jailbroken"] is None)

                # Always skip successful queries
                completed_ids = {r["example_id"] for r in results if r["jailbroken"] is True}

                # Conditionally skip failed and invalid queries
                if not retry_failed:
                    completed_ids.update(r["example_id"] for r in results if r["jailbroken"] is False)
                if not retry_invalid:
                    completed_ids.update(r["example_id"] for r in results if r["jailbroken"] is None)

                print(f"📁 Found: {success_count} successful, {failed_count} failed, {invalid_count} invalid")

                # Print what we're doing
                skip_count = success_count + (failed_count if not retry_failed else 0) + (invalid_count if not retry_invalid else 0)
                retry_count = (failed_count if retry_failed else 0) + (invalid_count if retry_invalid else 0)
                print(f"✅ Skipping: {skip_count} queries")
                print(f"🔄 Will retry: {retry_count} existing + unrun queries")

                return data, completed_ids
        except Exception as e:
            logger.warning(f"Could not load existing results: {e}")

    return None, set()


def initialize_results_file(args, attack_meta):
    """Initialize the results file with metadata and handle resume functionality."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = get_results_file_path(args, attack_meta)

    # Check if restart is disabled (i.e., resume mode)
    if not args.restart:
        retry_invalid = getattr(args, 'retry_invalid', True)
        retry_failed = getattr(args, 'retry_failed', False)

        existing_data, completed_ids = load_existing_results(output_file, retry_invalid=retry_invalid, retry_failed=retry_failed)
        if existing_data:
            # Update metadata with current timestamp but keep existing results
            existing_data["metadata"]["timestamp"] = timestamp
            existing_data["metadata"]["args"] = vars(args)

            with open(output_file, 'w') as f:
                json.dump(existing_data, f, indent=2)

            print(f"📁 Resuming from existing file: {output_file}")
            return output_file, completed_ids
    else:
        # Warn if user specified retry flags with --restart
        if getattr(args, 'retry_failed', False) or not getattr(args, 'retry_invalid', True):
            logger.warning("--retry-failed and --retry-invalid have no effect when --restart is used")                                                    

    # Create new file (or overwrite if resume is disabled)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Initialize file with metadata
    initial_data = {
        "metadata": {
            "timestamp": timestamp,
            "model": args.model,
            "provider": args.provider,
            "dataset": args.dataset,
            "attack": attack_meta,
            "system_info": {
                "modular_system_available": MODERN_SYSTEM_AVAILABLE,
                "attack_system_used": attack_meta.get("system", "modern")
            },
            "args": vars(args)
        },
        "results": []
    }
    
    with open(output_file, 'w') as f:
        json.dump(initial_data, f, indent=2)
    
    print(f"🆕 Created new results file: {output_file}")
    return output_file, set()


def process_single_example(args_tuple):
    """Process a single example (extracted for parallel processing)."""
    from jbfoundry.cost_tracker import CostTracker

    i, example, llm, attack, evaluator, attack_meta, args, output_file, completed_ids = args_tuple

    # Skip if already completed
    if i in completed_ids:
        logger.info(f"Skipping already completed example {i+1}")
        return None

    logger.info(f"Running {attack_meta['name']} attack on {args.dataset} example {i+1} via {args.provider}/{args.model}")
    
    attempts_per_query = max(1, int(getattr(args, "attempts_per_query", 1)))
    success_threshold = getattr(args, "attempts_success_threshold", None)
    if success_threshold is None:
        success_threshold = attempts_per_query

    aggregated_cost = {
        "by_model": {},
        "totals": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "reasoning_tokens": 0}
    }
    attempts = []
    success_count = 0
    valid_attempts = 0

    for attempt_index in range(1, attempts_per_query + 1):
        # Create cost tracker for this attempt
        cost_tracker = CostTracker()

        try:
            jailbroken_prompt = attack.generate_attack(
                prompt=example["goal"],
                goal=example["goal"],
                target=example.get("target", ""),
                attempt_index=attempt_index,
                attempts_per_query=attempts_per_query,
                attempt_success_threshold=success_threshold,
                cost_tracker=cost_tracker
            )
        except Exception as e:
            logger.error(f"Error generating attack for example {i} (attempt {attempt_index}): {e}")
            jailbroken_prompt = None
            response = None
            success = None
        else:
            try:
                response = llm.query(
                    jailbroken_prompt,
                    defense=args.defense,
                    cost_tracker=cost_tracker
                )
            except Exception as e:
                logger.error(f"Error querying model for example {i} (attempt {attempt_index}): {e}")
                response = None
                success = None
            else:
                eval_input = dict(example)
                eval_input["question"] = example["goal"]
                eval_input["answer"] = response

                try:
                    success = evaluator(eval_input)
                except Exception as e:
                    logger.error(f"Error evaluating response for example {i} (attempt {attempt_index}): {e}")
                    success = None

        if success is not None:
            valid_attempts += 1
        if success:
            success_count += 1

        cost_summary = cost_tracker.get_summary() if cost_tracker else None
        if cost_summary:
            for model_name, model_costs in cost_summary.get("by_model", {}).items():
                if model_name not in aggregated_cost["by_model"]:
                    aggregated_cost["by_model"][model_name] = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                        "reasoning_tokens": 0
                    }
                aggregated_cost["by_model"][model_name]["prompt_tokens"] += model_costs.get("prompt_tokens", 0)
                aggregated_cost["by_model"][model_name]["completion_tokens"] += model_costs.get("completion_tokens", 0)
                aggregated_cost["by_model"][model_name]["total_tokens"] += model_costs.get("total_tokens", 0)
                aggregated_cost["by_model"][model_name]["reasoning_tokens"] += model_costs.get("reasoning_tokens", 0)

            totals = cost_summary.get("totals", {})
            aggregated_cost["totals"]["prompt_tokens"] += totals.get("prompt_tokens", 0)
            aggregated_cost["totals"]["completion_tokens"] += totals.get("completion_tokens", 0)
            aggregated_cost["totals"]["total_tokens"] += totals.get("total_tokens", 0)
            aggregated_cost["totals"]["reasoning_tokens"] += totals.get("reasoning_tokens", 0)

        attempts.append({
            "attempt_index": attempt_index,
            "attack_prompt": jailbroken_prompt,
            "model_response": response,
            "jailbroken": success,
            "usage": response.get_usage() if response else None,
            "reasoning_content": response.get_reasoning_content() if response else None,
            "cost_summary": cost_summary
        })

    overall_success = None if valid_attempts == 0 else (success_count >= success_threshold)
    last_attempt = attempts[-1] if attempts else {}

    # Store result
    result = {
        "example_id": i,
        "goal": example["goal"],
        "attack_prompt": last_attempt.get("attack_prompt"),
        "model_response": last_attempt.get("model_response"),
        "jailbroken": overall_success,
        "usage": last_attempt.get("usage"),
        "reasoning_content": last_attempt.get("reasoning_content"),
        "cost_summary": aggregated_cost,
        "attempts_per_query": attempts_per_query,
        "attempt_success_threshold": success_threshold,
        "attempt_successes": success_count,
        "attempt_valid_count": valid_attempts,
        "attempts": attempts,
        # "attack_meta": attack_meta
    }

    # Save result to file immediately (upsert: replace if exists, append if not)
    import fcntl
    try:
        with open(output_file, 'r+') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            data = json.load(f)

            # Find existing result with same example_id
            existing_idx = None
            for idx, r in enumerate(data["results"]):
                if r["example_id"] == i:
                    existing_idx = idx
                    break

            # Upsert: replace if exists, append if not
            if existing_idx is not None:
                data["results"][existing_idx] = result
            else:
                data["results"].append(result)

            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    except Exception as e:
        logger.warning(f"Could not save result to file: {e}")

    if overall_success is None:
        status = "INVALID"
    else:
        status = "SUCCESS" if overall_success else "FAILED"
    logger.info(f"Example {i+1} Result: {status} ({success_count}/{attempts_per_query})")
    
    return result


def run_attack_on_dataset(llm, attack, dataset, evaluator, attack_meta, args):
    """Run the attack on the dataset and return results."""
    # Initialize output file and get completed IDs
    output_file, completed_ids = initialize_results_file(args, attack_meta)

    # Prepare arguments for parallel processing
    task_args = [
        (i, example, llm, attack, evaluator, attack_meta, args, output_file, completed_ids)
        for i, example in enumerate(dataset)
    ]

    # Process in parallel with configurable workers
    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        # Just execute, don't collect results (they're saved to file incrementally)
        executor.map(process_single_example, task_args)

    return output_file


def update_final_metadata(output_file, evaluation_info):
    """Update the results file with final metadata."""
    # Update metadata with final results
    try:
        with open(output_file, 'r+') as f:
            data = json.load(f)
           
            # Get results
            results = data["results"]
            
            # Calculate success rate
            valid_count = sum(1 for r in results if r["jailbroken"] is not None)
            invalid_count = len(results) - valid_count
            success_count = sum(1 for r in results if r["jailbroken"])
            success_rate = success_count / valid_count if valid_count > 0 else 0
            
            print(f"Attack success rate: {success_rate:.2%} ({success_count}/{valid_count})")
            
            # Update metadata
            data["metadata"]["valid_count"] = valid_count
            data["metadata"]["invalid_count"] = invalid_count
            data["metadata"]["success_rate"] = success_rate
            data["metadata"]["evaluation"] = evaluation_info
            
            # Sort results by example_id
            data["results"].sort(key=lambda x: x["example_id"])
            
            # Save updated data
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except Exception as e:
        logger.warning(f"Could not update final metadata: {e}")
    
    print(f"\nResults saved to: {output_file}")
    return output_file


def run_single_attack(args, llm, evaluator, evaluation_info, dataset, attack_name=None):
    """Run a single attack and return results."""
    # Set up attack
    attack, attack_meta = setup_attack(args, attack_name)

    print(f"\nRunning {attack_meta['name']} attack using {attack_meta['system']} system...")
    logger.info(f"Attack paper: {attack_meta.get('paper', 'unknown')}")
    
    # Run the attack
    output_file = run_attack_on_dataset(llm, attack, dataset, evaluator, attack_meta, args)
    
    # Update final metadata in the file
    update_final_metadata(output_file, evaluation_info)
    
    return output_file


def main():
    """Main function."""
    # Parse arguments using context-aware parser
    args = create_argument_parser()
    
    if args.verbose:
        configure_logging(verbose=True)

    # Set random seed
    random.seed(args.seed)

    attempts_per_query = max(1, int(getattr(args, "attempts_per_query", 1)))
    success_threshold = getattr(args, "attempts_success_threshold", None)
    if success_threshold is None:
        success_threshold = attempts_per_query
    if attempts_per_query < 1:
        raise ValueError("--attempts-per-query must be >= 1")
    if success_threshold < 1 or success_threshold > attempts_per_query:
        raise ValueError("--attempts-success-threshold must be between 1 and attempts-per-query")

    args.attempts_per_query = attempts_per_query
    args.attempts_success_threshold = success_threshold
    
    print("Universal JBFoundry Attack Script - Modular Architecture")
    print("=" * 60)
    print(f"Modular attack system available: {MODERN_SYSTEM_AVAILABLE}")
    
    # Set up model
    print("\nSetting up model...")
    llm = setup_model(args)
    
    # Set up evaluator
    print("Setting up evaluator...")
    evaluator, evaluation_info = setup_evaluator(args)
    
    # Load dataset
    print("Loading dataset...")
    dataset = load_dataset(args)
    if args.all_samples:
        print(f"Loaded all {len(dataset)} examples from {args.dataset}")
    else:
        print(f"Loaded {len(dataset)} examples from {args.dataset} (limited by --samples={args.samples})")
    
    # Run the specified attack
    if not args.attack_name:
        print("Error: --attack_name is required")
        print("Use --list_attacks to see available attacks")
        return
    
    # Run single attack
    output_file = run_single_attack(args, llm, evaluator, evaluation_info, dataset)
    print(f"\nAttack completed. Results saved to: {output_file}")


if __name__ == "__main__":
    main()
