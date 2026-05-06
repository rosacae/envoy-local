"""Tests for envoy_local.freeze_cli module."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.freeze import freeze_key, frozen_keys
from envoy_local.freeze_cli import cmd_freeze_add, cmd_freeze_list, cmd_freeze_remove


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"dir": None, "key": ""}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_freeze_add_returns_0(base_dir: Path) -> None:
    ns = _ns(dir=str(base_dir), key="API_KEY")
    assert cmd_freeze_add(ns) == 0


def test_cmd_freeze_add_persists(base_dir: Path) -> None:
    ns = _ns(dir=str(base_dir), key="DB_PASS")
    cmd_freeze_add(ns)
    assert "DB_PASS" in frozen_keys(base_dir)


def test_cmd_freeze_add_duplicate_still_returns_0(base_dir: Path) -> None:
    ns = _ns(dir=str(base_dir), key="X")
    cmd_freeze_add(ns)
    assert cmd_freeze_add(ns) == 0


def test_cmd_freeze_remove_returns_0_when_frozen(base_dir: Path) -> None:
    freeze_key("TOKEN", base_dir)
    ns = _ns(dir=str(base_dir), key="TOKEN")
    assert cmd_freeze_remove(ns) == 0


def test_cmd_freeze_remove_returns_1_when_not_frozen(base_dir: Path) -> None:
    ns = _ns(dir=str(base_dir), key="GHOST")
    assert cmd_freeze_remove(ns) == 1


def test_cmd_freeze_remove_clears_key(base_dir: Path) -> None:
    freeze_key("SECRET", base_dir)
    ns = _ns(dir=str(base_dir), key="SECRET")
    cmd_freeze_remove(ns)
    assert "SECRET" not in frozen_keys(base_dir)


def test_cmd_freeze_list_returns_0_empty(base_dir: Path) -> None:
    ns = _ns(dir=str(base_dir))
    assert cmd_freeze_list(ns) == 0


def test_cmd_freeze_list_returns_0_with_keys(base_dir: Path, capsys) -> None:
    freeze_key("ALPHA", base_dir)
    freeze_key("BETA", base_dir)
    ns = _ns(dir=str(base_dir))
    rc = cmd_freeze_list(ns)
    out = capsys.readouterr().out
    assert rc == 0
    assert "ALPHA" in out
    assert "BETA" in out
