"""Local JSON, JSONL, and CSV dataset loader with image references."""

import json
import logging
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union

import pandas as pd

from ..payloads import ImageAsset
from .base import JailbreakDataset, JailbreakDatasetLoader, MultimodalJailbreakDataset

logger = logging.getLogger(__name__)


FIELD_MAPPING = {
    "behavior": [
        "behavior",
        "behaviors",
        "behaviours",
        "behaviour",
        "prompt",
        "prompts",
        "query",
        "queries",
    ],
    "goal": ["goal", "goals", "prompt", "prompts", "query", "queries"],
    "target": ["target", "targets", "response", "responses"],
    "category": ["category", "categories", "type", "types"],
}
MEDIA_FIELDS = ("media", "images", "image", "image_path", "image_paths")
COLUMNAR_FIELDS = frozenset({"behaviors", "goals", "targets", "categories"})


class LocalFileLoader(JailbreakDatasetLoader):
    """Load text or text/image datasets from local manifest files."""

    name = "local_file"
    description = "Local file loader for JSON, JSONL, and CSV formats"

    def load(
        self, dataset_name: str, **kwargs
    ) -> Union[JailbreakDataset, MultimodalJailbreakDataset]:
        path = Path(dataset_name).expanduser()
        if not path.exists():
            raise FileNotFoundError(f"Dataset file not found: {path}")

        suffix = path.suffix.lower()
        if suffix == ".json":
            records = self._read_json_records(path)
        elif suffix == ".jsonl":
            records = self._read_jsonl_records(path)
        elif suffix == ".csv":
            records = self._read_csv_records(path)
        else:
            raise ValueError(f"Unsupported file format for dataset: {path}")

        return self._records_to_dataset(records, path, suffix)

    def _read_json_records(self, path: Path) -> List[Dict[str, Any]]:
        with path.open("r") as dataset_file:
            data = json.load(dataset_file)

        if isinstance(data, list):
            if not all(isinstance(record, dict) for record in data):
                raise ValueError(f"JSON dataset entries must be objects: {path}")
            return data

        if not isinstance(data, dict):
            raise ValueError(f"Unsupported JSON format in dataset: {path}")
        if isinstance(data.get("data"), list):
            records = data["data"]
            if not all(isinstance(record, dict) for record in records):
                raise ValueError(f"JSON dataset entries must be objects: {path}")
            return records

        is_columnar = any(
            str(key).lower() in COLUMNAR_FIELDS and isinstance(value, list)
            for key, value in data.items()
        )
        if is_columnar:
            list_fields = {key: value for key, value in data.items() if isinstance(value, list)}
            record_count = max(len(value) for value in list_fields.values())
            records = []
            for index in range(record_count):
                record = {}
                for key, value in data.items():
                    if isinstance(value, list):
                        record[key] = value[index] if index < len(value) else None
                    else:
                        record[key] = value
                records.append(record)
            return records

        return [data]

    def _read_jsonl_records(self, path: Path) -> List[Dict[str, Any]]:
        records = []
        with path.open("r") as dataset_file:
            for line_number, line in enumerate(dataset_file, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    logger.warning("Skipping invalid JSON on line %s: %s", line_number, exc)
                    continue
                if not isinstance(record, dict):
                    logger.warning("Skipping non-object JSON on line %s", line_number)
                    continue
                records.append(record)
        return records

    def _read_csv_records(self, path: Path) -> List[Dict[str, Any]]:
        dataframe = pd.read_csv(path)
        dataframe = dataframe.where(pd.notna(dataframe), None)
        return dataframe.to_dict(orient="records")

    def _records_to_dataset(
        self,
        records: Iterable[Dict[str, Any]],
        manifest_path: Path,
        format_name: str,
    ) -> Union[JailbreakDataset, MultimodalJailbreakDataset]:
        behaviors: List[str] = []
        goals: List[str] = []
        targets: List[str] = []
        categories: List[str] = []
        media: List[List[ImageAsset]] = []
        metadata: List[Dict[str, Any]] = []
        has_media_field = False

        default_category = manifest_path.stem or "jailbreak"
        for record in records:
            behavior = self._text_value(
                self._first_value(record, FIELD_MAPPING["behavior"])
            )
            goal = self._text_value(self._first_value(record, FIELD_MAPPING["goal"]))
            target = self._text_value(self._first_value(record, FIELD_MAPPING["target"]))
            category = self._text_value(
                self._first_value(record, FIELD_MAPPING["category"])
            )
            if format_name == ".jsonl":
                goal = goal or behavior
                category = category or default_category

            media_value = None
            for field_name in MEDIA_FIELDS:
                if field_name in record:
                    has_media_field = True
                    media_value = record[field_name]
                    break

            record_metadata = record.get("metadata")
            if not isinstance(record_metadata, dict):
                record_metadata = {}

            behaviors.append(behavior)
            goals.append(goal)
            targets.append(target)
            categories.append(category)
            media.append(self._parse_media(media_value, manifest_path.parent))
            metadata.append(record_metadata)

        common = {
            "behaviors": behaviors,
            "goals": goals,
            "targets": targets,
            "categories": categories,
        }
        if has_media_field:
            return MultimodalJailbreakDataset(media=media, metadata=metadata, **common)
        return JailbreakDataset(**common)

    @staticmethod
    def _first_value(record: Dict[str, Any], names: Iterable[str]) -> Any:
        lowered = {str(key).lower(): key for key in record}
        for name in names:
            original_key = lowered.get(name.lower())
            if original_key is not None:
                return record[original_key]
        return None

    @staticmethod
    def _text_value(value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, float) and math.isnan(value):
            return ""
        return str(value)

    def _parse_media(self, value: Any, base_dir: Path) -> List[ImageAsset]:
        if value is None or (isinstance(value, float) and math.isnan(value)):
            return []
        if isinstance(value, ImageAsset):
            return [value]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("[") or stripped.startswith("{"):
                try:
                    return self._parse_media(json.loads(stripped), base_dir)
                except json.JSONDecodeError:
                    pass
            return [self._asset_from_source(stripped, base_dir)]
        if isinstance(value, list):
            assets = []
            for item in value:
                assets.extend(self._parse_media(item, base_dir))
            return assets
        if isinstance(value, dict):
            source = value.get("source") or value.get("path") or value.get("url")
            if not source:
                raise ValueError(f"Image object is missing source/path/url: {value}")
            detail = value.get("detail")
            asset_metadata = value.get("metadata")
            if not isinstance(asset_metadata, dict):
                asset_metadata = {}
            source_text = str(source)
            if source_text.startswith(("http://", "https://")):
                return [
                    ImageAsset.from_url(
                        source_text,
                        mime_type=value.get("mime_type"),
                        detail=detail,
                        metadata=asset_metadata,
                    )
                ]
            local_path = Path(source_text).expanduser()
            if not local_path.is_absolute():
                local_path = base_dir / local_path
            return [
                ImageAsset.from_path(local_path, detail=detail, metadata=asset_metadata)
            ]
        raise TypeError(f"Unsupported image manifest value: {value!r}")

    @staticmethod
    def _asset_from_source(source: str, base_dir: Path) -> ImageAsset:
        if source.startswith(("http://", "https://")):
            return ImageAsset.from_url(source)
        path = Path(source).expanduser()
        if not path.is_absolute():
            path = base_dir / path
        return ImageAsset.from_path(path)


def register_local_presets():
    """Register local file presets (empty for now, but allows extension)."""
    return {}
