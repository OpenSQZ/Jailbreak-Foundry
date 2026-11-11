"""Provider-neutral payload types for text and image model inputs."""

from __future__ import annotations

import base64
import hashlib
import mimetypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, FrozenSet, Iterable, Mapping, Optional, Tuple, Union
from urllib.parse import urlparse


SUPPORTED_MODALITIES = frozenset({"text", "image"})
SUPPORTED_IMAGE_MIME_TYPES = frozenset(
    {"image/png", "image/jpeg", "image/webp", "image/gif"}
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as image_file:
        for chunk in iter(lambda: image_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class ImageAsset:
    """A local or remote image with optional integrity and display metadata."""

    source: str
    mime_type: Optional[str] = None
    sha256: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    detail: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("Image source must not be empty")
        if self.mime_type and self.mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
            supported = ", ".join(sorted(SUPPORTED_IMAGE_MIME_TYPES))
            raise ValueError(
                f"Unsupported image MIME type '{self.mime_type}'. Supported types: {supported}"
            )
        if self.sha256 and (
            len(self.sha256) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in self.sha256)
        ):
            raise ValueError("Image sha256 must be a 64-character hexadecimal digest")
        if self.detail not in {None, "auto", "low", "high"}:
            raise ValueError("Image detail must be one of: auto, low, high")

        parsed = urlparse(self.source)
        if "://" in self.source and parsed.scheme not in {"http", "https"}:
            raise ValueError("Image sources must be local paths or HTTP(S) URLs")

    @property
    def is_remote(self) -> bool:
        return urlparse(self.source).scheme in {"http", "https"}

    @property
    def path(self) -> Path:
        if self.is_remote:
            raise ValueError("Remote image assets do not have a local path")
        return Path(self.source).expanduser()

    @classmethod
    def from_path(
        cls,
        path: Union[str, Path],
        *,
        detail: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> "ImageAsset":
        """Validate and describe a local raster image without retaining image bytes."""
        from PIL import Image

        resolved = Path(path).expanduser().resolve()
        if not resolved.is_file():
            raise FileNotFoundError(f"Image file not found: {resolved}")

        with Image.open(str(resolved)) as image:
            width, height = image.size
            image_format = image.format
            image.verify()

        mime_type = Image.MIME.get(image_format or "") or mimetypes.guess_type(str(resolved))[0]
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"

        return cls(
            source=str(resolved),
            mime_type=mime_type,
            sha256=_sha256_file(resolved),
            width=width,
            height=height,
            detail=detail,
            metadata=dict(metadata or {}),
        )

    @classmethod
    def from_url(
        cls,
        url: str,
        *,
        mime_type: Optional[str] = None,
        detail: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> "ImageAsset":
        """Describe a remote image without downloading it."""
        if urlparse(url).scheme not in {"http", "https"}:
            raise ValueError("Remote image URL must use HTTP or HTTPS")
        return cls(
            source=url,
            mime_type=mime_type,
            detail=detail,
            metadata=dict(metadata or {}),
        )

    def to_data_url(self, max_bytes: int) -> str:
        """Read a local image and encode it at the provider transport boundary."""
        if self.is_remote:
            raise ValueError("Remote image assets should be sent by URL")
        if max_bytes <= 0:
            raise ValueError("Maximum image size must be greater than zero")

        path = self.path
        if not path.is_file():
            raise FileNotFoundError(f"Image file not found: {path}")
        image_bytes = path.read_bytes()
        size = len(image_bytes)
        if size > max_bytes:
            raise ValueError(
                f"Image exceeds configured size limit: {size} bytes > {max_bytes} bytes"
            )
        if self.sha256:
            current_digest = hashlib.sha256(image_bytes).hexdigest()
            if current_digest.lower() != self.sha256.lower():
                raise ValueError(f"Image integrity check failed for {path}")

        mime_type = self.mime_type or mimetypes.guess_type(str(path))[0]
        if mime_type == "image/jpg":
            mime_type = "image/jpeg"
        if mime_type not in SUPPORTED_IMAGE_MIME_TYPES:
            raise ValueError(f"Cannot transport unsupported image MIME type: {mime_type}")

        encoded = base64.b64encode(image_bytes).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def to_dict(self, relative_to: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        """Serialize metadata and a file reference, never the image bytes."""
        if self.is_remote:
            source_key = "url"
            source_value = self.source
        else:
            source_key = "path"
            path = self.path.resolve()
            source_value = str(path)
            if relative_to is not None:
                try:
                    source_value = str(path.relative_to(Path(relative_to).resolve()))
                except ValueError:
                    pass

        result: Dict[str, Any] = {
            "type": "image",
            source_key: source_value,
            "mime_type": self.mime_type,
            "sha256": self.sha256,
            "width": self.width,
            "height": self.height,
        }
        if self.detail is not None:
            result["detail"] = self.detail
        if self.metadata:
            result["metadata"] = dict(self.metadata)
        return {key: value for key, value in result.items() if value is not None}


@dataclass(frozen=True)
class TextPart:
    """Text content in a provider-neutral message."""

    text: str

    def to_dict(self) -> Dict[str, str]:
        return {"type": "text", "text": self.text}


@dataclass(frozen=True)
class ImagePart:
    """Image content in a provider-neutral message."""

    image: ImageAsset

    def to_dict(self, relative_to: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        return self.image.to_dict(relative_to=relative_to)


ContentPart = Union[TextPart, ImagePart]


@dataclass(frozen=True)
class Message:
    """A chat message containing ordered text and image parts."""

    role: str
    parts: Tuple[ContentPart, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "parts", tuple(self.parts))
        if self.role not in {"system", "user", "assistant"}:
            raise ValueError(f"Unsupported message role: {self.role}")
        if not self.parts:
            raise ValueError("A multimodal message must contain at least one part")
        if any(not isinstance(part, (TextPart, ImagePart)) for part in self.parts):
            raise TypeError("Message parts must be TextPart or ImagePart instances")

    @property
    def modalities(self) -> FrozenSet[str]:
        return frozenset(
            "image" if isinstance(part, ImagePart) else "text" for part in self.parts
        )

    def to_dict(self, relative_to: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        parts = []
        for part in self.parts:
            if isinstance(part, ImagePart):
                parts.append(part.to_dict(relative_to=relative_to))
            else:
                parts.append(part.to_dict())
        return {"role": self.role, "content": parts}


@dataclass(frozen=True)
class AttackPayload:
    """Canonical text/image attack payload independent of any model provider."""

    messages: Tuple[Message, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "messages", tuple(self.messages))
        if not self.messages:
            raise ValueError("Attack payload must contain at least one message")
        if any(not isinstance(message, Message) for message in self.messages):
            raise TypeError("Attack payload messages must be Message instances")

    @property
    def modalities(self) -> FrozenSet[str]:
        modalities = set()
        for message in self.messages:
            modalities.update(message.modalities)
        return frozenset(modalities)

    def to_dict(self, relative_to: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "type": "attack_payload",
            "version": 1,
            "modalities": sorted(self.modalities),
            "messages": [
                message.to_dict(relative_to=relative_to) for message in self.messages
            ],
        }
        if self.metadata:
            result["metadata"] = dict(self.metadata)
        return result


@dataclass(frozen=True)
class JudgedOutput:
    """Final answer produced by the attack itself, judged without another victim query.

    Use only when the paper scores an artifact other than the victim's reply to a
    single prompt (e.g. an auxiliary model synthesizes the answer from victim
    replies to fragmented probes). ``source`` names who produced ``response`` and
    is recorded with the result so ASR reports can tell the two cases apart.
    """

    response: str
    source: str
    modalities: FrozenSet[str] = frozenset({"text"})
    transcript: Any = None

    def __post_init__(self) -> None:
        if not isinstance(self.response, str) or not self.response.strip():
            raise ValueError("JudgedOutput.response must be a non-empty string")
        if not self.source:
            raise ValueError("JudgedOutput.source must name the producer of the response")
        object.__setattr__(self, "modalities", frozenset(self.modalities))

    def to_dict(self, relative_to: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
        return {
            "type": "judged_output",
            "version": 1,
            "source": self.source,
            "modalities": sorted(self.modalities),
            "transcript": serialize_attack_prompt(self.transcript, relative_to=relative_to),
        }


@dataclass(frozen=True)
class ModelCapabilities:
    """Model input/output capabilities used for fail-fast compatibility checks."""

    input_modalities: FrozenSet[str] = field(default_factory=lambda: frozenset({"text"}))
    output_modalities: FrozenSet[str] = field(default_factory=lambda: frozenset({"text"}))
    source: str = "default"

    def __post_init__(self) -> None:
        unsupported = (set(self.input_modalities) | set(self.output_modalities)) - set(
            SUPPORTED_MODALITIES
        )
        if unsupported:
            raise ValueError(
                "Only text and image modalities are supported in this release; got: "
                + ", ".join(sorted(unsupported))
            )

    def supports_input(self, modalities: Iterable[str]) -> bool:
        return set(modalities).issubset(self.input_modalities)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "input_modalities": sorted(self.input_modalities),
            "output_modalities": sorted(self.output_modalities),
            "source": self.source,
        }


def infer_prompt_modalities(prompt: Any) -> FrozenSet[str]:
    """Infer text/image modalities from canonical or LiteLLM-style prompts."""
    if isinstance(prompt, AttackPayload):
        return prompt.modalities
    if isinstance(prompt, str):
        return frozenset({"text"})
    if isinstance(prompt, (list, tuple)):
        modalities = set()
        for item in prompt:
            if isinstance(item, AttackPayload):
                modalities.update(item.modalities)
                continue
            if isinstance(item, str):
                modalities.add("text")
                continue
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if isinstance(content, str):
                modalities.add("text")
            elif isinstance(content, list):
                for part in content:
                    if not isinstance(part, dict):
                        continue
                    part_type = part.get("type")
                    if part_type in {"image", "image_url", "input_image"}:
                        modalities.add("image")
                    elif part_type in {"text", "input_text"}:
                        modalities.add("text")
        return frozenset(modalities or {"text"})
    return frozenset({"text"})


def serialize_attack_prompt(
    prompt: Any, relative_to: Optional[Union[str, Path]] = None
) -> Any:
    """Convert canonical payloads to JSON-safe manifests while preserving legacy prompts."""
    if isinstance(prompt, (AttackPayload, JudgedOutput)):
        return prompt.to_dict(relative_to=relative_to)
    if isinstance(prompt, Path):
        return str(prompt)
    if isinstance(prompt, (list, tuple)):
        return [serialize_attack_prompt(item, relative_to=relative_to) for item in prompt]
    if isinstance(prompt, dict):
        if prompt.get("type") in {"image", "image_url", "input_image"}:
            return {
                "type": prompt.get("type"),
                "image": "[provider-specific image omitted]",
            }
        return {
            key: serialize_attack_prompt(value, relative_to=relative_to)
            for key, value in prompt.items()
        }
    if isinstance(prompt, str) and prompt.startswith("data:image/"):
        return "[inline image data omitted]"
    return prompt
