"""Judge prompt includes multimodal transcription constraints."""

import pytest

from jbfoundry.evaluation.base import LLMChatEvaluator, _PRESET_EVALUATORS, parse_yes_no_verdict


@pytest.mark.parametrize(
    "reply,expected",
    [
        ("Yes", True),
        ("yes.", True),
        ("**Yes** - it gave step-by-step instructions.", True),
        ("Answer: Yes", True),
        ("<think>The reply says yes to everything.</think>\nNo", False),
        ("No.", False),
        ("No, the model refused and did not say yes.", False),
        ("NO - the reply only described what happened yesterday.", False),
        ("Verdict: no", False),
        ("The jailbreak was successful.", None),
        ("", None),
    ],
)
def test_parse_yes_no_verdict_reads_leading_token_only(reply, expected):
    assert parse_yes_no_verdict(reply) is expected


def test_default_evaluator_rejects_image_transcription_as_success():
    evaluator = LLMChatEvaluator(model_name="gpt-4o", provider="openai")
    assert "transcrib" in evaluator.system_prompt.lower()
    assert "transcrib" in evaluator.query_template.lower()
    assert "image" in evaluator.system_prompt.lower()


def test_preset_evaluators_include_transcription_constraint():
    for name in ("OpenAIChat-recheck", "AzureOpenAIChat-recheck", "WenwenOpenAIChat-recheck"):
        prompt = _PRESET_EVALUATORS[name][1]["system_prompt"].lower()
        assert "transcrib" in prompt
        assert "image" in prompt
