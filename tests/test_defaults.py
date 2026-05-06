"""Tests for envoy_local.defaults."""

from __future__ import annotations

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.defaults import apply_defaults


def _parse(text: str):
    return parse_env_text(text)


def test_apply_defaults_adds_missing_key():
    result = _parse("FOO=bar\n")
    out = apply_defaults(result, {"BAZ": "qux"})
    keys = [e.key for e in out.entries if e.key]
    assert "BAZ" in keys
    assert "BAZ" in out.applied


def test_apply_defaults_skips_existing_non_empty_key():
    result = _parse("FOO=bar\n")
    out = apply_defaults(result, {"FOO": "default_val"})
    assert "FOO" in out.skipped
    assert "FOO" not in out.applied
    # Original value preserved
    entry = next(e for e in out.entries if e.key == "FOO")
    assert entry.value == "bar"


def test_apply_defaults_overwrites_empty_value_by_default():
    result = _parse("FOO=\n")
    out = apply_defaults(result, {"FOO": "filled"})
    assert "FOO" in out.applied
    entry = next(e for e in out.entries if e.key == "FOO")
    assert entry.value == "filled"


def test_apply_defaults_no_overwrite_empty_when_flag_false():
    result = _parse("FOO=\n")
    out = apply_defaults(result, {"FOO": "filled"}, overwrite_empty=False)
    assert "FOO" in out.skipped
    entry = next(e for e in out.entries if e.key == "FOO")
    assert entry.value == ""


def test_apply_defaults_multiple_keys():
    result = _parse("A=1\nB=\n")
    out = apply_defaults(result, {"B": "2", "C": "3"})
    assert "B" in out.applied
    assert "C" in out.applied
    assert len(out.applied) == 2


def test_apply_defaults_empty_defaults_dict():
    result = _parse("FOO=bar\n")
    out = apply_defaults(result, {})
    assert out.applied == []
    assert out.skipped == []
    assert out.summary() == "no defaults to apply"


def test_apply_defaults_summary_applied_only():
    result = _parse("")
    out = apply_defaults(result, {"X": "1"})
    assert "applied 1 default" in out.summary()
    assert "X" in out.summary()


def test_apply_defaults_summary_skipped_only():
    result = _parse("X=existing\n")
    out = apply_defaults(result, {"X": "default"})
    assert "skipped 1" in out.summary()


def test_apply_defaults_summary_mixed():
    result = _parse("A=val\n")
    out = apply_defaults(result, {"A": "default", "B": "new"})
    summary = out.summary()
    assert "applied" in summary
    assert "skipped" in summary


def test_apply_defaults_writes_file(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    result = _parse("FOO=bar\n")
    apply_defaults(result, {"NEW_KEY": "hello"}, env_file=str(env_file))
    content = env_file.read_text()
    assert "NEW_KEY" in content
    assert "hello" in content


def test_apply_defaults_does_not_write_file_when_no_changes(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n")
    mtime_before = env_file.stat().st_mtime
    result = _parse("FOO=bar\n")
    apply_defaults(result, {"FOO": "ignored"}, env_file=str(env_file))
    # File should not have been rewritten (no applied changes)
    assert env_file.stat().st_mtime == mtime_before


def test_ok_is_always_true():
    result = _parse("")
    out = apply_defaults(result, {})
    assert out.ok is True
