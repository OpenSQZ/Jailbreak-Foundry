"""
Defense factory with auto-discovery support.
"""

from typing import Any, Dict

try:
    from .registry import registry
    MODERN_SYSTEM_AVAILABLE = True
except ImportError:
    MODERN_SYSTEM_AVAILABLE = False
    registry = None


class DefenseFactory:
    """Factory for creating defense instances using the modular system."""

    @classmethod
    def get_default_config(cls, defense_name: str) -> Dict[str, Any]:
        """
        Get the default configuration for a defense.

        Args:
            defense_name: Name of the defense

        Returns:
            Default configuration dictionary
        """
        if not MODERN_SYSTEM_AVAILABLE:
            return {}

        try:
            defense_class = registry.get_defense(defense_name)
            return getattr(defense_class, 'default_config', {})
        except (ValueError, ImportError, RuntimeError):
            return {}

    @classmethod
    def create_defense(cls, defense_name: str, defense_config: Dict[str, Any] = None, **kwargs) -> Any:
        """
        Create a defense instance using the modular system.

        Args:
            defense_name: Name of the defense to create
            defense_config: Configuration dictionary (optional)
            **kwargs: Additional arguments for defense initialization

        Returns:
            Defense instance
        """
        if not MODERN_SYSTEM_AVAILABLE:
            raise ImportError("Defense registry not available")

        try:
            defense_class = registry.get_defense(defense_name)
            config = defense_config or {}
            return defense_class(**config, **kwargs)
        except (ValueError, ImportError, RuntimeError) as e:
            raise ValueError(
                f"Failed to create defense '{defense_name}'. "
                f"This might be due to missing dependencies, incorrect defense name, "
                f"or the defense not being properly defined. "
                f"Original error: {e}"
            ) from e
