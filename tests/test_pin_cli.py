"""Tests for envoy_local.pin_cli."""
from __future__ import annotations

import argparse
import pytest
from pathlib import Path

from envoy_local.pin import pin_key, list_pins
from envoy_local.pin_cli import cmd_pin_set, cmd_pin_remove, cmd_pin_list


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"dir": None, "key": "", "value": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_pin_set_returns_0(base_dir: Path) -> None:
    ns = _ns(dir=str(base_dir), key="DB_PORT", value="5432")
    assert cmd_pin_set(ns) == 0


def test_cmd_pin_set_persists(base_dir: Path) -> None:
    ns = _ns(dir=str(base_dir), key="APP_ENV", value="production")
    cmd_pin_set(ns)
    assert list_pins(base_dir)["APP_ENV"] == "production"


def test_cmd_pin_remove_returns_0_when_pinned(base_dir: Path) -> None:
    pin_key(base_dir, "TO_REMOVE", "val")
    ns = _ns(dir=str(base_dir), key="TO_REMOVE")
    assert cmd_pin_remove(ns) == 0


def test_cmd_pin_remove_returns_1_when_not_pinned(base_dir: Path) -> None:
    ns = _ns(dir=str(base_dir), key="GHOST")
    assert cmd_pin_remove(ns) == 1


def test_cmd_pin_list_returns_0_with_pins(base_dir: Path, capsys: pytest.CaptureFixture) -> None:
    pin_key(base_dir, "K", "V")
    ns = _ns(dir=str(base_dir))
    code = cmd_pin_list(ns)
    assert code == 0
    out = capsys.readouterr().out
    assert "K=V" in out


def test_cmd_pin_list_returns_0_when_empty(base_dir: Path, capsys: pytest.CaptureFixture) -> None:
    ns = _ns(dir=str(base_dir))
    code = cmd_pin_list(ns)
    assert code == 0
    out = capsys.readouterr().out
    assert "No pins" in out


def test_cmd_pin_remove_deletes_key(base_dir: Path) -> None:
    pin_key(base_dir, "GONE", "bye")
    cmd_pin_remove(_ns(dir=str(base_dir), key="GONE"))
    assert "GONE" not in list_pins(base_dir)
