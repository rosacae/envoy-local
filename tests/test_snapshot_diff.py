"""Tests for snapshot_diff module."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy_local.snapshot import create_snapshot
from envoy_local.snapshot_diff import diff_against_snapshot


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    d = tmp_path / "snaps"
    d.mkdir()
    return d


def test_diff_against_latest_snapshot_no_changes(env_file, snap_dir):
    create_snapshot(env_file, snap_dir=snap_dir)
    result, snap = diff_against_snapshot(env_file, snap_dir=snap_dir)
    assert result.added == []
    assert result.removed == []
    assert result.changed == []


def test_diff_detects_added_key(env_file, snap_dir):
    create_snapshot(env_file, snap_dir=snap_dir)
    # Add a new key after snapshot
    env_file.write_text("FOO=bar\nBAZ=qux\nNEW=value\n")
    result, _ = diff_against_snapshot(env_file, snap_dir=snap_dir)
    assert any(e.key == "NEW" for e in result.added)


def test_diff_detects_removed_key(env_file, snap_dir):
    create_snapshot(env_file, snap_dir=snap_dir)
    env_file.write_text("FOO=bar\n")
    result, _ = diff_against_snapshot(env_file, snap_dir=snap_dir)
    assert any(e.key == "BAZ" for e in result.removed)


def test_diff_detects_changed_value(env_file, snap_dir):
    create_snapshot(env_file, snap_dir=snap_dir)
    env_file.write_text("FOO=changed\nBAZ=qux\n")
    result, _ = diff_against_snapshot(env_file, snap_dir=snap_dir)
    assert any(e.key == "FOO" for e in result.changed)


def test_raises_when_env_file_missing(tmp_path, snap_dir):
    with pytest.raises(FileNotFoundError, match="Env file not found"):
        diff_against_snapshot(tmp_path / "missing.env", snap_dir=snap_dir)


def test_raises_when_no_snapshots_exist(env_file, snap_dir):
    with pytest.raises(ValueError, match="No snapshots found"):
        diff_against_snapshot(env_file, snap_dir=snap_dir)


def test_raises_when_snapshot_id_not_found(env_file, snap_dir):
    with pytest.raises(FileNotFoundError, match="Snapshot not found"):
        diff_against_snapshot(env_file, snapshot_id="nonexistent-id", snap_dir=snap_dir)


def test_uses_specific_snapshot_id(env_file, snap_dir):
    snap = create_snapshot(env_file, snap_dir=snap_dir)
    env_file.write_text("FOO=bar\nBAZ=qux\nEXTRA=1\n")
    result, used_snap = diff_against_snapshot(
        env_file, snapshot_id=snap.snapshot_id, snap_dir=snap_dir
    )
    assert used_snap.snapshot_id == snap.snapshot_id
    assert any(e.key == "EXTRA" for e in result.added)
