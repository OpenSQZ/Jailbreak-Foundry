#!/usr/bin/env python3
"""
Plot Success@K from one or more attack_selector_results.json files.

Usage examples:
  # Single input (previous behavior)
  python3 tools/attack_selector/scripts/plot_success_at_k.py \
    --input results/jbb_sample_queries/selector=asr_sort__max=10/attack_selector_results.json \
    --metric rate \
    --output tools/attack_selector/ploted_results/success_at_k_rate_asr_sort_max10.png

  # Multiple inputs overlaid with labels
  python3 tools/attack_selector/scripts/plot_success_at_k.py \
    --input \
      results/jbb_sample_queries/selector=asr_sort__max=10/attack_selector_results.json \
      results/jbb_sample_queries/selector=asr_cost__max=10/attack_selector_results.json \
      results/jbb_sample_queries/selector=ts__prior=0.15__kmax=100__decay=1__lambda=0__dg=0__dz=0__ps=100__max=10/attack_selector_results.json \
    --label asr_sort --label asr_cost --label ts \
    --metric rate \
    --title "Success@K (rate) — JBB sample queries" \
    --output tools/attack_selector/ploted_results/success_at_k_rate_combined_max10.png
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Tuple


def _find_success_at_k(node: Any) -> Optional[Dict[str, Any]]:
    """Depth-first search for the first mapping under key 'success_at_k'.

    Returns the value associated with 'success_at_k' if found; otherwise None.
    Traverses dicts and lists recursively.
    """
    if isinstance(node, dict):
        if "success_at_k" in node and isinstance(node["success_at_k"], dict):
            return node["success_at_k"]
        for value in node.values():
            found = _find_success_at_k(value)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = _find_success_at_k(item)
            if found is not None:
                return found
    return None


def _extract_k_and_metric(
    success_at_k: Dict[str, Any],
    metric: str,
    k_max: Optional[int] = None,
) -> Tuple[list[int], list[float]]:
    """Extract sorted K values and corresponding metric values.

    - success_at_k is expected to be a mapping of str K to a dict with the metric.
    - metric is either 'rate' or 'count'.
    - If k_max is provided, only include K <= k_max.
    """
    k_to_value: Dict[int, float] = {}
    for k_str, entry in success_at_k.items():
        try:
            k_int = int(k_str)
        except (TypeError, ValueError):
            # Skip non-integer keys
            continue
        if not isinstance(entry, dict):
            continue
        if metric not in entry:
            continue
        try:
            val = float(entry[metric])
        except (TypeError, ValueError):
            continue
        if k_max is not None and k_int > k_max:
            continue
        k_to_value[k_int] = val

    ks = sorted(k_to_value.keys())
    ys = [k_to_value[k] for k in ks]
    return ks, ys


def _derive_output_path_single(
    input_path: Path,
    metric: str,
    explicit_output: Optional[Path],
) -> Path:
    if explicit_output is not None:
        return explicit_output

    # Default to repo_root/results/plots/<input_stem>_success_at_k_<metric>.png
    # Repo root: .../jbfoundry from this script path
    repo_root = Path(__file__).resolve().parents[3]
    out_dir = repo_root / "results" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"{input_path.stem}_success_at_k_{metric}.png"
    return out_dir / base_name


def _derive_output_path_multi(
    metric: str,
    explicit_output: Optional[Path],
) -> Path:
    if explicit_output is not None:
        return explicit_output

    repo_root = Path(__file__).resolve().parents[3]
    out_dir = repo_root / "results" / "plots"
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"success_at_k_{metric}_combined.png"
    return out_dir / base_name


def _derive_label_from_json(data: Dict[str, Any], fallback: str) -> str:
    try:
        policy = data.get("summary", {}).get("policy", {})
        slug = policy.get("policy_slug")
        if isinstance(slug, str) and slug:
            return slug
        selector = policy.get("selector")
        if isinstance(selector, str) and selector:
            return selector
    except Exception:
        pass
    return fallback


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot Success@K from results JSON")
    parser.add_argument(
        "--input",
        nargs="+",
        required=True,
        help="Path(s) to attack_selector_results.json (one or more)",
    )
    parser.add_argument(
        "--label",
        action="append",
        default=None,
        help="Series label(s) for legend; repeat to match each --input",
    )
    parser.add_argument(
        "--metric",
        choices=["rate", "count"],
        default="rate",
        help="Y-axis metric to plot",
    )
    parser.add_argument(
        "--k-max",
        type=int,
        default=None,
        help="Optional cap for maximum K to include",
    )
    parser.add_argument(
        "--title",
        type=str,
        default=None,
        help="Optional plot title (defaults to 'Success@K (<metric>)')",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Optional path to save PNG (default: results/plots/...)",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Display the plot interactively in addition to saving",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)

    input_paths = [Path(p).expanduser().resolve() for p in args.input]
    for p in input_paths:
        if not p.exists():
            print(f"Error: input file not found: {p}", file=sys.stderr)
            return 1

    # Use non-interactive backend unless --show is requested
    if not args.show:
        import matplotlib

        matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    series: list[tuple[list[int], list[float], str]] = []  # (ks, ys, label)

    provided_labels = args.label or []
    for idx, input_path in enumerate(input_paths):
        with input_path.open("r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Error: failed to parse JSON: {e}", file=sys.stderr)
                return 1

        success_at_k = _find_success_at_k(data)
        if success_at_k is None:
            print(
                f"Error: could not find 'success_at_k' in JSON: {input_path}",
                file=sys.stderr,
            )
            return 1

        ks, ys = _extract_k_and_metric(success_at_k, metric=args.metric, k_max=args.k_max)
        if not ks:
            print(
                f"Error: no valid K entries found to plot in: {input_path}",
                file=sys.stderr,
            )
            return 1

        fallback_label = input_path.stem
        label = (
            provided_labels[idx]
            if idx < len(provided_labels)
            else _derive_label_from_json(data, fallback_label)
        )
        series.append((ks, ys, label))

    # Build union of K values for axis ticks
    all_ks: list[int] = sorted({k for ks, _ys, _lbl in series for k in ks})

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    for ks, ys, label in series:
        ax.plot(ks, ys, marker="o", linestyle="-", linewidth=2.0, label=label)

    ax.set_xlabel("K")
    y_label = "Success rate" if args.metric == "rate" else "Success count"
    ax.set_ylabel(y_label)
    title = args.title or f"Success@K ({args.metric})"
    ax.set_title(title)
    ax.grid(True, linestyle=":", linewidth=0.7, alpha=0.7)
    if args.metric == "rate":
        ax.set_ylim(0.0, 1.0)
    ax.set_xticks(all_ks)
    ax.legend(loc="lower right")
    fig.tight_layout()

    explicit_output = Path(args.output).expanduser().resolve() if args.output else None
    output_path = (
        _derive_output_path_single(input_paths[0], args.metric, explicit_output)
        if len(input_paths) == 1
        else _derive_output_path_multi(args.metric, explicit_output)
    )

    fig.savefig(output_path, dpi=200)
    if args.show:
        plt.show()
    plt.close(fig)

    print(
        (
            f"Saved plot to: {output_path}"
            if len(input_paths) == 1
            else f"Saved combined plot to: {output_path}"
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


