"""
Dataset base classes and main loading functionality.
"""

import os
import json
import pandas as pd
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
import logging
import re
from abc import ABC, abstractmethod

# Domain-specific loaders will be imported after base classes are defined
WMDP_AVAILABLE = False
GSM8K_AVAILABLE = False


@dataclass
class JailbreakDataset:
    """A dataset of jailbreak prompts, targets, and categories."""
    
    behaviors: List[str]
    goals: List[str]
    targets: List[str]
    categories: List[str]
    
    def __len__(self) -> int:
        """Get the number of behaviors in the dataset."""
        return len(self.behaviors)
    
    def __getitem__(self, idx: int) -> Dict[str, str]:
        """Get a specific behavior by index."""
        return {
            "behavior": self.behaviors[idx],
            "goal": self.goals[idx],
            "target": self.targets[idx],
            "category": self.categories[idx]
        }
    
    def as_dataframe(self) -> pd.DataFrame:
        """Convert the dataset to a pandas DataFrame."""
        return pd.DataFrame({
            "behavior": self.behaviors,
            "goal": self.goals,
            "target": self.targets,
            "category": self.categories
        })
    
    def filter_by_category(self, category: str) -> "JailbreakDataset":
        """Filter the dataset to include only behaviors in the given category."""
        indices = [i for i, c in enumerate(self.categories) if c == category]
        return JailbreakDataset(
            behaviors=[self.behaviors[i] for i in indices],
            goals=[self.goals[i] for i in indices],
            targets=[self.targets[i] for i in indices],
            categories=[self.categories[i] for i in indices]
        )
    
    def sample(self, n: int, seed: Optional[int] = None) -> "JailbreakDataset":
        """Sample n behaviors from the dataset."""
        import random
        random.seed(seed)
        indices = random.sample(range(len(self)), min(n, len(self)))
        return JailbreakDataset(
            behaviors=[self.behaviors[i] for i in indices],
            goals=[self.goals[i] for i in indices],
            targets=[self.targets[i] for i in indices],
            categories=[self.categories[i] for i in indices]
        )


@dataclass
class WMDPDataset(JailbreakDataset):
    """WMDP dataset with multiple choice questions."""
    
    choices: List[List[str]]  # Multiple choice options for each question
    answer_indices: List[int]  # Correct answer indices (0-3 for A-D)
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """Get a specific WMDP question by index."""
        base_item = super().__getitem__(idx)
        base_item.update({
            "choices": self.choices[idx],
            "answer_index": self.answer_indices[idx],
            "correct_answer": "ABCD"[self.answer_indices[idx]]
        })
        return base_item
    
    def sample(self, n: int, seed: Optional[int] = None) -> "WMDPDataset":
        """Sample n behaviors from the WMDP dataset, preserving WMDP-specific fields."""
        import random
        random.seed(seed)
        indices = random.sample(range(len(self)), min(n, len(self)))
        return WMDPDataset(
            behaviors=[self.behaviors[i] for i in indices],
            goals=[self.goals[i] for i in indices],
            targets=[self.targets[i] for i in indices],
            categories=[self.categories[i] for i in indices],
            choices=[self.choices[i] for i in indices],
            answer_indices=[self.answer_indices[i] for i in indices]
        )


@dataclass 
class GSM8KDataset(JailbreakDataset):
    """GSM8K dataset with numerical answers."""
    
    numeric_answers: List[float]  # Ground truth numerical answers
    
    def __getitem__(self, idx: int) -> Dict[str, Any]:
        """Get a specific GSM8K question by index."""
        base_item = super().__getitem__(idx)
        base_item.update({
            "numeric_answer": self.numeric_answers[idx]
        })
        return base_item
    
    def sample(self, n: int, seed: Optional[int] = None) -> "GSM8KDataset":
        """Sample n behaviors from the GSM8K dataset, preserving numeric answers."""
        import random
        random.seed(seed)
        indices = random.sample(range(len(self)), min(n, len(self)))
        return GSM8KDataset(
            behaviors=[self.behaviors[i] for i in indices],
            goals=[self.goals[i] for i in indices],
            targets=[self.targets[i] for i in indices],
            categories=[self.categories[i] for i in indices],
            numeric_answers=[self.numeric_answers[i] for i in indices]
        )


class JailbreakDatasetLoader(ABC):
    """Base class for dataset loaders."""
    
    name: str = "base"
    description: str = "Base dataset loader"
    
    def __init__(self, **kwargs):
        """Initialize loader with parameters."""
        self.params = kwargs
    
    @abstractmethod
    def load(self, dataset_name: str, **kwargs) -> Union[JailbreakDataset, WMDPDataset, GSM8KDataset]:
        """
        Load a dataset.
        
        Args:
            dataset_name: Name or identifier of the dataset to load
            **kwargs: Additional loading parameters
            
        Returns:
            Dataset object containing the loaded data
        """
        pass
    
    @classmethod
    def from_preset(cls, preset_name: str) -> "JailbreakDatasetLoader":
        """Create a loader from a preset."""
        loader_class, params = _get_preset_loader(preset_name)
        return loader_class(**params)


    

