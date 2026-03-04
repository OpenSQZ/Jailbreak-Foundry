"""
HarmBench dataset loader.
"""

import logging

logger = logging.getLogger(__name__)

from typing import Union

from .base import JailbreakDatasetLoader, JailbreakDataset



class HarmBenchLoader(JailbreakDatasetLoader):
    """Loader for HarmBench dataset with support for all subsets."""
    
    name = "harmbench"
    description = "HarmBench dataset loader (standard/contextual/copyright subsets)"
    
    def load(self, dataset_name: str, **kwargs) -> JailbreakDataset:
        """Load HarmBench dataset from Hugging Face."""
        from datasets import load_dataset
        
        try:
            # Map dataset names to HarmBench subsets
            harmbench_subsets = {
                "harmbench-standard": "standard",
                "harmbench-contextual": "contextual", 
                "harmbench-copyright": "copyright",
                "harmbench": "standard"  # Default to standard
            }
            
            if dataset_name not in harmbench_subsets:
                raise ValueError(f"Unknown HarmBench dataset: {dataset_name}")
            
            subset = harmbench_subsets[dataset_name]
            
            # Load the dataset with the appropriate subset
            dataset = load_dataset("walledai/HarmBench", subset, split="train")
            
            # HarmBench has different structures based on subset:
            # - 'standard': prompt, category (200 behaviors)
            # - 'contextual': prompt, context, category (100 behaviors)
            # - 'copyright': prompt, tags (100 behaviors)
            
            prompts = dataset['prompt']
            behaviors = prompts
            goals = prompts  # Same as behavior for all HarmBench subsets
            targets = [""] * len(behaviors)  # No target column in any subset
            
            # Handle categories based on subset structure
            if subset == "standard" or subset == "contextual":
                # Both have 'category' column
                categories = dataset['category']
            elif subset == "copyright":
                # Copyright has 'tags' column instead of 'category'
                categories = [str(tag) for tag in dataset['tags']]
            else:
                # Fallback
                categories = [f"harmbench_{subset}"] * len(behaviors)
            
            return JailbreakDataset(
                behaviors=behaviors,
                goals=goals,
                targets=targets,
                categories=categories
            )
        except Exception as e:
            logger.error(f"Error loading HarmBench dataset: {e}")
            raise


def register_harmbench_presets():
    """Register HarmBench dataset presets for auto-discovery."""
    return {
        "harmbench": (HarmBenchLoader, {}),
        "harmbench-standard": (HarmBenchLoader, {}),
        "harmbench-contextual": (HarmBenchLoader, {}),
        "harmbench-copyright": (HarmBenchLoader, {})
    }