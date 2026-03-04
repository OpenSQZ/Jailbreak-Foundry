"""Enhanced base classes for modular attack system."""

from abc import ABC, ABCMeta, abstractmethod
from typing import Dict, Any, List, Optional, Union, Callable
import argparse
import logging
from contextvars import Token

from .context import AttackContext, _attack_context

logger = logging.getLogger(__name__)


class AttackMetaclass(ABCMeta):
    """
    Metaclass that automatically wraps attack methods with context management.

    This allows existing attack code to continue using generate_attack normally,
    while automatically adding thread-safe context management and cost tracking.
    """

    def __new__(mcs, name, bases, class_dict):
        # Create the class first
        cls = super().__new__(mcs, name, bases, class_dict)

        # Only wrap if this is a concrete attack class (has generate_attack)
        if 'generate_attack' in class_dict and name != 'ModernBaseAttack':
            # Store the original generate_attack method
            original_generate_attack = class_dict['generate_attack']

            # Create a context-wrapped version
            def wrapped_generate_attack(self, prompt: str, goal: str, target: str, **kwargs) -> str:
                """Context-wrapped generate_attack method."""
                # Create isolated context for this attack run
                context = AttackContext(**kwargs)

                # Set context (similar to Flask's request context)
                token: Token = _attack_context.set(context)
                try:
                    # Call the original generate_attack method
                    return original_generate_attack(self, prompt, goal, target, **kwargs)
                finally:
                    # Clean up context
                    _attack_context.reset(token)

            # Replace the method on the class
            setattr(cls, 'generate_attack', wrapped_generate_attack)


        return cls



class AttackParameter:
    """Represents a configurable attack parameter."""
    
    def __init__(
        self,
        name: str,
        param_type: type,
        default: Any = None,
        description: str = "",
        cli_arg: Optional[str] = None,
        choices: Optional[List[Any]] = None,
        required: bool = False,
        validator: Optional[Callable[[Any], bool]] = None
    ):
        self.name = name
        self.type = param_type
        self.default = default
        self.description = description
        self.cli_arg = cli_arg
        self.choices = choices
        self.required = required
        self.validator = validator
    
    def validate(self, value: Any) -> bool:
        """Validate a parameter value."""
        if self.choices and value not in self.choices:
            return False
        if self.validator and not self.validator(value):
            return False
        return True
    
    def to_argparse_kwargs(self) -> Dict[str, Any]:
        """Convert to argparse.add_argument kwargs."""
        kwargs = {
            "type": self.type,
            "help": self.description,
            "default": self.default
        }
        if self.choices:
            kwargs["choices"] = self.choices
        if self.required:
            kwargs["required"] = True
        return {k: v for k, v in kwargs.items() if v is not None}


class ModernBaseAttack(ABC, metaclass=AttackMetaclass):
    """Enhanced base class for all attacks with embedded configuration."""
    
    # Class-level configuration - must be overridden by subclasses
    NAME: str = ""
    PAPER: str = ""
    PARAMETERS: Dict[str, AttackParameter] = {}
    
    def __init__(self, args=None, **kwargs):
        """Initialize attack with parameters."""
        self.args = args
        self.kwargs = kwargs
        self._validate_configuration()
    
    def _validate_configuration(self):
        """Validate the attack configuration."""
        required_fields = ["NAME"]
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Attack {self.__class__.__name__} missing required field: {field}")
    
    @abstractmethod
    def generate_attack(self, prompt: str, goal: str, target: str, **kwargs) -> str:
        """
        Generate an attack string.

        Subclasses implement this method normally. The metaclass automatically
        wraps it with thread-safe context management for cost tracking.

        Args:
            prompt: The input prompt
            goal: The attack goal
            target: The target string
            **kwargs: Additional parameters

        Returns:
            The generated attack string
        """
        pass
    
    def get_parameter_value(self, param_name: str) -> Any:
        """Get a parameter value from args, kwargs, or default."""
        if param_name not in self.PARAMETERS:
            raise ValueError(f"Unknown parameter: {param_name}")
        
        param = self.PARAMETERS[param_name]
        
        # Check CLI args first
        if self.args and hasattr(self.args, param_name):
            value = getattr(self.args, param_name)
            if value is not None:
                return value
        
        # Check kwargs
        if param_name in self.kwargs:
            return self.kwargs[param_name]
        
        # Return default
        return param.default


    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Return the complete attack configuration."""
        return {
            "name": cls.NAME,
            "paper": cls.PAPER,
            "parameters": {name: {
                "type": param.type.__name__,
                "default": param.default,
                "description": param.description,
                "cli_arg": param.cli_arg,
                "choices": param.choices,
                "required": param.required
            } for name, param in cls.PARAMETERS.items()}
        }
    
    @classmethod
    def get_cli_arguments(cls) -> List[Dict[str, Any]]:
        """Return CLI argument specifications for this attack."""
        args = []
        for param_name, param in cls.PARAMETERS.items():
            if param.cli_arg:
                args.append({
                    "name": param.cli_arg,
                    "kwargs": param.to_argparse_kwargs(),
                    "param_name": param_name
                })
        return args


# All attacks now inherit directly from ModernBaseAttack with minimal required attributes.