"""Tests for envoy_local.freeze module."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_local.freeze import (
    FreezeManifest,
    freeze_key,
    frozen_keys,
    is_frozen,
    load_frozen,
    unfreeze_key,
)


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_frozen_returns_empty_when_no_file(base_dir: Path) -> None:
    manifest = load_frozen(base_dir)
    assert manifest.frozen == []


def test_freeze_key_creates_manifest_file(base_dir: Path) -> None:
    freeze_key("SECRET_KEY", base_dir)
    assert (base_dir / ".envoy_frozen.json").exists()


def test_freeze_key_returns_true_when_newly_frozen(base_dir: Path) -> None:
    assert freeze_key("API_KEY", base_dir) is True


def test_freeze_key_returns_false_when_already_frozen(base_dir: Path) -> None:
    freeze_key("API_KEY", base_dir)
    assert freeze_key("API_KEY", base_dir) is False


def test_is_frozen_true_after_freeze(base_dir: Path) -> None:
    freeze_key("DB_PASS", base_dir)
    assert is_frozen("DB_PASS", base_dir) is True


def test_is_frozen_false_for_unknown_key(base_dir: Path) -> None:
    assert is_frozen("UNKNOWN", base_dir) is False


def test_unfreeze_key_returns_true_when_removed(base_dir: Path) -> None:
    freeze_key("TOKEN", base_dir)
    assert unfreeze_key("TOKEN", base_dir) is True


def test_unfreeze_key_returns_false_when_not_present(base_dir: Path) -> None:
    assert unfreeze_key("NOPE", base_dir) is False


def test_unfreeze_removes_key(base_dir: Path) -> None:
    freeze_key("TOKEN", base_dir)
    unfreeze_key("TOKEN", base_dir)
    assert is_frozen("TOKEN", base_dir) is False


def test_frozen_keys_returns_sorted_list(base_dir: Path) -> None:
    freeze_key("Z_KEY", base_dir)
    freeze_key("A_KEY", base_dir)
    assert frozen_keys(base_dir) == ["A_KEY", "Z_KEY"]


def test_manifest_persisted_as_valid_json(base_dir: Path) -> None:
    freeze_key("MY_KEY", base_dir)
    raw = json.loads((base_dir / ".envoy_frozen.json").read_text())
    assert "frozen" in raw
    assert "MY_KEY" in raw["frozen"]


def test_freeze_manifest_roundtrip() -> None:
    m = FreezeManifest(frozen=["A", "B"])
    assert FreezeManifest.from_dict(m.to_dict()).frozen == ["A", "B"]
