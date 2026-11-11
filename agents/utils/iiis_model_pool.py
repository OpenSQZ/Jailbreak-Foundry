"""
IIIS Model Pool — health-check and auto-fallback for LiteLLM proxy channels.

Given a base model name (e.g. 'claude-sonnet-4-6'), probes available
prefix/channel variants (bh/, aws/, etc.) and returns the first working one.

Usage:
    from agents.utils.iiis_model_pool import resolve_model
    model = resolve_model("claude-sonnet-4-6")  # -> "aws/claude-sonnet-4-6"
    model = resolve_model("bh/claude-sonnet-4-6")  # tries bh/ first, falls back

Environment:
    IIIS_API_KEY   — required (same key used by paper_preprocessor)
    IIIS_BASE_URL  — optional override (default: https://router.ai.iiis.co:9443/v1)
"""

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

import requests

DEFAULT_BASE_URL = "https://router.ai.iiis.co:9443/v1"
KNOWN_PREFIXES = ["bh", "aws", "hh", "iiis", "infi", "wj", "ora"]

log = logging.getLogger(__name__)

# Module-level cache for /v1/models list
_models_cache: Optional[Tuple[float, List[str]]] = None
_CACHE_TTL = 300  # 5 minutes


def _get_api_key() -> str:
    key = os.environ.get("IIIS_API_KEY")
    if not key:
        raise ValueError("IIIS_API_KEY environment variable not set")
    return key


def _get_base_url() -> str:
    return os.environ.get("IIIS_BASE_URL", DEFAULT_BASE_URL)


def _fetch_models(api_key: str, base_url: str) -> List[str]:
    """Fetch and cache the full model list from /v1/models."""
    global _models_cache
    now = time.time()
    if _models_cache and (now - _models_cache[0]) < _CACHE_TTL:
        return _models_cache[1]

    resp = requests.get(
        f"{base_url}/models",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=10,
    )
    resp.raise_for_status()
    models = [m["id"] for m in resp.json().get("data", [])]
    _models_cache = (now, models)
    return models


def _find_variants(base_model: str, all_models: List[str]) -> List[str]:
    """Find all prefixed variants of a base model in the model list."""
    # Strip existing prefix if present
    if "/" in base_model:
        base = base_model.split("/", 1)[1]
    else:
        base = base_model

    variants = []
    for m in all_models:
        if "/" in m and m.split("/", 1)[1] == base:
            variants.append(m)
    return variants


def _probe_model(model_id: str, api_key: str, base_url: str, timeout: float) -> Optional[Tuple[str, float]]:
    """Send a 1-token completion to check if a model is alive. Returns (model_id, latency) or None."""
    start = time.time()
    try:
        resp = requests.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 1,
            },
            timeout=timeout,
        )
        data = resp.json()
        if resp.status_code == 200 and data.get("choices"):
            return (model_id, time.time() - start)
        else:
            elapsed = time.time() - start
            error_msg = data.get("error", {}).get("message", f"HTTP {resp.status_code}")
            log.debug(f"{model_id} — {error_msg} ({elapsed:.1f}s)")
    except requests.exceptions.Timeout:
        log.debug(f"{model_id} — timeout ({timeout:.0f}s)")
    except Exception as e:
        log.debug(f"{model_id} — {type(e).__name__}: {e}")
    return None


def resolve_model(
    base_model: str,
    api_key: Optional[str] = None,
    timeout: float = 15.0,
) -> str:
    """
    Resolve a base model name to a working prefixed variant.

    Args:
        base_model: Model name, with or without prefix (e.g. 'claude-sonnet-4-6' or 'bh/claude-sonnet-4-6')
        api_key: IIIS API key (defaults to IIIS_API_KEY env var)
        timeout: Per-probe timeout in seconds

    Returns:
        Working model ID (e.g. 'aws/claude-sonnet-4-6')

    Raises:
        RuntimeError: If no working variant found
        ValueError: If IIIS_API_KEY not set
    """
    api_key = api_key or _get_api_key()
    base_url = _get_base_url()

    # If already prefixed, try it first (fast path)
    original_prefix = None
    if "/" in base_model:
        original_prefix = base_model
        result = _probe_model(base_model, api_key, base_url, timeout)
        if result:
            print(f"✅ Model {base_model} is available ({result[1]:.1f}s)")
            return base_model

        print(f"⚠️  Model {base_model} is down, searching alternatives...")

    # Fetch model list and find variants
    all_models = _fetch_models(api_key, base_url)
    variants = _find_variants(base_model, all_models)

    if not variants:
        if original_prefix:
            raise RuntimeError(f"No variants found for {base_model} and original is down")
        raise RuntimeError(f"No model matching '{base_model}' found in IIIS pool")

    # Remove the already-failed original
    if original_prefix and original_prefix in variants:
        variants.remove(original_prefix)

    if not variants:
        raise RuntimeError(f"No alternative variants for {base_model} — only had {original_prefix} which is down")

    print(f"🔍 Probing {len(variants)} alternatives: {', '.join(variants[:5])}{'...' if len(variants) > 5 else ''}")

    # Probe all variants in parallel
    with ThreadPoolExecutor(max_workers=min(len(variants), 6)) as pool:
        futures = {pool.submit(_probe_model, v, api_key, base_url, timeout): v for v in variants}
        for future in as_completed(futures):
            result = future.result()
            if result:
                model_id, latency = result
                print(f"✅ Resolved to {model_id} ({latency:.1f}s)")
                # Cancel remaining probes
                for f in futures:
                    f.cancel()
                return model_id

    raise RuntimeError(f"All {len(variants) + (1 if original_prefix else 0)} variants of '{base_model}' are down")


def list_available_variants(
    base_model: str,
    api_key: Optional[str] = None,
    timeout: float = 15.0,
) -> List[Tuple[str, float]]:
    """
    Return all working variants for a base model, sorted by latency.

    Returns:
        List of (model_id, latency_seconds) tuples, fastest first
    """
    api_key = api_key or _get_api_key()
    base_url = _get_base_url()

    all_models = _fetch_models(api_key, base_url)
    variants = _find_variants(base_model, all_models)

    if not variants:
        return []

    results = []
    with ThreadPoolExecutor(max_workers=min(len(variants), 6)) as pool:
        futures = {pool.submit(_probe_model, v, api_key, base_url, timeout): v for v in variants}
        for future in as_completed(futures):
            result = future.result()
            if result:
                results.append(result)

    results.sort(key=lambda x: x[1])
    return results


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.WARNING)
    _log = logging.getLogger(__name__)
    _log.setLevel(logging.DEBUG)
    _log.propagate = False
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("   ❌ %(message)s"))
    _log.addHandler(_handler)

    parser = argparse.ArgumentParser(description="Test IIIS model pool health check")
    parser.add_argument("model", nargs="?", default="claude-sonnet-4-6", help="Base model to test")
    args = parser.parse_args()
    model = args.model

    print(f"=== resolve_model('{model}') ===")
    try:
        resolved = resolve_model(model)
        print(f"Result: {resolved}\n")
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}\n")

    base = model.split("/", 1)[1] if "/" in model else model
    print(f"=== list_available_variants('{base}') ===")
    try:
        variants = list_available_variants(base)
        if variants:
            for v, latency in variants:
                print(f"  {v} — {latency:.2f}s")
        else:
            print("  No working variants found")
    except (RuntimeError, ValueError) as e:
        print(f"Error: {e}")
