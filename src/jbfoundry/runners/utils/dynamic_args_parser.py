"""Dynamic argument parser that auto-discovers attack arguments."""

import argparse
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

# Try to import the modern system
try:
    from jbfoundry.attacks.registry import registry
    MODERN_SYSTEM_AVAILABLE = True
except ImportError:
    MODERN_SYSTEM_AVAILABLE = False
    registry = None


class DynamicArgumentParser:
    """Argument parser that dynamically includes attack-specific arguments."""
    
    def __init__(self, attack_name=None, pre_parse_mode=False):
        self.attack_name = attack_name
        self.pre_parse_mode = pre_parse_mode
        self.parser = self._create_base_parser()
        
        if MODERN_SYSTEM_AVAILABLE:
            if not pre_parse_mode and attack_name:
                self._add_attack_specific_arguments(attack_name)
            elif not pre_parse_mode:
                # Fallback to current behavior for backwards compatibility
                self._add_dynamic_attack_arguments()
    
    def _create_base_parser(self) -> argparse.ArgumentParser:
        """Create the base argument parser with core arguments."""
        parser = argparse.ArgumentParser(
            description="Universal JBFoundry Attack Script with Modular Architecture",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._generate_help_epilog()
        )
        
        # Core configuration
        core_group = parser.add_argument_group("Core Configuration")
        core_group.add_argument("--attack_name", type=str,
                               help="Specific attack to run")
        core_group.add_argument("--config", type=str, default=None,
                               help="Path to YAML attack config. CLI flags override values from the config.")
        core_group.add_argument("--attack_path", type=str, default=None,
                               help="Path to external attack .py file (for pip-installed usage)")
        core_group.add_argument("--list_attacks", action="store_true",
                               help="List all available attacks and exit")
        
        # Model configuration
        model_group = parser.add_argument_group("Model Configuration")
        model_group.add_argument("--model", type=str, default="gpt-3.5-turbo",
                                help="Model to attack")
        model_group.add_argument("--provider", type=str, default="openai",
                                help="Model provider (common: openai, anthropic, azure, bedrock, vertex_ai, aliyun, wenwen, infini, or any custom provider)")
        model_group.add_argument("--api_key", type=str, default=None,
                                help="API key for the model provider")
        model_group.add_argument("--api_base", type=str, default=None,
                                help="Base URL for API requests")
        
        # Dataset and output configuration
        data_group = parser.add_argument_group("Dataset and Output")
        data_group.add_argument("--dataset", type=str, default="jbb-harmful",
                               help="Dataset to use for evaluation")
        data_group.add_argument("--samples", type=int, default=10,
                               help="Number of samples to test")
        data_group.add_argument("--all_samples", action="store_true",
                               help="Use all samples from the dataset (overrides --samples)")
        data_group.add_argument("--output_dir", type=str, default="results",
                               help="Directory to save results")
        data_group.add_argument("--output", type=str, default=None,
                               help="Specific output file path")
        
        # Defense configuration
        defense_group = parser.add_argument_group("Defense Configuration")
        defense_group.add_argument("--defense", type=str, default=None,
                                  help="Defense mechanism to apply")
        defense_group.add_argument("--paraphrase_model", type=str, default="gpt-3.5-turbo",
                                  help="Model for paraphrase defense")
        
        # Evaluation configuration
        eval_group = parser.add_argument_group("Evaluation Configuration")
        eval_group.add_argument("--eval_model", type=str, default="gpt-4",
                               help="Model to use for evaluation")
        eval_group.add_argument("--eval_provider", type=str, default="openai",
                               help="Provider for evaluation model (common: openai, anthropic, azure, wenwen, or any custom provider)")
        
        # Debug and control
        debug_group = parser.add_argument_group("Debug and Control")
        debug_group.add_argument("--verbose", action="store_true",
                                help="Enable verbose logging")
        debug_group.add_argument("--seed", type=int, default=42,
                                help="Random seed for reproducibility")
        debug_group.add_argument("--attempts-per-query", type=int, default=1,
                                help="Number of attack attempts per query (default: 1)")
        debug_group.add_argument("--attempts-success-threshold", type=int, default=None,
                                help="Minimum successful attempts required to count a query as successful (default: attempts-per-query)")
        debug_group.add_argument("--max_workers", type=int, default=1,
                            help="Maximum number of parallel workers for processing samples (default: 1 for sequential execution)")
        debug_group.add_argument("--restart",
                                type=self._str_to_bool,
                                nargs='?',
                                const=True,
                                default=False,
                                metavar='{true,false}',
                                help="Restart from scratch, deleting existing results. "
                                     "Supports --restart (sets to true) or --restart true/false. "
                                     "(default: false - resume from existing results)")
        debug_group.add_argument("--retry-invalid",
                                type=self._str_to_bool,
                                nargs='?',
                                const=True,
                                default=True,
                                metavar='{true,false}',
                                help="When resuming, retry queries with invalid/error results (jailbroken=None). "
                                     "Has no effect when --restart is used. "
                                     "(default: true - retry invalid queries)")
        debug_group.add_argument("--retry-failed",
                                type=self._str_to_bool,
                                nargs='?',
                                const=True,
                                default=False,
                                metavar='{true,false}',
                                help="When resuming, retry queries that failed normally (jailbroken=False). "
                                     "Has no effect when --restart is used. "
                                     "(default: false - only retry invalid/unrun queries)")
        debug_group.add_argument("--per-query-timeout", type=int, default=None,
                                metavar='SECONDS',
                                help="Maximum time (in seconds) allowed per attack query (default: None - no timeout). "
                                     "If exceeded, raises AttackTimeoutError to stop implementation.")

        return parser
    
    def _add_attack_specific_arguments(self, attack_name: str):
        """Add arguments for a specific attack only."""
        try:
            if registry is None:
                raise RuntimeError("Registry is not available")
            attack_args = registry.get_attack_cli_arguments(attack_name)
            
            if attack_args:
                attack_group = self.parser.add_argument_group(f"{attack_name.upper()} Attack Arguments")
                
                for arg_name, arg_config in attack_args.items():
                    kwargs = arg_config["kwargs"].copy()
                    original_help = kwargs.get("help", "")
                    kwargs["help"] = f"{original_help}"
                    
                    # Special handling for boolean arguments
                    if kwargs.get("type") == bool:
                        kwargs["type"] = self._str_to_bool
                        kwargs["metavar"] = "{true,false}"
                        kwargs["help"] += " (accepts: true, false, True, False)"

                    if kwargs.get("type") == dict:
                        kwargs["type"] = self._parse_dict_arg
                        kwargs["metavar"] = "OBJECT"
                        kwargs["help"] += " (JSON/YAML object)"
                    
                    attack_group.add_argument(arg_name, **kwargs)
                    
        except Exception as e:
            raise RuntimeError(
                f"Failed to load arguments for attack '{attack_name}'. \n"
                f"This might be due to missing dependencies or the attack not being properly defined. \n"
                f"Error: {e}"
            )
    
    def _str_to_bool(self, value):
        """Convert string representation to boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            if value.lower() in ('true', 't', 'yes', 'y', '1'):
                return True
            elif value.lower() in ('false', 'f', 'no', 'n', '0'):
                return False
            else:
                raise argparse.ArgumentTypeError(f"Boolean value expected, got: {value}")
        raise argparse.ArgumentTypeError(f"Boolean value expected, got: {value}")

    def _parse_dict_arg(self, value):
        """Parse a dict-valued CLI argument from a JSON or YAML object string."""
        if isinstance(value, dict):
            return value
        if not isinstance(value, str):
            raise argparse.ArgumentTypeError(f"Object value expected, got: {value!r}")

        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            try:
                import yaml
                parsed = yaml.safe_load(value)
            except Exception as e:
                raise argparse.ArgumentTypeError(
                    f"Expected JSON/YAML object, got: {value!r}"
                ) from e

        if not isinstance(parsed, dict):
            raise argparse.ArgumentTypeError(
                f"Expected JSON/YAML object, got {type(parsed).__name__}"
            )
        return parsed
    
    def _add_dynamic_attack_arguments(self):
        """Removed: Dynamic attack arguments loading is no longer supported.
        
        Use attack-specific argument loading instead by specifying --attack_name.
        """
        logger.warning("Dynamic attack arguments loading is deprecated. Please specify --attack_name for attack-specific arguments.")
        pass
    
    def _generate_help_epilog(self) -> str:
        """Generate help text with usage examples."""
        try:
            if not MODERN_SYSTEM_AVAILABLE:
                return "Modern attack system not available."
                
            lines = ["Usage Examples:"]
            lines.append("  python -m jbfoundry.runners.universal_attack --attack_name many_shot")
            lines.append("  python -m jbfoundry.runners.universal_attack --attack_name simple_override --all_samples")
            lines.append("  python -m jbfoundry.runners.universal_attack --attack_name translate_chain --samples 50")
            lines.append("\nFor attack-specific arguments, specify the attack name first:")
            lines.append("  python -m jbfoundry.runners.universal_attack --attack_name many_shot --help")
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.warning(f"Failed to generate help epilog: {e}")
            return "Error loading help information"
    
    def parse_args(self) -> argparse.Namespace:
        """Parse command line arguments."""
        return self.parser.parse_args()
    
    def parse_with_context(self) -> argparse.Namespace:
        """Two-stage parsing: pre-parse for attack, then full parse."""
        import sys
        
        # Stage 1: Pre-parse to get attack name
        pre_parser = DynamicArgumentParser(pre_parse_mode=True)
        try:
            pre_args, unknown_args = pre_parser.parser.parse_known_args()
        except SystemExit:
            # If pre-parsing fails (e.g., --help), let it handle normally
            return self.parser.parse_args()
        
        config_attack_name = None
        if getattr(pre_args, "config", None) and not getattr(pre_args, "attack_name", None):
            config_attack_name = _load_attack_name_from_config(pre_args.config)

        attack_name = getattr(pre_args, 'attack_name', None) or config_attack_name

        # Stage 2: Full parse with attack context
        if attack_name:
            if pre_args.list_attacks:
                # Handle --list_attacks flag
                list_available_attacks()
                sys.exit(0)
            
            # Load external attack file before creating attack-specific parser
            attack_path = getattr(pre_args, 'attack_path', None)
            if attack_path and registry is not None:
                registry.load_external_attack(attack_path)

            # Create attack-specific parser
            try:
                full_parser = DynamicArgumentParser(attack_name=attack_name)
                return full_parser.parser.parse_args()
            except Exception as e:
                logger.error(f"Failed to create attack-specific parser for '{attack_name}': {e}")
                sys.exit(1)
        else:
            # No specific attack or --list_attacks, use current behavior
            if hasattr(pre_args, 'list_attacks') and pre_args.list_attacks:
                list_available_attacks()
                sys.exit(0)
            return self.parser.parse_args()


def create_dynamic_parser() -> DynamicArgumentParser:
    """Create a dynamic argument parser."""
    return DynamicArgumentParser()

def create_context_aware_parser() -> DynamicArgumentParser:
    """Create a context-aware argument parser that only loads relevant attack parameters."""
    return DynamicArgumentParser(pre_parse_mode=True)

def parse_args_with_context():
    """Parse command line arguments with context awareness."""
    parser = create_context_aware_parser()
    return parser.parse_with_context()


def _load_attack_name_from_config(config_path: str) -> Optional[str]:
    """Load attack_name from YAML config for parser context selection."""
    try:
        import yaml
    except ImportError as e:
        logger.error(f"Cannot parse --config without PyYAML installed: {e}")
        return None

    path = Path(config_path)
    if not path.exists():
        logger.error(f"Config file not found: {config_path}")
        return None

    try:
        with path.open("r") as f:
            data = yaml.safe_load(f) or {}
    except Exception as e:
        logger.error(f"Failed to load config file {config_path}: {e}")
        return None

    return data.get("attack_name")


def list_available_attacks():
    """List all discovered attack files without loading them."""
    print("Available Attacks (discovered from attack files):")
    print("=" * 60)

    if MODERN_SYSTEM_AVAILABLE and registry is not None:
        # Get discovered attack file stems (no loading needed)
        attack_files = sorted(registry.list_attacks())

        if attack_files:
            print(f"\nTotal: {len(attack_files)} attacks discovered\n")

            # Group by subdirectory if possible
            manual_attacks = []
            generated_attacks = []
            root_attacks = []

            for file_stem in attack_files:
                file_path = registry._attack_metadata[file_stem]["file_path"]
                if "/manual/" in file_path:
                    manual_attacks.append(file_stem)
                elif "/generated/" in file_path:
                    generated_attacks.append(file_stem)
                else:
                    root_attacks.append(file_stem)

            if manual_attacks:
                print(f"Manual Attacks ({len(manual_attacks)}):")
                for attack in manual_attacks:
                    print(f"  - {attack}")
                print()

            if generated_attacks:
                print(f"Generated Attacks ({len(generated_attacks)}):")
                for attack in generated_attacks:
                    print(f"  - {attack}")
                print()

            if root_attacks:
                print(f"Root Attacks ({len(root_attacks)}):")
                for attack in root_attacks:
                    print(f"  - {attack}")
                print()
        else:
            print("\nNo attacks discovered!")
    else:
        print("\nModern attack system not available!")

    print("\nUsage Examples:")
    print("  python -m jbfoundry.runners.universal_attack --attack_name many_shot")
    print("  python -m jbfoundry.runners.universal_attack --attack_name simple_override --all_samples")
    print("  python -m jbfoundry.runners.universal_attack --attack_name translate_chain --samples 50")
    print("\nFor attack-specific arguments, specify the attack name first:")
    print("  python -m jbfoundry.runners.universal_attack --attack_name many_shot --help")


if __name__ == "__main__":
    # Test the parser
    parser = create_dynamic_parser()
    args = parser.parse_args()
    print(f"Parsed arguments: {args}")
