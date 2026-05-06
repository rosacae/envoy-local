"""Tests for envoy_local.alias."""
from __future__ import annotations

import pytest

from envoy_local.alias import alias_keys
from envoy_local.parser import ParseResult, EnvEntry


def _make_result(*pairs) -> ParseResult:
    """Build a minimal ParseResult from (key, value) pairs."""
    entries = [
        EnvEntry(key=k, value=v, comment=None, original_line=f"{k}={v}")
        for k, v in pairs
    ]
    return ParseResult(entries=entries, errors=[])


def _keys(result) -> list:
    return [e.key for e in result.entries if e.key]


def test_alias_creates_new_key():
    parsed = _make_result(("DB_HOST", "localhost"))
    ar = alias_keys(parsed, {"DATABASE_HOST": "DB_HOST"})
    assert "DATABASE_HOST" in _keys(ar)
    assert ar.created == ["DATABASE_HOST"]
    assert ar.ok


def test_alias_copies_value():
    parsed = _make_result(("SECRET", "abc123"))
    ar = alias_keys(parsed, {"APP_SECRET": "SECRET"})
    entry = next(e for e in ar.entries if e.key == "APP_SECRET")
    assert entry.value == "abc123"


def test_alias_missing_source_reported():
    parsed = _make_result(("EXISTING", "val"))
    ar = alias_keys(parsed, {"ALIAS": "NONEXISTENT"})
    assert "NONEXISTENT" in ar.missing_sources
    assert not ar.ok
    assert "ALIAS" not in _keys(ar)


def test_alias_skips_existing_without_overwrite():
    parsed = _make_result(("SRC", "hello"), ("DST", "old"))
    ar = alias_keys(parsed, {"DST": "SRC"}, overwrite=False)
    assert "DST" in ar.skipped
    assert "DST" not in ar.created
    # original value preserved
    entry = next(e for e in ar.entries if e.key == "DST")
    assert entry.value == "old"


def test_alias_overwrites_existing_when_flag_set():
    parsed = _make_result(("SRC", "new_val"), ("DST", "old_val"))
    ar = alias_keys(parsed, {"DST": "SRC"}, overwrite=True)
    assert "DST" in ar.created
    assert "DST" not in ar.skipped
    entry = next(e for e in ar.entries if e.key == "DST")
    assert entry.value == "new_val"


def test_alias_multiple_mappings():
    parsed = _make_result(("A", "1"), ("B", "2"))
    ar = alias_keys(parsed, {"ALIAS_A": "A", "ALIAS_B": "B"})
    assert set(ar.created) == {"ALIAS_A", "ALIAS_B"}
    assert ar.ok


def test_alias_summary_contains_created():
    parsed = _make_result(("X", "10"))
    ar = alias_keys(parsed, {"Y": "X"})
    assert "created" in ar.summary()
    assert "Y" in ar.summary()


def test_alias_summary_no_changes_when_empty_mapping():
    parsed = _make_result(("X", "10"))
    ar = alias_keys(parsed, {})
    assert ar.summary() == "no changes"


def test_alias_writes_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=secret\n")
    parsed = _make_result(("API_KEY", "secret"))
    alias_keys(parsed, {"APP_API_KEY": "API_KEY"}, output_path=str(env_file))
    content = env_file.read_text()
    assert "APP_API_KEY" in content
