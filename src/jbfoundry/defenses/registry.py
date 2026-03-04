"""Defense registry with lazy loading capabilities."""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type

from .base import BaseDefense, _DEFENSE_REGISTRY

logger = logging.getLogger(__name__)


class DefenseRegistry:
    """Registry for lazy-loading defense implementations."""

    def __init__(self):
        # Store metadata about discovered defenses without loading them
        self._defense_metadata: Dict[str, Dict[str, str]] = {}
        # Cache for loaded defense classes
        self._loaded_defenses: Dict[str, Type[BaseDefense]] = {}
        # Cache for loaded modules to avoid re-imports
        self._loaded_modules: Dict[str, object] = {}

        self._discovery_paths: List[Path] = []
        self._initialize_discovery_paths()
        self._discover_defense_files()

    def _initialize_discovery_paths(self):
        """Initialize paths to search for defenses."""
        base_path = Path(__file__).parent
        self._discovery_paths = [base_path]

    def _discover_defense_files(self):
        """Discover defense files without importing them."""
        excluded_files = {"__init__.py", "base.py", "registry.py", "context.py", "factory.py"}

        for path in self._discovery_paths:
            if path.exists() and path.is_dir():
                for py_file in path.rglob("*.py"):
                    if py_file.name in excluded_files:
                        continue

                    try:
                        relative_path = py_file.relative_to(path)
                        module_parts = ["jbfoundry", "defenses"] + list(relative_path.parts[:-1]) + [py_file.stem]
                        module_name = ".".join(module_parts)

                        file_stem = py_file.stem

                        self._defense_metadata[file_stem] = {
                            "file_path": str(py_file),
                            "module_name": module_name
                        }

                        logger.debug(f"Registered defense file: {file_stem} ({module_name})")
                    except Exception as e:
                        logger.warning(f"Failed to register defense file {py_file}: {e}")

        logger.debug(f"Discovered {len(self._defense_metadata)} defense files: {list(self._defense_metadata.keys())}")

    def _load_defense_on_demand(self, defense_name: str) -> Type[BaseDefense]:
        """Load a defense module on demand and return the defense class."""
        if defense_name in self._loaded_defenses:
            return self._loaded_defenses[defense_name]

        defense_class = None

        if defense_name in self._defense_metadata:
            defense_class = self._load_defense_from_metadata(defense_name, self._defense_metadata[defense_name])

        if defense_class is None:
            available_files = list(self._defense_metadata.keys())
            loaded_defenses = list(self._loaded_defenses.keys())
            raise ValueError(
                f"Defense '{defense_name}' not found. "
                f"Available defense files: {available_files}. "
                f"Loaded defenses: {loaded_defenses}. "
                f"This might be due to missing dependencies or the defense class not being properly defined."
            )

        return defense_class

    def _load_defense_from_metadata(self, file_stem: str, metadata: Dict[str, str]) -> Optional[Type[BaseDefense]]:
        """Load defense class from file metadata."""
        module_name = metadata["module_name"]

        try:
            if module_name in self._loaded_modules:
                module = self._loaded_modules[module_name]
            else:
                module = importlib.import_module(module_name)
                self._loaded_modules[module_name] = module

            # Prefer registered defense class after import
            if file_stem in _DEFENSE_REGISTRY:
                self._loaded_defenses[file_stem] = _DEFENSE_REGISTRY[file_stem]
                return _DEFENSE_REGISTRY[file_stem]

            # Fallback: scan module for a BaseDefense subclass with a name
            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseDefense) and obj is not BaseDefense and getattr(obj, "name", ""):
                    _DEFENSE_REGISTRY[obj.name] = obj
                    self._loaded_defenses[obj.name] = obj
                    logger.debug(f"Loaded defense: {obj.name} from {module_name}")
                    return obj

            logger.warning(f"No valid defense class found in {module_name}")
            return None

        except ImportError as e:
            logger.error(f"Failed to import {module_name}: {e}")
            raise ImportError(
                f"Failed to load defense from {module_name}. "
                f"This is likely due to missing dependencies. "
                f"Error: {e}"
            )
        except Exception as e:
            logger.error(f"Unexpected error loading {module_name}: {e}")
            raise RuntimeError(
                f"Unexpected error loading defense from {module_name}. "
                f"Error: {e}"
            )

    def get_defense(self, name: str) -> Type[BaseDefense]:
        """Get a defense class by name with lazy loading."""
        return self._load_defense_on_demand(name)

    def list_defenses(self) -> List[str]:
        """List all available defense names.

        Returns:
            List of defense names that have been discovered.
        """
        return list(self._defense_metadata.keys())


# Global registry instance
registry = DefenseRegistry()
