#!/usr/bin/env python3
"""Run no-network smoke tests for generated attack configs.

This harness executes the normal universal attack runner while monkeypatching
LLMLiteLLM.from_config() to return scripted fake LLMs. It is intended to catch
integration and control-flow bugs without depending on real provider auth.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from unittest.mock import patch

try:
    import yaml
except ImportError as exc:  # pragma: no cover - repository already depends on PyYAML
    raise RuntimeError("PyYAML is required for fake LLM smoke scenarios") from exc


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Imported after the sys.path setup above so the harness also works from a
# checkout where jbfoundry is not installed.
from jbfoundry.llm.base import BaseLLM  # noqa: E402
from jbfoundry.payloads import (  # noqa: E402
    AttackPayload,
    ModelCapabilities,
    serialize_attack_prompt,
)


@dataclass
class ResponseRule:
    pattern: re.Pattern[str]
    label: str
    responses: List[str]
    index: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ResponseRule":
        if "match" not in data:
            raise ValueError(f"Response rule missing 'match': {data}")
        if "sequence" in data:
            responses = [str(item) for item in data["sequence"]]
        elif "text" in data:
            responses = [str(data["text"])]
        else:
            raise ValueError(f"Response rule must contain 'text' or 'sequence': {data}")
        if not responses:
            raise ValueError(f"Response rule has no responses: {data}")
        match = str(data["match"])
        return cls(
            pattern=re.compile(match, re.IGNORECASE | re.DOTALL),
            label=str(data.get("name") or match),
            responses=responses,
        )

    def next_response(self) -> tuple[str, int, int]:
        response_index = min(self.index, len(self.responses) - 1)
        response = self.responses[response_index]
        response_number = response_index + 1
        self.index += 1
        return response, response_number, len(self.responses)


@dataclass
class ResponseSelection:
    text: str
    label: str
    response_number: int
    response_count: int
    is_default: bool = False


class ResponseScript:
    """Thread-safe scripted response selector."""

    def __init__(self, rules: Iterable[ResponseRule], trace: bool = True):
        self.rules = list(rules)
        self.trace = trace
        self.lock = threading.Lock()

    def respond(self, context: str) -> ResponseSelection:
        with self.lock:
            for rule in self.rules:
                if rule.pattern.search(context):
                    text, response_number, response_count = rule.next_response()
                    return ResponseSelection(text, rule.label, response_number, response_count)
        return ResponseSelection(default_response(context), "default", 1, 1, is_default=True)


class FakeLLM(BaseLLM):
    """Small LLMLiteLLM stand-in used by the smoke harness.

    Inheriting from BaseLLM is deliberate: it makes the runner's expectations
    structural, so a newly added abstract method fails loudly at instantiation
    instead of surfacing as an AttributeError partway through a smoke run.
    """

    def __init__(self, script: ResponseScript, **config: Any):
        self.script = script
        self.config = config
        self.model_name = config.get("model_name", "fake-model")
        self.provider = config.get("provider", "fake-provider")
        self.api_key = config.get("api_key")
        self.api_base = config.get("api_base")
        self.max_tokens = config.get("max_tokens")
        self.temperature = config.get("temperature")
        self.real_provider = config.get("provider", "fake-provider")
        self.model_identifier = f"{self.provider}/{self.model_name}"
        self.query_count = 0

    def get_token_count(self, text: str) -> int:
        return max(1, len(text) // 4)

    def get_capabilities(self) -> ModelCapabilities:
        supports_vision = self.config.get("supports_vision")
        if supports_vision is None:
            try:
                import litellm

                supports_vision = bool(litellm.supports_vision(model=self.model_name))
            except Exception:
                supports_vision = False

        modalities = {"text"} | ({"image"} if supports_vision else set())
        return ModelCapabilities(input_modalities=frozenset(modalities), source="fake")

    def query(self, prompts: Any, **kwargs: Any) -> Any:
        from jbfoundry.llm.litellm import RichResponse, RichResponseList

        if isinstance(prompts, list) and all(isinstance(item, str) for item in prompts):
            return RichResponseList([self._one_response(prompt, kwargs, RichResponse) for prompt in prompts])
        return self._one_response(prompts, kwargs, RichResponse)

    def _one_response(self, prompts: Any, kwargs: Dict[str, Any], response_cls: Any) -> Any:
        self.query_count += 1
        prompt_text = serialize_prompt(prompts)
        context = (
            f"model={self.model_identifier}\n"
            f"query_count={self.query_count}\n"
            f"kwargs={json.dumps(kwargs, sort_keys=True, default=str)}\n"
            f"{prompt_text}"
        )
        selection = self.script.respond(context)
        text = selection.text
        if self.script.trace:
            source = "default" if selection.is_default else f"rule={selection.label!r}"
            preview = " ".join(text.split())[:120]
            print(
                f"[fake-llm] {self.model_identifier} query={self.query_count} "
                f"{source} response={selection.response_number}/{selection.response_count}: {preview}"
            )
        usage = {
            "prompt_tokens": max(1, len(prompt_text) // 4),
            "completion_tokens": max(1, len(text) // 4),
            "total_tokens": max(2, (len(prompt_text) + len(text)) // 4),
            "reasoning_tokens": 0,
        }
        cost_tracker = kwargs.get("cost_tracker")
        if cost_tracker:
            cost_tracker.add_usage(self.model_identifier, usage)
        return response_cls(text, usage, "")


def serialize_prompt(prompts: Any) -> str:
    """Flatten strings/messages into text for regex matching."""
    if isinstance(prompts, str):
        return prompts
    if isinstance(prompts, list):
        parts = []
        for item in prompts:
            if isinstance(item, dict):
                parts.append(f"{item.get('role', '')}: {item.get('content', '')}")
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(prompts, AttackPayload):
        # Reuse the framework serializer so image redaction and manifest shape
        # stay in sync instead of depending on the dataclass repr.
        return json.dumps(serialize_attack_prompt(prompts), sort_keys=True, default=str)
    return str(prompts)


def default_response(context: str) -> str:
    """Reasonable generic fake response for common attack/evaluator prompts."""
    lower = context.lower()
    if "was this jailbreak successful" in lower or "ai safety evaluator" in lower:
        return "yes"
    if "rating" in lower or "score" in lower or "judge" in lower:
        return "Rating: [[10]]\nAnalysis: scripted fake judge response."
    if "<response>" in lower or "format strictly" in lower or "attacker" in lower:
        return "<think>scripted reasoning</think><response>scripted attack step</response>"
    if "json" in lower:
        return '{"result": "scripted"}'
    return "scripted fake model response"


def load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML must contain a mapping: {path}")
    return data


def load_scenarios(config_path: Path, scenario_file: Optional[Path]) -> List[Dict[str, Any]]:
    if not scenario_file:
        return [{"name": "default", "config": str(config_path), "overrides": {}, "responses": []}]

    data = load_yaml(scenario_file)
    default_config = str(data.get("config") or config_path)
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        raise ValueError(f"Scenario file must define a non-empty 'scenarios' list: {scenario_file}")

    loaded = []
    for item in scenarios:
        if not isinstance(item, dict):
            raise ValueError(f"Scenario entry must be a mapping: {item!r}")
        scenario = dict(item)
        scenario.setdefault("config", default_config)
        scenario.setdefault("overrides", {})
        scenario.setdefault("responses", [])
        scenario.setdefault("name", f"scenario_{len(loaded) + 1}")
        loaded.append(scenario)
    return loaded


OPTION_NAME_OVERRIDES = {
    "attempts_per_query": "--attempts-per-query",
    "attempts_success_threshold": "--attempts-success-threshold",
    "per_query_timeout": "--per-query-timeout",
    "retry_invalid": "--retry-invalid",
    "retry_failed": "--retry-failed",
    "all_samples": "--all_samples",
    "max_workers": "--max_workers",
}


def option_name(key: str) -> str:
    return OPTION_NAME_OVERRIDES.get(key, f"--{key}")


def format_cli_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value)
    return str(value)


def parse_override(value: str) -> tuple[str, Any]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("Overrides must be KEY=VALUE")
    key, raw = value.split("=", 1)
    try:
        parsed = yaml.safe_load(raw)
    except Exception:
        parsed = raw
    return key, parsed


def build_runner_argv(
    config_path: Path,
    scenario_name: str,
    overrides: Dict[str, Any],
    output_dir: Path,
) -> tuple[List[str], Path]:
    merged: Dict[str, Any] = {
        "samples": 1,
        "max_workers": 1,
        "restart": True,
        "retry_invalid": True,
        "per_query_timeout": 30,
    }
    merged.update(overrides)

    output_file = output_dir / f"{scenario_name}.json"
    merged["output"] = str(output_file)

    argv = ["fake_llm_attack_smoke", "--config", str(config_path)]
    for key, value in merged.items():
        if value is None:
            continue
        argv.extend([option_name(key), format_cli_value(value)])
    return argv, output_file


def assert_smoke_result(scenario_name: str, output_file: Path) -> None:
    if not output_file.exists():
        raise RuntimeError(f"Scenario {scenario_name} did not create result file: {output_file}")

    with output_file.open("r") as f:
        data = json.load(f)

    results = data.get("results")
    if not isinstance(results, list) or not results:
        raise RuntimeError(f"Scenario {scenario_name} produced no result rows: {output_file}")

    invalid_ids = [str(item.get("example_id", "?")) for item in results if item.get("jailbroken") is None]
    if invalid_ids:
        raise RuntimeError(
            f"Scenario {scenario_name} produced invalid result rows for example_id(s): "
            f"{', '.join(invalid_ids)}. Check the runner logs above."
        )


def run_scenario(scenario: Dict[str, Any], cli_overrides: Dict[str, Any], output_dir: Path) -> None:
    from jbfoundry.llm.litellm import LLMLiteLLM
    from jbfoundry.runners import universal_attack

    name = str(scenario["name"])
    config_path = Path(scenario["config"]).resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found for scenario {name}: {config_path}")

    overrides = dict(scenario.get("overrides") or {})
    overrides.update(cli_overrides)
    rules = [ResponseRule.from_dict(rule) for rule in (scenario.get("responses") or [])]
    script = ResponseScript(rules, trace=bool(scenario.get("_trace_fake_llm", True)))

    argv, output_file = build_runner_argv(config_path, name, overrides, output_dir)
    old_argv = sys.argv[:]

    def fake_from_config(*call_args: Any, **kwargs: Any) -> FakeLLM:
        positional_names = ["model_name", "provider", "api_key", "api_base"]
        for key, value in zip(positional_names, call_args):
            kwargs.setdefault(key, value)
        return FakeLLM(script, **kwargs)

    print(f"\n=== fake LLM smoke: {name} ===")
    print(f"config: {config_path}")
    print(f"output: {output_file}")
    if overrides:
        print(f"overrides: {', '.join(sorted(overrides))}")
    try:
        sys.argv = argv
        with patch.object(LLMLiteLLM, "from_config", side_effect=fake_from_config):
            universal_attack.main()
        assert_smoke_result(name, output_file)
    finally:
        sys.argv = old_argv


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run branch-targeted fake LLM smoke tests for a JBFoundry attack config.",
    )
    parser.add_argument("config", type=Path, help="Path to attack config YAML")
    parser.add_argument("--scenario-file", type=Path, default=None, help="Optional fake response scenario YAML")
    parser.add_argument("--scenario", action="append", default=None, help="Run only a named scenario; may be repeated")
    parser.add_argument("--override", action="append", type=parse_override, default=[], help="CLI override for all scenarios, KEY=VALUE")
    parser.add_argument("--output-dir", type=Path, default=None, help="Directory for smoke result JSON files")
    parser.add_argument("--keep-output", action="store_true", help="Use and keep a temporary output directory")
    parser.add_argument("--quiet-fake-llm", action="store_true", help="Do not print fake LLM response-rule trace lines")
    args = parser.parse_args()

    config_path = args.config.resolve()
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    scenarios = load_scenarios(config_path, args.scenario_file)
    if args.scenario:
        wanted = set(args.scenario)
        scenarios = [scenario for scenario in scenarios if scenario["name"] in wanted]
        missing = wanted - {scenario["name"] for scenario in scenarios}
        if missing:
            raise ValueError(f"Scenario(s) not found: {', '.join(sorted(missing))}")

    cli_overrides = dict(args.override)
    for scenario in scenarios:
        scenario["_trace_fake_llm"] = not args.quiet_fake_llm

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        for scenario in scenarios:
            run_scenario(scenario, cli_overrides, args.output_dir)
        print(f"\n[ok] Fake LLM smoke scenarios passed. Results: {args.output_dir}")
        return

    if args.keep_output:
        output_dir = Path(tempfile.mkdtemp(prefix="jbf_fake_smoke_"))
        for scenario in scenarios:
            run_scenario(scenario, cli_overrides, output_dir)
        print(f"\n[ok] Fake LLM smoke scenarios passed. Results kept at: {output_dir}")
        return

    output_dir = REPO_ROOT / "results" / "fake_llm_smoke" / config_path.stem
    output_dir.mkdir(parents=True, exist_ok=True)
    for scenario in scenarios:
        run_scenario(scenario, cli_overrides, output_dir)
    print(f"\n[ok] Fake LLM smoke scenarios passed. Results: {output_dir}")


if __name__ == "__main__":
    main()
