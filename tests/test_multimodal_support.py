"""Offline tests for the image-only multimodal execution path."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from jbfoundry.attacks.base import ModernBaseAttack
from jbfoundry.dataset.base import JailbreakDataset, MultimodalJailbreakDataset
from jbfoundry.dataset.local_loader import LocalFileLoader
from jbfoundry.llm.litellm import LLMLiteLLM
from jbfoundry.payloads import (
    AttackPayload,
    ImageAsset,
    ImagePart,
    JudgedOutput,
    Message,
    ModelCapabilities,
    TextPart,
)
from jbfoundry.runners.universal_attack import (
    _process_single_example_inner,
    validate_payload_compatibility,
    validate_run_compatibility,
)
from jbfoundry.runners.utils.dynamic_args_parser import DynamicArgumentParser


class ImageFixtureAttack(ModernBaseAttack):
    """Minimal image-producing attack used only to test framework contracts."""

    NAME = "image_fixture_attack"
    REQUIRED_DATASET_MODALITIES = frozenset({"text"})

    def generate_attack(self, prompt, goal, target, **kwargs):
        artifact_dir = Path(kwargs["artifact_dir"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        image_path = artifact_dir / "fixture.png"
        Image.new("RGB", (32, 24), "white").save(image_path, format="PNG")
        return AttackPayload(
            messages=(
                Message(
                    role="user",
                    parts=(
                        ImagePart(ImageAsset.from_path(image_path)),
                        TextPart(goal),
                    ),
                ),
            )
        )


class ProviderSpecificImageAttack(ModernBaseAttack):
    """Invalid fixture proving runner image payloads must be provider-neutral."""

    NAME = "provider_specific_image_attack"

    def generate_attack(self, prompt, goal, target, **kwargs):
        return [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64,unsafe"},
                    }
                ],
            }
        ]


def _create_image(path: Path, color="white") -> Path:
    Image.new("RGB", (32, 24), color).save(path, format="PNG")
    return path


def _payload_for_image(path: Path) -> AttackPayload:
    return AttackPayload(
        messages=(
            Message(
                role="user",
                parts=(
                    ImagePart(ImageAsset.from_path(path, detail="low")),
                    TextPart("Describe the image."),
                ),
            ),
        )
    )


def test_payload_manifest_references_image_without_embedding_bytes(tmp_path):
    image_path = _create_image(tmp_path / "sample.png")
    payload = _payload_for_image(image_path)

    manifest = payload.to_dict(relative_to=tmp_path)
    serialized = json.dumps(manifest)

    assert manifest["modalities"] == ["image", "text"]
    assert manifest["messages"][0]["content"][0]["path"] == "sample.png"
    assert manifest["messages"][0]["content"][0]["sha256"]
    assert "base64" not in serialized
    assert "data:image" not in serialized


def test_payload_accepts_lists_but_stores_immutable_sequences(tmp_path):
    asset = ImageAsset.from_path(_create_image(tmp_path / "sample.png"))
    message = Message(role="user", parts=[ImagePart(asset), TextPart("test")])
    payload = AttackPayload(messages=[message])

    assert isinstance(message.parts, tuple)
    assert isinstance(payload.messages, tuple)


def test_image_integrity_is_checked_at_transport_time(tmp_path):
    image_path = _create_image(tmp_path / "sample.png")
    asset = ImageAsset.from_path(image_path)
    _create_image(image_path, color="black")

    with pytest.raises(ValueError, match="integrity check failed"):
        asset.to_data_url(max_bytes=1024 * 1024)


def test_local_loader_resolves_relative_image_manifests(tmp_path):
    image_path = _create_image(tmp_path / "input.png")
    manifest_path = tmp_path / "dataset.jsonl"
    manifest_path.write_text(
        json.dumps(
            {
                "behavior": "A test behavior",
                "goal": "A test goal",
                "target": "",
                "category": "test",
                "image": image_path.name,
                "metadata": {"case": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    dataset = LocalFileLoader().load(str(manifest_path))

    assert isinstance(dataset, MultimodalJailbreakDataset)
    assert dataset.modalities == frozenset({"text", "image"})
    assert dataset[0]["media"][0].path == image_path.resolve()
    assert dataset[0]["metadata"] == {"case": 1}


def test_local_loader_keeps_multiple_images_in_one_json_record(tmp_path):
    first = _create_image(tmp_path / "first.png")
    second = _create_image(tmp_path / "second.png", color="black")
    manifest_path = tmp_path / "dataset.json"
    manifest_path.write_text(
        json.dumps(
            {
                "behavior": "A test behavior",
                "goal": "A test goal",
                "images": [first.name, second.name],
            }
        ),
        encoding="utf-8",
    )

    dataset = LocalFileLoader().load(str(manifest_path))

    assert len(dataset) == 1
    assert len(dataset[0]["media"]) == 2


def test_text_only_local_loader_defaults_remain_backward_compatible(tmp_path):
    json_path = tmp_path / "dataset.json"
    json_path.write_text(json.dumps([{"behavior": "json behavior"}]), encoding="utf-8")
    json_dataset = LocalFileLoader().load(str(json_path))
    assert json_dataset[0]["goal"] == ""
    assert json_dataset[0]["category"] == ""

    jsonl_path = tmp_path / "dataset.jsonl"
    jsonl_path.write_text('{"behavior":"jsonl behavior"}\n', encoding="utf-8")
    jsonl_dataset = LocalFileLoader().load(str(jsonl_path))
    assert jsonl_dataset[0]["goal"] == "jsonl behavior"
    assert jsonl_dataset[0]["category"] == "dataset"

    csv_path = tmp_path / "dataset.csv"
    csv_path.write_text("behavior\ncsv behavior\n", encoding="utf-8")
    csv_dataset = LocalFileLoader().load(str(csv_path))
    assert csv_dataset[0]["goal"] == ""
    assert csv_dataset[0]["category"] == ""


def test_dataset_only_declares_required_image_when_every_record_has_one(tmp_path):
    image = ImageAsset.from_path(_create_image(tmp_path / "first.png"))
    dataset = MultimodalJailbreakDataset(
        behaviors=["first", "second"],
        goals=["first", "second"],
        targets=["", ""],
        categories=["test", "test"],
        media=[[image], []],
        metadata=[{}, {}],
    )

    assert dataset.modalities == frozenset({"text"})


def test_litellm_converts_images_only_at_transport_and_redacts_logs(tmp_path, monkeypatch):
    payload = _payload_for_image(_create_image(tmp_path / "sample.png"))
    captured = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok", reasoning_content=""))],
            usage=SimpleNamespace(
                prompt_tokens=2,
                completion_tokens=1,
                total_tokens=3,
                completion_tokens_details=None,
            ),
        )

    monkeypatch.setattr("jbfoundry.llm.litellm.completion", fake_completion)
    llm = LLMLiteLLM.from_config(
        model_name="test-vlm",
        provider="openai",
        api_key="secret",
        supports_vision=True,
        log_dir=str(tmp_path / "logs"),
    )

    response = llm.query(payload)

    image_url = captured["messages"][0]["content"][0]["image_url"]["url"]
    assert image_url.startswith("data:image/png;base64,")
    assert str(response) == "ok"

    query_log = next((tmp_path / "logs").glob("*_query.json"))
    logged = query_log.read_text(encoding="utf-8")
    assert "base64" not in logged
    assert "secret" not in logged
    assert "image reference omitted" in logged
    assert len(captured["messages"]) == 1


def test_litellm_text_prompt_behavior_is_unchanged(monkeypatch):
    captured = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="ok", reasoning_content=""))],
            usage=SimpleNamespace(
                prompt_tokens=1,
                completion_tokens=1,
                total_tokens=2,
                completion_tokens_details=None,
            ),
        )

    monkeypatch.setattr("jbfoundry.llm.litellm.completion", fake_completion)
    llm = LLMLiteLLM.from_config(
        model_name="text-only-model",
        provider="openai",
        api_key="test",
        supports_vision=False,
        log_dir=None,
    )

    response = llm.query("hello")

    assert str(response) == "ok"
    assert captured["messages"] == [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "hello"},
    ]


def test_text_only_model_rejects_image_before_completion(tmp_path, monkeypatch):
    payload = _payload_for_image(_create_image(tmp_path / "sample.png"))
    called = False

    def fake_completion(**kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("jbfoundry.llm.litellm.completion", fake_completion)
    llm = LLMLiteLLM.from_config(
        model_name="text-only-model",
        provider="openai",
        api_key="test",
        supports_vision=False,
        log_dir=None,
    )

    with pytest.raises(ValueError, match="does not support required input modalities: image"):
        llm.query(payload)
    assert called is False


def test_run_preflight_checks_only_attack_dataset_requirements():
    dataset = JailbreakDataset(
        behaviors=["test"], goals=["test"], targets=[""], categories=["test"]
    )

    class DatasetImageAttack(ModernBaseAttack):
        NAME = "dataset_image_test"
        REQUIRED_DATASET_MODALITIES = frozenset({"text", "image"})

        def generate_attack(self, prompt, goal, target, **kwargs):
            return prompt

    class FakeLLM:
        def get_capabilities(self):
            return ModelCapabilities()

    with pytest.raises(ValueError, match="requires dataset modalities.*image"):
        validate_run_compatibility(FakeLLM(), DatasetImageAttack(), dataset)

    compatibility = validate_run_compatibility(
        FakeLLM(),
        DatasetImageAttack(),
        SimpleNamespace(modalities=frozenset({"text", "image"})),
    )
    assert compatibility["required_dataset_modalities"] == ["image", "text"]


def test_attack_config_does_not_duplicate_access_or_payload_modalities():
    config = ImageFixtureAttack.get_config()

    assert config["required_dataset_modalities"] == ["text"]
    assert "access_level" not in config
    assert "output_modalities" not in config
    assert "victim_input_modalities" not in config


def test_payload_compatibility_infers_actual_victim_inputs(tmp_path):
    payload = _payload_for_image(_create_image(tmp_path / "sample.png"))

    class FakeLLM:
        def __init__(self, modalities):
            self.capabilities = ModelCapabilities(input_modalities=frozenset(modalities))

        def get_capabilities(self):
            return self.capabilities

    with pytest.raises(ValueError, match="generated payload modalities: image"):
        validate_payload_compatibility(FakeLLM({"text"}), payload)

    modalities = validate_payload_compatibility(FakeLLM({"text", "image"}), payload)
    assert modalities == frozenset({"text", "image"})


def test_runner_saves_image_manifest_instead_of_base64(tmp_path):
    class FakeResponse(str):
        def get_usage(self):
            return {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}

        def get_reasoning_content(self):
            return ""

    class FakeLLM:
        def get_capabilities(self):
            return ModelCapabilities(input_modalities=frozenset({"text", "image"}))

        def query(self, payload, **kwargs):
            assert isinstance(payload, AttackPayload)
            return FakeResponse("refused")

    args = SimpleNamespace(
        provider="test",
        model="test-vlm",
        defense=None,
        attempts_per_query=1,
        attempts_success_threshold=1,
    )
    output_path = tmp_path / "results.json"
    output_path.write_text('{"metadata": {}, "results": []}', encoding="utf-8")
    evaluated_attempt = {}

    def evaluator(attempt):
        evaluated_attempt.update(attempt)
        return False

    result = _process_single_example_inner(
        0,
        {"behavior": "test", "goal": "test goal", "target": "", "category": "test"},
        FakeLLM(),
        ImageFixtureAttack(),
        evaluator,
        {"name": "image_fixture_attack"},
        args,
        str(output_path),
        set(),
    )

    serialized = output_path.read_text(encoding="utf-8")
    image_manifest = result["attack_prompt"]["messages"][0]["content"][0]
    assert image_manifest["path"].startswith("artifacts/image_fixture_attack/")
    assert (tmp_path / image_manifest["path"]).is_file()
    assert evaluated_attempt["modalities"] == ["image", "text"]
    assert evaluated_attempt["attack_prompt"]["type"] == "attack_payload"
    assert "base64" not in serialized
    assert "data:image" not in serialized


def test_runner_rejects_provider_specific_image_payloads(tmp_path):
    class FakeLLM:
        called = False

        def get_capabilities(self):
            return ModelCapabilities(input_modalities=frozenset({"text", "image"}))

        def query(self, payload, **kwargs):
            self.called = True

    args = SimpleNamespace(
        provider="test",
        model="test-vlm",
        defense=None,
        attempts_per_query=1,
        attempts_success_threshold=1,
    )
    output_path = tmp_path / "results.json"
    output_path.write_text('{"metadata": {}, "results": []}', encoding="utf-8")
    llm = FakeLLM()

    with pytest.raises(TypeError, match="must return AttackPayload"):
        _process_single_example_inner(
            0,
            {"behavior": "test", "goal": "test", "target": "", "category": "test"},
            llm,
            ProviderSpecificImageAttack(),
            lambda attempt: False,
            {"name": "provider_specific_image_attack"},
            args,
            str(output_path),
            set(),
        )

    assert llm.called is False
    assert "base64" not in output_path.read_text(encoding="utf-8")


def test_runner_judges_attack_output_without_querying_victim(tmp_path):
    class JudgedFixtureAttack(ModernBaseAttack):
        NAME = "judged_fixture_attack"

        def generate_attack(self, prompt, goal, target, **kwargs):
            return JudgedOutput(
                response="synthesized answer",
                source="fixture_synthesizer",
                modalities={"text", "image"},
                transcript={"scene_image": tmp_path / "scene.png"},
            )

    class FakeLLM:
        called = False

        def get_capabilities(self):
            return ModelCapabilities(input_modalities=frozenset({"text"}))

        def query(self, payload, **kwargs):
            self.called = True

    args = SimpleNamespace(
        provider="test",
        model="test-vlm",
        defense=None,
        attempts_per_query=1,
        attempts_success_threshold=1,
    )
    output_path = tmp_path / "results.json"
    output_path.write_text('{"metadata": {}, "results": []}', encoding="utf-8")
    llm = FakeLLM()
    evaluated_attempt = {}

    def evaluator(attempt):
        evaluated_attempt.update(attempt)
        return True

    result = _process_single_example_inner(
        0,
        {"behavior": "test", "goal": "test goal", "target": "", "category": "test"},
        llm,
        JudgedFixtureAttack(),
        evaluator,
        {"name": "judged_fixture_attack"},
        args,
        str(output_path),
        set(),
    )

    assert llm.called is False
    assert evaluated_attempt["answer"] == "synthesized answer"
    assert evaluated_attempt["modalities"] == ["image", "text"]
    assert result["jailbroken"] is True
    assert result["judged_source"] == "fixture_synthesizer"
    saved = json.loads(output_path.read_text(encoding="utf-8"))["results"][0]
    assert saved["attack_prompt"]["type"] == "judged_output"
    assert saved["attack_prompt"]["transcript"]["scene_image"] == str(tmp_path / "scene.png")


def test_runner_marks_victim_as_judged_source_by_default(tmp_path):
    class FakeResponse(str):
        def get_usage(self):
            return {}

        def get_reasoning_content(self):
            return ""

    class FakeLLM:
        def get_capabilities(self):
            return ModelCapabilities(input_modalities=frozenset({"text", "image"}))

        def query(self, payload, **kwargs):
            return FakeResponse("victim reply")

    args = SimpleNamespace(
        provider="test",
        model="test-vlm",
        defense=None,
        attempts_per_query=1,
        attempts_success_threshold=1,
    )
    output_path = tmp_path / "results.json"
    output_path.write_text('{"metadata": {}, "results": []}', encoding="utf-8")

    result = _process_single_example_inner(
        0,
        {"behavior": "test", "goal": "test goal", "target": "", "category": "test"},
        FakeLLM(),
        ImageFixtureAttack(),
        lambda attempt: False,
        {"name": "image_fixture_attack"},
        args,
        str(output_path),
        set(),
    )

    assert result["judged_source"] == "victim"
    assert result["model_response"] == "victim reply"


def test_cli_accepts_explicit_vision_capability_override():
    parser = DynamicArgumentParser()
    enabled = parser.parser.parse_args(["--supports-vision", "true"])
    disabled = parser.parser.parse_args(["--supports-vision", "false"])

    assert enabled.supports_vision is True
    assert disabled.supports_vision is False
