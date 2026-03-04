"""
GSM8K (Grade School Math 8K) dataset loader.
"""

import logging

logger = logging.getLogger(__name__)

import re
from typing import Union

from .base import JailbreakDatasetLoader, GSM8KDataset



class GSM8KDatasetLoader(JailbreakDatasetLoader):
    """Loader for GSM8K datasets from Hugging Face."""
    
    name = "gsm8k"
    description = "GSM8K dataset loader for math problems"
    
    def load(self, dataset_name: str, **kwargs) -> GSM8KDataset:
        """
        Load GSM8K dataset from Hugging Face.
        
        Args:
            dataset_name: GSM8K dataset name ("gsm8k" or "gsm8k-evil")
            **kwargs: Additional loading parameters
            
        Returns:
            GSM8KDataset object containing GSM8K math problems
        """
        from datasets import load_dataset
        
        try:
            if dataset_name == "gsm8k":
                # Load standard GSM8K
                dataset = load_dataset("gsm8k", "main")
                test_data = dataset["test"]
                
                behaviors = []
                goals = []
                targets = []
                categories = []
                numeric_answers = []
                
                for item in test_data:
                    question = item["question"]
                    answer_str = item["answer"]
                    # Extract numeric answer from answer string (after ####)
                    numeric_answer = self._extract_numeric_answer(answer_str)
                    
                    behaviors.append(question)
                    goals.append("Solve this math problem step by step")
                    targets.append(f"The answer is: {numeric_answer}")
                    categories.append("math")
                    numeric_answers.append(numeric_answer)
                    
            elif dataset_name == "gsm8k-evil":
                # Load Evil GSM8K dataset
                dataset = load_dataset("ethz-spylab/EvilMath")
                train_data = dataset["train"]
                
                behaviors = []
                goals = []
                targets = []
                categories = []
                numeric_answers = []
                
                for item in train_data:
                    evil_question = item["evil_question"]
                    original_answer = item["original_answer"]
                    # Extract numeric answer
                    numeric_answer = self._extract_numeric_answer(original_answer)
                    
                    behaviors.append(evil_question)
                    goals.append("Solve this math problem step by step")
                    targets.append(f"The answer is: {numeric_answer}")
                    categories.append("evil_math")
                    numeric_answers.append(numeric_answer)
                    
            else:
                raise ValueError(f"Unknown GSM8K dataset: {dataset_name}")
            
            return GSM8KDataset(
                behaviors=behaviors,
                goals=goals,
                targets=targets,
                categories=categories,
                numeric_answers=numeric_answers
            )
            
        except Exception as e:
            logger.error(f"Error loading GSM8K dataset {dataset_name}: {e}")
            raise

    def _extract_numeric_answer(self, answer_str: str) -> float:
        """Extract numeric answer from GSM8K answer string."""
        if '####' in answer_str:
            # Split on #### and take the last part
            try:
                number_str = answer_str.split('####')[-1].strip().replace(',', '')
                return float(number_str)
            except ValueError:
                pass
        
        # Fallback: find any number in the string
        numbers = re.findall(r'-?\d+\.?\d*', answer_str)
        if numbers:
            return float(numbers[-1])
        
        return 0.0


def register_gsm8k_presets():
    """Register GSM8K dataset presets for auto-discovery."""
    return {
        "gsm8k": (GSM8KDatasetLoader, {}),
        "gsm8k-evil": (GSM8KDatasetLoader, {})
    }