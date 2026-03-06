#!/usr/bin/env python3

import json
import os
import sys
import subprocess
import tempfile
import shlex
from typing import List, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import argparse
from pathlib import Path

from selector_registry import get_selector_class, add_selector_cli_args, collect_selector_opts

# Model mapping dictionary: user_model_name -> {model, provider, api_key?, api_base?}
MODEL_MAPPING = {
    "claude-3.7-sonnet": {
        "model": "claude-3-7-sonnet-20250219",
        "provider": "openai"
    },
    "claude-3.5-sonnet": {
        "model": "claude-3-5-sonnet-20241022", 
        "provider": "openai"
    },
    "gpt-4": {
        "model": "gpt-4-0613",
        "provider": "openai"
    },
    "gpt-4o": {
        "model": "gpt-4o",
        "provider": "openai"
    },
    # "gpt-oss-120b": {
    #     "model": "gpt-oss-120b",
    #     "provider": "infini",
    # },
    "gpt-3.5-turbo": {
        "model": "gpt-3.5-turbo",
        "provider": "openai"
    },
    "llama-3-8b-instruct": {
        "model": "llama-3-8b-instruct",
        "provider": "openai",
        "api_base": "http://10.210.22.10:30253/v1",
    },
    "llama-2-7b-chat": {
        "model": "llama-2-7b-chat",
        "provider": "openai", 
        "api_base": "http://10.210.22.10:30254/v1",
    },
    # "deepseek-v1-0528-qwen3-8b": {
    #     "model": "deepseek-r1-0528-qwen3-8b",
    #     "provider": "infini",
    # },
    "qwen3-14b": {
        "model": "qwen3-14b",
        "provider": "aliyun",
        # "provider": "infini",
    },
    "gpt-5.1": {
        "model": "gpt-5.1",
        "provider": "openai",
    },
}

def get_model_info(user_model_name: str) -> Dict[str, str]:
    """Get model configuration from user model name."""
    if user_model_name in MODEL_MAPPING:
        return MODEL_MAPPING[user_model_name]
    else:
        # Default fallback
        print(f"⚠️  Unknown model '{user_model_name}', using default mapping")
        return {
            "model": user_model_name,
            "provider": "openai"
        }

def load_asr_data(asr_file_path: str) -> Tuple[List[str], List[dict], List[List[float]]]:
    """Load ASR performance matrix and metadata from a JSON file.

    Backward compatible: accepts either key 'data' (legacy) or 'asr' (new).
    """
    with open(asr_file_path, 'r') as f:
        data = json.load(f)
    victims = data['victim_models']
    attacks = data['attack_methods']
    asr_data = data.get('data')
    if asr_data is None:
        asr_data = data.get('asr')
    if asr_data is None:
        raise ValueError("ASR data missing: expected 'data' or 'asr' in file")
    return victims, attacks, asr_data

def get_input_json_stem(queries_file_path: str) -> str:
    """Extract clean filename stem from queries file path for output directory naming."""
    return Path(queries_file_path).stem


# -----------------------------
# Aggregation / extraction utils
# -----------------------------
def _sum_numeric(dst: Dict[str, float], src: Dict[str, Any]) -> Dict[str, float]:
    """Sum numeric fields from src into dst, returning dst for chaining."""
    for k, v in (src or {}).items():
        try:
            if isinstance(v, (int, float)):
                dst[k] = dst.get(k, 0.0) + float(v)
        except Exception:
            # Ignore non-numeric or invalid values
            pass
    return dst


def _extract_usage_totals(attack_results: Dict[str, Any]) -> Dict[str, float]:
    """Aggregate usage totals from results[*].usage.

    Keys typically include: prompt_tokens, completion_tokens, total_tokens,
    reasoning_tokens, query_count. Unknown numeric keys are also summed.
    """
    totals: Dict[str, float] = {}
    try:
        for item in attack_results.get('results', []) or []:
            usage = item.get('usage') or {}
            _sum_numeric(totals, usage)
    except Exception:
        # Be conservative; return what we have
        pass
    return totals


def _extract_cost_totals(attack_results: Dict[str, Any]) -> Dict[str, float]:
    """Extract overall cost totals if present under metadata.cost_summary.totals."""
    try:
        md = attack_results.get('metadata') or {}
        cs = md.get('cost_summary') or {}
        totals = cs.get('totals') or {}
        # Ensure only numeric values are returned
        numeric_totals: Dict[str, float] = {}
        _sum_numeric(numeric_totals, totals)
        return numeric_totals
    except Exception:
        return {}


