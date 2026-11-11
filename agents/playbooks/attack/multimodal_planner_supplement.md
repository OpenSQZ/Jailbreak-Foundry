# Multimodal Attack Planning Supplement

Append these instructions whenever the paper is a vision / multimodal jailbreak
(typographic prompts, image-text risk splitting, text-to-image helpers, etc.).

## Extra framework files to read

In addition to the standard framework files, you MUST also read:

- `src/jbfoundry/payloads.py`
- `docs/MULTIMODAL.md`
- `src/jbfoundry/runners/universal_attack.py` (artifact_dir + modality checks)

## Image Construction Spec (required plan section)

Insert a new section **after** "Prompts and Templates" titled
`## 3.5 Image Construction Spec` with:

| Property | Value | Notes |
|---|---|---|
| Canvas size | WxH | |
| Font / font size | ... | |
| Colors | foreground / background | |
| Layout | title, list, panels, wrap rules | |
| Split / Pro mode | if applicable | |
| Output files | relative to `artifact_dir` | |
| Sidecar | `rendered_text.txt` fields | |
| REQUIRED_DATASET_MODALITIES | `{"text"}` or `{"text","image"}` | |

## Return contract

- Image-producing attacks MUST return `AttackPayload` with `ImagePart` /
  `TextPart` parts. Returning provider-native `image_url` dicts is rejected by
  the runner.
- Local images must be created under `kwargs["artifact_dir"]`. The runner does
  **not** create that directory; the attack must `mkdir(parents=True)`.
- Prefer CPU-safe image tooling (Pillow). External text-to-image APIs are
  acceptable when the paper requires them and credentials are passed like any
  other helper model dict parameter.

## Single-attack rule

Variants such as FigStep-Pro remain parameters of one registerable attack
(`mode=figstep_pro`), not a second generated attack file.
