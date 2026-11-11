"""Regression tests for paper-preprocessor modality eligibility policy.

These tests assert the triage prompt text encodes the framework's actual
support: black-box attacks that send text and/or raster images to a remote
victim model are eligible, while audio/video inputs and local GPU/training/
inference dependencies remain disqualifying.
"""

from agents.utils.paper_preprocessor import ABSTRACT_TRIAGE_PROMPT, DEEP_TRIAGE_PROMPT


def test_direct_text_paper_passes_modality_check(monkeypatch):
    import json
    from agents.utils import paper_preprocessor

    monkeypatch.setattr(paper_preprocessor, "fetch_arxiv_metadata", lambda _id: ("Text attack", "Abstract"))

    class Client:
        model = "fake"

        def chat(self, _messages):
            return json.dumps({"eligible": True, "payload_modalities": ["text"], "reason": "black-box"})

    result = paper_preprocessor.check_abstract_eligibility(Client(), "test-id")
    assert result["payload_modalities"] == ["text"]


def test_abstract_triage_allows_remote_raster_image_attacks():
    prompt = ABSTRACT_TRIAGE_PROMPT.lower()

    assert "text and/or raster-image inputs" in prompt
    assert "vision-language and multimodal image attacks are allowed" in prompt
    assert "do not reject a paper merely because" in prompt
    # The old blanket text-only rule must be gone.
    assert "text-only (not vision" not in prompt


def test_deep_triage_allows_cpu_safe_visual_attacks():
    prompt = DEEP_TRIAGE_PROMPT.lower()

    assert "raster images" in prompt
    assert "remote vision-language victim api is acceptable" in prompt
    assert "cpu-safe libraries is acceptable" in prompt
    # The old disqualifier that rejected all vision/multimodal inputs must be gone.
    assert "requires vision/audio/multimodal inputs" not in prompt


def test_deep_triage_still_rejects_unsupported_or_non_cpu_methods():
    prompt = DEEP_TRIAGE_PROMPT.lower()

    assert "requires audio, video, or another unsupported input modality" in prompt
    assert "requires torch/cuda" in prompt
    assert "requires fine-tuning or training any model" in prompt
    assert "requires running inference on a local llm" in prompt
    assert "white-box/gray-box access" in prompt
