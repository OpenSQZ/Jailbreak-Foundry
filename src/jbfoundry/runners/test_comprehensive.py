#!/usr/bin/env python3
"""
Comprehensive Attack Testing Script (Attack-Agnostic)
Tests multiple models against multiple datasets with resumeable capability
Generates comprehensive Attack Success Rate (ASR) table

Usage:
    python src/jbfoundry/runners/test_comprehensive.py --attack_name <attack> --dataset <dataset> [additional_args...]
    
Examples:
    python src/jbfoundry/runners/test_comprehensive.py --attack_name ice --dataset harmbench --all_samples --eval_model gpt-4o
    python src/jbfoundry/runners/test_comprehensive.py --attack_name many_shot --dataset jbb-harmful --samples 10 --verbose
    python src/jbfoundry/runners/test_comprehensive.py --attack_name simple_override --all_samples --eval_provider openai
    
Features:
    - Tests multiple models × multiple datasets combinations
    - Attack-agnostic: supports any attack from universal_attack.py
    - Parallel execution for faster completion
    - Resumeable progress (saved to comprehensive_results.json)
    - Real-time ASR table updates
    - Markdown report generation (final_results.md)
    - 20-hour timeout per test
    - Automatic retry on network issues
    - Forwards arbitrary arguments to universal_attack.py
"""

import json
import os
import sys
import subprocess
import time
import argparse
import fcntl
import shutil
from datetime import datetime
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed

