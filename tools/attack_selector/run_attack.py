#!/usr/bin/env python3
"""
Central Attack Runner Script

Usage:
    python tools/attack_selector/run_attack.py ATTACK_NAME --model MODEL --provider PROVIDER --dataset DATASET --output_dir OUTPUT_DIR [additional_args]

Examples:
    python tools/attack_selector/run_attack.py abj --model gpt-4 --provider openai --dataset /tmp/query.json --output_dir results
    python tools/attack_selector/run_attack.py masterkey --model claude-3.5-sonnet --provider anthropic --dataset my_queries.json --output_dir ./results --verbose
"""

import os
import sys
import yaml
import subprocess
import argparse
from typing import Dict, Any

def load_attack_configs() -> Dict[str, Any]:
    """Load attack configurations from YAML file."""
    config_path = os.path.join(os.path.dirname(__file__), "attack_configs.yaml")
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def create_argument_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Central Attack Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    # Required arguments
    parser.add_argument("attack_name", 
                       help="Name of the attack to run")
    parser.add_argument("--model", required=True,
                       help="Target model name")
    parser.add_argument("--provider", required=True,
                       help="Target model provider")
    parser.add_argument("--dataset", required=True,
                       help="Path to dataset file")
    parser.add_argument("--output_dir", required=True,
                       help="Output directory for results")
    parser.add_argument("--defense",
                       help="Defense to apply (optional, forwarded to universal_attack.py)")
    
    # Optional overrides
    parser.add_argument("--eval_model",
                       help="Evaluation model (overrides config default)")
    parser.add_argument("--eval_provider",
                       help="Evaluation provider (overrides config default)")
    
    # API configuration
    parser.add_argument("--api_key",
                       help="API key for the model provider")
    parser.add_argument("--api_base",
                       help="Base URL for the model API")
    
    # Pass-through arguments
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--all_samples", action="store_true",
                       help="Use all samples in dataset")
    parser.add_argument("--samples", type=int,
                       help="Number of samples to use")
    
    return parser

def build_universal_attack_command(attack_key: str, attack_name: str, args: argparse.Namespace,
                                 attack_config: Dict[str, Any]) -> list:
    """Build the universal_attack.py command with proper parameters."""

    # Start with the base command
    output_file = os.path.join(args.output_dir, f"results_{attack_key}.json")
    cmd = [
        sys.executable, "-m", "jbfoundry.runners.universal_attack",
        "--attack_name", attack_name,
        "--model", args.model,
        "--provider", args.provider,
        "--dataset", args.dataset,
        "--output_dir", args.output_dir,
        "--output", output_file
    ]
    if args.defense:
        cmd.extend(["--defense", args.defense])
    
    # Add API configuration if provided
    if args.api_key:
        cmd.extend(["--api_key", args.api_key])
    if args.api_base:
        cmd.extend(["--api_base", args.api_base])
    
    # Add samples argument
    if args.all_samples:
        cmd.append("--all_samples")
    elif args.samples:
        cmd.extend(["--samples", str(args.samples)])
    else:
        cmd.append("--all_samples")  # Default to all samples
    
    # Add attack-specific parameters from config
    default_params = attack_config.get("default_params", {})
    for param_name, param_value in default_params.items():
        # Allow command line overrides
        if param_name == "eval_model" and args.eval_model:
            cmd.extend([f"--{param_name}", args.eval_model])
        elif param_name == "eval_provider" and args.eval_provider:
            cmd.extend([f"--{param_name}", args.eval_provider])
        else:
            cmd.extend([f"--{param_name}", str(param_value)])
    
    # Add verbose flag if requested
    if args.verbose:
        cmd.append("--verbose")
    
    return cmd

def main():
    """Main function."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Load attack configurations
    try:
        configs = load_attack_configs()
        attacks = configs.get("attacks", {})
    except Exception as e:
        print(f"Error loading attack configurations: {e}")
        sys.exit(1)
    

    # Check if attack exists
    if args.attack_name not in attacks:
        print(f"Error: Unknown attack '{args.attack_name}'")
        print(f"Available attacks: {', '.join(sorted(attacks.keys()))}")
        sys.exit(1)
    
    # Get attack configuration
    attack_config = attacks[args.attack_name]
    attack_name = attack_config.get("attack_name", args.attack_name)
    
    # Build command
    cmd = build_universal_attack_command(args.attack_name, attack_name, args, attack_config)
    
    # Print command for debugging
    if args.verbose:
        print(f"🚀 Executing command:")
        print(f"   {' '.join(cmd)}")
        print()
    
    # Execute the command
    try:
        result = subprocess.run(cmd, text=True)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n❌ Attack interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error executing attack: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
