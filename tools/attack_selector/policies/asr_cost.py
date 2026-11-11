from typing import List, Dict, Any, Optional

from policies.base import AttackSelector


def compute_cost_aware_ranking(
    victim_idx: int,
    attack_methods: List[Dict[str, Any]],
    asr_data: List[List[float]],
    opts: Optional[Dict[str, Any]] = None,
) -> List[int]:
    """
    Shared ranking helper combining ASR and cost via a Markov-chain Rank Centrality model.
    """
    opts = opts or {}
    scores = asr_data[victim_idx] if (asr_data and len(asr_data) > victim_idx) else []

    def _cost(i: int) -> float:
        try:
            c = attack_methods[i].get('cost', 0.0)
            return float(c) if c is not None else 0.0
        except Exception:
            return 0.0

    # If ASR data is missing, fall back to cost-only ordering (stable by index).
    if not scores:
        return sorted(range(len(attack_methods)), key=lambda i: _cost(i))

    return _ranking_by_markov_chain(victim_idx, attack_methods, asr_data, opts)


def _ranking_by_markov_chain(
    victim_idx: int,
    attack_methods: List[Dict[str, Any]],
    asr_data: List[List[float]],
    opts: Dict[str, Any],
) -> List[int]:
    from math import exp, log1p

    n = len(attack_methods)
    if n == 0:
        return []

    raw_scores = asr_data[victim_idx] if (asr_data and len(asr_data) > victim_idx) else []
    scores: List[float] = []
    for i in range(n):
        try:
            v = float(raw_scores[i]) if raw_scores else 0.0
        except Exception:
            v = 0.0
        scores.append(v)

    costs: List[float] = []
    for i in range(n):
        try:
            c = attack_methods[i].get('cost', 0.0)
            costs.append(float(c) if c is not None else 0.0)
        except Exception:
            costs.append(0.0)

    alpha_raw = float(opts.get('asr_weight', opts.get('mc_alpha', 0.90)))    # ASR weight
    beta_raw = float(opts.get('cost_weight', opts.get('mc_beta', 0.10)))      # cost weight
    norm = alpha_raw + beta_raw
    if norm <= 0:
        alpha = 0.5
        beta = 0.5
    else:
        alpha = alpha_raw / norm
        beta = beta_raw / norm
    damping = float(opts.get('mc_damping', 0.85))
    iters = int(opts.get('mc_iters', 200))
    tol = float(opts.get('mc_tol', 1e-10))

    def sigmoid(x: float) -> float:
        if x >= 0.0:
            z = exp(-x)
            return 1.0 / (1.0 + z)
        z = exp(x)
        return z / (1.0 + z)

    def zscore(arr: List[float]) -> List[float]:
        m = len(arr)
        if m == 0:
            return []
        mu = sum(arr) / m
        var = sum((x - mu) * (x - mu) for x in arr) / max(1, m - 1)
        sd = var ** 0.5 or 1.0
        return [(x - mu) / sd for x in arr]

    cost_rescale = float(opts.get('mc_cost_rescale', 10000.0))
    if cost_rescale <= 0.0:
        cost_rescale = 1.0

    def _rescale_cost(x: float) -> float:
        # Compress heavy-tailed costs before z-scoring so mid-range attacks separate better.
        scaled = max(0.0, x) / cost_rescale
        return log1p(scaled)

    s_norm = zscore([float(x or 0.0) for x in scores])
    c_norm = zscore([_rescale_cost(float(x)) for x in costs])

    P: List[List[float]] = [[0.0] * n for _ in range(n)]
    for j in range(n):
        denom = 0.0
        pref = [0.0] * n
        for i in range(n):
            if i == j:
                continue
            delta = alpha * (s_norm[i] - s_norm[j]) + beta * (c_norm[j] - c_norm[i])
            pij = sigmoid(delta)
            pref[i] = pij
            denom += pij

        if denom == 0.0:
            w = 1.0 / (n - 1) if n > 1 else 1.0
            for i in range(n):
                if i != j:
                    P[j][i] = w
        else:
            inv = 1.0 / denom
            for i in range(n):
                if i != j:
                    P[j][i] = pref[i] * inv

    u = 1.0 / float(n)
    for j in range(n):
        for i in range(n):
            P[j][i] = damping * P[j][i] + (1.0 - damping) * u

    pi = [u] * n
    for _ in range(iters):
        new = [0.0] * n
        for j in range(n):
            pj = pi[j]
            row = P[j]
            for i in range(n):
                new[i] += pj * row[i]
        ssum = sum(new)
        if ssum > 0.0:
            inv = 1.0 / ssum
            new = [x * inv for x in new]
        diff = sum(abs(new[i] - pi[i]) for i in range(n))
        pi = new
        if diff < tol:
            break

    idx = list(range(n))
    idx.sort(key=lambda i: (-pi[i], costs[i], -(scores[i] or 0.0)))
    return idx


class AsrCostSortSelector(AttackSelector):
    def __init__(self, victim_idx: int, attack_methods: List[Dict[str, Any]], asr_data: List[List[float]], **opts: Any) -> None:
        super().__init__(victim_idx, attack_methods, asr_data, **opts)
        self.min_success_prob: float = float(self.opts.get('min_success_prob', 1e-6))
        self._ranking = compute_cost_aware_ranking(
            victim_idx=self.victim_idx,
            attack_methods=self.attack_methods,
            asr_data=self.asr_data,
            opts=self.opts,
        )
        self._attempts_this_query = 0

    def reset_for_query(self, query_text: str) -> None:
        self._attempts_this_query = 0
        return None

    def select_batch(self, remaining_attack_indices: List[int], batch_size: int) -> List[int]:
        if not remaining_attack_indices or batch_size <= 0:
            return []
        remaining_set = set(remaining_attack_indices)
        ordered_remaining = [i for i in self._ranking if i in remaining_set]
        return ordered_remaining[:max(0, batch_size)]

    def update(self, attack_idx: int, success: bool) -> None:
        self._attempts_this_query += 1
        return None

    @staticmethod
    def add_cli_args(parser) -> None:
        parser.add_argument("--min_success_prob", type=float, default=1e-6,
                           help="Floor for success probability when ASR is zero; avoids infinite ratios")
        parser.add_argument("--mc_cost_rescale", type=float, default=10000.0,
                           help="Divide costs by this value before applying log1p+zscore (default: 10000)")
        parser.add_argument("--asr_weight", type=float, default=1.00,
                           help="Weight on ASR in cost-aware rank centrality (alpha)")
        parser.add_argument("--cost_weight", type=float, default=0.00,
                           help="Weight on cost in cost-aware rank centrality (beta)")

    @staticmethod
    def collect_opts_from_args(args) -> dict:
        return {
            "min_success_prob": getattr(args, "min_success_prob", 1e-6),
            "mc_cost_rescale": getattr(args, "mc_cost_rescale", 10000.0),
            "asr_weight": getattr(args, "asr_weight", 0.90),
            "cost_weight": getattr(args, "cost_weight", 0.10),
        }

    def ranking_by_markov_chain(self) -> List[int]:
        """Backward-compat wrapper; prefer compute_cost_aware_ranking for reuse."""
        return compute_cost_aware_ranking(
            victim_idx=self.victim_idx,
            attack_methods=self.attack_methods,
            asr_data=self.asr_data,
            opts=self.opts,
        )