# Dictionary of preset loaders
_PRESET_LOADERS = {}

# Import and register domain-specific loaders after base classes are defined
try:
    from .jbb_behaviors_loader import JBBBehaviorsLoader, register_jbb_behaviors_presets
    _PRESET_LOADERS.update(register_jbb_behaviors_presets())
except ImportError:
    pass

try:
    from .advbench_loader import AdvBenchLoader, register_advbench_presets
    _PRESET_LOADERS.update(register_advbench_presets())
except ImportError:
    pass

try:
    from .harmbench_loader import HarmBenchLoader, register_harmbench_presets
    _PRESET_LOADERS.update(register_harmbench_presets())
except ImportError:
    pass

try:
    from .wmdp_loader import WMDPDatasetLoader, register_wmdp_presets
    WMDP_AVAILABLE = True
    _PRESET_LOADERS.update(register_wmdp_presets())
except ImportError:
    WMDP_AVAILABLE = False

try:
    from .gsm8k_loader import GSM8KDatasetLoader, register_gsm8k_presets
    GSM8K_AVAILABLE = True
    _PRESET_LOADERS.update(register_gsm8k_presets())
except ImportError:
    GSM8K_AVAILABLE = False

try:
    from .local_loader import LocalFileLoader, register_local_presets
    _PRESET_LOADERS.update(register_local_presets())
except ImportError:
    pass


def _get_preset_loader(preset_name: str) -> tuple:
    """Get a preset loader by name."""
    if preset_name not in _PRESET_LOADERS:
        raise ValueError(f"Preset '{preset_name}' not found. Available presets: {list(_PRESET_LOADERS.keys())}")
    
    return _PRESET_LOADERS[preset_name]


def load_dataset(dataset_name: str = "jbb-harmful", path: Optional[str] = None) -> Union[JailbreakDataset, WMDPDataset, GSM8KDataset]:
    """
    Load a jailbreak dataset from a file or Hugging Face.
    
    Args:
        dataset_name: Name of the dataset to load. Options are:
            - "jbb-harmful": Harmful behaviors from JBB-Behaviors
            - "jbb-benign": Benign behaviors from JBB-Behaviors
            - "jbb-all": Both harmful and benign behaviors from JBB-Behaviors
            - "advbench": AdvBench dataset
            - "harmbench": HarmBench dataset
            - "harmbench-standard": HarmBench standard subset
            - "harmbench-contextual": HarmBench contextual subset
            - "harmbench-copyright": HarmBench copyright subset
            - "wmdp-bio": WMDP Biology questions
            - "wmdp-chem": WMDP Chemistry questions  
            - "wmdp-cyber": WMDP Cybersecurity questions
            - "gsm8k": GSM8K math problems
            - "gsm8k-evil": Evil GSM8K math problems
            - Path to a local JSON, JSONL, or CSV file
        path: Optional path to a local file. If provided, dataset_name is ignored.
        
    Returns:
        JailbreakDataset, WMDPDataset, or GSM8KDataset object containing the loaded data
    """
    if path:
        # Load from local file
        from .local_loader import LocalFileLoader
        loader = LocalFileLoader()
        return loader.load(path)
    
    # Check if it's a preset
    if dataset_name in _PRESET_LOADERS:
        loader_class, params = _PRESET_LOADERS[dataset_name]
        loader = loader_class()
        return loader.load(dataset_name, **params)
    
    # Try to determine loader based on dataset name pattern
    if dataset_name.startswith("wmdp"):
        if WMDP_AVAILABLE:
            from .wmdp_loader import WMDPDatasetLoader
            loader = WMDPDatasetLoader()
            return loader.load(dataset_name)
        else:
            raise ImportError("WMDP loader not available. Please install required dependencies.")
    elif dataset_name.startswith("gsm8k"):
        if GSM8K_AVAILABLE:
            from .gsm8k_loader import GSM8KDatasetLoader  
            loader = GSM8KDatasetLoader()
            return loader.load(dataset_name)
        else:
            raise ImportError("GSM8K loader not available. Please install required dependencies.")
    else:
        # Assume dataset_name is a path and try local file loader
        from .local_loader import LocalFileLoader
        loader = LocalFileLoader()
        return loader.load(dataset_name)


# Maintain backward compatibility
read_dataset = load_dataset