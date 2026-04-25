"""Tests for envoy_local.diff and envoy_local.diff_formatter."""
from __future__ import annotations

import textwrap

import pytest

from envoy_local.diff import diff_env, DiffResult
from envoy_local.diff_formatter import format_diff, format_diff_json
from envoy_local.parser import parse_env_text
from envoy_local.redactor import Redactor, RedactionConfig


def _parse(text: str):
    return parse_env_text(textwrap.dedent(text))


@pytest.fixture()
def source():
    return _parse("""
        APP_NAME=myapp
        SECRET_KEY=supersecret
        OLD_VAR=gone
    """)


@pytest.fixture()
def target():
    return _parse("""
        APP_NAME=myapp
        SECRET_KEY=newsecret
        NEW_VAR=hello
    """)


def test_diff_detects_added(source, target):
    result = diff_env(source, target)
    keys = {e.key for e in result.added}
    assert "NEW_VAR" in keys


def test_diff_detects_removed(source, target):
    result = diff_env(source, target)
    keys = {e.key for e in result.removed}
    assert "OLD_VAR" in keys


def test_diff_detects_changed(source, target):
    result = diff_env(source, target)
    keys = {e.key for e in result.changed}
    assert "SECRET_KEY" in keys


def test_diff_detects_unchanged(source, target):
    result = diff_env(source, target)
    keys = {e.key for e in result.unchanged}
    assert "APP_NAME" in keys


def test_diff_has_changes(source, target):
    result = diff_env(source, target)
    assert result.has_changes is True


def test_diff_no_changes():
    src = _parse("FOO=bar\nBAZ=qux\n")
    tgt = _parse("FOO=bar\nBAZ=qux\n")
    result = diff_env(src, tgt)
    assert result.has_changes is False
    assert "No changes" in result.summary()


def test_summary_string(source, target):
    result = diff_env(source, target)
    summary = result.summary()
    assert "+" in summary or "-" in summary or "~" in summary


def test_format_diff_text_contains_keys(source, target):
    result = diff_env(source, target)
    text = format_diff(result, color=False)
    assert "NEW_VAR" in text
    assert "OLD_VAR" in text
    assert "SECRET_KEY" in text


def test_format_diff_redacts_secrets(source, target):
    result = diff_env(source, target)
    redactor = Redactor(RedactionConfig())
    text = format_diff(result, redactor=redactor, color=False)
    assert "supersecret" not in text
    assert "newsecret" not in text


def test_format_diff_json_structure(source, target):
    result = diff_env(source, target)
    data = format_diff_json(result)
    assert isinstance(data, list)
    statuses = {item["status"] for item in data}
    assert statuses <= {"added", "removed", "changed", "unchanged"}


def test_format_diff_hides_unchanged_by_default(source, target):
    result = diff_env(source, target)
    text = format_diff(result, color=False, show_unchanged=False)
    assert "APP_NAME" not in text


def test_format_diff_shows_unchanged_when_flag_set(source, target):
    result = diff_env(source, target)
    text = format_diff(result, color=False, show_unchanged=True)
    assert "APP_NAME" in text
