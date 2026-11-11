# Multimodal Framework Support

JBFoundry supports black-box attacks that send text and images to a remote victim model and
receive text responses. The built-in `image_text` attack provides a minimal framework smoke test;
it is not a reproduction of a published multimodal attack.

## Scope

- Victim access: black-box API calls only
- Input modalities: text and raster images
- Output modality: text
- Local execution: CPU-only image validation and encoding
- Image formats: PNG, JPEG, WebP, and GIF

Existing attacks may continue returning strings or preformatted chat messages. An
image-producing attack returns an `AttackPayload` instead.

## Attack Contract

`REQUIRED_DATASET_MODALITIES` describes what the attack algorithm needs in every dataset
record. The default is `{"text"}`, so attacks that generate an image from text can omit it.
An algorithm that consumes source images from the dataset declares `{"text", "image"}`.

The runner infers what will be sent to the victim from the actual value returned by
`generate_attack`; the attack does not declare victim-input modalities separately:

```python
from pathlib import Path

from jbfoundry.attacks.base import ModernBaseAttack
from jbfoundry.payloads import AttackPayload, ImageAsset, ImagePart, Message, TextPart


class ExampleImageAttack(ModernBaseAttack):
    NAME = "example_image_attack"
    REQUIRED_DATASET_MODALITIES = frozenset({"text"})

    def generate_attack(self, prompt, goal, target, **kwargs):
        artifact_dir = Path(kwargs["artifact_dir"])
        artifact_dir.mkdir(parents=True, exist_ok=True)
        image_path = artifact_dir / "generated.png"

        # The attack implementation creates image_path here using CPU-safe tooling.

        return AttackPayload(
            messages=(
                Message(
                    role="user",
                    parts=(
                        ImagePart(ImageAsset.from_path(image_path)),
                        TextPart("Text sent alongside the image"),
                    ),
                ),
            ),
        )
```

For every attempt, the runner also passes:

- `artifact_dir`: a dedicated directory for generated files
- `example`: the complete dataset record, including `media` and `metadata` when present
- Existing context such as `example_id`, `attempt_index`, and `cost_tracker`

The framework remains black-box by architecture: attack code can query model adapters but is not
given model weights, gradients, hidden states, or logits. There is no access-mode declaration
because no alternative access mode exists. After each payload is generated, the runner checks its
inferred modalities against the selected model and defense before making the victim call.

## Built-in Smoke Test

`image_text` renders each text goal into a PNG with Pillow and sends it to the victim with a short
text instruction. It makes no auxiliary model calls and requires no GPU. Run the included
one-sample configuration with:

```bash
python src/jbfoundry/runners/universal_attack.py \
  --config scripts/attack_configs/image_text.yaml
```

The victim model must support image input. The example configuration uses OpenAI environment
credentials; change its model/provider block when using another compatible endpoint.

## Image Datasets

Local JSON, JSONL, and CSV manifests accept `image`, `image_path`, `images`, `image_paths`, or
`media`. Relative paths are resolved from the manifest directory.

```json
{"goal":"Evaluate this input","images":["images/a.png","images/b.png"],"metadata":{"case_id":"demo-1"}}
```

Each image entry may also be an object:

```json
{"goal":"Evaluate this input","image":{"path":"images/a.png","detail":"low"}}
```

HTTP(S) image URLs are retained as remote references and are not downloaded by the dataset
loader.

## Model Configuration

LiteLLM model metadata is used to detect vision support. For compatible custom endpoints,
override detection explicitly:

```yaml
victim_model:
  model: "your-vision-model"
  provider: "openai"
  api_base: "https://provider.example/v1"
  supports_vision: true
  max_image_bytes: 20971520
```

Local images are checked with Pillow, hashed, and converted to data URLs only immediately before
the provider call. Query and error logs redact image bytes and remote image URLs. Result files
store paths, dimensions, MIME types, and SHA-256 hashes instead of base64 data.

## Defenses

Defenses remain text-only unless they explicitly declare otherwise:

```python
SUPPORTED_MODALITIES = frozenset({"text", "image"})
```

An image-aware defense must accept and return the canonical `AttackPayload`. The runner fails
before victim calls when a selected defense cannot process the attack's modalities.

## First multimodal attack

`figstep_gen` (FigStep / FigStep-Pro, arXiv 2311.05608) is the reference image-producing
attack. It returns an `AttackPayload`, writes artifacts under the runner-provided
`artifact_dir`, and emits a `rendered_text.txt` sidecar for intent auditing.

Offline acceptance:

```bash
python scripts/smoke_tests/fake_llm_attack_smoke.py scripts/attack_configs/figstep_gen.yaml --override samples=1
```

Live vision evaluation requires a vision-capable victim (`supports_vision: true` or a model
that LiteLLM autodetection marks as vision-capable) and provider credentials. Without an API
key, only the offline smoke path can be verified.
