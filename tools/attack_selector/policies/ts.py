import random
from typing import List, Dict, Any
import math

from policies.base import AttackSelector


class ThompsonSamplingSelector(AttackSelector):
    def __init__(self, victim_idx: int, attack_methods: List[Dict[str, Any]], asr_data: List[List[float]], **opts: Any) -> None:
        super().__init__(victim_idx, attack_methods, asr_data, **opts)
        self.ts_prior_weight = float(self.opts.get('ts_prior_weight', 0.25))
        self.ts_kappa_max = int(self.opts.get('ts_kappa_max', 200))
        self.ts_decay = float(self.opts.get('ts_decay', 1.0))
        self.lambda_cost = float(self.opts.get('lambda_cost', 0.0))
        self.diversity_gamma = float(self.opts.get('diversity_gamma', 0.0))
        self.diversity_zeta = float(self.opts.get('diversity_zeta', 0.0))
        self.ts_propensity_samples = int(self.opts.get('ts_propensity_samples', 200))
        # Normalize costs: log1p after rescale, then sigmoid to map into [0,1]
        self.ts_cost_rescale = float(self.opts.get('ts_cost_rescale', 10000.0))
        if self.ts_cost_rescale <= 0.0:
            self.ts_cost_rescale = 1.0

        scores = self.asr_data[self.victim_idx]
        base_n = 520
        kappa = int(min(max(1, round(base_n * self.ts_prior_weight)), self.ts_kappa_max))
        self.alpha: Dict[int, float] = {}
        self.beta_: Dict[int, float] = {}
        self.p_prior: Dict[int, float] = {}
        self._cost_norm: Dict[int, float] = {}
        for i, asr in enumerate(scores):
            p = max(0.0, min(1.0, (asr or 0.0) / 100.0))
            self.p_prior[i] = p
            self.alpha[i] = 1.0 + kappa * p
            self.beta_[i] = 1.0 + kappa * (1.0 - p)

        # Precompute normalized costs per attack
        raw_costs: List[float] = []
        for i in range(len(self.attack_methods)):
            try:
                c = self.attack_methods[i].get('cost', 0.0)
                raw_costs.append(float(c) if c is not None else 0.0)
            except Exception:
                raw_costs.append(0.0)
        transformed = [math.log1p(max(0.0, x) / self.ts_cost_rescale) for x in raw_costs]
        m = len(transformed)
        mu = sum(transformed) / m if m else 0.0
        var = sum((x - mu) * (x - mu) for x in transformed) / max(1, m - 1) if m else 0.0
        sd = var ** 0.5 or 1.0
        norm_costs = [1.0 / (1.0 + math.exp(-((x - mu) / sd))) for x in transformed]
        for i, c_norm in enumerate(norm_costs):
            self._cost_norm[i] = c_norm

        self._used_families: set = set()
        self.last_selection_debug: Dict[int, Dict[str, Any]] = {}

    def reset_for_query(self, query_text: str) -> None:
        self._used_families = set()

    def _get_cost(self, idx: int) -> float:
        # Sigmoid-normalized cost in [0,1]
        return float(self._cost_norm.get(idx, 0.0))

    def _get_family(self, idx: int) -> str:
        info = self.attack_methods[idx]
        return info.get('family') or info.get('paper_name') or info.get('class_name')

    def select_batch(self, remaining_attack_indices: List[int], batch_size: int) -> List[int]:
        if not remaining_attack_indices or batch_size <= 0:
            return []
        pool = list(remaining_attack_indices)
        # Approximate probability of being the best under current posterior (ignoring diversity/cost).
        # This estimates: prob_best[idx] ≈ P(θ_idx = max_j θ_j), using Monte Carlo with S draws.
        prop_counts: Dict[int, int] = {idx: 0 for idx in pool}
        S = max(0, self.ts_propensity_samples)
        if S > 0:
            for _ in range(S):
                draw: Dict[int, float] = {idx: random.betavariate(self.alpha[idx], self.beta_[idx]) for idx in pool}
                best_idx = max(draw, key=draw.get)
                prop_counts[best_idx] += 1
        prop_best: Dict[int, float] = {idx: (prop_counts[idx] / S) if S > 0 else 0.0 for idx in pool}

        # Keep the top-3 arms by prob_best for guidance/inspection.
        sorted_prob = sorted(prop_best.items(), key=lambda kv: kv[1], reverse=True)
        pool_top3 = [
            {
                'attack_idx': idx,
                'class_name': self.attack_methods[idx].get('class_name'),
                'prob_best': prob
            }
            for idx, prob in sorted_prob[:3]
        ]

        # Build debug stats for current pool (pre-selection)
        self.last_selection_debug = {}
        for idx in pool:
            a = self.alpha[idx]
            b = self.beta_[idx]
            mean = a / (a + b) if (a + b) > 0 else 0.0
            var = (a * b) / (((a + b) ** 2) * (a + b + 1)) if (a + b) > 1 else 0.0
            # theta_sample: one Thompson draw from Beta(a,b) used to rank this arm in this round.
            theta = random.betavariate(a, b)
            fam = self._get_family(idx)
            base_score = theta
            # score_pre_pick: base score before same-family collision penalty:
            # score_pre_pick = theta_sample - lambda_cost * cost + diversity_zeta
            # Note: a later per-batch penalty (diversity_gamma) is applied if the family was already chosen.
            score = base_score - self.lambda_cost * self._get_cost(idx) + self.diversity_zeta
            self.last_selection_debug[idx] = {
                'alpha': a,
                'beta': b,
                'mean': mean,
                'var': var,
                # theta_sample: single Beta posterior draw for this arm
                'theta_sample': theta,
                # prob_best: MC-approximated probability this arm's sample is the max among the pool
                'prob_best': prop_best.get(idx, 0.0),
                'family': fam,
                'cost': float(self._get_cost(idx)),
                # score_pre_pick: pre-collision score, before same-family penalty
                'score_pre_pick': score,
                'propensity_samples': S,
                # pool_top3_prob_best: top-3 arms by prob_best in the current pool (for guidance)
                'pool_top3_prob_best': pool_top3,
            }
        chosen: List[int] = []
        used = set()
        while len(chosen) < batch_size and pool:
            scores: Dict[int, float] = {}
            for idx in pool:
                theta = random.betavariate(self.alpha[idx], self.beta_[idx])
                s = theta - self.lambda_cost * self._get_cost(idx)
                fam = self._get_family(idx)
                if fam in used:
                    s -= self.diversity_gamma
                else:
                    s += self.diversity_zeta
                scores[idx] = s
            best = max(scores, key=scores.get)
            chosen.append(best)
            used.add(self._get_family(best))
            pool.remove(best)
        return chosen

    def update(self, attack_idx: int, success: bool) -> None:
        if success:
            self.alpha[attack_idx] = self.ts_decay * self.alpha[attack_idx] + 1.0
        else:
            self.beta_[attack_idx] = self.ts_decay * self.beta_[attack_idx] + 1.0

    @staticmethod
    def add_cli_args(parser) -> None:
        parser.add_argument("--ts_prior_weight", type=float, default=0.15,
                           help="Weight to scale advbench size (520) into kappa; capped by ts_kappa_max")
        parser.add_argument("--ts_kappa_max", type=int, default=100,
                           help="Maximum kappa (prior strength) for TS priors")
        parser.add_argument("--ts_decay", type=float, default=1.0,
                           help="Decay factor applied to alpha/beta upon each update (<=1.0; use <1 for drift)")
        parser.add_argument("--lambda_cost", type=float, default=0.0,
                           help="Cost multiplier in TS scoring; requires 'cost' in attack metadata to take effect")
        parser.add_argument("--diversity_gamma", type=float, default=0.0,
                           help="Penalty when selecting multiple attacks from the same family within a batch")
        parser.add_argument("--diversity_zeta", type=float, default=0.0,
                           help="Bonus for selecting new families within a batch")
        parser.add_argument("--ts_propensity_samples", type=int, default=100,
                           help="Monte Carlo samples to approximate probability of being best (propensity)")
        parser.add_argument("--ts_cost_rescale", type=float, default=10000.0,
                           help="Divide costs by this value before log1p+sigmoid normalization (default: 10000)")

    @staticmethod
    def collect_opts_from_args(args) -> Dict[str, Any]:
        keys = [
            'ts_prior_weight', 'ts_kappa_max', 'ts_decay',
            'lambda_cost', 'diversity_gamma', 'diversity_zeta',
            'ts_propensity_samples', 'ts_cost_rescale'
        ]
        opts: Dict[str, Any] = {}
        for k in keys:
            if hasattr(args, k):
                opts[k] = getattr(args, k)
        return opts
