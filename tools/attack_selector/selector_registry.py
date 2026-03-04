from typing import Type, Dict, Any, List

from policies.base import AttackSelector
from policies.asr_sort import AsrSortSelector
from policies.ts import ThompsonSamplingSelector
from policies.asr_cost import AsrCostSortSelector
from policies.llm_select import LLMSortSelector


_REGISTRY: Dict[str, Type[AttackSelector]] = {
    "asr_sort": AsrSortSelector,
    "ts": ThompsonSamplingSelector,
    "asr_cost": AsrCostSortSelector,
    "llm_select": LLMSortSelector,
}


def get_selector_class(name: str) -> Type[AttackSelector]:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown selector '{name}'. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name]


def add_selector_cli_args(parser, selector_name: str) -> None:
    """Let specific selector inject its own CLI flags."""
    cls = get_selector_class(selector_name)
    if hasattr(cls, 'add_cli_args') and callable(getattr(cls, 'add_cli_args')):
        cls.add_cli_args(parser)  # type: ignore


def collect_selector_opts(args: Any, selector_name: str) -> Dict[str, Any]:
    """Collect selector-specific options from parsed args into a dict."""
    cls = get_selector_class(selector_name)
    if hasattr(cls, 'collect_opts_from_args') and callable(getattr(cls, 'collect_opts_from_args')):
        return cls.collect_opts_from_args(args)  # type: ignore
    return {}


