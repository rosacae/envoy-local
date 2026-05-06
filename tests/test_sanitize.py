"""Tests for envoy_local.sanitize."""
from __future__ import annotations

import pytest

from envoy_local.parser import ParseResult, EnvEntry
from envoy_local.sanitize import SanitizeOptions, SanitizeResult, sanitize_entries


def _make_result(*pairs) -> ParseResult:
    """Build a ParseResult from (key, value) tuples."""
    entries = [
        EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return ParseResult(entries=entries, errors=[])


def test_sanitize_strips_leading_trailing_whitespace():
    pr = _make_result(("FOO", "  hello  "), ("BAR", "world"))
    result = sanitize_entries(pr)
    values = {e.key: e.value for e in result.entries}
    assert values["FOO"] == "hello"
    assert values["BAR"] == "world"


def test_sanitize_changed_list_only_includes_modified_keys():
    pr = _make_result(("FOO", "  hello  "), ("BAR", "clean"))
    result = sanitize_entries(pr)
    assert "FOO" in result.changed
    assert "BAR" not in result.changed


def test_sanitize_removes_non_printable_characters():
    pr = _make_result(("KEY", "val\x00ue"), ("OTHER", "normal"))
    result = sanitize_entries(pr)
    values = {e.key: e.value for e in result.entries}
    assert "\x00" not in values["KEY"]
    assert values["KEY"] == "value"


def test_sanitize_no_change_when_already_clean():
    pr = _make_result(("A", "clean"), ("B", "also_clean"))
    result = sanitize_entries(pr)
    assert result.changed == []
    assert result.total == 2


def test_sanitize_normalize_quotes_strips_surrounding_double_quotes():
    pr = _make_result(("SECRET", '"my_secret"'))
    opts = SanitizeOptions(normalize_quotes=True)
    result = sanitize_entries(pr, opts)
    values = {e.key: e.value for e in result.entries}
    assert values["SECRET"] == "my_secret"


def test_sanitize_normalize_quotes_strips_surrounding_single_quotes():
    pr = _make_result(("TOKEN", "'abc123'"))
    opts = SanitizeOptions(normalize_quotes=True)
    result = sanitize_entries(pr, opts)
    values = {e.key: e.value for e in result.entries}
    assert values["TOKEN"] == "abc123"


def test_sanitize_normalize_quotes_off_by_default():
    pr = _make_result(("K", '"quoted"'))
    result = sanitize_entries(pr)
    values = {e.key: e.value for e in result.entries}
    assert values["K"] == '"quoted"'


def test_sanitize_preserves_comment_entries():
    comment_entry = EnvEntry(key=None, value=None, comment="# a comment", raw="# a comment")
    pr = ParseResult(entries=[comment_entry], errors=[])
    result = sanitize_entries(pr)
    assert result.entries[0].comment == "# a comment"
    assert result.total == 0


def test_sanitize_summary_message():
    pr = _make_result(("X", "  spaces  "), ("Y", "fine"))
    result = sanitize_entries(pr)
    summary = result.summary()
    assert "1 value(s) modified" in summary
    assert "2 entries" in summary


def test_sanitize_ok_always_true():
    pr = _make_result(("A", "val"))
    result = sanitize_entries(pr)
    assert result.ok() is True
