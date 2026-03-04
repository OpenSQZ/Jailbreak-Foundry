#!/usr/bin/env python
"""
Batch convert every results_*.json under results/ into Inspect eval logs using
convert_attack_results_to_eval.py, grouping outputs by test model.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from convert_attack_results_to_eval import convert_file


def find_project_root(script_path: Path) -> Path:
    return script_path.resolve().parents[2]


def _slug(value: str | None) -> str:
    if not value:
        return "unknown_model"
    return value.replace(" ", "_").replace("/", "_")


def infer_model(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    metadata = data.get("metadata") or {}
    return _slug(metadata.get("model"))


def main() -> None:
    script_path = Path(__file__)
    project_root = find_project_root(script_path)
    results_dir = project_root / "results"
    output_root = results_dir / "attack_eval_by_model"

    json_paths = sorted(
        p
        for p in results_dir.rglob("results_*.json")
        if any(part.endswith("_comprehensive") for part in p.relative_to(results_dir).parts)
    )
    if not json_paths:
        print(f"No results_*.json files found under {results_dir}")
        sys.exit(0)

    print(f"Found {len(json_paths)} results_*.json files under {results_dir}\n")

    for json_path in json_paths:
        model = infer_model(json_path)
        log_dir = output_root / model
        log_dir.mkdir(parents=True, exist_ok=True)

        print(f"Converting {json_path} -> {log_dir}")
        out_path = convert_file(json_path, log_dir)
        print(f"  wrote {out_path}\n")

    print(f"Done. Eval logs written under {output_root}")
    print("Open in Inspect with e.g.:")
    print(f"  uv run inspect view --log-dir {output_root}")
    print("or:")
    print(f"  inspect view --log-dir {output_root}")


if __name__ == "__main__":
    main()
