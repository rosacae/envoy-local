"""Tests for envoy_local.filter."""
from __future__ import annotations

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.filter import FilterOptions, filter_entries


SAMPLE = """
# database config
DB_HOST=localhost
DB_PORT=5432
DB_PASSWORD=
APP_DEBUG=true
APP_SECRET=s3cr3t
app_lower=yes
"""


@pytest.fixture()
def parsed():
    return parse_env_text(SAMPLE)


def test_no_filter_returns_all_keyed_entries(parsed):
    opts = FilterOptions()
    result = filter_entries(parsed, opts)
    keys = [e.key for e in result.matched]
    assert "DB_HOST" in keys
    assert "APP_DEBUG" in keys
    assert "app_lower" in keys


def test_key_pattern_filters_by_prefix(parsed):
    opts = FilterOptions(key_pattern=r"^DB_")
    result = filter_entries(parsed, opts)
    keys = [e.key for e in result.matched]
    assert keys == ["DB_HOST", "DB_PORT", "DB_PASSWORD"]


def test_value_pattern_matches_non_empty(parsed):
    opts = FilterOptions(value_pattern=r"^\d+$")
    result = filter_entries(parsed, opts)
    keys = [e.key for e in result.matched]
    assert keys == ["DB_PORT"]


def test_only_empty_returns_blank_values(parsed):
    opts = FilterOptions(only_empty=True)
    result = filter_entries(parsed, opts)
    keys = [e.key for e in result.matched]
    assert keys == ["DB_PASSWORD"]


def test_only_set_excludes_blank_values(parsed):
    opts = FilterOptions(only_set=True)
    result = filter_entries(parsed, opts)
    keys = [e.key for e in result.matched]
    assert "DB_PASSWORD" not in keys
    assert "DB_HOST" in keys


def test_invert_flips_key_pattern(parsed):
    opts = FilterOptions(key_pattern=r"^DB_", invert=True)
    result = filter_entries(parsed, opts)
    keys = [e.key for e in result.matched]
    assert "DB_HOST" not in keys
    assert "APP_DEBUG" in keys
    assert "app_lower" in keys


def test_combined_key_and_value_pattern(parsed):
    opts = FilterOptions(key_pattern=r"^APP_", value_pattern=r"true")
    result = filter_entries(parsed, opts)
    keys = [e.key for e in result.matched]
    assert keys == ["APP_DEBUG"]


def test_comments_never_matched(parsed):
    opts = FilterOptions()
    result = filter_entries(parsed, opts)
    for entry in result.matched:
        assert entry.key is not None


def test_summary_string(parsed):
    opts = FilterOptions(key_pattern=r"^DB_")
    result = filter_entries(parsed, opts)
    summary = result.summary()
    assert "3 matched" in summary


def test_to_dict_contains_matched_keys(parsed):
    opts = FilterOptions(key_pattern=r"^APP_")
    result = filter_entries(parsed, opts)
    d = result.to_dict()
    assert "APP_DEBUG" in d["matched"]
    assert "APP_SECRET" in d["matched"]
    assert isinstance(d["total"], int)
