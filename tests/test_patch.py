"""Tests for envoy_local.patch."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy_local.patch import PatchOptions, patch_env_file
from envoy_local.parser import parse_env_file


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nBAZ=qux\n")
    return f


def _keys(path: Path) -> dict[str, str]:
    result = parse_env_file(path)
    return {e.key: e.value for e in result.entries if e.key}


def test_patch_adds_new_key(env_file: Path) -> None:
    opts = PatchOptions(upsert={"NEW_KEY": "hello"})
    result = patch_env_file(env_file, opts)
    assert result.ok
    assert "NEW_KEY" in result.added
    assert _keys(env_file)["NEW_KEY"] == "hello"


def test_patch_updates_existing_key(env_file: Path) -> None:
    opts = PatchOptions(upsert={"FOO": "newval"})
    result = patch_env_file(env_file, opts)
    assert result.ok
    assert "FOO" in result.updated
    assert _keys(env_file)["FOO"] == "newval"


def test_patch_skips_existing_when_no_overwrite(env_file: Path) -> None:
    opts = PatchOptions(upsert={"FOO": "changed"}, overwrite_existing=False)
    result = patch_env_file(env_file, opts)
    assert result.ok
    assert "FOO" in result.skipped
    assert _keys(env_file)["FOO"] == "bar"


def test_patch_deletes_key(env_file: Path) -> None:
    opts = PatchOptions(delete=["BAZ"])
    result = patch_env_file(env_file, opts)
    assert result.ok
    assert "BAZ" in result.deleted
    assert "BAZ" not in _keys(env_file)


def test_patch_delete_missing_key_is_noop(env_file: Path) -> None:
    opts = PatchOptions(delete=["DOES_NOT_EXIST"])
    result = patch_env_file(env_file, opts)
    assert result.ok
    assert result.deleted == []


def test_patch_frozen_key_blocked(env_file: Path) -> None:
    opts = PatchOptions(upsert={"FOO": "blocked"}, overwrite_existing=True)
    result = patch_env_file(env_file, opts, frozen_keys=["FOO"])
    assert result.ok
    assert "FOO" in result.frozen_blocked
    assert _keys(env_file)["FOO"] == "bar"


def test_patch_frozen_delete_blocked(env_file: Path) -> None:
    opts = PatchOptions(delete=["BAZ"])
    result = patch_env_file(env_file, opts, frozen_keys=["BAZ"])
    assert result.ok
    assert "BAZ" in result.frozen_blocked
    assert "BAZ" in _keys(env_file)


def test_patch_missing_file_returns_error(tmp_path: Path) -> None:
    opts = PatchOptions(upsert={"X": "1"})
    result = patch_env_file(tmp_path / "nonexistent.env", opts)
    assert not result.ok
    assert result.error is not None


def test_patch_summary_no_changes(env_file: Path) -> None:
    opts = PatchOptions()
    result = patch_env_file(env_file, opts)
    assert result.summary() == "no changes"


def test_patch_summary_includes_counts(env_file: Path) -> None:
    opts = PatchOptions(upsert={"FOO": "x", "NEWK": "y"}, delete=["BAZ"])
    result = patch_env_file(env_file, opts)
    summary = result.summary()
    assert "added=1" in summary
    assert "updated=1" in summary
    assert "deleted=1" in summary
