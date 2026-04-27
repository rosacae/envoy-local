"""Tests for envoy_local.pin."""
from __future__ import annotations

import pytest
from pathlib import Path

from envoy_local.pin import (
    pin_key,
    unpin_key,
    list_pins,
    load_pins,
    apply_pins,
    PinManifest,
    PIN_FILE_NAME,
)
from envoy_local.parser import EnvEntry


@pytest.fixture
def pin_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_pins_returns_empty_when_no_file(pin_dir: Path) -> None:
    manifest = load_pins(pin_dir)
    assert manifest.pins == {}


def test_pin_key_creates_file(pin_dir: Path) -> None:
    pin_key(pin_dir, "DB_HOST", "localhost")
    assert (pin_dir / PIN_FILE_NAME).exists()


def test_pin_key_roundtrip(pin_dir: Path) -> None:
    pin_key(pin_dir, "API_KEY", "secret123")
    pins = list_pins(pin_dir)
    assert pins["API_KEY"] == "secret123"


def test_pin_multiple_keys(pin_dir: Path) -> None:
    pin_key(pin_dir, "KEY_A", "alpha")
    pin_key(pin_dir, "KEY_B", "beta")
    pins = list_pins(pin_dir)
    assert pins["KEY_A"] == "alpha"
    assert pins["KEY_B"] == "beta"


def test_pin_overwrite_existing(pin_dir: Path) -> None:
    pin_key(pin_dir, "HOST", "old")
    pin_key(pin_dir, "HOST", "new")
    assert list_pins(pin_dir)["HOST"] == "new"


def test_unpin_key_returns_true_when_exists(pin_dir: Path) -> None:
    pin_key(pin_dir, "REMOVE_ME", "val")
    result = unpin_key(pin_dir, "REMOVE_ME")
    assert result is True
    assert "REMOVE_ME" not in list_pins(pin_dir)


def test_unpin_key_returns_false_when_missing(pin_dir: Path) -> None:
    result = unpin_key(pin_dir, "GHOST")
    assert result is False


def test_apply_pins_overrides_matching_entry(pin_dir: Path) -> None:
    pin_key(pin_dir, "DB_HOST", "pinned-host")
    manifest = load_pins(pin_dir)
    entries = [
        EnvEntry(key="DB_HOST", value="original", comment=None, raw="DB_HOST=original"),
        EnvEntry(key="OTHER", value="unchanged", comment=None, raw="OTHER=unchanged"),
    ]
    result = apply_pins(entries, manifest)
    assert result[0].value == "pinned-host"
    assert result[1].value == "unchanged"


def test_apply_pins_leaves_unmatched_entries_intact(pin_dir: Path) -> None:
    manifest = PinManifest(pins={"X": "1"})
    entries = [
        EnvEntry(key="Y", value="2", comment=None, raw="Y=2"),
    ]
    result = apply_pins(entries, manifest)
    assert result[0].value == "2"


def test_to_dict_from_dict_roundtrip() -> None:
    m = PinManifest(pins={"A": "1", "B": "2"})
    assert PinManifest.from_dict(m.to_dict()).pins == m.pins
