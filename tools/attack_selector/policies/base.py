from typing import List, Dict, Any


class AttackSelector:
    def __init__(self, victim_idx: int, attack_methods: List[Dict[str, Any]], asr_data: List[List[float]], **opts: Any) -> None:
        self.victim_idx = victim_idx
        self.attack_methods = attack_methods
        self.asr_data = asr_data
        self.opts = opts

    def reset_for_query(self, query_text: str) -> None:
        return None

    def select_batch(self, remaining_attack_indices: List[int], batch_size: int) -> List[int]:
        raise NotImplementedError

    def update(self, attack_idx: int, success: bool) -> None:
        return None


