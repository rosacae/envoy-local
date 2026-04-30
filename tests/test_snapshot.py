"""Tests for envoy_local.snapshot."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_local.snapshot import (
    create_snapshot,
    list_snapshots,
    load_snapshot,
    restore_snapshot,
)


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nSECRET_KEY=supersecret\n", encoding="utf-8")
    return p


@pytest.fixture()
def snap_dir(tmp_path: Path) -> Path:
    return tmp_path / "snapshots"


def test_create_snapshot_returns_snapshot_object(env_file, snap_dir):
    snap = create_snapshot(env_file, label="v1", snapshot_dir=snap_dir)
    assert snap.label == "v1"
    assert snap.entries["DB_HOST"] == "localhost"
    assert snap.entries["DB_PORT"] == "5432"
    assert snap.entries["SECRET_KEY"] == "supersecret"


def test_create_snapshot_persists_json_file(env_file, snap_dir):
    create_snapshot(env_file, label="v1", snapshot_dir=snap_dir)
    snap_file = snap_dir / "v1.json"
    assert snap_file.exists()
    data = json.loads(snap_file.read_text())
    assert data["label"] == "v1"
    assert "created_at" in data


def test_load_snapshot_roundtrip(env_file, snap_dir):
    create_snapshot(env_file, label="release-1", snapshot_dir=snap_dir)
    snap = load_snapshot("release-1", snapshot_dir=snap_dir)
    assert snap.label == "release-1"
    assert snap.entries["DB_HOST"] == "localhost"


def test_load_snapshot_missing_raises(snap_dir):
    with pytest.raises(FileNotFoundError, match="Snapshot 'ghost'"):
        load_snapshot("ghost", snapshot_dir=snap_dir)


def test_list_snapshots_empty_when_dir_missing(snap_dir):
    assert list_snapshots(snap_dir) == []


def test_list_snapshots_returns_sorted_labels(env_file, snap_dir):
    create_snapshot(env_file, label="beta", snapshot_dir=snap_dir)
    create_snapshot(env_file, label="alpha", snapshot_dir=snap_dir)
    create_snapshot(env_file, label="gamma", snapshot_dir=snap_dir)
    assert list_snapshots(snap_dir) == ["alpha", "beta", "gamma"]


def test_restore_snapshot_writes_original_path(env_file, snap_dir):
    create_snapshot(env_file, label="snap1", snapshot_dir=snap_dir)
    # Overwrite env file to simulate drift
    env_file.write_text("DB_HOST=changed\n", encoding="utf-8")
    restored_path = restore_snapshot("snap1", snapshot_dir=snap_dir)
    content = restored_path.read_text(encoding="utf-8")
    assert "DB_HOST=localhost" in content
    assert "SECRET_KEY=supersecret" in content


def test_restore_snapshot_to_custom_target(env_file, snap_dir, tmp_path):
    create_snapshot(env_file, label="snap2", snapshot_dir=snap_dir)
    target = tmp_path / "restored.env"
    restore_snapshot("snap2", target_path=target, snapshot_dir=snap_dir)
    assert target.exists()
    content = target.read_text(encoding="utf-8")
    assert "DB_PORT=5432" in content


def test_create_snapshot_uses_timestamp_label_when_none(env_file, snap_dir):
    snap = create_snapshot(env_file, snapshot_dir=snap_dir)
    assert snap.label is not None
    assert len(snap.label) > 0
    # The auto-generated label should correspond to a persisted file
    snap_file = snap_dir / f"{snap.label}.json"
    assert snap_file.exists()


def test_create_snapshot_stores_source_path(env_file, snap_dir):
    """Snapshot JSON should record the source env file path for later restore."""
    create_snapshot(env_file, label="with-source", snapshot_dir=snap_dir)
    snap_file = snap_dir / "with-source.json"
    data = json.loads(snap_file.read_text())
    assert "source_path" in data
    assert data["source_path"] == str(env_file)