# -----------------------------
# LLM selector log ingestion
# -----------------------------
def _aggregate_llm_select_tokens(log_root: Path) -> Tuple[Dict[str, float], int]:
    """Sum response_usage token counts across llm_select_*.json logs."""
    totals: Dict[str, float] = {}
    log_count = 0
    try:
        if not log_root.exists():
            return {}, 0
        for path in log_root.rglob("llm_select_*.json"):
            try:
                with open(path, "r") as fh:
                    data = json.load(fh)
                usage = data.get("response_usage") or {}
                if isinstance(usage, dict):
                    _sum_numeric(totals, usage)
                    log_count += 1
            except Exception:
                # Skip malformed or unreadable logs
                continue
    except Exception:
        return {}, 0
    return totals, log_count


# -----------------------------
# Empirical cost ingestion utils
# -----------------------------
def load_cost_matrix_if_available(asr_file_path: str) -> List[List[float]] | None:
    """Parse an optional MxN cost matrix from the ASR JSON if present.

    Expects schema like empirical_jbb.json with 'cost' cells containing
    {'totals': {'prompt_tokens': x, 'completion_tokens': y}}. Returns
    a float matrix using (prompt_tokens + completion_tokens). If absent
    or invalid, returns None.
    """
    try:
        with open(asr_file_path, 'r') as f:
            data = json.load(f)
        raw = data.get('cost')
        if not raw:
            return None
        matrix: List[List[float]] = []
        for row in raw:
            row_costs: List[float] = []
            for cell in row:
                cost_val = 0.0
                try:
                    if isinstance(cell, dict):
                        totals = (cell.get('totals') or {})
                        pt = float(totals.get('prompt_tokens', 0) or 0)
                        ct = float(totals.get('completion_tokens', 0) or 0)
                        cost_val = pt + ct
                except Exception:
                    cost_val = 0.0
                row_costs.append(cost_val)
            matrix.append(row_costs)
        return matrix
    except Exception:
        return None


