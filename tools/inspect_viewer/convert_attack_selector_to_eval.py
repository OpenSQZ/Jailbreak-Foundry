#!/usr/bin/env python
"""
Convert attack_selector_results.json into an Inspect eval log.

Usage (basic):

    python convert_attack_selector_to_eval.py \
        --input attack_selector_results.json \
        --log-dir ./logs_attack_selector

Then view in Inspect:

    uv run inspect view --log-dir ./logs_attack_selector
or
    inspect view --log-dir ./logs_attack_selector

This script assumes the JSON structure:

{
  "summary": { ... },
  "results": [ { per-query data ... }, ... ]
}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, List

import inspect_ai  # just for __version__

from inspect_ai.log import (
    EvalLog,
    EvalSpec,
    EvalDataset,
    EvalConfig,
    EvalPlan,
    EvalPlanStep,
    EvalResults,
    EvalScore,
    EvalMetric,
    EvalStats,
    EvalSample,
    write_eval_log,
)
from inspect_ai.event import InfoEvent
from inspect_ai.model import GenerateConfig, ModelOutput, ModelUsage
from inspect_ai.scorer import Score


# ---------- helpers ----------

def _safe_int(x: Any) -> int:
    if x is None:
        return 0
    try:
        return int(x)
    except (TypeError, ValueError):
        return 0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------- builders for pieces of the EvalLog ----------

def build_eval_spec(raw: Dict[str, Any], task_name: str) -> EvalSpec:
    summary = raw["summary"]
    inputs = summary.get("inputs", {})

    created = _now_iso()
    eval_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    dataset = EvalDataset(
        name=task_name,
        location=str(inputs.get("queries_file") or ""),
        samples=summary.get("total_queries"),
        sample_ids=None,
        shuffled=None,
    )

    eval_config = EvalConfig()

    # Handle case where there are multiple victim models
    victim_models = set(sample['victim_model'] for sample in raw["results"])
    if len(victim_models) > 1:
        model_name = "mixed"  # Set the model name as "mixed" if there are multiple victim models
    else:
        model_name = list(victim_models)[0]

    spec = EvalSpec(
        eval_set_id=None,
        eval_id=eval_id,
        run_id=run_id,
        created=created,
        task=task_name,
        task_id=task_id,
        task_version=1,
        task_file=None,
        task_display_name=f"{task_name} ({model_name} model)",
        task_registry_name=task_name,
        task_attribs={},
        task_args={
            "attack_concurrency": summary.get("attack_concurrency"),
            "query_concurrency": summary.get("query_concurrency"),
        },
        task_args_passed={},
        solver=summary["policy"].get("selector"),
        solver_args=summary.get("policy", {}),
        tags=["imported", summary["policy"].get("selector")],
        dataset=dataset,
        sandbox=None,
        model=model_name,
        model_generate_config=GenerateConfig(),
        model_base_url=None,
        model_args={},
        model_roles=None,
        config=eval_config,
        revision=None,
        packages={
            "inspect_ai": inspect_ai.__version__,
        },
        metadata={
            "policy": summary.get("policy", {}),
            "inputs": summary.get("inputs", {}),
        },
        scorers=None,
        metrics=None,
    )

    return spec


def build_eval_results(raw: Dict[str, Any], samples: List[EvalSample]) -> EvalResults:
    summary = raw["summary"]
    m = summary.get("metrics", {}) or {}

    # Remove success_at_k metrics
    success_at_k = {}  # Clear this to remove success_at_k from the metrics bar

    metrics: Dict[str, EvalMetric] = {}

    # Add other metrics as needed
    if "success_rate" in summary:
        metrics["success_rate"] = EvalMetric(
            name="success_rate",
            value=float(summary["success_rate"]),
            params={},
            metadata={
                "total_queries": summary.get("total_queries"),
                "successful_queries": summary.get("successful_queries"),
            },
        )

    if "fail_rate" in m:
        metrics["fail_rate"] = EvalMetric(
            name="fail_rate",
            value=float(m["fail_rate"]),
            params={},
        )

    if "avg_attempts_to_success" in m:
        metrics["avg_attempts_to_success"] = EvalMetric(
            name="avg_attempts_to_success",
            value=float(m["avg_attempts_to_success"]),
            params={},
        )

    if "median_attempts_to_success" in m:
        metrics["median_attempts_to_success"] = EvalMetric(
            name="median_attempts_to_success",
            value=float(m["median_attempts_to_success"]),
            params={},
        )

    if "timeouts_total" in m:
        metrics["timeouts_total"] = EvalMetric(
            name="timeouts_total",
            value=float(m["timeouts_total"]),
            params={},
        )

    score = EvalScore(
        name="attack_success",
        scorer="attack_success",
        reducer="mean",
        scored_samples=len(samples),
        unscored_samples=0,
        params={},
        metrics=metrics,
        metadata={
            "total_queries": summary.get("total_queries"),
            "successful_queries": summary.get("successful_queries"),
        },
    )

    return EvalResults(
        total_samples=len(samples),
        completed_samples=len(samples),
        scores=[score],
        metadata={
            "attack_concurrency": summary.get("attack_concurrency"),
            "query_concurrency": summary.get("query_concurrency"),
        },
        sample_reductions=None,
    )


def build_attempt_events(record: Dict[str, Any]) -> List[InfoEvent]:
    """
    Convert each attack attempt into an Inspect info event so the transcript
    view surfaces per-attempt data instead of leaving events empty.
    """
    events: List[InfoEvent] = []
    for idx, attempt in enumerate(record.get("all_attempts") or [], start=1):
        events.append(
            InfoEvent(
                source="attack_attempt",
                data={
                    "attempt_idx": idx,
                    **attempt,
                },
            )
        )
    return events


def build_samples(raw: Dict[str, Any]) -> List[EvalSample]:
    samples: List[EvalSample] = []

    for idx, record in enumerate(raw["results"], start=1):
        query_text = record["query"]
        success_attack = record.get("successful_attack")
        success_bool = bool(success_attack)

        # Per-sample token usage
        usage = record.get("usage_totals", {}) or {}
        usage_obj = ModelUsage(
            input_tokens=_safe_int(usage.get("prompt_tokens")),
            output_tokens=_safe_int(usage.get("completion_tokens")),
            total_tokens=_safe_int(usage.get("total_tokens")),
            input_tokens_cache_write=_safe_int(usage.get("input_tokens_cache_write")),
            input_tokens_cache_read=_safe_int(usage.get("input_tokens_cache_read")),
            reasoning_tokens=_safe_int(usage.get("reasoning_tokens")),
        )

        # === Where you customise what shows in the "Scoring" tab per sample ===
        # Score 1: overall success / failure
        success_score = Score(
            value=success_bool,
            answer=record.get("success_attack_name"),
            explanation=(
                "True if at least one attack in `all_attempts` succeeded "
                "(see sample metadata for details)."
            ),
            metadata={
                "success_attack_name": record.get("success_attack_name"),
                "success_attack_idx": record.get("success_attack_idx"),
                "total_attempts": record.get("total_attempts"),
                "attempts_tried": record.get("attempts_tried"),
            },
        )

        # Score 2: number of timeouts for this query
        timeouts = _safe_int(record.get("timeouts"))
        timeout_score = Score(
            value=timeouts,
            explanation="Number of timeouts for this query.",
        )

        # We don't have the actual model transcript. Instead we add a stub
        # output and put all the juicy stuff in metadata + scores.
        output = ModelOutput.from_content(
            model=record.get("victim_model"),
            content=(
                "No conversation transcript captured in "
                "attack_selector_results.json; see sample metadata "
                "for attack attempts and per-attack details."
            ),
        )

        # Anything you put here shows up in the Metadata tab for the sample.
        metadata = {
            "query": query_text,
            "victim_model": record.get("victim_model"),
            "total_attempts": record.get("total_attempts"),
            "attempts_tried": record.get("attempts_tried"),
            "timeouts": timeouts,
            "successful_attack": success_attack,
            "all_attempts": record.get("all_attempts", []),
            "usage_totals": usage,
            "cost_totals": record.get("cost_totals", {}),
        }

        sample = EvalSample(
            id=idx,
            epoch=1,
            input=query_text,
            choices=None,
            target="",
            sandbox=None,
            files=None,
            setup=None,
            messages=[],  # no full chat history available
            output=output,
            score=success_score,
            metadata=metadata,
            answer=record.get("success_attack_name"),
            store={},
            events=build_attempt_events(record),
            model_usage={record.get("victim_model"): usage_obj},
            total_time=None,
            working_time=None,
            uuid=str(uuid.uuid4()),
            error=None,
            error_retries=None,
            attachments={},
            limit=None,
        )

        samples.append(sample)

    return samples


def build_eval_plan(raw: Dict[str, Any], task_name: str) -> EvalPlan:
    """
    This is mostly cosmetic – it shows up in the Info panel as the "plan".
    You can rename the solver here if you prefer some other label.
    """
    return EvalPlan(
        name=f"{task_name}_plan",
        steps=[
            EvalPlanStep(
                solver=raw["summary"]["policy"].get("selector"),
                params={},
            )
        ],
        finish=None,
        config=GenerateConfig(),
    )

def build_eval_stats(raw: Dict[str, Any], model_name: str) -> EvalStats:
    summary = raw["summary"]
    usage = summary.get("usage_totals", {})

    model_usage = ModelUsage(
        input_tokens=_safe_int(usage.get("prompt_tokens")),
        output_tokens=_safe_int(usage.get("completion_tokens")),
        total_tokens=_safe_int(usage.get("total_tokens")),
        input_tokens_cache_write=_safe_int(usage.get("input_tokens_cache_write")),
        input_tokens_cache_read=_safe_int(usage.get("input_tokens_cache_read")),
        reasoning_tokens=_safe_int(usage.get("reasoning_tokens")),
    )

    now = _now_iso()
    return EvalStats(
        started_at=now,
        completed_at=now,
        model_usage={model_name: model_usage},
    )

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert attack_selector_results.json to an Inspect eval log."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to attack_selector_results.json",
    )
    parser.add_argument(
        "--log-dir",
        "-L",
        type=Path,
        default=Path("./logs_attack_selector"),
        help="Directory where the .eval log will be written (Inspect will read from here).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Optional explicit path for the .eval file. "
             "If omitted, a name is generated inside --log-dir.",
    )
    parser.add_argument(
        "--task-name",
        default="attack_selector",
        help="Name for the synthetic Inspect task.",
    )
    parser.add_argument(
        "--model-name",
        default=None,
        help="Override model name recorded in the log "
             "(otherwise inferred from the first result's victim_model).",
    )

    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    if not raw.get("results"):
        raise SystemExit("Input JSON has no 'results' – is this the right file?")

    inferred_model = raw["results"][0].get("victim_model") or "unknown_model"
    model_name = args.model_name or inferred_model

    # Ensure log directory exists
    args.log_dir.mkdir(parents=True, exist_ok=True)

    if args.output is not None:
        out_path = args.output
        if out_path.suffix == "":
            out_path = out_path.with_suffix(".eval")
    else:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        out_path = args.log_dir / f"{args.task_name}-{timestamp}.eval"

    samples = build_samples(raw)

    # Build pieces
    spec = build_eval_spec(raw, args.task_name)
    plan = build_eval_plan(raw, args.task_name)
    stats = build_eval_stats(raw, model_name)
    eval_results = build_eval_results(raw, samples)

    # version is currently 1 in the Inspect log schema; if this ever changes,
    # you can update this constant.
    log = EvalLog(
        version=1,
        status="success",
        eval=spec,
        plan=plan,
        # Pass a dict so the 'resolve_sample_reductions' validator can mutate it
        results=eval_results.model_dump() if eval_results else {},
        stats=stats,
        error=None,
        samples=samples,
        reductions=None,
        location=str(out_path),
        etag=None,
    )

    write_eval_log(log, location=out_path)

    print(f"Wrote Inspect eval log to: {out_path}")
    print()
    print("Open it in Inspect with e.g.:")
    print(f"  uv run inspect view --log-dir {args.log_dir}")
    print("or:")
    print(f"  inspect view --log-dir {args.log_dir}")


if __name__ == "__main__":
    main()
