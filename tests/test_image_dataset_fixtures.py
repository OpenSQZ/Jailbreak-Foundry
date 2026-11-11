"""Loader tests against the committed image fixtures under assets/multimodal.

tests/test_multimodal_support.py builds its manifests at runtime, so nothing
exercised the loader against real on-disk assets. These tests lock the five
media field names and the three manifest formats the loader claims to support.
"""

from pathlib import Path

import pytest

from jbfoundry.dataset.local_loader import LocalFileLoader
from jbfoundry.payloads import ImageAsset

FIXTURE_DIR = Path(__file__).resolve().parents[1] / "assets" / "multimodal"


@pytest.mark.parametrize(
    "manifest_name",
    ["field_name_coverage.jsonl", "records.json", "records.csv"],
)
def test_every_manifest_format_declares_image_modality(manifest_name):
    dataset = LocalFileLoader().load(str(FIXTURE_DIR / manifest_name))

    assert dataset.modalities == frozenset({"text", "image"})
    assert len(dataset) > 0
    for index in range(len(dataset)):
        record = dataset[index]
        assert record["goal"]
        assert record["media"]
        assert all(isinstance(asset, ImageAsset) for asset in record["media"])


def test_all_five_media_field_names_resolve_to_assets():
    dataset = LocalFileLoader().load(str(FIXTURE_DIR / "field_name_coverage.jsonl"))

    by_case = {dataset[i]["metadata"]["case_id"]: dataset[i] for i in range(len(dataset))}
    assert set(by_case) == {
        "field-image",
        "field-image-path",
        "field-images",
        "field-image-paths",
        "field-media",
    }

    assert len(by_case["field-image"]["media"]) == 1
    assert len(by_case["field-image-path"]["media"]) == 1
    assert len(by_case["field-images"]["media"]) == 2
    assert len(by_case["field-image-paths"]["media"]) == 3

    media_asset = by_case["field-media"]["media"][0]
    assert media_asset.detail == "low"
    assert media_asset.metadata["panel"] == "c"


def test_relative_paths_resolve_against_the_manifest_directory():
    dataset = LocalFileLoader().load(str(FIXTURE_DIR / "records.json"))
    asset = dataset[0]["media"][0]

    assert asset.path.is_absolute()
    assert asset.path.exists()
    assert asset.mime_type == "image/png"
    assert asset.width == 48 and asset.height == 48
    assert asset.sha256 and len(asset.sha256) == 64


def test_csv_media_column_accepts_both_scalar_and_json_list():
    dataset = LocalFileLoader().load(str(FIXTURE_DIR / "records.csv"))

    assert len(dataset[0]["media"]) == 1
    assert len(dataset[1]["media"]) == 2
