"""
WMDP (Weapons of Mass Destruction Proxy) dataset loader.
"""

import logging

logger = logging.getLogger(__name__)

from typing import Union

from .base import JailbreakDatasetLoader, WMDPDataset



class WMDPDatasetLoader(JailbreakDatasetLoader):
    """Loader for WMDP datasets from Hugging Face."""
    
    name = "wmdp"
    description = "WMDP dataset loader for biology, chemistry, and cybersecurity questions"
    
    def load(self, dataset_name: str, **kwargs) -> WMDPDataset:
        """
        Load WMDP dataset from Hugging Face.
        
        Args:
            dataset_name: WMDP dataset name (e.g., "wmdp-bio", "wmdp-chem", "wmdp-cyber")
            **kwargs: Additional loading parameters
            
        Returns:
            WMDPDataset object containing WMDP questions and choices
        """
        from datasets import load_dataset
        
        try:
            # Map dataset names to WMDP splits
            wmdp_splits = {
                "wmdp-bio": "wmdp-bio",
                "wmdp-chem": "wmdp-chem", 
                "wmdp-cyber": "wmdp-cyber"
            }
            
            if dataset_name not in wmdp_splits:
                raise ValueError(f"Unknown WMDP dataset: {dataset_name}")
            
            # Load from Hugging Face
            dataset = load_dataset("cais/wmdp", wmdp_splits[dataset_name])
            test_data = dataset["test"]
            
            # Extract questions and choices
            behaviors = []
            goals = []
            targets = []
            categories = []
            choices = []
            answer_indices = []
            
            for item in test_data:
                question = item["question"]
                choice_list = item["choices"]  # choices are already in a list
                answer_idx = item["answer"]  # answer is already an index (0-3)
                
                behaviors.append(question)
                goals.append(f"Answer this {dataset_name.split('-')[1]} question correctly")
                targets.append(f"The correct answer is: {['A', 'B', 'C', 'D'][answer_idx]}")
                categories.append(dataset_name.split('-')[1])  # bio, chem, cyber
                choices.append(choice_list)
                answer_indices.append(answer_idx)
            
            return WMDPDataset(
                behaviors=behaviors,
                goals=goals,
                targets=targets,
                categories=categories,
                choices=choices,
                answer_indices=answer_indices
            )
            
        except Exception as e:
            logger.error(f"Error loading WMDP dataset {dataset_name}: {e}")
            raise


def register_wmdp_presets():
    """Register WMDP dataset presets for auto-discovery."""
    return {
        "wmdp-bio": (WMDPDatasetLoader, {}),
        "wmdp-chem": (WMDPDatasetLoader, {}),
        "wmdp-cyber": (WMDPDatasetLoader, {})
    }