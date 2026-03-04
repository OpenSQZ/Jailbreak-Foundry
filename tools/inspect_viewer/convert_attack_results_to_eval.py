#!/usr/bin/env python
"""
Convert all results_<attack>.json files under a results directory into
Inspect-ready .eval logs (one .eval per results file).

Example:
    python convert_attack_results_to_eval.py \\
        --results-dir ./results \\
        --log-dir ./logs_attack_runs

Then view in Inspect:
    uv run inspect view --log-dir ./logs_attack_runs
or
    inspect view --log-dir ./logs_attack_runs
"""

from __future__ import annotations

import argparse
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List

import inspect_ai  # for __version__
from inspect_ai.event import InfoEvent
from inspect_ai.log import (
    EvalConfig,
    EvalDataset,
    EvalLog,
    EvalMetric,
    EvalPlan,
    EvalPlanStep,
    EvalResults,
    EvalSample,
    EvalScore,
    EvalSpec,
    EvalStats,
    write_eval_log,
)
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


def _find_result_files(results_dir: Path) -> List[Path]:
    return sorted(results_dir.rglob("results_*.json"))


def _coerce_response_text(resp: Any) -> str:
    """
    The attack JSON sometimes stores model_response as a list of strings.
    Inspect's ModelOutput expects a single string or structured content, so
    join lists into one blob.
    """
    if resp is None:
        return ""
    if isinstance(resp, list):
        return "\n\n".join(str(part) for part in resp)
    return str(resp)


# ---------- builders ----------

def build_eval_spec(
    metadata: Dict[str, Any],
    task_name: str,
    dataset_samples: int,
) -> EvalSpec:
    created = _now_iso()
    eval_id = str(uuid.uuid4())
    run_id = str(uuid.uuid4())
    task_id = str(uuid.uuid4())

    dataset = EvalDataset(
        name=task_name,
        location=str(metadata.get("dataset") or ""),
        samples=dataset_samples,
        sample_ids=None,
        shuffled=None,
    )

    return EvalSpec(
        eval_set_id=None,
        eval_id=eval_id,
        run_id=run_id,
        created=created,
        task=task_name,
        task_id=task_id,
        task_version=1,
        task_file=None,
        task_display_name=f"{task_name} ({metadata.get('model','unknown_model')})",
        task_registry_name=task_name,
        task_attribs={},
        task_args={},
        task_args_passed={},
        solver=metadata.get("attack", {}).get("name", "attack"),
        solver_args=metadata.get("attack", {}),
        tags=["imported", metadata.get("attack", {}).get("name", "attack")],
        dataset=dataset,
        sandbox=None,
        model=metadata.get("model"),
        model_generate_config=GenerateConfig(),
        model_base_url=None,
        model_args={},
        model_roles=None,
        config=EvalConfig(),
        revision=None,
        packages={"inspect_ai": inspect_ai.__version__},
        metadata=metadata,
        scorers=None,
        metrics=None,
    )


