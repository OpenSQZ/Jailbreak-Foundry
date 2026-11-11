"""Attack registry with lazy loading capabilities."""

import os
import importlib
import inspect
import logging
from typing import Dict, Type, List, Optional
from pathlib import Path
from .base import ModernBaseAttack

logger = logging.getLogger(__name__)


class AttackRegistry:
    """Registry for lazy-loading attack implementations."""
    
    def __init__(self):
        # Store metadata about discovered attacks without loading them
        self._attack_metadata: Dict[str, Dict[str, str]] = {}
        # Cache for loaded attack classes
        self._loaded_attacks: Dict[str, Type[ModernBaseAttack]] = {}
        # Cache for loaded modules to avoid re-imports
        self._loaded_modules: Dict[str, object] = {}
        
        self._discovery_paths: List[Path] = []
        self._initialize_discovery_paths()
        self._discover_attack_files()
    
    def _initialize_discovery_paths(self):
        """Initialize paths to search for attacks."""
        base_path = Path(__file__).parent
        self._discovery_paths = [base_path]  # Only scan root attacks directory
    
    def _discover_attack_files(self):
        """Discover attack files without importing them."""
        for path in self._discovery_paths:
            if path.exists() and path.is_dir():
                self._discover_attack_files_in_path(path)

        logger.debug(f"Discovered {len(self._attack_metadata)} attack files: {list(self._attack_metadata.keys())}")
    
    def _discover_attack_files_in_path(self, path: Path):
        """Discover attack files in a specific directory without importing."""
        excluded_files = {"__init__.py", "base.py", "factory.py", "registry.py", "context.py"}

        # Recursively search for .py files in subdirectories too
        for py_file in path.rglob("*.py"):
            if py_file.name in excluded_files:
                continue

            try:
                # Calculate relative path from attacks directory
                relative_path = py_file.relative_to(path)

                # Build module name with subdirectory structure
                # e.g., manual/abj_attack.py -> src.jbfoundry.attacks.manual.abj_attack
                module_parts = ["jbfoundry", "attacks"] + list(relative_path.parts[:-1]) + [py_file.stem]
                module_name = ".".join(module_parts)

                file_stem = py_file.stem

                # Store metadata for lazy loading
                self._attack_metadata[file_stem] = {
                    "file_path": str(py_file),
                    "module_name": module_name
                }

                logger.debug(f"Registered attack file: {file_stem} ({module_name})")

            except Exception as e:
                logger.warning(f"Failed to register attack file {py_file}: {e}")
    
    def _load_attack_on_demand(self, attack_name: str) -> Type[ModernBaseAttack]:
        """Load an attack module on demand and return the attack class."""
        # Check if attack is already loaded
        if attack_name in self._loaded_attacks:
            return self._loaded_attacks[attack_name]

        # Try to find the attack in discovered files (package auto-discovery)
        if attack_name in self._attack_metadata:
            attack_class = self._load_attack_from_metadata(attack_name, self._attack_metadata[attack_name])
            if attack_class is not None:
                return attack_class

        # Fallback: look for {attack_name}.py in CWD (pip user with co-located files)
        cwd_file = Path.cwd() / f"{attack_name}.py"
        if cwd_file.exists():
            logger.info(f"Found {attack_name}.py in working directory, loading externally")
            self.load_external_attack(str(cwd_file))
            if attack_name in self._loaded_attacks:
                return self._loaded_attacks[attack_name]

        # Generate helpful error message
        available_files = list(self._attack_metadata.keys())
        loaded_attacks = [cls.NAME for cls in self._loaded_attacks.values()]
        raise ValueError(
            f"Attack '{attack_name}' not found. "
            f"Available attack files: {available_files}. "
            f"Loaded attacks: {loaded_attacks}. "
            f"This might be due to missing dependencies or the attack class not being properly defined."
        )
    
    def _load_attack_from_metadata(self, file_stem: str, metadata: Dict[str, str]) -> Optional[Type[ModernBaseAttack]]:
        """Load attack class from file metadata."""
        module_name = metadata["module_name"]
        
        try:
            # Check if module is already loaded
            if module_name in self._loaded_modules:
                module = self._loaded_modules[module_name]
            else:
                # Import the module
                module = importlib.import_module(module_name)
                self._loaded_modules[module_name] = module
            
            # Find attack classes in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if (issubclass(obj, ModernBaseAttack) and
                    obj != ModernBaseAttack and
                    hasattr(obj, 'NAME') and
                    obj.NAME):

                    # Enforce NAME matches file stem
                    if obj.NAME != file_stem:
                        raise ValueError(
                            f"Class {name} in {module_name} has NAME = \"{obj.NAME}\" "
                            f"but the file is named \"{file_stem}.py\". "
                            f"Fix: set NAME = \"{file_stem}\""
                        )

                    # Cache the loaded attack
                    self._loaded_attacks[obj.NAME] = obj
                    logger.debug(f"Loaded attack: {obj.NAME} from {module_name}")
                    return obj

            # Module loaded but no class matched — diagnose why
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj is ModernBaseAttack:
                    continue
                # Wrong import path: class has "ModernBaseAttack" in MRO by name
                # but issubclass() fails due to duplicate module identity
                base_names = [b.__name__ for b in getattr(obj, '__mro__', [])]
                if 'ModernBaseAttack' in base_names and not issubclass(obj, ModernBaseAttack):
                    actual_mod = next(
                        (b.__module__ for b in obj.__mro__ if b.__name__ == 'ModernBaseAttack'), '?'
                    )
                    raise ImportError(
                        f"Class {name} in {module_name} inherits ModernBaseAttack from "
                        f"'{actual_mod}', but the registry expects it from "
                        f"'{ModernBaseAttack.__module__}'. "
                        f"Fix: use 'from jbfoundry.attacks.base import ModernBaseAttack' (not 'from src.jbfoundry...')."
                    )
                # Missing NAME attribute
                if issubclass(obj, ModernBaseAttack) and not getattr(obj, 'NAME', None):
                    raise ValueError(
                        f"Class {name} in {module_name} extends ModernBaseAttack "
                        f"but has no NAME attribute. Add: NAME = \"{file_stem}\""
                    )

            logger.warning(f"No valid attack class found in {module_name}")
            return None
            
        except ImportError as e:
            logger.error(f"Failed to import {module_name}: {e}")
            raise ImportError(
                f"Failed to load attack from {module_name}. "
                f"This is likely due to missing dependencies. "
                f"Error: {e}"
            )
        except Exception as e:
            logger.error(f"Unexpected error loading {module_name}: {e}")
            raise RuntimeError(
                f"Unexpected error loading attack from {module_name}. "
                f"Error: {e}"
            )
    
    def get_attack(self, name: str) -> Type[ModernBaseAttack]:
        """Get an attack class by name with lazy loading."""
        return self._load_attack_on_demand(name)
    
    def get_attack_cli_arguments(self, attack_name: str) -> Dict[str, Dict[str, any]]:
        """Get CLI arguments for a specific attack only."""
        attack_class = self.get_attack(attack_name)
        cli_args = attack_class.get_cli_arguments()
        
        result = {}
        for arg_spec in cli_args:
            result[arg_spec["name"]] = {
                "kwargs": arg_spec["kwargs"],
                "param_name": arg_spec["param_name"],
                "attack": attack_name
            }
        return result
    
    def manual_register(self, attack_class: Type[ModernBaseAttack]):
        """Manually register an attack class (for testing or external plugins)."""
        attack_name = attack_class.NAME
        if attack_name in self._loaded_attacks:
            logger.warning(f"Attack {attack_name} already registered, skipping")
            return

        self._loaded_attacks[attack_name] = attack_class
        logger.debug(f"Manually registered attack: {attack_name}")

    def load_external_attack(self, attack_path: str):
        """Load an attack class from an external .py file and register it.

        Args:
            attack_path: Path to a .py file containing a ModernBaseAttack subclass.
        """
        import importlib.util

        path = Path(attack_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Attack file not found: {path}")

        spec = importlib.util.spec_from_file_location("external_attack", str(path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        registered = False
        for obj in vars(mod).values():
            if (isinstance(obj, type)
                    and issubclass(obj, ModernBaseAttack)
                    and obj is not ModernBaseAttack
                    and getattr(obj, 'NAME', None)):
                self.manual_register(obj)
                logger.info(f"Loaded external attack: {obj.NAME} from {path}")
                registered = True

        if not registered:
            raise ValueError(f"No ModernBaseAttack subclass found in {path}")

    def list_attacks(self) -> List[str]:
        """List all available attack names.

        Returns:
            List of attack names that have been discovered.
        """
        return list(self._attack_metadata.keys())


# Global registry instance
registry = AttackRegistry()