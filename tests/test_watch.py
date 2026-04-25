"""Tests for envoy_local.watch."""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from envoy_local.watch import EnvWatcher, WatchResult, _file_hash


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("KEY=value\n")
    return f


def test_file_hash_returns_string_for_existing_file(env_file: Path) -> None:
    h = _file_hash(env_file)
    assert isinstance(h, str) and len(h) == 32


def test_file_hash_returns_none_for_missing_file(tmp_path: Path) -> None:
    assert _file_hash(tmp_path / "missing.env") is None


def test_no_changes_on_first_check(env_file: Path) -> None:
    watcher = EnvWatcher([env_file])
    results = watcher.check()
    assert results == []


def test_detects_content_change(env_file: Path) -> None:
    watcher = EnvWatcher([env_file])
    # Force mtime change by touching with a new mtime
    env_file.write_text("KEY=changed\n")
    # Manually clear cached mtime so check() re-hashes
    watcher._states[env_file].last_mtime = 0.0
    results = watcher.check()
    assert len(results) == 1
    r = results[0]
    assert r.path == env_file
    assert r.changed is True
    assert r.previous_hash != r.current_hash


def test_no_change_when_content_identical(env_file: Path) -> None:
    watcher = EnvWatcher([env_file])
    original_hash = watcher._states[env_file].last_hash
    # Rewrite same content — hash stays the same
    env_file.write_text("KEY=value\n")
    watcher._states[env_file].last_mtime = 0.0
    results = watcher.check()
    assert results == []


def test_detects_file_appearance(tmp_path: Path) -> None:
    new_file = tmp_path / ".env.new"
    watcher = EnvWatcher([new_file])  # file doesn't exist yet
    assert watcher._states[new_file].last_hash is None
    new_file.write_text("APPEARED=1\n")
    watcher._states[new_file].last_mtime = 0.0
    results = watcher.check()
    assert len(results) == 1
    assert results[0].appeared is True
    assert results[0].disappeared is False


def test_detects_file_disappearance(env_file: Path) -> None:
    watcher = EnvWatcher([env_file])
    env_file.unlink()
    watcher._states[env_file].last_mtime = 0.0
    results = watcher.check()
    assert len(results) == 1
    assert results[0].disappeared is True
    assert results[0].appeared is False


def test_watch_calls_callback(env_file: Path) -> None:
    watcher = EnvWatcher([env_file], poll_interval=0.0)
    collected: list[WatchResult] = []

    def _modify_and_stop(result: WatchResult) -> None:
        collected.append(result)

    # Prime a change before starting
    env_file.write_text("KEY=new\n")
    watcher._states[env_file].last_mtime = 0.0

    watcher.watch(callback=_modify_and_stop, max_iterations=1)
    assert len(collected) == 1
    assert collected[0].changed is True
