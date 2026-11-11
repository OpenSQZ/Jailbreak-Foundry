from pathlib import Path

import pytest
import yaml
from PIL import Image

from jbfoundry.attacks.generated.furina_gen import FurinaGenAttack


class _FakeSceneLLM:
    def __init__(self, response: str):
        self.response = response

    def query(self, messages):
        return self.response


def test_scene_generation_uses_low_reasoning_and_large_token_budget(monkeypatch):
    attack = FurinaGenAttack()
    captured = {}

    def fake_make_helper(param_name, temperature, max_tokens, reasoning_effort=None):
        captured.update(
            {
                "param_name": param_name,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "reasoning_effort": reasoning_effort,
            }
        )
        return _FakeSceneLLM("A person works quietly at a desk beneath a window.")

    monkeypatch.setattr(attack, "_make_helper_llm", fake_make_helper)

    scene = attack._generate_scene_description("example goal", temp=0.4, max_tokens=2048)

    assert scene == "A person works quietly at a desk beneath a window."
    assert captured == {
        "param_name": "scene_generator_model",
        "temperature": 0.4,
        "max_tokens": 2048,
        "reasoning_effort": "low",
    }


def test_scene_generation_rejects_empty_text(monkeypatch):
    attack = FurinaGenAttack()
    monkeypatch.setattr(attack, "_make_helper_llm", lambda *args, **kwargs: _FakeSceneLLM("  "))

    with pytest.raises(RuntimeError, match="empty text"):
        attack._generate_scene_description("example goal", temp=0.4, max_tokens=2048)


def test_typography_render_contains_visible_text(tmp_path):
    attack = FurinaGenAttack()

    image_path, _ = attack._render_scene_image(
        "A person works quietly at a desk beneath a bright window.",
        tmp_path,
        "typo",
    )

    darkest, _ = Image.open(image_path).convert("L").getextrema()
    assert darkest < 50


def test_furina_config_enables_typo_with_low_reasoning():
    config_path = Path(__file__).resolve().parents[1] / "scripts" / "attack_configs" / "furina_gen.yaml"
    params = yaml.safe_load(config_path.read_text(encoding="utf-8"))["attack_parameters"]

    assert params["mode"] == "typo"
    assert params["typography_max_tokens"] == 2048
    assert params["typography_reasoning_effort"] == "low"
