"""Tests for envoy_local.trim."""
from pathlib import Path

import pytest

from envoy_local.trim import trim_keys
from envoy_local.parser import parse_env_file


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "APP_NAME=myapp\n"
        "APP_SECRET=hunter2\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "# a comment\n"
        "DEBUG=true\n"
    )
    return p


def _keys(path: Path):
    return [e.key for e in parse_env_file(path).entries if e.key is not None]


def test_trim_removes_explicit_key(env_file: Path):
    result = trim_keys(env_file, keys=["APP_SECRET"])
    assert result.ok
    assert "APP_SECRET" in result.trimmed
    assert "APP_SECRET" not in _keys(env_file)


def test_trim_preserves_other_keys(env_file: Path):
    trim_keys(env_file, keys=["APP_SECRET"])
    remaining = _keys(env_file)
    assert "APP_NAME" in remaining
    assert "DB_HOST" in remaining


def test_trim_multiple_explicit_keys(env_file: Path):
    result = trim_keys(env_file, keys=["DB_HOST", "DB_PORT"])
    assert result.ok
    assert set(result.trimmed) == {"DB_HOST", "DB_PORT"}
    assert "DB_HOST" not in _keys(env_file)
    assert "DB_PORT" not in _keys(env_file)


def test_trim_by_pattern(env_file: Path):
    result = trim_keys(env_file, pattern=r"^DB_")
    assert result.ok
    assert "DB_HOST" in result.trimmed
    assert "DB_PORT" in result.trimmed
    remaining = _keys(env_file)
    assert "DB_HOST" not in remaining
    assert "DB_PORT" not in remaining
    assert "APP_NAME" in remaining


def test_trim_pattern_and_keys_union(env_file: Path):
    result = trim_keys(env_file, keys=["DEBUG"], pattern=r"^APP_")
    assert result.ok
    assert "DEBUG" in result.trimmed
    assert "APP_NAME" in result.trimmed
    assert "APP_SECRET" in result.trimmed


def test_trim_missing_key_not_in_trimmed(env_file: Path):
    result = trim_keys(env_file, keys=["NONEXISTENT"])
    assert result.ok
    assert result.trimmed == []


def test_trim_dry_run_does_not_modify_file(env_file: Path):
    original = env_file.read_text()
    result = trim_keys(env_file, keys=["APP_NAME"], dry_run=True)
    assert result.ok
    assert "APP_NAME" in result.trimmed
    assert env_file.read_text() == original


def test_trim_missing_file_returns_error(tmp_path: Path):
    result = trim_keys(tmp_path / "missing.env", keys=["X"])
    assert not result.ok
    assert "not found" in result.error


def test_trim_no_keys_or_pattern_returns_error(env_file: Path):
    result = trim_keys(env_file)
    assert not result.ok
    assert "pattern" in result.error


def test_trim_invalid_pattern_returns_error(env_file: Path):
    result = trim_keys(env_file, pattern="[invalid")
    assert not result.ok
    assert "invalid pattern" in result.error


def test_trim_kept_count_is_accurate(env_file: Path):
    result = trim_keys(env_file, pattern=r"^DB_")
    assert result.kept == 3  # APP_NAME, APP_SECRET, DEBUG
