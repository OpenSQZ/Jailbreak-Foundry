"""Single source of truth for the framework's supported attack payload modalities.

The paper-search / pipeline / preprocessor layers all need to decide whether a
candidate attack's *payload* (what the attack actually feeds to the victim) is
something this framework can run. Historically each layer hand-rolled its own
check (a `model_type` enum, an `IMAGE_MODEL_TYPES` set, prompt text), and they
drifted apart -- e.g. a video attack (TempJail) slipped through because the
victim was tagged "vlm", while a text-template attack on a VLM was mis-filed.

This module derives the supported set from the runtime payload type system
(`jbfoundry.payloads.ContentPart`) so it can never drift: the moment a
`VideoPart`/`AudioPart` is added to `ContentPart`, the supported set widens
automatically and the filter lets those through. Until then, video/audio are
*structurally* rejected, not keyword-rejected.

Payload modality vocabulary (the values `payload_modalities` may contain):
    text, image, video, audio, 3d, other

Only `text` and `image` are currently supported by the runtime.
"""

from __future__ import annotations

from typing import Iterable, Tuple

# --- Derive supported modalities from the runtime payload type system -------
# ContentPart is a Union of the concrete part classes the runner can actually
# emit. We map each concrete class to a modality label. Adding a new part class
# to ContentPart (and registering it here) is the *only* change needed to widen
# support -- every consumer imports SUPPORTED_PAYLOAD / payload_ok from here.
try:
    from jbfoundry.payloads import ContentPart  # noqa: F401  (import for side-effect / introspection)
    from jbfoundry.payloads import TextPart, ImagePart

    _PART_TO_MODALITY = {
        TextPart: "text",
        ImagePart: "image",
    }
except Exception:  # pragma: no cover - import guard for environments without src on path
    TextPart = ImagePart = None  # type: ignore[assignment]
    _PART_TO_MODALITY = {}

# The complete set of payload modalities the framework can actually send to a
# victim model right now. Derived, not hand-written.
SUPPORTED_PAYLOAD = frozenset(m for m in _PART_TO_MODALITY.values()) or frozenset({"text", "image"})

# Unknown labels are dropped during normalization. If no recognized labels
# remain, the payload is rejected; mixed inputs retain their known labels.
KNOWN_MODALITIES = frozenset({"text", "image", "video", "audio", "3d", "other"})

# Temporary harvest control: when True, only attacks whose payload includes an
# image are admitted. This is the "initial acceptance" knob -- flip it back to
# False once multimodal attacks are being collected reliably and text-only
# attacks should be re-admitted. No other code needs to change.
REQUIRE_IMAGE = True


def normalise_modalities(mods: Iterable[str] | None) -> Tuple[str, ...]:
    """Lowercase, dedupe, drop unknowns, return a sorted tuple. None/[] -> ()."""
    if not mods:
        return ()
    out = set()
    for m in mods:
        if not isinstance(m, str):
            continue
        m = m.strip().lower()
        if m in KNOWN_MODALITIES:
            out.add(m)
    return tuple(sorted(out))


def payload_ok(mods: Iterable[str] | None, *, require_image: bool | None = None) -> Tuple[bool, str]:
    """Check runtime support and, when requested, require image input.

    Returns (ok, reason). reason is "" on success, else a short stable code:
      - "payload_unknown"        : no modalities could be determined
      - "unsupported_payload:[...]" : contains a modality the runtime can't send
                                     (e.g. video, audio) -> structurally out
      - "text_only_payload"      : image input is required and none is present

    video/audio are rejected structurally (not in SUPPORTED_PAYLOAD), so they
    can never sneak in regardless of keyword matching.
    """
    if require_image is None:
        require_image = REQUIRE_IMAGE
    mods = set(normalise_modalities(mods))
    if not mods:
        return False, "payload_unknown"
    if not mods <= SUPPORTED_PAYLOAD:
        unsupported = sorted(mods - SUPPORTED_PAYLOAD)
        return False, f"unsupported_payload:{unsupported}"
    if require_image and "image" not in mods:
        return False, "text_only_payload"
    return True, ""


def infer_model_type(mods: Iterable[str] | None) -> str:
    """Back-compat: derive a legacy `model_type` value from payload modalities.

    Legacy consumers that still read `model_type` get a sensible value
    without the classifier having to emit one.
    text_only | vlm | audio | video | multimodal | unclear.
    """
    mods = set(normalise_modalities(mods))
    if not mods:
        return "unclear"
    if "audio" in mods and "image" not in mods and "video" not in mods:
        return "audio"
    if "video" in mods:
        return "video"
    if "image" in mods and "text" in mods:
        return "multimodal"
    if "image" in mods:
        return "vlm"
    if mods == {"text"}:
        return "text_only"
    return "unclear"
