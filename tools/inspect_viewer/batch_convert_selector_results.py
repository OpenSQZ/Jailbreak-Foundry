#!/usr/bin/env python
"""
Batch convert every attack_selector_results.json under results/ into Inspect
eval logs using convert_attack_selector_to_eval.py.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def find_project_root(script_path: Path) -> Path:
    return script_path.resolve().parents[2]


def build_task_name(dataset: str, selector: str, model: str) -> str:
    def _slug(value: str) -> str:
        return value.replace(" ", "_")

    return "__".join(
        [
            _slug(dataset) or "dataset",
            _slug(selector) or "selector",
        ]
    )


def main() -> None:
    script_path = Path(__file__)
    project_root = find_project_root(script_path)
    results_dir = project_root / "results"
    converter = script_path.parent / "convert_attack_selector_to_eval.py"
    output_root = results_dir / "selector_viz"

    json_paths = sorted(results_dir.rglob("attack_selector_results.json"))
    if not json_paths:
        print(f"No attack_selector_results.json files found under {results_dir}")
        sys.exit(0)

    for json_path in json_paths:
        rel = json_path.relative_to(results_dir)
        dataset = rel.parts[0] if rel.parts else "unknown_dataset"
        selector_dir = json_path.parent.name

        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        policy = data.get("summary", {}).get("policy", {}) or {}
        selector = policy.get("selector") or selector_dir
        policy_slug = policy.get("policy_slug") or selector_dir
        model = (data.get("results") or [{}])[0].get("victim_model") or "unknown_model"

        out_dir = output_root / dataset
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{policy_slug}.eval"
        task_name = build_task_name(dataset, selector, model)

        print(f"Converting {json_path} -> {out_path} (task={task_name})")

        cmd = [
            sys.executable,
            str(converter),
            "-i",
            str(json_path),
            "-o",
            str(out_path),
            "-L",
            str(out_dir),
            "--task-name",
            task_name,
        ]

        subprocess.run(cmd, check=True)

    print(f"\nDone. Eval logs written under {output_root}")


if __name__ == "__main__":
    main()
