"""
Modern attack factory with auto-discovery support.

This factory provides a unified interface for creating attacks using the
modular attack system with auto-discovery.
"""

from typing import Dict, Any, Type, List
# Legacy imports removed - using only modular system
from .base import ModernBaseAttack

# Try to import the modern registry, fall back to legacy if not available
try:
    from .registry import registry
    MODERN_SYSTEM_AVAILABLE = True
except ImportError:
    MODERN_SYSTEM_AVAILABLE = False
    registry = None


class AttackFactory:
    """Factory for creating attack instances using the modular system."""
    
    # Legacy system removed - only modular system available
    
    @classmethod
    def create_attack(cls, attack_name: str, attack_config: Dict[str, Any] = None, 
                     args=None, **kwargs) -> Any:
        """
        Create an attack instance using the modular system.
        
        Args:
            attack_name: Name of the attack to create
            attack_config: Configuration dictionary (ignored - config embedded in attacks)
            args: Command line arguments object
            **kwargs: Additional arguments for attack initialization
            
        Returns:
            Attack instance
        """
        if not MODERN_SYSTEM_AVAILABLE:
            raise ImportError("Modular attack system not available")
        
        try:
            attack_class = registry.get_attack(attack_name)
            return attack_class(args=args, **kwargs)
        except (ValueError, ImportError, RuntimeError) as e:
            raise ValueError(
                f"Failed to create attack '{attack_name}'. "
                f"This might be due to missing dependencies, incorrect attack name, "
                f"or the attack not being properly defined. "
                f"Original error: {e}"
            ) from e
    
    @classmethod
    def get_available_attacks(cls) -> Dict[str, Dict[str, str]]:
        """Get all available attacks - REMOVED for performance reasons."""
        raise NotImplementedError(
            "Bulk attack listing has been removed for performance reasons. "
            "Use create_attack() with specific attack names instead."
        )
    
    # Removed get_attacks_by_type as part of flattening architecture
    # Use create_attack() with individual attack names instead
    
    @classmethod
    def list_attack_names(cls) -> List[str]:
        """Get a list of all attack names - REMOVED for performance reasons."""
        raise NotImplementedError(
            "Bulk attack name listing has been removed for performance reasons. "
            "Use create_attack() with specific attack names instead."
        )
    
    @classmethod
    def get_attack_config(cls, attack_name: str) -> Dict[str, Any]:
        """Get the configuration of an attack."""
        if not MODERN_SYSTEM_AVAILABLE:
            return {}
        
        try:
            attack_class = registry.get_attack(attack_name)
            return attack_class.get_config()
        except ValueError:
            return {} 