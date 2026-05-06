"""Tests for envoy_local.coerce."""
from __future__ import annotations

import pytest

from envoy_local.parser import EnvEntry, ParseResult
from envoy_local.coerce import coerce_entries, CoerceResult


def _make_result(*pairs: tuple[str, str]) -> ParseResult:
    entries = [
        EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}")
        for k, v in pairs
    ]
    return ParseResult(entries=entries, errors=[])


def test_coerce_bool_true_variants():
    for raw in ("1", "true", "yes", "on", "True", "YES"):
        r = _make_result(("FLAG", raw))
        result = coerce_entries(r, {"FLAG": "bool"})
        assert result.ok
        entry = next(e for e in result.entries if e.key == "FLAG")
        assert entry.value == "true"


def test_coerce_bool_false_variants():
    for raw in ("0", "false", "no", "off", "False"):
        r = _make_result(("FLAG", raw))
        result = coerce_entries(r, {"FLAG": "bool"})
        entry = next(e for e in result.entries if e.key == "FLAG")
        assert entry.value == "false"


def test_coerce_bool_invalid_skipped():
    r = _make_result(("FLAG", "maybe"))
    result = coerce_entries(r, {"FLAG": "bool"})
    assert "FLAG" in result.skipped
    assert "FLAG" not in result.changed


def test_coerce_int_valid():
    r = _make_result(("PORT", "8080"))
    result = coerce_entries(r, {"PORT": "int"})
    assert "PORT" not in result.changed  # already canonical
    assert "PORT" not in result.skipped


def test_coerce_int_strips_whitespace():
    r = _make_result(("PORT", "  8080  "))
    result = coerce_entries(r, {"PORT": "int"})
    entry = next(e for e in result.entries if e.key == "PORT")
    assert entry.value == "8080"
    assert "PORT" in result.changed


def test_coerce_int_invalid_skipped():
    r = _make_result(("PORT", "abc"))
    result = coerce_entries(r, {"PORT": "int"})
    assert "PORT" in result.skipped


def test_coerce_float_valid():
    r = _make_result(("RATIO", "3.14"))
    result = coerce_entries(r, {"RATIO": "float"})
    assert "RATIO" not in result.skipped


def test_coerce_float_invalid_skipped():
    r = _make_result(("RATIO", "not-a-float"))
    result = coerce_entries(r, {"RATIO": "float"})
    assert "RATIO" in result.skipped


def test_coerce_str_strips_whitespace():
    r = _make_result(("NAME", "  hello  "))
    result = coerce_entries(r, {"NAME": "str"})
    entry = next(e for e in result.entries if e.key == "NAME")
    assert entry.value == "hello"
    assert "NAME" in result.changed


def test_keys_not_in_type_map_are_unchanged():
    r = _make_result(("A", "1"), ("B", "hello"))
    result = coerce_entries(r, {"A": "bool"})
    b_entry = next(e for e in result.entries if e.key == "B")
    assert b_entry.value == "hello"
    assert "B" not in result.changed
    assert "B" not in result.skipped


def test_summary_reflects_counts():
    r = _make_result(("FLAG", "yes"), ("PORT", "abc"))
    result = coerce_entries(r, {"FLAG": "bool", "PORT": "int"})
    s = result.summary()
    assert "1 coerced" in s
    assert "1 skipped" in s


def test_comment_entries_passed_through():
    from envoy_local.parser import EnvEntry
    comment_entry = EnvEntry(key=None, value=None, comment="# section", raw="# section")
    pr = ParseResult(entries=[comment_entry], errors=[])
    result = coerce_entries(pr, {})
    assert result.entries[0].comment == "# section"
