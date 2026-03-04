"""
Attack package with backward compatibility and modern modular system.

This module provides both the legacy interface and the new modular system.
"""

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Legacy base class for backward compatibility
class BaseAttack(ABC):
    """Legacy base class for backward compatibility."""
    
    name: str = "base"
    description: str = "Base attack class"
    
    def __init__(self, **kwargs):
        """Initialize attack with parameters."""
        self.params = kwargs
    
    @abstractmethod
    def generate_attack(self, prompt: str, goal: str, target: str, **kwargs) -> str:
        """
        Generate an attack string based on the prompt, goal, and target.
        
        Args:
            prompt: The original prompt to be jailbroken
            goal: The goal of the jailbreak
            target: The target response we want to elicit
            **kwargs: Additional parameters
            
        Returns:
            The jailbroken prompt
        """
        pass
    
    @classmethod
    def from_config(cls, config: dict) -> "BaseAttack":
        """Create an attack instance from a configuration dictionary."""
        return cls(**config)


# Modern modular system imports
try:
    from .base import ModernBaseAttack
    from .factory import AttackFactory
    from .registry import registry
    MODERN_SYSTEM_AVAILABLE = True
except ImportError as e:
    MODERN_SYSTEM_AVAILABLE = False
    logger.warning(f"Modern attack system not available: {e}")

# Legacy system removed - only modular system available
LEGACY_AVAILABLE = False


# Public API functions
def get_attack(name: str):
    """Get an attack class by name (modern interface)."""
    if MODERN_SYSTEM_AVAILABLE:
        return registry.get_attack(name)
    else:
        raise ImportError("Modern attack system not available")

def list_attacks():
    """
    List all available attacks.

    Returns:
        List of attack names that have been discovered.
    """
    if MODERN_SYSTEM_AVAILABLE:
        return registry.list_attacks()
    else:
        raise ImportError("Modern attack system not available")

def create_attack(name: str, args=None, **kwargs):
    """Create an attack instance (modern interface)."""
    if MODERN_SYSTEM_AVAILABLE:
        return AttackFactory.create_attack(name, args=args, **kwargs)
    else:
        raise ImportError("Modern attack system not available")


# Removed get_attacks_by_type function as part of flattening
# Individual attacks should be accessed by name using get_attack() or create_attack()


# Export everything for compatibility
__all__ = [
    # Legacy interface
    "BaseAttack",
    # Modern interface (if available)
    "ModernBaseAttack",
    "AttackFactory", "registry",
    # Public API
    "get_attack", "create_attack", "list_attacks",
    # System availability flags
    "MODERN_SYSTEM_AVAILABLE", "LEGACY_AVAILABLE"
]

# Legacy classes removed - only modular system available 