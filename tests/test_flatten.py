"""Tests for envoy_local.flatten."""
from __future__ import annotations

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.flatten import flatten_env, flatten_to_dict


def _parse(text: str):
    return parse_env_text(text)


# ---------------------------------------------------------------------------
# flatten_env
# ---------------------------------------------------------------------------

def test_flatten_no_prefix_stripping_keeps_all_keys():
    result = _parse("APP__HOST=localhost\nAPP__PORT=5432\n")
    flat = flatten_env(result)
    keys = [e.key for e in flat.entries if e.key]
    assert keys == ["APP__HOST", "APP__PORT"]


def test_flatten_strips_single_prefix():
    result = _parse("APP__HOST=localhost\nAPP__PORT=5432\n")
    flat = flatten_env(result, strip_prefixes=["APP"])
    keys = [e.key for e in flat.entries if e.key]
    assert keys == ["HOST", "PORT"]


def test_flatten_strips_only_matching_prefix():
    result = _parse("APP__HOST=localhost\nDB__NAME=mydb\n")
    flat = flatten_env(result, strip_prefixes=["APP"])
    keys = [e.key for e in flat.entries if e.key]
    assert "HOST" in keys
    assert "DB__NAME" in keys


def test_flatten_reports_used_prefixes():
    result = _parse("APP__HOST=localhost\nDB__NAME=mydb\n")
    flat = flatten_env(result, strip_prefixes=["APP", "DB"])
    assert set(flat.stripped_prefixes) == {"APP", "DB"}


def test_flatten_unused_prefix_not_reported():
    result = _parse("APP__HOST=localhost\n")
    flat = flatten_env(result, strip_prefixes=["APP", "OTHER"])
    assert "OTHER" not in flat.stripped_prefixes


def test_flatten_custom_separator():
    result = _parse("APP_HOST=localhost\nAPP_PORT=5432\n")
    flat = flatten_env(result, strip_prefixes=["APP"], separator="_")
    keys = [e.key for e in flat.entries if e.key]
    assert keys == ["HOST", "PORT"]


def test_flatten_preserves_values():
    result = _parse("APP__SECRET=hunter2\n")
    flat = flatten_env(result, strip_prefixes=["APP"])
    entry = next(e for e in flat.entries if e.key == "SECRET")
    assert entry.value == "hunter2"


def test_flatten_skips_blank_lines_and_comments():
    result = _parse("# a comment\n\nAPP__KEY=val\n")
    flat = flatten_env(result, strip_prefixes=["APP"])
    assert flat.skipped == 2  # comment + blank


def test_flatten_ok_is_always_true():
    flat = flatten_env(_parse(""))
    assert flat.ok() is True


def test_flatten_summary_contains_count():
    result = _parse("APP__A=1\nAPP__B=2\n")
    flat = flatten_env(result, strip_prefixes=["APP"])
    assert "2 entries flattened" in flat.summary()


def test_flatten_summary_mentions_prefix():
    result = _parse("APP__A=1\n")
    flat = flatten_env(result, strip_prefixes=["APP"])
    assert "APP" in flat.summary()


# ---------------------------------------------------------------------------
# flatten_to_dict
# ---------------------------------------------------------------------------

def test_flatten_to_dict_returns_mapping():
    result = _parse("APP__HOST=localhost\nAPP__PORT=5432\n")
    d = flatten_to_dict(result, strip_prefixes=["APP"])
    assert d == {"HOST": "localhost", "PORT": "5432"}


def test_flatten_to_dict_no_keyless_entries():
    result = _parse("# comment\n\nKEY=val\n")
    d = flatten_to_dict(result)
    assert "" not in d
    assert d == {"KEY": "val"}
