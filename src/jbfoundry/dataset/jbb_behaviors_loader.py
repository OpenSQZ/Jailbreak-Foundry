"""
JailbreakBench Behaviors dataset loader.
"""

import logging

logger = logging.getLogger(__name__)

from typing import Union

from .base import JailbreakDatasetLoader, JailbreakDataset



class JBBBehaviorsLoader(JailbreakDatasetLoader):
    """Loader for JailbreakBench Behaviors dataset."""
    
    name = "jbb_behaviors"
    description = "JailbreakBench Behaviors dataset loader"
    
    def load(self, dataset_name: str, **kwargs) -> JailbreakDataset:
        """Load JBB-Behaviors dataset from Hugging Face."""
        from datasets import load_dataset
        
        try:
            # Map dataset names to JBB splits
            jbb_splits = {
                "jbb-harmful": "harmful",
                "jbb-benign": "benign",
                "jbb-all": "all"
            }
            
            if dataset_name not in jbb_splits:
                raise ValueError(f"Unknown JBB dataset: {dataset_name}")
            
            split = jbb_splits[dataset_name]
            
            # Add the required 'behaviors' configuration name
            dataset = load_dataset("JailbreakBench/JBB-Behaviors", "behaviors", split=split)
            
            # Convert to JailbreakDataset
            return JailbreakDataset(
                behaviors=dataset["Behavior"],
                goals=dataset["Goal"],
                targets=dataset["Target"],
                categories=dataset["Category"]
            )
        except Exception as e:
            logger.error(f"Error loading JBB-Behaviors dataset: {e}")
            raise


def register_jbb_behaviors_presets():
    """Register JBB Behaviors dataset presets for auto-discovery."""
    return {
        "jbb-harmful": (JBBBehaviorsLoader, {}),
        "jbb-benign": (JBBBehaviorsLoader, {}),
        "jbb-all": (JBBBehaviorsLoader, {})
    }