class ComprehensiveAttackTester:
    """Attack-agnostic comprehensive testing framework"""

    @staticmethod
    def sanitize_dataset_name(dataset):
        """Sanitize dataset name for use in file paths by replacing slashes with underscores"""
        return dataset.replace('/', '_')

    # Hardcoded providers and datasets (configurable)
    PROVIDERS = [
        {
            "name": "llama-2-7b-chat",
            "model": "llama-2-7b-chat",
            "api_base": "http://10.210.22.10:30254/v1",
            "provider": "openai",
        },
        {
            "name": "llama-3-8b-instruct",
            "model": "llama-3-8b-instruct",
            "api_base": "http://10.210.22.10:30253/v1",
            "provider": "openai",
        },
        {
            "name": "gpt-3.5-turbo",
            "model": "gpt-3.5-turbo",
            "provider": "openai",
        },
        {
            "name": "gpt-4",
            "model": "gpt-4",
            "provider": "openai",
        },
        {
            "name": "gpt-5.1",
            "model": "gpt-5.1",
            "provider": "openai",
        },
        {
            "name": "gpt-4o",
            "model": "gpt-4o",
            "provider": "azure",
        },
        {
            "name": "claude-3-5-sonnet",
            "model": "claude-3-5-sonnet",
            "provider": "anthropic",
        },
        {
            "name": "claude-3-7-sonnet",
            "model": "claude-3-7-sonnet",
            "provider": "anthropic",
        },
        {
            "name": "qwen3-14b",
            "model": "qwen3-14b",
            "provider": "infini",
        },
    ]

    DATASETS = [
        "jbb-harmful", "advbench", "harmbench", "assets/jbb-harmful-behaviors-32.csv", "assets/benchmark-advbench-50.csv",
                "assets/harmful_behaviors_custom_50.csv"]

    def __init__(self, attack_name, extra_args=None, defense_name=None):
        self.attack_name = attack_name
        self.extra_args = extra_args or []
        self.defense_name = defense_name
        if self.defense_name:
            self.base_output_dir = f"results/{self.defense_name}/{attack_name}_comprehensive"
        else:
            self.base_output_dir = f"results/{attack_name}_comprehensive"
        self.results_file = os.path.join(self.base_output_dir, f"{attack_name}_comprehensive_results.json")

        # Ensure base directory exists
        os.makedirs(self.base_output_dir, exist_ok=True)

    def load_progress(self):
        """Load existing progress from JSON file with file locking"""
        try:
            with open(self.results_file, 'r+') as f:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"completed": {}}

    def save_progress(self, progress):
        """Save progress to JSON file with atomic read-merge-write operation"""
        if not os.path.exists(self.results_file):
            with open(self.results_file, 'w') as f:
                json.dump({"completed": {}}, f, indent=2)

        with open(self.results_file, 'r+') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.seek(0)
            try:
                latest_progress = json.load(f)
            except (json.JSONDecodeError, ValueError):
                latest_progress = {"completed": {}}

            if "completed" not in latest_progress:
                latest_progress["completed"] = {}

            latest_progress["completed"].update(progress["completed"])

            f.seek(0)
            f.truncate()
            json.dump(latest_progress, f, indent=2)
            f.flush()

    def delete_progress_key(self, key):
        """Delete a specific key from progress (thread-safe)"""
        if not os.path.exists(self.results_file):
            return  # Nothing to delete

        with open(self.results_file, 'r+') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.seek(0)
            try:
                data = json.load(f)
            except (json.JSONDecodeError, ValueError):
                data = {"completed": {}}

            if key in data.get("completed", {}):
                del data["completed"][key]

            f.seek(0)
            f.truncate()
            json.dump(data, f, indent=2)
            f.flush()

    def run_attack(self, provider_config, dataset, output_dir):
        """Run attack for a specific model-dataset combination"""
        print(f"🎯 Testing {self.attack_name} attack with {provider_config['name']} on {dataset}...")

        cmd = [
            "python", "src/jbfoundry/runners/universal_attack.py",
            "--attack_name", self.attack_name,
            "--model", provider_config["model"],
            "--provider", provider_config["provider"],
            "--dataset", dataset,
            "--output_dir", output_dir
        ]

        # Add provider-specific arguments
        for key in ["api_base", "api_key"]:
            if key in provider_config:
                cmd.extend([f"--{key}", provider_config[key]])

        # Add extra arguments
        cmd.extend(self.extra_args)
        
        try:
            print(f"🔥 Running command: {' '.join(cmd)}")
            print("-" * 80)
            result = subprocess.run(cmd, timeout=72000)
            return (True, "Success") if result.returncode == 0 else (False, f"Exit code: {result.returncode}")
        except subprocess.TimeoutExpired:
            return False, "Timeout after 20 hours"
        except Exception as e:
            return False, str(e)

    def extract_result(self, output_dir):
        """Extract ASR from results file by counting jailbroken results"""
        # Define EMPTY_COST outside try block so it's accessible in except block
        EMPTY_COST = { "by_model": {}, "totals": { "prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0, "total_tokens": 0 } }

        try:
            results_files = list(Path(output_dir).glob("results_*.json"))

            if not results_files:
                return {"asr": -1, "valid_count": 0, "invalid_count": 0, "aggregated_cost": EMPTY_COST, "average_cost": EMPTY_COST }

            # Get most recent results file
            results_file = max(results_files, key=lambda f: f.stat().st_mtime)

            with open(results_file, 'r') as f:
                data = json.load(f)
                all_results = data.get("results", [])
                attack_name = data.get("metadata", {}).get("attack", {}).get("name", "")
                metadata_args = data.get("metadata", {}).get("args", {}) or {}
                default_threshold = metadata_args.get("attempts_success_threshold")
                default_attempts = metadata_args.get("attempts_per_query")
                if default_threshold is None and default_attempts:
                    default_threshold = default_attempts

                # Filter valid results and aggregate cost summaries
                valid_results = []
                aggregated_cost = {"by_model": {}, "totals": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0, "reasoning_tokens": 0}}

                def compute_overall_jailbroken(result):
                    attempts = result.get("attempts") or []
                    if not attempts:
                        return result.get("jailbroken")

                    valid_attempts = sum(1 for a in attempts if a.get("jailbroken") is not None)
                    if valid_attempts == 0:
                        return None

                    threshold = result.get("attempt_success_threshold", default_threshold)
                    if threshold is None:
                        threshold = len(attempts)
                    success_count = sum(1 for a in attempts if a.get("jailbroken") is True)
                    return success_count >= threshold

                for result in all_results:
                    overall_success = compute_overall_jailbroken(result)
                    if overall_success is not None:
                        example_id = result.get("example_id", {})
                        
                        # Skip LLM-Virus attack on the first example to exclude caching costs
                        if attack_name == "llm_virus" and example_id == 0:
                            continue
                        
                        result_copy = dict(result)
                        result_copy["jailbroken"] = overall_success
                        valid_results.append(result_copy)
                        
                        # Get individual cost summary
                        individual_cost_summary = result.get("cost_summary", {})

                        # Aggregate by_model costs
                        if "by_model" in individual_cost_summary:
                            for model_name, model_costs in individual_cost_summary["by_model"].items():
                                if model_name not in aggregated_cost["by_model"]:
                                    aggregated_cost["by_model"][model_name] = {
                                        "prompt_tokens": 0,
                                        "completion_tokens": 0,
                                        "total_tokens": 0,
                                        "reasoning_tokens": 0,
                                    }

                                aggregated_cost["by_model"][model_name]["prompt_tokens"] += model_costs.get("prompt_tokens", 0)
                                aggregated_cost["by_model"][model_name]["completion_tokens"] += model_costs.get("completion_tokens", 0)
                                aggregated_cost["by_model"][model_name]["total_tokens"] += model_costs.get("total_tokens", 0)
                                aggregated_cost["by_model"][model_name]["reasoning_tokens"] += model_costs.get("reasoning_tokens", 0)

                        # Aggregate totals
                        if "totals" in individual_cost_summary:
                            totals = individual_cost_summary["totals"]
                            aggregated_cost["totals"]["prompt_tokens"] += totals.get("prompt_tokens", 0)
                            aggregated_cost["totals"]["completion_tokens"] += totals.get("completion_tokens", 0)
                            aggregated_cost["totals"]["total_tokens"] += totals.get("total_tokens", 0)
                            aggregated_cost["totals"]["reasoning_tokens"] += totals.get("reasoning_tokens", 0)

                valid_count = len(valid_results)
                invalid_count = len(all_results) - valid_count

                # Calculate ASR
                asr = sum(1 for r in valid_results if r.get("jailbroken", False)) / valid_count if valid_count > 0 else -1

                # Calculate average cost (same structure as aggregated_cost but averaged by valid_count)
                average_cost = {"by_model": {}, "totals": {}}

                if valid_count > 0:
                    # Average by_model costs (rounded to 2 decimal places for readability)
                    for model_name, model_costs in aggregated_cost["by_model"].items():
                        average_cost["by_model"][model_name] = {
                            "prompt_tokens": round(model_costs["prompt_tokens"] / valid_count, 2),
                            "completion_tokens": round(model_costs["completion_tokens"] / valid_count, 2),
                            "total_tokens": round(model_costs["total_tokens"] / valid_count, 2),
                            "reasoning_tokens": round(model_costs["reasoning_tokens"] / valid_count, 2),
                        }

                    # Average totals (rounded to 2 decimal places for readability)
                    average_cost["totals"] = {
                        "prompt_tokens": round(aggregated_cost["totals"]["prompt_tokens"] / valid_count, 2),
                        "completion_tokens": round(aggregated_cost["totals"]["completion_tokens"] / valid_count, 2),
                        "total_tokens": round(aggregated_cost["totals"]["total_tokens"] / valid_count, 2),
                        "reasoning_tokens": round(aggregated_cost["totals"]["reasoning_tokens"] / valid_count, 2),
                    }
                else:
                    # No valid results, use empty structure
                    average_cost = EMPTY_COST

                return {
                    "asr": asr,
                    "valid_count": valid_count,
                    "invalid_count": invalid_count,
                    "aggregated_cost": aggregated_cost,
                    "average_cost": average_cost,
                }

        except Exception as e:
            print(f"Warning: Could not extract ASR from {output_dir}: {e}")
            import traceback
            traceback.print_exc()
            return {"asr": -1, "valid_count": 0, "invalid_count": 0, "aggregated_cost": EMPTY_COST, "average_cost": EMPTY_COST }

    def print_progress_table(self, progress):
        """Print current progress as a table"""
        print(f"\n{'='*90}")
        print(f"{self.attack_name.upper()} Attack Progress - Attack Success Rate (ASR)")
        print("="*90)
        
        # Header
        print(f"{'Dataset':<15}", end="")
        for provider in self.PROVIDERS:
            print(f"{provider['name']:<14}", end="")
        print()
        
        print("-" * 90)
        
        # Rows
        for dataset in self.DATASETS:
            print(f"{dataset:<15}", end="")
            for provider in self.PROVIDERS:
                key = f"{provider['name']}_{self.sanitize_dataset_name(dataset)}"
                if key in progress["completed"]:
                    asr = progress["completed"][key]["asr"]
                    print(f"{asr:.1%}".ljust(14), end="")
                else:
                    print("PENDING".ljust(14), end="")
            print()
        
        print("="*90)

    def generate_markdown_report(self, progress):
        """Generate markdown report with progress table"""
        lines = [
            f"## {self.attack_name.upper()} Attack Success Rate (ASR) Results",
            "",
            "| Dataset | " + " | ".join(p["name"] for p in self.PROVIDERS) + " |",
            "|" + "---|" * (len(self.PROVIDERS) + 1)
        ]
        
        for dataset in self.DATASETS:
            row = f"| {dataset} |"
            for provider in self.PROVIDERS:
                key = f"{provider['name']}_{self.sanitize_dataset_name(dataset)}"
                if key in progress["completed"]:
                    asr = progress["completed"][key]["asr"]
                    valid_count = progress["completed"][key].get("valid_count", 0)
                    invalid_count = progress["completed"][key].get("invalid_count", 0)
                    run_count = progress["completed"][key].get("run_count", 1)
                    if invalid_count > 0:
                        row += f" {asr:.1%} ({valid_count}v/{invalid_count}i, runs={run_count}) |"
                    else:
                        row += f" {asr:.1%} (runs={run_count}) |"
                else:
                    row += " PENDING |"
            lines.append(row)
        
        return "\n".join(lines)

    def fix_progress_from_results(self):
        """Fix progress JSON by scanning existing results files"""
        print(f"🔧 Fixing progress JSON from existing results for {self.attack_name}...")
        
        progress = {"completed": {}}
        
        for provider_config in self.PROVIDERS:
            for dataset in self.DATASETS:
                combination_key = f"{provider_config['name']}_{self.sanitize_dataset_name(dataset)}"
                output_dir = os.path.join(self.base_output_dir, combination_key)
                
                if os.path.exists(output_dir):
                    result = self.extract_result(output_dir)
                    if result["asr"] > -1:
                        progress["completed"][combination_key] = {
                            "asr": result["asr"],
                            "valid_count": result["valid_count"],
                            "invalid_count": result["invalid_count"],
                            "aggregated_cost": result["aggregated_cost"],
                            "average_cost": result["average_cost"],
                            "run_count": 1,
                            "timestamp": datetime.now().isoformat(),
                            "model": provider_config["name"],
                            "provider": provider_config["provider"],
                            "dataset": dataset,
                            "attack_name": self.attack_name,
                            "fixed_from_results": True
                        }
                        print(f"✅ Found results for {combination_key}: ASR = {result['asr']:.1%}")
                    else:
                        print(f"⚠️  Found directory but no valid results for {combination_key}")
                else:
                    print(f"❌ No results found for {combination_key}")
        
        self.save_progress(progress)
        print(f"\n🎉 Updated {len(progress['completed'])} combinations in progress JSON")
        
        # Generate and save markdown report
        markdown_report = self.generate_markdown_report(progress)
        final_results_file = f"{self.base_output_dir}/final_results.md"
        with open(final_results_file, 'w') as f:
            f.write(markdown_report)
        print(f"📝 Markdown report saved to: {final_results_file}")
        
        self.print_progress_table(progress)

    def run_comprehensive_test(self, model_filter=None, dataset_filter=None, restart=False, retry_invalid=True, retry_failed=False):
        """Run comprehensive testing with optional filters"""
        # Support comma-separated model names
        if model_filter:
            model_names = [m.strip() for m in model_filter.split(',')]
            available_model_names = [p["name"] for p in self.PROVIDERS]

            # Check which models are invalid
            invalid_models = [m for m in model_names if m not in available_model_names]
            if invalid_models:
                print(f"❌ Invalid model(s): {', '.join(invalid_models)}")
                print(f"Available models: {', '.join(available_model_names)}")
                return

            providers = [p for p in self.PROVIDERS if p["name"] in model_names]
        else:
            providers = self.PROVIDERS

        datasets = [d for d in self.DATASETS if not dataset_filter or d == dataset_filter]

        if not datasets:
            print(f"❌ Dataset '{dataset_filter}' not found!")
            return

        print(f"🎯 {self.attack_name.upper()} Attack Comprehensive Testing")
        print("="*50)
        print(f"Testing {len(providers)} models × {len(datasets)} datasets")
        print(f"Total combinations: {len(providers) * len(datasets)}")
        print(f"Attack: {self.attack_name}")
        if model_filter:
            print(f"Model filter: {', '.join([p['name'] for p in providers])}")
        if dataset_filter:
            print(f"Dataset filter: {dataset_filter}")
        if restart:
            print(f"⚠️  Restart: ENABLED (will delete existing results)")
        if retry_failed:
            print(f"⚠️  Retry failed: ENABLED (will retry failed queries)")
        if not retry_invalid:
            print(f"⚠️  Retry invalid: DISABLED (will skip invalid queries)")
        if self.extra_args:
            print(f"Extra arguments: {' '.join(self.extra_args)}")
        print()

        progress = self.load_progress()
        print(f"Loaded progress: {len(progress['completed'])} completed combinations")

        # Collect pending tasks
        tasks = []
        for provider_config in providers:
            for dataset in datasets:
                combination_key = f"{provider_config['name']}_{self.sanitize_dataset_name(dataset)}"
                output_dir = os.path.join(self.base_output_dir, combination_key)

                # Check if already completed
                already_completed = combination_key in progress["completed"]

                if restart:
                    print(f"🔥 Restart: Deleting existing results for {combination_key}")
                    # Delete the output directory
                    if os.path.exists(output_dir):
                        shutil.rmtree(output_dir)
                    # Remove from progress using thread-safe deletion
                    self.delete_progress_key(combination_key)
                    already_completed = False

                if already_completed and not retry_failed and not retry_invalid:
                    # Skip if completed and not retrying anything
                    print(f"⏭️  Skipping {combination_key} (already completed)")
                    continue

                os.makedirs(output_dir, exist_ok=True)
                tasks.append((provider_config, dataset, output_dir, combination_key))
        
        if not tasks:
            print("🎉 All combinations already completed!")
            self.print_progress_table(progress)
            return
        
        print(f"🚀 Starting {len(tasks)} tasks in parallel...")
        
        # Run all tasks in parallel
        total_combinations = len(providers) * len(datasets)
        completed_count = len(progress["completed"])
        
        with ProcessPoolExecutor(max_workers=len(tasks)) as executor:
            future_to_task = {
                executor.submit(self.run_attack, provider_config, dataset, output_dir): 
                (provider_config, dataset, output_dir, combination_key)
                for provider_config, dataset, output_dir, combination_key in tasks
            }
            
            for future in as_completed(future_to_task):
                provider_config, dataset, output_dir, combination_key = future_to_task[future]
                
                try:
                    success, output = future.result()
                    
                    if success:
                        result = self.extract_result(output_dir)
                        current_progress = self.load_progress()
                        previous_runs = current_progress["completed"].get(combination_key, {}).get("run_count", 0)
                        current_progress["completed"][combination_key] = {
                            "asr": result["asr"],
                            "valid_count": result["valid_count"],
                            "invalid_count": result["invalid_count"],
                            "aggregated_cost": result["aggregated_cost"],
                            "average_cost": result["average_cost"],
                            "run_count": previous_runs + 1,
                            "timestamp": datetime.now().isoformat(),
                            "model": provider_config["name"],
                            "provider": provider_config["provider"],
                            "dataset": dataset,
                            "attack_name": self.attack_name,
                        }
                        print(f"✅ {combination_key}: ASR = {result['asr']:.1%}")
                        self.save_progress(current_progress)
                        completed_count += 1
                    else:
                        print(f"❌ {combination_key}: FAILED - {output[:100]}...")
                        print("⚠️  This test will be retried on next run.")
                    
                    print(f"Progress: {completed_count}/{total_combinations} ({completed_count/total_combinations:.1%})")
                    
                except Exception as e:
                    print(f"❌ {combination_key}: EXCEPTION - {str(e)}")
                    print("⚠️  This test will be retried on next run.")
        
        # Generate final report
        final_progress = self.load_progress()
        print(f"\n{'='*90}")
        print(f"🎉 {self.attack_name.upper()} ATTACK COMPREHENSIVE TESTING COMPLETED!")
        print("="*90)
        self.print_progress_table(final_progress)
        
        markdown_report = self.generate_markdown_report(final_progress)
        final_results_file = f"{self.base_output_dir}/final_results.md"
        with open(final_results_file, 'w') as f:
            f.write(markdown_report)
        
        print(f"\n📝 Markdown report saved to: {final_results_file}")
        print(f"Individual test results in: {self.base_output_dir}/")

def parse_args():
    """Parse command line arguments, separating known from unknown"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Attack Testing Script (Attack-Agnostic)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        allow_abbrev=False
    )
    
    parser.add_argument("--attack_name", required=True, help="Name of the attack to test")
    parser.add_argument("--defense", help="Defense name to test (optional)")
    parser.add_argument("--dataset", help="Test only this dataset")
    parser.add_argument("--model", help="Test only this model (supports comma-separated list: 'llama-2-7b-chat,gpt-4,gpt-4o')")
    parser.add_argument("--status", action="store_true", help="Only print progress table and exit")
    parser.add_argument("--fix-progress", action="store_true", help="Fix progress JSON from existing results and exit")
    parser.add_argument("--restart", action="store_true", default=False,
                       help="Restart from scratch by deleting existing results")
    parser.add_argument("--retry-invalid", action="store_true", default=True,
                       help="When resuming, retry queries with invalid/error results (jailbroken=None) (default: true)")
    parser.add_argument("--retry-failed", action="store_true", default=False,
                       help="When resuming, retry queries that failed (jailbroken=False) (also passed to universal_attack.py) (default: false)")
    parser.add_argument("--attempts-per-query", type=int, default=1,
                        help="Number of attack attempts per query (default: 1)")
    parser.add_argument("--attempts-success-threshold", type=int, default=None,
                        help="Minimum successful attempts required to count a query as successful (default: attempts-per-query)")
    
    known_args, unknown_args = parser.parse_known_args()
    return known_args, unknown_args

def main():
    """Main function"""
    args, extra_args = parse_args()

    if args.attempts_per_query < 1:
        raise ValueError("--attempts-per-query must be >= 1")
    if args.attempts_success_threshold is not None:
        if args.attempts_success_threshold < 1 or args.attempts_success_threshold > args.attempts_per_query:
            raise ValueError("--attempts-success-threshold must be between 1 and attempts-per-query")

    extra_args = list(extra_args)
    extra_args.extend(["--attempts-per-query", str(args.attempts_per_query)])
    if args.attempts_success_threshold is not None:
        extra_args.extend(["--attempts-success-threshold", str(args.attempts_success_threshold)])
    
    # Forward defense argument to universal_attack.py
    if args.defense:
        extra_args.extend(["--defense", args.defense])

    # Forward retry flags to universal_attack.py
    if args.restart:
        extra_args.extend(["--restart"])
    if args.retry_failed:
        extra_args.extend(["--retry-failed"])
    if not args.retry_invalid:
        extra_args.extend(["--retry-invalid", "false"])

    tester = ComprehensiveAttackTester(args.attack_name, extra_args, defense_name=args.defense)
    
    if args.status:
        progress = tester.load_progress()
        tester.print_progress_table(progress)
        return
    
    if args.fix_progress:
        tester.fix_progress_from_results()
        return

    tester.run_comprehensive_test(args.model, args.dataset, args.restart, args.retry_invalid, args.retry_failed)

if __name__ == "__main__":
    main() 
