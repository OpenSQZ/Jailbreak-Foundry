#!/usr/bin/env python3
"""Probe one model block from an attack config with a hard timeout."""

from __future__ import annotations

import argparse
import multiprocessing as mp
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML must contain a mapping: {path}")
    return data


def get_path(data: Dict[str, Any], dotted_path: str) -> Dict[str, Any]:
    current: Any = data
    for part in dotted_path.split("."):
        if not isinstance(current, dict) or part not in current:
            raise KeyError(f"Config path not found: {dotted_path}")
        current = current[part]
    if not isinstance(current, dict):
        raise TypeError(f"Config path is not a model mapping: {dotted_path}")
    for key in ("model", "provider"):
        if not current.get(key):
            raise ValueError(f"Model block {dotted_path} is missing required key: {key}")
    return current


def find_model_blocks(data: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    blocks: List[Tuple[str, Dict[str, Any]]] = []
    for name in ("victim_model", "eval_model"):
        value = data.get(name)
        if isinstance(value, dict) and value.get("model") and value.get("provider"):
            blocks.append((name, value))

    attack_parameters = data.get("attack_parameters")
    if isinstance(attack_parameters, dict):
        for name, value in attack_parameters.items():
            if isinstance(value, dict) and value.get("model") and value.get("provider"):
                blocks.append((f"attack_parameters.{name}", value))
    return blocks


def describe(block_name: str, config: Dict[str, Any]) -> str:
    key_state = "set" if config.get("api_key") else "not set"
    base = config.get("api_base") or "(default)"
    return (
        f"{block_name}: provider={config.get('provider')} model={config.get('model')} "
        f"api_base={base} api_key={key_state}"
    )


def query_worker(config: Dict[str, Any], prompt: str, max_tokens: int, queue: mp.Queue) -> None:
    try:
        from jbfoundry.llm.litellm import LLMLiteLLM

        llm = LLMLiteLLM.from_config(
            model_name=config["model"],
            provider=config["provider"],
            api_key=config.get("api_key"),
            api_base=config.get("api_base"),
            max_tokens=max_tokens,
            max_retries=1,
        )
        response = llm.query(prompt, temperature=0.0, max_tokens=max_tokens)
        queue.put(
            {
                "ok": True,
                "text": str(response),
                "usage": response.get_usage() if hasattr(response, "get_usage") else None,
            }
        )
    except Exception as exc:
        queue.put({"ok": False, "error": str(exc), "traceback": traceback.format_exc()})


def probe(config: Dict[str, Any], prompt: str, timeout: int, max_tokens: int) -> Dict[str, Any]:
    ctx = mp.get_context("fork")
    queue: mp.Queue = ctx.Queue()
    process = ctx.Process(target=query_worker, args=(config, prompt, max_tokens, queue))
    process.start()
    process.join(timeout)
    if process.is_alive():
        process.terminate()
        process.join(5)
        return {"ok": False, "timeout": True, "error": f"Timed out after {timeout}s"}
    if queue.empty():
        return {"ok": False, "error": f"Probe exited with code {process.exitcode} and no result"}
    return queue.get()


def main() -> None:
    parser = argparse.ArgumentParser(description="Check one exact LLM model block from an attack config.")
    parser.add_argument("config", type=Path, help="Attack config YAML")
    parser.add_argument("--block", default=None, help="Optional single dotted path, e.g. attack_parameters.attacker_model")
    parser.add_argument("--timeout", type=int, default=60, help="Hard timeout in seconds")
    parser.add_argument("--max-tokens", type=int, default=8, help="Max response tokens")
    parser.add_argument("--prompt", default="Reply with OK only.", help="Probe prompt")
    args = parser.parse_args()

    data = load_yaml(args.config.resolve())
    blocks = [(args.block, get_path(data, args.block))] if args.block else find_model_blocks(data)
    if not blocks:
        raise ValueError("No model blocks found")

    failed = 0
    for name, config in blocks:
        print(describe(name, config))
        result = probe(config, args.prompt, args.timeout, args.max_tokens)
        if result.get("ok"):
            print(f"  [ok] {result.get('text')!r}")
            continue

        failed += 1
        print(f"  [error] {result.get('error', 'unknown error')}", file=sys.stderr)

    if failed:
        print(f"\n{failed}/{len(blocks)} model checks failed", file=sys.stderr)
        sys.exit(1)

    print(f"\n[ok] all {len(blocks)} model checks passed")


if __name__ == "__main__":
    main()
