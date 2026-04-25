"""Tests for snapshot CLI commands."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy_local.snapshot_cli import (
    cmd_snapshot_create,
    cmd_snapshot_list,
    cmd_snapshot_show,
)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("API_KEY=abc123\nDEBUG=true\n")
    return p


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    d = tmp_path / "snaps"
    d.mkdir()
    return d


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"snap_dir": None, "label": None, "verbose": False, "snapshot_id": None}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_snapshot_create_returns_0(env_file, snap_dir):
    ns = _ns(env_file=str(env_file), snap_dir=str(snap_dir))
    assert cmd_snapshot_create(ns) == 0


def test_cmd_snapshot_create_missing_file(tmp_path, snap_dir):
    ns = _ns(env_file=str(tmp_path / "missing.env"), snap_dir=str(snap_dir))
    assert cmd_snapshot_create(ns) == 2


def test_cmd_snapshot_create_verbose_prints_json(env_file, snap_dir, capsys):
    ns = _ns(env_file=str(env_file), snap_dir=str(snap_dir), verbose=True)
    rc = cmd_snapshot_create(ns)
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out.split("\n", 1)[1])
    assert "snapshot_id" in data
    assert "entries" in data


def test_cmd_snapshot_list_empty(env_file, snap_dir, capsys):
    ns = _ns(env_file=str(env_file), snap_dir=str(snap_dir))
    rc = cmd_snapshot_list(ns)
    assert rc == 0
    assert "no snapshots" in capsys.readouterr().out


def test_cmd_snapshot_list_shows_created(env_file, snap_dir, capsys):
    create_ns = _ns(env_file=str(env_file), snap_dir=str(snap_dir), label="v1")
    cmd_snapshot_create(create_ns)

    list_ns = _ns(env_file=str(env_file), snap_dir=str(snap_dir))
    rc = cmd_snapshot_list(list_ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[v1]" in out


def test_cmd_snapshot_show_missing_id(env_file, snap_dir):
    ns = _ns(env_file=str(env_file), snap_dir=str(snap_dir), snapshot_id="nonexistent")
    assert cmd_snapshot_show(ns) == 2


def test_cmd_snapshot_show_valid(env_file, snap_dir, capsys):
    from envoy_local.snapshot import create_snapshot

    snap = create_snapshot(env_file, snap_dir=snap_dir)
    ns = _ns(env_file=str(env_file), snap_dir=str(snap_dir), snapshot_id=snap.snapshot_id)
    rc = cmd_snapshot_show(ns)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert data["snapshot_id"] == snap.snapshot_id