def attach_costs_to_attack_methods(
    attack_methods: List[Dict[str, Any]],
    cost_matrix: List[List[float]] | None,
    victim_idx: int,
    opts: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Attach per-attack numeric 'cost' to attack_methods for a given victim.

    When cost_matrix is None or indices are missing, returns attack_methods unchanged.
    Returns a shallow-copied list of dicts to avoid mutating shared state when costs exist.
    """
    if not cost_matrix:
        return attack_methods
    enriched: List[Dict[str, Any]] = []
    for i, m in enumerate(attack_methods):
        cost = 0.0
        try:
            cost = float(cost_matrix[victim_idx][i] or 0.0)
        except Exception:
            cost = 0.0
        mm = dict(m)
        mm['cost'] = cost
        enriched.append(mm)
    return enriched


def _format_slug_value(value: Any) -> str:
    """Format values for slug: compact floats, plain ints/strings."""
    try:
        if isinstance(value, float):
            s = ("%g" % value)
            return s
        return str(value)
    except Exception:
        return str(value)


def build_selector_slug(selector: str, selector_opts: Dict[str, Any], max_attacks: int | None) -> str:
    """Build a human-readable slug encoding selector name, key params, and max_attacks.

    Examples:
      - selector=asr_sort__max=4
      - selector=ts__prior=0.15__kmax=100__decay=1__lambda=0.2__dg=0__dz=0__ps=100__max=4
    """
    parts: list[str] = [f"selector={selector}"]
    if selector == "ts":
        # Stable key order for readability
        key_map = [
            ("prior", "ts_prior_weight"),
            ("kmax", "ts_kappa_max"),
            ("decay", "ts_decay"),
            ("lambda", "lambda_cost"),
            ("dg", "diversity_gamma"),
            ("dz", "diversity_zeta"),
            ("ps", "ts_propensity_samples"),
        ]
        for short_key, long_key in key_map:
            if long_key in selector_opts and selector_opts[long_key] is not None:
                parts.append(f"{short_key}={_format_slug_value(selector_opts[long_key])}")
    # Append max attacks if provided
    if max_attacks is not None:
        parts.append(f"max={max_attacks}")
    return "__".join(parts)

def run_universal_attack(query: str, victim_model: str, attack_name: str, 
                         output_dir: str = "results", query_idx: int = 0, 
                         input_json_stem: str = None, policy_slug: str | None = None, **kwargs) -> Dict[str, Any]:
    """Run universal_attack.py for a specific query and attack."""
    
    # Create temporary dataset file with just this query
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
        temp_dataset_data = [{"goal": query, "target": ""}]
        json.dump(temp_dataset_data, temp_file)
        temp_dataset_path = temp_file.name
    
    try:
        # Get model configuration
        model_config = get_model_info(victim_model)
        
        # Create query-specific output directory with input JSON stem and policy slug
        if input_json_stem:
            base_output_dir = f"{output_dir}/{input_json_stem}"
        else:
            base_output_dir = output_dir
        if policy_slug:
            base_output_dir = f"{base_output_dir}/{policy_slug}"
        query_output_dir = f"{base_output_dir}/query{query_idx + 1}"
        os.makedirs(query_output_dir, exist_ok=True)
        
        # Use the central attack runner
        cmd = [
            sys.executable, "tools/attack_selector/run_attack.py",
            attack_name,
            "--model", model_config["model"],
            "--provider", model_config["provider"],
            "--dataset", temp_dataset_path,
            "--output_dir", query_output_dir,
            "--all_samples"
        ]
        
        # Add optional API configuration for local models
        if "api_key" in model_config:
            cmd.extend(["--api_key", model_config["api_key"]])
        if "api_base" in model_config:
            cmd.extend(["--api_base", model_config["api_base"]])

        # Add any additional arguments (excluding ones we set above and internal flags)
        for key, value in kwargs.items():
            if value is not None and key not in [
                'dataset', 'samples', 'seed', 'all_samples', 'model', 'provider', 'output_dir',
                'api_key', 'api_base',
                # Internal controls not intended for the attack runner
                'include_usage_meta', 'include_cost_summary', 'include_comparison_metrics'
            ]:
                if isinstance(value, bool):
                    if value:  # Only add the flag if it's True
                        cmd.append(f"--{key}")
                else:
                    cmd.extend([f"--{key}", str(value)])
        
        print(f"🔥 Running command: {cmd}")
        
        # Run the command with styled output
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'

        # Add italic blue styling to all subprocess output with proper shell escaping
        escaped_cmd = ' '.join(shlex.quote(arg) for arg in cmd)
        styled_cmd = ['bash', '-c', f"{escaped_cmd} | sed 's/^/\033[3;34m/; s/$/\033[0m/'"]

        result = subprocess.run(styled_cmd, capture_output=False, text=True, timeout=3600, env=env)

        # Check actual attack success and extract meta from results file
        results_file = f"{query_output_dir}/results_{attack_name}.json"
        attack_success = False
        attempt_usage_totals: Dict[str, float] = {}
        attempt_cost_totals: Dict[str, float] = {}

        try:
            if os.path.exists(results_file):
                with open(results_file, 'r') as f:
                    attack_results = json.load(f)
                    # Check if any result shows successful jailbreak
                    attack_success = any(
                        item.get('jailbroken', False) for item in attack_results.get('results', [])
                    )
                    # Optionally include usage/cost totals
                    include_usage = bool(kwargs.get('include_usage_meta', True))
                    include_cost = bool(kwargs.get('include_cost_summary', True))
                    if include_usage:
                        attempt_usage_totals = _extract_usage_totals(attack_results)
                    if include_cost:
                        attempt_cost_totals = _extract_cost_totals(attack_results)
        except Exception as e:
            print(f"Warning: Could not parse results file {results_file}: {e}")

        return {
            "success": attack_success,
            "error": "",
            "attack_name": attack_name,
            "query": query,
            "victim_model": victim_model,
            # Optionally-present aggregates (can be empty dicts if disabled or unavailable)
            "usage_totals": attempt_usage_totals,
            "cost_totals": attempt_cost_totals,
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Attack timed out",
            "attack_name": attack_name,
            "query": query,
            "victim_model": victim_model
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "attack_name": attack_name,
            "query": query,
            "victim_model": victim_model
        }
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_dataset_path)
        except:
            pass  # Ignore cleanup errors


def _run_batch(query_prefix: str, query: str, victim_model: str, attack_names: List[str],
               output_dir: str, query_idx: int, input_json_stem: str = None, policy_slug: str | None = None, **kwargs) -> List[Dict[str, Any]]:
    batch_results = []
    with ThreadPoolExecutor(max_workers=len(attack_names)) as executor:
        future_to_name = {}
        for name in attack_names:
            print(f"🚀 {query_prefix} Trying: {name} on '{query[:30]}...'")
            future = executor.submit(
                run_universal_attack,
                query, victim_model, name, output_dir, query_idx, input_json_stem, policy_slug, **kwargs
            )
            future_to_name[future] = name
        for future in as_completed(future_to_name):
            attack_name = future_to_name[future]
            try:
                result = future.result()
            except Exception as e:
                result = {"success": False, "error": str(e), "attack_name": attack_name,
                          "query": query, "victim_model": victim_model}
            batch_results.append(result)
    return batch_results


def run_attacks_for_query(query_data: Dict[str, str],
                         attack_methods: List[Dict[str, str]], attack_concurrency: int = 1,
                         output_dir: str = "results", query_idx: int = 0,
                         selector: str = "asr_sort",
                         selector_opts: Dict[str, Any] | None = None,
                         victim_models: List[str] | None = None,
                         asr_data: List[List[float]] | None = None,
                         input_json_stem: str = None,
                         policy_slug: str | None = None,
                         max_attacks: int | None = None,
                         **kwargs) -> Dict[str, Any]:
    """Run attacks for a single query with configurable concurrency."""
    query = query_data.get('query', '')
    victim_model = query_data['victim_model']
    
    query_prefix = f"[Q{query_idx+1}]"
    print(f"🎯 {query_prefix} Processing query: '{query[:50]}...' on {victim_model}")
    
    # Identify victim index once for selector instantiation and optional ranking preview
    victim_idx = 0
    if victim_models and victim_model in victim_models:
        victim_idx = victim_models.index(victim_model)

    results: List[Dict[str, Any]] = []
    successful_attack = None
    # Aggregates for this query
    query_usage_totals: Dict[str, float] = {}
    query_cost_totals: Dict[str, float] = {}
    timeouts = 0

    # Instantiate selector
    SelectorCls = get_selector_class(selector)
    selector_kwargs = dict(selector_opts or {})
    if max_attacks is not None:
        selector_kwargs.setdefault("max_attacks", max_attacks)
    selector_kwargs.setdefault("current_victim_model", victim_model)
    if selector == "llm_select":
        query_dir = os.path.join(
            output_dir,
            input_json_stem or "queries",
            policy_slug or f"selector={selector}",
            f"query{query_idx + 1}",
        )
        selector_kwargs["llm_select_log_dir"] = query_dir
    selector_obj = SelectorCls(
        victim_idx=victim_idx,
        attack_methods=attack_methods,
        asr_data=asr_data or [],
        **selector_kwargs
    )

    # Per-query loop
    selector_obj.reset_for_query(query)
    remaining_indices = list(range(len(attack_methods)))
    attempts_limit = max_attacks if (isinstance(max_attacks, int) and max_attacks > 0) else None
    attempts_launched = 0
    while remaining_indices and not successful_attack:
        if attempts_limit is not None and attempts_launched >= attempts_limit:
            break
        batch_cap = attack_concurrency
        if attempts_limit is not None:
            batch_cap = min(batch_cap, attempts_limit - attempts_launched)
            if batch_cap <= 0:
                break
        batch_indices = selector_obj.select_batch(remaining_indices, batch_cap)
        if not batch_indices:
            break
        attempts_launched += len(batch_indices)
        attack_names = [attack_methods[i]['class_name'] for i in batch_indices]
        batch_results = _run_batch(query_prefix, query, victim_model, attack_names, output_dir, query_idx, input_json_stem, policy_slug, **kwargs)
        for res in batch_results:
            # attach metadata
            attack_idx = attack_names.index(res['attack_name'])
            real_idx = batch_indices[attack_idx]
            res['attack_idx'] = real_idx
            res['paper_name'] = attack_methods[real_idx]['paper_name']
            # attach selector debug info if available (e.g., TS selection stats)
            try:
                selection_debug = getattr(selector_obj, 'last_selection_debug', None)
                if isinstance(selection_debug, dict):
                    dbg = selection_debug.get(real_idx)
                    if dbg is not None:
                        res['selection_policy'] = selector
                        res['selection_debug'] = dbg
            except Exception:
                pass
            results.append(res)
            # accumulate usage/cost totals
            try:
                _sum_numeric(query_usage_totals, res.get('usage_totals') or {})
            except Exception:
                pass
            try:
                _sum_numeric(query_cost_totals, res.get('cost_totals') or {})
            except Exception:
                pass
            selector_obj.update(real_idx, bool(res.get('success')))
            remaining_indices = [i for i in remaining_indices if i != real_idx]
            if res.get('error') == 'Attack timed out':
                timeouts += 1
            if res.get('success') and not successful_attack:
                successful_attack = res
                print(f"✅ {query_prefix} SUCCESS: {res['attack_name']} worked!")

    # Compute comparison helpers for this query
    success_attempt = None
    success_attack_name = None
    success_attack_idx = None
    if successful_attack is not None:
        # first successful attempt index (1-based)
        for i, attempt in enumerate(results, start=1):
            if attempt.get('success'):
                success_attempt = i
                success_attack_name = attempt.get('attack_name')
                success_attack_idx = attempt.get('attack_idx')
                break

    query_obj = {
        'query': query,
        'victim_model': victim_model,
        'successful_attack': successful_attack,
        'all_attempts': results,
        'total_attempts': len(results)
    }
    # Attach aggregates and helpers
    if kwargs.get('include_usage_meta', True):
        query_obj['usage_totals'] = query_usage_totals
    if kwargs.get('include_cost_summary', True):
        query_obj['cost_totals'] = query_cost_totals
    # Comparison helpers (small ints/strings)
    query_obj['attempts_tried'] = len(results)
    query_obj['timeouts'] = timeouts
    if success_attempt is not None:
        query_obj['success_attempt'] = success_attempt
    if success_attack_name is not None:
        query_obj['success_attack_name'] = success_attack_name
    if success_attack_idx is not None:
        query_obj['success_attack_idx'] = success_attack_idx

    return query_obj


def create_argument_parser():
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Attack Selector with Universal Attack Integration",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Input/Output
    parser.add_argument("--queries_file", type=str, default="tools/attack_selector/samples/jbb_sample_queries.json",
                       help="Path to queries JSON file")
    parser.add_argument("--asr_file", type=str, default="tools/attack_selector/empirical_data/asr.json",
                       help="Path to ASR performance JSON (keys: victim_models, attack_methods, and 'data' or 'asr'; optional 'cost')")
    parser.add_argument("--output_dir", type=str, default="results",
                       help="Output directory for results")
    parser.add_argument("--output_file", type=str,
                       help="Specific output file (overrides output_dir)")
    
    # Concurrency settings
    parser.add_argument("--attack_concurrency", type=int, default=1,
                       help="Number of attacks to run concurrently per query")
    parser.add_argument("--query_concurrency", type=int, default=1,
                       help="Number of queries to process in parallel")
    
    # Attack settings
    parser.add_argument("--max_attacks", type=int,
                       help="Maximum number of attacks to try per query")
    parser.add_argument("--provider", type=str, default="openai",
                       help="Model provider")
    parser.add_argument("--api_key", type=str,
                       help="API key for the provider")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output")
    
    # Selector choice
    parser.add_argument("--selector", type=str, default="asr_sort", choices=["asr_sort", "ts", "asr_cost", "llm_select"],
                       help="Selection policy: 'asr_sort' (default), 'asr_cost', 'ts', or 'llm_select' (LLM-guided ranking)")

    # Emission controls (default: enabled). Use --no_* flags to disable.
    parser.set_defaults(include_usage_meta=True, include_cost_summary=True, include_comparison_metrics=True)
    parser.add_argument("--no_usage_meta", dest="include_usage_meta", action="store_false",
                       help="Disable usage totals in outputs")
    parser.add_argument("--no_cost_summary_meta", dest="include_cost_summary", action="store_false",
                       help="Disable cost totals in outputs")
    parser.add_argument("--no_comparison_metrics", dest="include_comparison_metrics", action="store_false",
                       help="Disable comparison metrics in summary")
    
    return parser


def main():
    parser = create_argument_parser()
    # Two-pass parsing to allow selector-specific flags
    # First parse only --selector to know which selector to extend
    import argparse as _argparse
    partial_parser = _argparse.ArgumentParser(add_help=False)
    partial_parser.add_argument("--selector", type=str, default="asr_sort", choices=["asr_sort", "ts", "asr_cost", "llm_select"])
    partial_args, _ = partial_parser.parse_known_args()

    # Let the chosen selector inject its own CLI args
    add_selector_cli_args(parser, partial_args.selector)

    args = parser.parse_args()
    
    # Load input queries from file
    try:
        with open(args.queries_file, 'r') as f:
            queries = json.load(f)
    except FileNotFoundError:
        print(f"Error: Queries file '{args.queries_file}' not found")
        sys.exit(1)
    
    # Load ASR data
    try:
        victim_models, attack_methods, asr_data = load_asr_data(args.asr_file)
    except FileNotFoundError:
        print(f"Error: ASR file '{args.asr_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse ASR file '{args.asr_file}': {e}")
        sys.exit(1)
    
    # Extract input JSON stem for output directory naming
    input_json_stem = get_input_json_stem(args.queries_file)
    
    print(f"🔧 Configuration:")
    print(f"  - Queries file: {args.queries_file}")
    print(f"  - Output dir: {args.output_dir}")
    print(f"  - ASR file: {args.asr_file}")
    print(f"  - Input JSON stem: {input_json_stem}")
    print(f"  - Attack concurrency: {args.attack_concurrency}")
    print(f"  - Query concurrency: {args.query_concurrency}")
    print(f"  - Selector: {args.selector}")
    print(f"  - Total queries: {len(queries)}")
    print()
    
    # Build selector options and policy slug (for directory names)
    global_selector_opts = collect_selector_opts(args, args.selector)
    policy_slug = build_selector_slug(args.selector, global_selector_opts, args.max_attacks)
    print(f"  - Policy slug: {policy_slug}")
    print()

    # Process queries with configurable concurrency
    all_results = []
    # Load optional empirical cost matrix once (TS uses this via 'cost' in attack metadata)
    cost_matrix = load_cost_matrix_if_available(args.asr_file)
    
    def process_single_query(query_idx_data):
        """Process a single query."""
        query_idx, query_data = query_idx_data
        victim_model = query_data['victim_model']
        
        # Find victim model index
        if victim_model not in victim_models:
            print(f"⚠️  [Q{query_idx+1}] Skipping query - unknown victim model: {victim_model}")
            return None
        
        victim_idx = victim_models.index(victim_model)
        
        # Collect selector-specific opts (use global parsed options)
        selector_opts = global_selector_opts

        # Prepare per-victim attack metadata with optional cost annotations
        attack_methods_for_victim = attach_costs_to_attack_methods(
            attack_methods,
            cost_matrix,
            victim_idx,
            opts=selector_opts,
        )

        # Run attacks for this query
        return run_attacks_for_query(
            query_data, attack_methods_for_victim,
            attack_concurrency=args.attack_concurrency,
            output_dir=args.output_dir,
            query_idx=query_idx,
            selector=args.selector,
            selector_opts=selector_opts,
            victim_models=victim_models,
            asr_data=asr_data,
            input_json_stem=input_json_stem,
            provider=args.provider,
            api_key=args.api_key,
            verbose=args.verbose,
            policy_slug=policy_slug,
            include_usage_meta=args.include_usage_meta,
            include_cost_summary=args.include_cost_summary,
            max_attacks=args.max_attacks,
        )
    
    # Process queries in parallel
    with ThreadPoolExecutor(max_workers=args.query_concurrency) as executor:
        future_to_query = {executor.submit(process_single_query, (idx, query)): query for idx, query in enumerate(queries)}
        
        for future in as_completed(future_to_query):
            try:
                result = future.result()
                if result:
                    all_results.append(result)
            except Exception as e:
                print(f"❌ Error processing query: {str(e)}")
    
    # Save results with input JSON stem and policy slug in path
    if args.output_file:
        output_file = args.output_file
    else:
        output_file = f"{args.output_dir}/{input_json_stem}/{policy_slug}/attack_selector_results.json"
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Calculate summary statistics
    total_queries = len(all_results)
    successful_queries = sum(1 for r in all_results if r['successful_attack'])
    success_rate = successful_queries / total_queries if total_queries > 0 else 0
    
    # Build summary payload
    final_results = {
        'summary': {
            'total_queries': total_queries,
            'successful_queries': successful_queries,
            'success_rate': success_rate,
            'attack_concurrency': args.attack_concurrency,
            'query_concurrency': args.query_concurrency
        },
        'results': all_results
    }

    # Attach selector policy and inputs metadata for comparison
    final_results['summary']['policy'] = {
        'selector': args.selector,
        'selector_opts': global_selector_opts,
        'policy_slug': policy_slug,
    }
    final_results['summary']['inputs'] = {
        'queries_file': args.queries_file,
        'asr_file': args.asr_file,
        'max_attacks': args.max_attacks,
        'attack_concurrency': args.attack_concurrency,
        'query_concurrency': args.query_concurrency,
    }

    # Aggregate usage and cost totals across queries if enabled
    if args.include_usage_meta:
        summary_usage_totals: Dict[str, float] = {}
        for q in all_results:
            _sum_numeric(summary_usage_totals, q.get('usage_totals') or {})
        final_results['summary']['usage_totals'] = summary_usage_totals
    if args.include_cost_summary:
        summary_cost_totals: Dict[str, float] = {}
        for q in all_results:
            _sum_numeric(summary_cost_totals, q.get('cost_totals') or {})
        final_results['summary']['cost_totals'] = summary_cost_totals

    # Comparison metrics (Success@k, attempts-to-success, fail rate, timeouts)
    if args.include_comparison_metrics:
        attempts_to_success: List[int] = []
        # Total attempts per query (regardless of success)
        attempts_over_all: List[int] = []
        timeouts_total = 0
        # Determine horizon for Success@k table
        observed_max_attempts = 0
        for q in all_results:
            total_attempts = int(q.get('total_attempts', 0))
            attempts_over_all.append(total_attempts)
            observed_max_attempts = max(observed_max_attempts, total_attempts)
        horizon = args.max_attacks or observed_max_attempts or 0
        success_at_k_counts: Dict[int, int] = {k: 0 for k in range(1, horizon + 1)}
        # Populate metrics
        for q in all_results:
            timeouts_total += int(q.get('timeouts', 0))
            s_attempt = q.get('success_attempt')
            if isinstance(s_attempt, int):
                attempts_to_success.append(s_attempt)
                for k in range(1, horizon + 1):
                    if s_attempt <= k:
                        success_at_k_counts[k] += 1
        # Rates
        success_at_k = {
            str(k): {
                'count': success_at_k_counts.get(k, 0),
                'rate': (success_at_k_counts.get(k, 0) / total_queries) if total_queries > 0 else 0.0,
            }
            for k in range(1, horizon + 1)
        }
        # Attempts stats
        def _avg_and_median(values: List[int]) -> Tuple[float | None, float | None]:
            if not values:
                return None, None
            avg = sum(values) / len(values)
            vals = sorted(values)
            mid = len(vals) // 2
            if len(vals) % 2 == 1:
                median_val = vals[mid]
            else:
                median_val = (vals[mid - 1] + vals[mid]) / 2
            return avg, median_val

        avg_success, median_success = _avg_and_median(attempts_to_success)
        avg_attempts_all, median_attempts_all = _avg_and_median(attempts_over_all)

        metrics = {
            'success_at_k': success_at_k,
            'avg_attempts_to_success_over_successes': avg_success,
            'median_attempts_to_success_over_successes': median_success,
            'avg_total_attempts_over_all_attempts': avg_attempts_all,
            'median_total_attempts_over_all_attempts': median_attempts_all,
            'fail_rate': (1 - success_rate) if total_queries > 0 else 0.0,
            'timeouts_total': timeouts_total,
        }
        final_results['summary']['metrics'] = metrics

    # Collect LLM selector ranking token usage if applicable
    if args.selector == "llm_select":
        llm_log_root = Path(args.output_dir) / input_json_stem / policy_slug
        llm_totals, llm_log_files = _aggregate_llm_select_tokens(llm_log_root)
        if llm_totals or llm_log_files:
            final_results['summary'].setdefault('metrics', {})
            final_results['summary']['metrics']['llm_select_tokens'] = {
                'totals': llm_totals,
                'log_files': llm_log_files,
            }
    
    with open(output_file, 'w') as f:
        json.dump(final_results, f, indent=2)
    
    print(f"\n📊 Summary:")
    print(f"  - Total queries: {total_queries}")
    print(f"  - Successful queries: {successful_queries}")
    print(f"  - Success rate: {success_rate:.2%}")
    print(f"  - Results saved to: {output_file}")

if __name__ == '__main__':
    main()
