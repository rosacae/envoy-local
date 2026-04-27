"""Tests for envoy_local.compare"""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy_local.compare import (
    CompareEntry,
    CompareResult,
    compare_env_files,
    compare_parse_results,
)
from envoy_local.parser import parse_env_text
from envoy_local.redactor import Redactor, RedactionConfig


def _parse(text: str):
    return parse_env_text(textwrap.dedent(text))


@pytest.fixture()
def left():
    return _parse("""
        APP_NAME=myapp
        DB_HOST=localhost
        SECRET_KEY=abc123
    """)


@pytest.fixture()
def right():
    return _parse("""
        APP_NAME=myapp
        DB_HOST=remotehost
        API_TOKEN=tok_xyz
    """)


def test_compare_detects_left_only(left, right):
    result = compare_parse_results(left, right)
    keys = [e.key for e in result.left_only()]
    assert "SECRET_KEY" in keys


def test_compare_detects_right_only(left, right):
    result = compare_parse_results(left, right)
    keys = [e.key for e in result.right_only()]
    assert "API_TOKEN" in keys


def test_compare_detects_changed(left, right):
    result = compare_parse_results(left, right)
    keys = [e.key for e in result.changed()]
    assert "DB_HOST" in keys


def test_compare_detects_equal(left, right):
    result = compare_parse_results(left, right)
    keys = [e.key for e in result.equal()]
    assert "APP_NAME" in keys


def test_has_differences_true(left, right):
    result = compare_parse_results(left, right)
    assert result.has_differences is True


def test_has_differences_false():
    p = _parse("FOO=bar\nBAZ=qux\n")
    result = compare_parse_results(p, p)
    assert result.has_differences is False


def test_to_dict_status_labels(left, right):
    result = compare_parse_results(left, right)
    statuses = {e.key: e.to_dict()["status"] for e in result.entries}
    assert statuses["APP_NAME"] == "equal"
    assert statuses["DB_HOST"] == "changed"
    assert statuses["SECRET_KEY"] == "left_only"
    assert statuses["API_TOKEN"] == "right_only"


def test_to_dict_redacts_secret_values(left, right):
    redactor = Redactor(RedactionConfig(patterns=["SECRET"]))
    result = compare_parse_results(left, right)
    secret_entry = next(e for e in result.entries if e.key == "SECRET_KEY")
    d = secret_entry.to_dict(redactor)
    assert d["left"] != "abc123"
    assert "*" in d["left"]


def test_compare_env_files(tmp_path: Path):
    a = tmp_path / "a.env"
    b = tmp_path / "b.env"
    a.write_text("FOO=1\nBAR=2\n")
    b.write_text("FOO=1\nBAR=99\nNEW=x\n")
    result = compare_env_files(a, b)
    assert result.has_differences
    changed_keys = [e.key for e in result.changed()]
    assert "BAR" in changed_keys
    right_only_keys = [e.key for e in result.right_only()]
    assert "NEW" in right_only_keys
