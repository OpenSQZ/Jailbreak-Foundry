# Multimodal Attack Implementation Supplement

Append these instructions whenever the implementation plan includes an
`Image Construction Spec` or otherwise requires image payloads.

## Payload template

```python
from pathlib import Path
from jbfoundry.attacks.base import ModernBaseAttack, AttackParameter, AttackPrompt
from jbfoundry.payloads import AttackPayload, ImageAsset, ImagePart, Message, TextPart

class ExampleImageAttack(ModernBaseAttack):
    NAME = "example_image_attack_gen"
    REQUIRED_DATASET_MODALITIES = frozenset({"text"})  # or {"text", "image"}

    def generate_attack(self, prompt, goal, target, **kwargs) -> AttackPrompt:
        artifact_dir = Path(kwargs["artifact_dir"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        image_path = artifact_dir / "generated.png"
        # Create image_path with CPU-safe tooling (Pillow, etc.).
        (artifact_dir / "rendered_text.txt").write_text("intent...\n", encoding="utf-8")
        return AttackPayload(
            messages=(
                Message(
                    role="user",
                    parts=(
                        ImagePart(ImageAsset.from_path(image_path)),
                        TextPart("Benign text sent alongside the image"),
                    ),
                ),
            ),
        )
```

## Hard rules

- Do NOT return provider-specific `{"type": "image_url", ...}` message lists.
  The runner raises `TypeError` unless the value is an `AttackPayload`.
- Do NOT modify `src/jbfoundry/payloads.py`, runners, litellm, base, factory, or
  registry. Import and use them.
- Always create `artifact_dir` yourself.
- Write a `rendered_text.txt` sidecar describing intended rendered text and
  layout parameters so auditors / smoke tests can assert intent.
- Prefer inline Pillow render checks (text fits canvas, font size above a
  minimum, non-blank pixel variance) inside the attack file. Do not add new
  evaluation helper modules elsewhere.
- Attack config YAML must set `victim_model.supports_vision: true` (or rely on
  litellm autodetection for known vision models) and may set
  `max_image_bytes`.

## Smoke testing

```bash
python scripts/smoke_tests/fake_llm_attack_smoke.py scripts/attack_configs/{attack_name}.yaml
```

The fake LLM mirrors production vision capability detection. Image bytes are
not sent to a provider during smoke; success means the payload path, registry,
runner modality gates, and result writer all complete without `jailbroken: null`.
