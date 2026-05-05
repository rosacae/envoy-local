"""Tests for envoy_local.transform."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.transform import TransformOptions, transform_entries


def _parse(text: str):
    return parse_env_text(textwrap.dedent(text))


def test_uppercase_keys():
    pr = _parse("db_host=localhost\ndb_port=5432\n")
    result = transform_entries(pr, TransformOptions(uppercase_keys=True))
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["DB_HOST", "DB_PORT"]
    assert result.changed == 2


def test_uppercase_already_upper_not_counted_as_changed():
    pr = _parse("DB_HOST=localhost\n")
    result = transform_entries(pr, TransformOptions(uppercase_keys=True))
    assert result.changed == 0
    assert result.skipped == 1


def test_strip_values():
    pr = _parse("KEY=  hello world  \n")
    result = transform_entries(pr, TransformOptions(strip_values=True))
    vals = [e.value for e in result.entries if e.key]
    assert vals == ["hello world"]
    assert result.changed == 1


def test_add_prefix():
    pr = _parse("HOST=localhost\nPORT=5432\n")
    result = transform_entries(pr, TransformOptions(prefix="APP_"))
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["APP_HOST", "APP_PORT"]


def test_add_prefix_skips_already_prefixed():
    pr = _parse("APP_HOST=localhost\n")
    result = transform_entries(pr, TransformOptions(prefix="APP_"))
    assert result.changed == 0


def test_add_suffix():
    pr = _parse("HOST=localhost\n")
    result = transform_entries(pr, TransformOptions(suffix="_VAR"))
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["HOST_VAR"]


def test_remove_prefix():
    pr = _parse("APP_HOST=localhost\nAPP_PORT=5432\n")
    result = transform_entries(pr, TransformOptions(remove_prefix="APP_"))
    keys = [e.key for e in result.entries if e.key]
    assert keys == ["HOST", "PORT"]
    assert result.changed == 2


def test_remove_prefix_no_match_unchanged():
    pr = _parse("HOST=localhost\n")
    result = transform_entries(pr, TransformOptions(remove_prefix="APP_"))
    assert result.changed == 0


def test_comments_are_skipped_not_changed():
    pr = _parse("# a comment\nKEY=val\n")
    result = transform_entries(pr, TransformOptions(uppercase_keys=True))
    # comment entry has no key, so skipped
    assert result.skipped == 2  # comment + already-upper key


def test_combined_options():
    pr = _parse("db_host=  localhost  \n")
    opts = TransformOptions(uppercase_keys=True, strip_values=True, prefix="MY_")
    result = transform_entries(pr, opts)
    entries = [e for e in result.entries if e.key]
    assert entries[0].key == "MY_DB_HOST"
    assert entries[0].value == "localhost"


def test_no_options_returns_unchanged():
    pr = _parse("KEY=value\n")
    result = transform_entries(pr, TransformOptions())
    assert result.changed == 0
    assert result.entries[0].key == "KEY"
    assert result.entries[0].value == "value"
