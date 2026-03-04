"""
SmoothLLM defense implementation based on the paper 
"SmoothLLM: Defending Large Language Models Against Jailbreaking Attacks"
by Robey et al., 2023.

Paper: https://arxiv.org/abs/2310.03684
"""

import logging

logger = logging.getLogger(__name__)

import random
from typing import List, Optional, Callable, Union

import nltk
from nltk.tokenize import word_tokenize

from ..base import BaseDefense, register_defense
from ...utils.nlp import tokenize_text, get_stopwords



@register_defense("smoothllm")
class SmoothLLM(BaseDefense):
    """
    SmoothLLM defense that uses word-level perturbations to defend against jailbreaking.
    
    This defense applies random perturbations to the input prompt and aggregates
    the results to produce a more robust response.
    """
    
    description = "SmoothLLM defense with random word perturbations"
    
    def __init__(
        self,
        n_samples: int = 10,
        sigma: float = 0.5,
        p: float = 0.3,
        llm_caller: Optional[Callable] = None,
        **kwargs
    ):
        """
        Initialize the SmoothLLM defense.
        
        Args:
            n_samples: Number of perturbed samples to generate
            sigma: Strength of the perturbation (between 0 and 1)
            p: Probability of perturbing each word
            llm_caller: Function to call the LLM with a prompt and get a response
            **kwargs: Additional parameters
        """
        super().__init__(**kwargs)
        self.n_samples = n_samples
        self.sigma = sigma
        self.p = p
        self.llm_caller = llm_caller
        self.stopwords = get_stopwords()
    
    def _perturb_text(self, text: str) -> str:
        """
        Apply random word-level perturbations to the text.
        
        Args:
            text: The text to perturb
            
        Returns:
            The perturbed text
        """
        words = tokenize_text(text)
        perturbed_words = []
        
        for word in words:
            # Skip stopwords and short words with higher probability
            if word.lower() in self.stopwords or len(word) <= 3:
                perturb_prob = self.p / 2
            else:
                perturb_prob = self.p
            
            if random.random() < perturb_prob:
                # Apply perturbation
                if len(word) > 3 and word.isalpha():
                    # Different types of perturbations with equal probability
                    perturbation_type = random.randint(0, 2)
                    
                    if perturbation_type == 0:
                        # Swap two adjacent characters
                        swap_idx = random.randint(0, len(word) - 2)
                        perturbed_word = (
                            word[:swap_idx] + 
                            word[swap_idx + 1] + 
                            word[swap_idx] + 
                            word[swap_idx + 2:]
                        )
                    elif perturbation_type == 1:
                        # Delete a character
                        del_idx = random.randint(0, len(word) - 1)
                        perturbed_word = word[:del_idx] + word[del_idx + 1:]
                    else:
                        # Duplicate a character
                        dup_idx = random.randint(0, len(word) - 1)
                        perturbed_word = (
                            word[:dup_idx] + 
                            word[dup_idx] + 
                            word[dup_idx:]
                        )
                    
                    perturbed_words.append(perturbed_word)
                else:
                    # For non-alphabetic or short words, just use as is
                    perturbed_words.append(word)
            else:
                perturbed_words.append(word)
        
        # Reconstruct the text while preserving whitespace
        perturbed_text = ""
        original_idx = 0
        for i, word in enumerate(words):
            # Find the position of this word in the original text
            word_idx = text.find(word, original_idx)
            
            # Add any whitespace/punctuation before the word
            if word_idx > original_idx:
                perturbed_text += text[original_idx:word_idx]
            
            # Add the perturbed word
            perturbed_text += perturbed_words[i]
            
            # Update the index
            original_idx = word_idx + len(word)
        
        # Add any remaining text
        if original_idx < len(text):
            perturbed_text += text[original_idx:]
        
        return perturbed_text
    
    def apply(self, prompt: str, **kwargs) -> str:
        """
        Apply the SmoothLLM defense to a prompt.
        
        This method doesn't modify the original prompt but returns it as is.
        The actual defense happens in process_response where multiple perturbed
        versions are sampled and their responses are aggregated.
        
        Args:
            prompt: The prompt to defend
            **kwargs: Additional parameters
            
        Returns:
            The original prompt (unmodified)
        """
        # Store the original prompt for later use in process_response
        self.original_prompt = prompt
        
        # Generate and store perturbed samples
        self.perturbed_samples = [
            self._perturb_text(prompt) for _ in range(self.n_samples)
        ]
        
        # For the direct query, return the original prompt
        return prompt
    
    def _aggregate_responses(self, responses: List[str]) -> str:
        """
        Aggregate multiple responses into a single response.
        
        This simple implementation checks if a majority of responses are refusals,
        and if so, returns a refusal. Otherwise, it returns the first non-refusal response.
        
        Args:
            responses: List of model responses to aggregate
            
        Returns:
            The aggregated response
        """
        # Simple refusal detection keywords
        refusal_keywords = [
            "sorry", "I cannot", "I apologize", "I'm not able", 
            "I am not able", "I can't", "I cannot", "I'm unable", 
            "against my ethical guidelines", "against my programming",
            "violation of", "not appropriate", "not ethical"
        ]
        
        # Check which responses are refusals
        is_refusal = []
        for response in responses:
            lower_resp = response.lower()
            if any(keyword in lower_resp for keyword in refusal_keywords):
                is_refusal.append(True)
            else:
                is_refusal.append(False)
        
        # If majority are refusals, return a refusal response
        if sum(is_refusal) > len(is_refusal) / 2:
            for i, refusal in enumerate(is_refusal):
                if refusal:
                    return responses[i]  # Return first refusal
        
        # Otherwise, return the first non-refusal
        for i, refusal in enumerate(is_refusal):
            if not refusal:
                return responses[i]  # Return first non-refusal
        
        # If all are refusals (shouldn't happen due to the majority check above)
        return responses[0]
    
    def process_response(self, response: str, **kwargs) -> str:
        """
        Process the model's response with the SmoothLLM defense.
        
        This method should be called with the response to the original prompt.
        It will query the model with each perturbed sample and then aggregate the results.
        
        Args:
            response: The model's response to the original prompt
            **kwargs: Additional parameters
            
        Returns:
            The processed response
        """
        if not hasattr(self, 'perturbed_samples'):
            logger.warning("SmoothLLM: apply() was not called before process_response()")
            return response
        
        if self.llm_caller is None:
            logger.warning("SmoothLLM: No LLM caller provided, returning original response")
            return response
        
        # Get responses for all perturbed samples
        perturbed_responses = []
        for sample in self.perturbed_samples:
            perturbed_response = self.llm_caller(sample)
            perturbed_responses.append(perturbed_response)
        
        # Add the original response
        all_responses = [response] + perturbed_responses
        
        # Aggregate the responses
        aggregated_response = self._aggregate_responses(all_responses)
        
        return aggregated_response 
