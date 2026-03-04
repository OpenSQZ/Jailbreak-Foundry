from typing import List, Dict, Any

from policies.base import AttackSelector


class AsrSortSelector(AttackSelector):
    def __init__(self, victim_idx: int, attack_methods: List[Dict[str, Any]], asr_data: List[List[float]], **opts: Any) -> None:
        super().__init__(victim_idx, attack_methods, asr_data, **opts)
        scores = self.asr_data[self.victim_idx]
        self._ranking = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

    def reset_for_query(self, query_text: str) -> None:
        return None

    def select_batch(self, remaining_attack_indices: List[int], batch_size: int) -> List[int]:
        if not remaining_attack_indices:
            return []
        ordered_remaining = [i for i in self._ranking if i in set(remaining_attack_indices)]
        return ordered_remaining[:max(0, batch_size)]

    def update(self, attack_idx: int, success: bool) -> None:
        return None

    @staticmethod
    def add_cli_args(parser) -> None:
        return None

    @staticmethod
    def collect_opts_from_args(args) -> dict:
        return {}


