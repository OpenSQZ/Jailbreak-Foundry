"""
JBFoundry dataset module.

This module provides dataset loading functionality for various jailbreak datasets
including JailbreakBench Behaviors, WMDP, GSM8K, and local file formats.
"""

# Import core classes and functions from base module
from .base import (
    JailbreakDataset,
    WMDPDataset, 
    GSM8KDataset,
    JailbreakDatasetLoader,
    load_dataset,
    read_dataset,  # Backward compatibility alias
    _PRESET_LOADERS
)

# Import loaders (optional imports with graceful degradation)
try:
    from .wmdp_loader import WMDPDatasetLoader
    WMDP_AVAILABLE = True
except ImportError:
    WMDP_AVAILABLE = False

try:
    from .gsm8k_loader import GSM8KDatasetLoader
    GSM8K_AVAILABLE = True
except ImportError:
    GSM8K_AVAILABLE = False

try:
    from .local_loader import LocalFileLoader
    LOCAL_AVAILABLE = True
except ImportError:
    LOCAL_AVAILABLE = False

# Public API - maintain exact same interface as original dataset.py
__all__ = [
    # Core data classes (exact same names as before)
    "JailbreakDataset",
    "WMDPDataset",
    "GSM8KDataset",
    
    # Main loading functions (exact same names as before)  
    "read_dataset",      # Original function name - MUST be preserved
    "load_dataset",      # New name (alias to read_dataset)
    
    # Loader classes (new functionality, but backward compatible)
    "JailbreakDatasetLoader",
    
    # Availability flags (useful for conditional imports)
    "WMDP_AVAILABLE",
    "GSM8K_AVAILABLE", 
    "LOCAL_AVAILABLE"
]

# Optional exports if loaders are available
if WMDP_AVAILABLE:
    __all__.extend(["WMDPDatasetLoader"])

if GSM8K_AVAILABLE:
    __all__.extend(["GSM8KDatasetLoader"])
    
if LOCAL_AVAILABLE:
    __all__.extend(["LocalFileLoader"])