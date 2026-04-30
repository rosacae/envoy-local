"""Tests for envoy_local.copy_key."""
from pathlib import Path
import pytest

from envoy_local.copy_key import copy_key
from envoy_local.parser import parse_env_file


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    p = tmp_path / "source.env"
    p.write_text("API_KEY=secret123\nDB_HOST=localhost\nPORT=5432\n")
    return p


@pytest.fixture()
def dest(tmp_path: Path) -> Path:
    return tmp_path / "dest.env"


def _keys(path: Path) -> dict:
    r = parse_env_file(path)
    return {e.key: e.value for e in r.entries if e.key}


def test_copy_key_creates_dest_file(source, dest):
    result = copy_key(source, dest, "DB_HOST")
    assert result.ok
    assert not result.skipped
    assert dest.exists()


def test_copy_key_value_is_present_in_dest(source, dest):
    copy_key(source, dest, "DB_HOST")
    assert _keys(dest)["DB_HOST"] == "localhost"


def test_copy_key_missing_source_returns_error(tmp_path, dest):
    result = copy_key(tmp_path / "nonexistent.env", dest, "FOO")
    assert not result.ok
    assert result.skipped
    assert "not found" in result.message


def test_copy_key_missing_key_in_source_returns_error(source, dest):
    result = copy_key(source, dest, "NONEXISTENT_KEY")
    assert not result.ok
    assert result.skipped


def test_copy_key_skips_existing_without_overwrite(source, dest):
    dest.write_text("DB_HOST=original\n")
    result = copy_key(source, dest, "DB_HOST")
    assert result.ok
    assert result.skipped
    # original value preserved
    assert _keys(dest)["DB_HOST"] == "original"


def test_copy_key_overwrites_when_flag_set(source, dest):
    dest.write_text("DB_HOST=original\n")
    result = copy_key(source, dest, "DB_HOST", overwrite=True)
    assert result.ok
    assert not result.skipped
    assert _keys(dest)["DB_HOST"] == "localhost"


def test_copy_key_with_rename(source, dest):
    result = copy_key(source, dest, "DB_HOST", dest_key="DATABASE_HOST")
    assert result.ok
    d = _keys(dest)
    assert "DATABASE_HOST" in d
    assert "DB_HOST" not in d
    assert d["DATABASE_HOST"] == "localhost"


def test_copy_key_redacts_secret(source, dest):
    result = copy_key(source, dest, "API_KEY", redact=True)
    assert result.ok
    assert _keys(dest)["API_KEY"] == ""


def test_copy_key_does_not_redact_non_secret(source, dest):
    result = copy_key(source, dest, "PORT", redact=True)
    assert result.ok
    assert _keys(dest)["PORT"] == "5432"


def test_copy_key_preserves_existing_dest_keys(source, dest):
    dest.write_text("EXISTING=value\n")
    copy_key(source, dest, "PORT")
    d = _keys(dest)
    assert "EXISTING" in d
    assert "PORT" in d


def test_copy_key_summary_message_is_string(source, dest):
    result = copy_key(source, dest, "PORT")
    assert isinstance(result.summary(), str)
    assert len(result.summary()) > 0
