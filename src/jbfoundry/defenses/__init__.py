"""
Defense implementations for the JBFoundry framework.
"""

from typing import List

from .base import BaseDefense, register_defense, _DEFENSE_REGISTRY
from .factory import DefenseFactory
from .registry import registry


def get_defense(name: str, **kwargs) -> BaseDefense:
    """
    Get a defense implementation by name.

    Args:
        name: Name of the defense
        **kwargs: Parameters to pass to the defense constructor

    Returns:
        An instance of the defense
    """
    if name not in _DEFENSE_REGISTRY:
        try:
            registry.get_defense(name)
        except Exception:
            pass

    if name not in _DEFENSE_REGISTRY:
        raise ValueError(f"Defense '{name}' not found. Available defenses: {list(_DEFENSE_REGISTRY.keys())}")

    return _DEFENSE_REGISTRY[name](**kwargs)


def list_defenses() -> List[str]:
    """
    List all available defenses.

    Returns:
        List of defense names that have been discovered.
    """
    return registry.list_defenses()