def build_samples(
    records: Iterable[Dict[str, Any]],
    model_name: str,
) -> List[EvalSample]:
    samples: List[EvalSample] = []

    for idx, record in enumerate(records, start=1):
        goal = record.get("goal", "")
        jailbroken = bool(record.get("jailbroken"))
        usage = record.get("usage") or {}
        response_text = _coerce_response_text(record.get("model_response"))

        usage_obj = ModelUsage(
            input_tokens=_safe_int(usage.get("prompt_tokens")),
            output_tokens=_safe_int(usage.get("completion_tokens")),
            total_tokens=_safe_int(usage.get("total_tokens")),
            input_tokens_cache_write=_safe_int(usage.get("input_tokens_cache_write")),
            input_tokens_cache_read=_safe_int(usage.get("input_tokens_cache_read")),
            reasoning_tokens=_safe_int(usage.get("reasoning_tokens")),
        )

        success_score = Score(
            value=jailbroken,
            answer="jailbroken" if jailbroken else "not_jailbroken",
            explanation="True when the attack was judged successful.",
            metadata={
                "example_id": record.get("example_id"),
                "jailbroken": jailbroken,
            },
        )

        metadata = {
            "example_id": record.get("example_id"),
            "goal": goal,
            "attack_prompt": record.get("attack_prompt"),
            "model_response": response_text,
            "reasoning_content": record.get("reasoning_content"),
            "usage": usage,
            "cost_summary": record.get("cost_summary", {}),
        }

        output = ModelOutput.from_content(model=model_name, content=response_text)

        sample = EvalSample(
            id=idx,
            epoch=1,
            input=goal,
            choices=None,
            target="",
            sandbox=None,
            files=None,
            setup=None,
            messages=[],
            output=output,
            score=success_score,
            metadata=metadata,
            answer=success_score.answer,
            store={},
            events=[
                InfoEvent(
                    source="attack_prompt",
                    data={"prompt": record.get("attack_prompt")},
                )
            ],
            model_usage={model_name: usage_obj},
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


def build_eval_results(samples: List[EvalSample]) -> EvalResults:
    total = len(samples)
    successes = sum(1 for s in samples if bool(getattr(s.score, "value", False)))
    success_rate = (successes / total) if total else 0.0

    metrics: Dict[str, EvalMetric] = {
        "success_rate": EvalMetric(
            name="success_rate",
            value=float(success_rate),
            params={},
            metadata={"total": total, "successes": successes},
        ),
        "fail_rate": EvalMetric(
            name="fail_rate",
            value=float(1 - success_rate),
            params={},
        ),
    }

    score = EvalScore(
        name="jailbreak_success",
        scorer="jailbreak_success",
        reducer="mean",
        scored_samples=total,
        unscored_samples=0,
        params={},
        metrics=metrics,
        metadata={"total": total, "successes": successes},
    )

    return EvalResults(
        total_samples=total,
        completed_samples=total,
        scores=[score],
        metadata={},
        sample_reductions=None,
    )


def build_eval_plan(attack_name: str) -> EvalPlan:
    return EvalPlan(
        name=f"{attack_name}_plan",
        steps=[
            EvalPlanStep(
                solver=attack_name,
                params={},
            )
        ],
        finish=None,
        config=GenerateConfig(),
    )


def build_eval_stats(model_name: str, samples: List[EvalSample]) -> EvalStats:
    agg_usage = ModelUsage(
        input_tokens=sum(
            _safe_int(s.model_usage.get(model_name, ModelUsage()).input_tokens)
            for s in samples
        ),
        output_tokens=sum(
            _safe_int(s.model_usage.get(model_name, ModelUsage()).output_tokens)
            for s in samples
        ),
        total_tokens=sum(
            _safe_int(s.model_usage.get(model_name, ModelUsage()).total_tokens)
            for s in samples
        ),
        input_tokens_cache_write=sum(
            _safe_int(
                s.model_usage.get(model_name, ModelUsage()).input_tokens_cache_write
            )
            for s in samples
        ),
        input_tokens_cache_read=sum(
            _safe_int(
                s.model_usage.get(model_name, ModelUsage()).input_tokens_cache_read
            )
            for s in samples
        ),
        reasoning_tokens=sum(
            _safe_int(s.model_usage.get(model_name, ModelUsage()).reasoning_tokens)
            for s in samples
        ),
    )

    now = _now_iso()
    return EvalStats(
        started_at=now,
        completed_at=now,
        model_usage={model_name: agg_usage},
    )


def convert_file(path: Path, log_dir: Path) -> Path | None:
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    metadata = raw.get("metadata") or {}
    records = raw.get("results") or []
    if not records:
        print(f"  SKIPPED: {path} has no 'results' entries.")
        return None

    attack_name = metadata.get("attack", {}).get("name") or path.stem.replace(
        "results_", ""
    )
    model_name = metadata.get("model") or "unknown_model"

    samples = build_samples(records, model_name)

    spec = build_eval_spec(metadata, attack_name, len(samples))
    plan = build_eval_plan(attack_name)
    stats = build_eval_stats(model_name, samples)
    eval_results = build_eval_results(samples)

    timestamp = metadata.get("timestamp") or datetime.now(timezone.utc).strftime(
        "%Y%m%d-%H%M%S"
    )
    out_name = f"{attack_name}-{model_name}-{timestamp}.eval"
    out_path = log_dir / out_name

    log = EvalLog(
        version=1,
        status="success",
        eval=spec,
        plan=plan,
        results=eval_results.model_dump() if eval_results else {},
        stats=stats,
        error=None,
        samples=samples,
        reductions=None,
        location=str(out_path),
        etag=None,
    )

    write_eval_log(log, location=out_path)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert results_<attack>.json files into Inspect .eval logs."
    )
    parser.add_argument(
        "--results-dir",
        type=Path,
        default=Path("./results"),
        help="Directory to search for results_<attack>.json files.",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        default=Path("./logs_attack_runs"),
        help="Directory where .eval files will be written.",
    )

    args = parser.parse_args()
    args.log_dir.mkdir(parents=True, exist_ok=True)

    files = _find_result_files(args.results_dir)
    if not files:
        raise SystemExit(f"No results_*.json files found under {args.results_dir}")

    print(f"Found {len(files)} result files. Writing evals to {args.log_dir}...")
    success_count = 0
    for path in files:
        out_path = convert_file(path, args.log_dir)
        if out_path:
            print(f"  wrote {out_path}")
            success_count += 1

    print(f"\nSuccessfully converted {success_count} of {len(files)} files.")
    print("\nOpen in Inspect with e.g.:")
    print(f"  uv run inspect view --log-dir {args.log_dir}")
    print("or:")
    print(f"  inspect view --log-dir {args.log_dir}")


if __name__ == "__main__":
    main()
