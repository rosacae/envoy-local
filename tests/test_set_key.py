"""Tests for envoy_local.set_key."""
from pathlib import Path

import pytest

from envoy_local.parser import parse_env_file
from envoy_local.set_key import set_key


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


# ---------------------------------------------------------------------------
# Basic mutation
# ---------------------------------------------------------------------------

def test_set_key_updates_existing(env_file: Path) -> None:
    result = set_key(env_file, "FOO", "new_value")
    assert result.ok
    assert not result.created
    assert result.previous_value == "bar"
    assert result.new_value == "new_value"


def test_set_key_value_persisted(env_file: Path) -> None:
    set_key(env_file, "FOO", "updated")
    d = parse_env_file(env_file).as_dict()
    assert d["FOO"] == "updated"


def test_set_key_other_keys_unchanged(env_file: Path) -> None:
    set_key(env_file, "FOO", "new")
    d = parse_env_file(env_file).as_dict()
    assert d["BAZ"] == "qux"


# ---------------------------------------------------------------------------
# Creating new keys
# ---------------------------------------------------------------------------

def test_set_key_creates_missing_key(env_file: Path) -> None:
    result = set_key(env_file, "NEW_KEY", "hello")
    assert result.ok
    assert result.created
    assert result.previous_value is None


def test_set_key_new_key_readable(env_file: Path) -> None:
    set_key(env_file, "NEW_KEY", "hello")
    d = parse_env_file(env_file).as_dict()
    assert d["NEW_KEY"] == "hello"


def test_set_key_creates_file_when_absent(tmp_path: Path) -> None:
    p = tmp_path / "fresh.env"
    result = set_key(p, "ALPHA", "1")
    assert result.ok
    assert p.exists()
    assert parse_env_file(p).as_dict()["ALPHA"] == "1"


# ---------------------------------------------------------------------------
# create_missing=False guard
# ---------------------------------------------------------------------------

def test_set_key_no_create_returns_error_when_key_absent(env_file: Path) -> None:
    result = set_key(env_file, "MISSING", "val", create_missing=False)
    assert not result.ok
    assert "key not found" in (result.error or "")


def test_set_key_no_create_returns_error_when_file_absent(tmp_path: Path) -> None:
    p = tmp_path / "nonexistent.env"
    result = set_key(p, "X", "1", create_missing=False)
    assert not result.ok
    assert "file not found" in (result.error or "")


# ---------------------------------------------------------------------------
# Quote flag
# ---------------------------------------------------------------------------

def test_set_key_quote_wraps_value(env_file: Path) -> None:
    set_key(env_file, "FOO", "hello world", quote=True)
    raw = env_file.read_text()
    assert 'FOO="hello world"' in raw


# ---------------------------------------------------------------------------
# Summary helper
# ---------------------------------------------------------------------------

def test_summary_created(env_file: Path) -> None:
    result = set_key(env_file, "BRAND_NEW", "42")
    assert "created" in result.summary()


def test_summary_updated(env_file: Path) -> None:
    result = set_key(env_file, "FOO", "new")
    assert "updated" in result.summary()
    assert "bar" in result.summary()  # previous value shown


def test_summary_error(env_file: Path) -> None:
    result = set_key(env_file, "GHOST", "x", create_missing=False)
    assert "error" in result.summary()
