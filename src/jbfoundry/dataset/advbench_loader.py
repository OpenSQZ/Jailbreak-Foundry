"""
AdvBench dataset loader.
"""

import logging

logger = logging.getLogger(__name__)

from typing import Union

from .base import JailbreakDatasetLoader, JailbreakDataset



class AdvBenchLoader(JailbreakDatasetLoader):
    """Loader for AdvBench dataset."""
    
    name = "advbench"
    description = "AdvBench dataset loader"
    
    def load(self, dataset_name: str, **kwargs) -> JailbreakDataset:
        """Load AdvBench dataset from Hugging Face."""
        from datasets import load_dataset
        
        try:
            # Load the dataset from Hugging Face with train split
            dataset = load_dataset("walledai/AdvBench", split="train")
            
            # AdvBench has 'prompt' and 'target' columns
            prompts = dataset['prompt']
            targets = dataset['target']
            
            # For AdvBench, we'll use the prompt as behavior and goal
            behaviors = prompts
            goals = prompts  # Same as behavior for AdvBench
            
            # Create categories - AdvBench doesn't have explicit categories
            categories = ["advbench"] * len(behaviors)
            
            return JailbreakDataset(
                behaviors=behaviors,
                goals=goals,
                targets=targets,
                categories=categories
            )
        except Exception as e:
            logger.error(f"Error loading AdvBench dataset: {e}")
            raise


def register_advbench_presets():
    """Register AdvBench dataset presets for auto-discovery."""
    return {
        "advbench": (AdvBenchLoader, {})
    }