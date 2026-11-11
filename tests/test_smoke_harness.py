"""Regression tests for the fake-LLM smoke harness.

The harness in ``scripts/smoke_tests/fake_llm_attack_smoke.py`` is a mandatory
acceptance gate for generated attacks, but it substitutes an ad-hoc ``FakeLLM``
for the real adapter. These tests exercise the harness itself so that changes to
the LLM interface cannot silently break it.
"""

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_PATH = REPO_ROOT / "scripts" / "smoke_tests" / "fake_llm_attack_smoke.py"
TEXT_CONFIG_PATH = REPO_ROOT / "scripts" / "attack_configs" / "aim_gen.yaml"


def load_harness():
    """Load the harness by path; it lives in scripts/ and is not an importable package."""
    spec = importlib.util.spec_from_file_location("smoke_harness", HARNESS_PATH)
    module = importlib.util.module_from_spec(spec)
    # dataclass field resolution looks the module up in sys.modules, so register first.
    sys.modules["smoke_harness"] = module
    spec.loader.exec_module(module)
    return module


def test_harness_runs_a_text_attack_config_end_to_end(tmp_path):
    harness = load_harness()

    scenarios = harness.load_scenarios(TEXT_CONFIG_PATH, None)
    scenario = scenarios[0]
    scenario["_trace_fake_llm"] = False

    harness.run_scenario(scenario, {"samples": 1}, tmp_path)

    output_file = tmp_path / f"{scenario['name']}.json"
    assert output_file.exists()

    results = json.loads(output_file.read_text())["results"]
    assert results
    assert all(row["jailbroken"] is not None for row in results)


def test_fake_llm_mirrors_production_vision_capability_semantics():
    harness = load_harness()
    script = harness.ResponseScript([], trace=False)

    text_only = harness.FakeLLM(script, model_name="gpt-4", provider="openai")
    assert text_only.get_capabilities().input_modalities == frozenset({"text"})

    explicit_override = harness.FakeLLM(
        script, model_name="gpt-4", provider="openai", supports_vision=True
    )
    assert "image" in explicit_override.get_capabilities().input_modalities

    explicit_disable = harness.FakeLLM(
        script, model_name="gpt-4o", provider="openai", supports_vision=False
    )
    assert explicit_disable.get_capabilities().input_modalities == frozenset({"text"})

    autodetected = harness.FakeLLM(script, model_name="gpt-4o", provider="openai")
    assert "image" in autodetected.get_capabilities().input_modalities


def test_fake_llm_capability_detection_survives_unknown_models():
    harness = load_harness()
    script = harness.ResponseScript([], trace=False)

    unknown = harness.FakeLLM(script, model_name="not-a-real-model", provider="fake")
    assert unknown.get_capabilities().input_modalities == frozenset({"text"})


def test_fake_llm_is_bound_to_the_real_llm_interface():
    """Structural binding is what keeps the harness from drifting again."""
    from jbfoundry.llm.base import BaseLLM

    harness = load_harness()
    assert issubclass(harness.FakeLLM, BaseLLM)


def test_serialize_prompt_keeps_text_shapes_and_adds_payload_support(tmp_path):
    from PIL import Image

    from jbfoundry.payloads import AttackPayload, ImageAsset, ImagePart, Message, TextPart

    harness = load_harness()

    # Existing shapes must be untouched: scenario regexes match against these.
    assert harness.serialize_prompt("plain prompt") == "plain prompt"
    assert (
        harness.serialize_prompt(
            [{"role": "system", "content": "sys"}, {"role": "user", "content": "usr"}]
        )
        == "system: sys\nuser: usr"
    )

    image_path = tmp_path / "sample.png"
    Image.new("RGB", (8, 8), "white").save(image_path)
    payload = AttackPayload(
        messages=(
            Message(
                role="user",
                parts=(
                    ImagePart(ImageAsset.from_path(image_path)),
                    TextPart("describe the image"),
                ),
            ),
        )
    )

    serialized = harness.serialize_prompt(payload)
    assert "describe the image" in serialized
    assert "sample.png" in serialized
    assert "base64" not in serialized
