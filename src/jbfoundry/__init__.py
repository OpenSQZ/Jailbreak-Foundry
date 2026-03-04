"""
JBFoundry: An integrated framework for automatic LLM jailbreak techniques.
"""

__version__ = "0.1.0"

from .utils.logging import configure_logging

configure_logging()

# Monkey-patch ThreadPoolExecutor to automatically propagate contextvars
# This ensures cost tracking works correctly in multi-threaded attacks
# without requiring any code changes in attack implementations
import concurrent.futures
from contextvars import copy_context

_original_submit = concurrent.futures.ThreadPoolExecutor.submit

def _context_aware_submit(self, fn, /, *args, **kwargs):
    """Submit function with current context automatically copied to worker thread."""
    context = copy_context()
    return _original_submit(self, context.run, fn, *args, **kwargs)

# Apply the monkey-patch
concurrent.futures.ThreadPoolExecutor.submit = _context_aware_submit

from .dataset import read_dataset
from .llm.base import BaseLLM
from .attacks import BaseAttack, list_attacks
from .defenses import BaseDefense, register_defense, get_defense, DefenseFactory, list_defenses
from .evaluation import JailbreakEvaluator

# Import domain-specific evaluators if available
try:
    from .evaluation.wmdp_evaluator import WMDPEvaluator
    WMDP_EVALUATOR_AVAILABLE = True
except ImportError:
    WMDP_EVALUATOR_AVAILABLE = False

try:
    from .evaluation.gsm8k_evaluator import GSM8KEvaluator
    GSM8K_EVALUATOR_AVAILABLE = True
except ImportError:
    GSM8K_EVALUATOR_AVAILABLE = False

# Modular attack system is now the primary interface
# Individual attacks are auto-discovered through the registry
# Defenses are auto-discovered through the defense registry (lazy loading)

__all__ = [
    # Core
    "read_dataset",
    # Logging
    "configure_logging",
    # LLM interfaces
    "BaseLLM",
    # Attacks
    "BaseAttack", "list_attacks",
    # Defenses
    "BaseDefense", "register_defense", "get_defense", "DefenseFactory", "list_defenses",
    # Evaluation
    "JailbreakEvaluator",
]

# Add domain-specific evaluators to exports if available
if WMDP_EVALUATOR_AVAILABLE:
    __all__.append("WMDPEvaluator")

if GSM8K_EVALUATOR_AVAILABLE:
    __all__.append("GSM8KEvaluator") 
