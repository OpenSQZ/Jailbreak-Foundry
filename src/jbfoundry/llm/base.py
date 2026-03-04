"""
Base LLM interface for JBFoundry.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Any


class BaseLLM(ABC):
    """
    Abstract base class for LLM interfaces.
    
    This defines the standard interface for interacting with language models in JBFoundry.
    Concrete implementations should inherit from this class.
    """
    
    @abstractmethod
    def __init__(self, model_name: str, **kwargs):
        """
        Initialize the LLM.
        
        Args:
            model_name: Name of the model to use
            **kwargs: Additional model-specific parameters
        """
        self.model_name = model_name
        self.kwargs = kwargs
        self.last_query = None
    
    @abstractmethod
    def query(self, prompts: Union[str, List[str]], behavior: Optional[str] = None, 
              defense: Optional[str] = None, phase: Optional[str] = None, **kwargs) -> Union[str, List[str]]:
        """
        Query the model with a prompt or list of prompts.
        
        Args:
            prompts: Prompt(s) to send to the model
            behavior: Behavior context for logging and evaluation
            defense: Defense to apply (if any)
            phase: Phase of querying (e.g., "test", "optimization")
            **kwargs: Additional query parameters
            
        Returns:
            Model response(s)
        """
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """
        Count the number of tokens in the text.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    def format_prompt(self, prompt: str) -> Union[str, Dict[str, Any]]:
        """
        Format a prompt according to the model's requirements.
        
        Args:
            prompt: Raw prompt text
            
        Returns:
            Formatted prompt
        """
        return prompt
    
    def parse_response(self, response: Any) -> str:
        """
        Parse the raw model response.
        
        Args:
            response: Raw model response
            
        Returns:
            Parsed response text
        """
        return str(response)
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary with model information
        """
        return {
            "model_name": self.model_name,
            "model_type": self.__class__.__name__,
        } 