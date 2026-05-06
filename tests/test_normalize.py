"""Tests for envoy_local.normalize."""
from __future__ import annotations

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.normalize import normalize_env_file, _normalize_value


# ---------------------------------------------------------------------------
# Unit tests for _normalize_value
# ---------------------------------------------------------------------------

def test_normalize_value_strips_trailing_whitespace():
    assert _normalize_value("hello   ") == "hello"


def test_normalize_value_strips_leading_whitespace():
    assert _normalize_value("   world") == "world"


def test_normalize_value_quotes_value_with_spaces():
    result = _normalize_value("hello world")
    assert result == '"hello world"'


def test_normalize_value_does_not_double_quote_already_quoted():
    result = _normalize_value('"hello world"')
    assert result == '"hello world"'


def test_normalize_value_does_not_double_quote_single_quoted():
    result = _normalize_value("'hello world'")
    assert result == "'hello world'"


def test_normalize_value_plain_no_spaces_unchanged():
    assert _normalize_value("mysecret") == "mysecret"


def test_normalize_value_empty_string_unchanged():
    assert _normalize_value("") == ""


# ---------------------------------------------------------------------------
# Integration tests for normalize_env_file
# ---------------------------------------------------------------------------

def _parse(text: str):
    return parse_env_text(text)


def test_normalize_detects_changed_key():
    pr = _parse("DB_HOST=localhost  \nDB_PASS=secret\n")
    result = normalize_env_file(pr)
    assert "DB_HOST" in result.changed


def test_normalize_skips_already_clean_key():
    pr = _parse("API_KEY=abc123\n")
    result = normalize_env_file(pr)
    assert "API_KEY" in result.skipped
    assert result.changed == []


def test_normalize_quotes_spaced_value():
    pr = _parse("GREETING=hello world\n")
    result = normalize_env_file(pr)
    assert "GREETING" in result.changed


def test_normalize_total_counts_keyed_entries_only():
    pr = _parse("# comment\nFOO=bar\nBAZ=qux\n")
    result = normalize_env_file(pr)
    assert result.total == 2


def test_normalize_written_false_without_path():
    pr = _parse("FOO=bar  \n")
    result = normalize_env_file(pr)
    assert result.written is False


def test_normalize_writes_file_when_output_path_given(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar  \nBAZ=hello world\n")
    pr = _parse(env_file.read_text())
    out = tmp_path / ".env.out"
    result = normalize_env_file(pr, output_path=str(out))
    assert result.written is True
    content = out.read_text()
    assert "FOO=bar" in content
    assert '"hello world"' in content


def test_normalize_overwrites_source_in_place(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("KEY=value  \n")
    pr = _parse(env_file.read_text())
    result = normalize_env_file(pr, source_path=str(env_file))
    assert result.written is True
    assert "KEY=value" in env_file.read_text()


def test_normalize_summary_no_changes():
    pr = _parse("FOO=bar\n")
    result = normalize_env_file(pr)
    assert result.summary() == "Nothing to normalize."


def test_normalize_summary_with_changes():
    pr = _parse("FOO=bar  \nBAZ=clean\n")
    result = normalize_env_file(pr)
    summary = result.summary()
    assert "1 key(s) normalized" in summary
    assert "1 key(s) unchanged" in summary
