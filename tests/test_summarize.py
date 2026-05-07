"""Tests for envoy_local.summarize and envoy_local.summarize_cli."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.redactor import RedactionConfig
from envoy_local.summarize import summarize_parse_result
from envoy_local.summarize_cli import cmd_summarize


ENV_TEXT = """
# database config
DB_HOST=localhost
DB_PASSWORD=secret123
DB_USER=admin
EMPTY_VAL=
DB_HOST=duplicate

API_KEY=abc
"""


def _parse(text: str):
    return parse_env_text(text)


def test_key_count():
    result = _parse(ENV_TEXT)
    summary = summarize_parse_result(result)
    assert summary.key_count == 6


def test_comment_count():
    result = _parse(ENV_TEXT)
    summary = summarize_parse_result(result)
    assert summary.comment_count == 1


def test_blank_line_count():
    result = _parse(ENV_TEXT)
    summary = summarize_parse_result(result)
    assert summary.blank_line_count >= 1


def test_empty_value_detected():
    result = _parse(ENV_TEXT)
    summary = summarize_parse_result(result)
    assert summary.empty_value_count == 1
    assert "EMPTY_VAL" in summary.empty_keys


def test_duplicate_keys_detected():
    result = _parse(ENV_TEXT)
    summary = summarize_parse_result(result)
    assert "DB_HOST" in summary.duplicate_keys


def test_secret_detection_default_patterns():
    result = _parse(ENV_TEXT)
    summary = summarize_parse_result(result)
    # DB_PASSWORD and API_KEY should be detected as secrets
    assert "DB_PASSWORD" in summary.secret_keys
    assert "API_KEY" in summary.secret_keys


def test_secret_detection_extra_pattern():
    result = _parse("DB_USER=admin\nDB_HOST=localhost\n")
    cfg = RedactionConfig(extra_patterns=[r"DB_USER"])
    summary = summarize_parse_result(result, cfg)
    assert "DB_USER" in summary.secret_keys


def test_to_dict_has_expected_keys():
    result = _parse(ENV_TEXT)
    summary = summarize_parse_result(result)
    d = summary.to_dict()
    for key in (
        "total_lines", "key_count", "empty_value_count",
        "secret_count", "comment_count", "blank_line_count",
        "duplicate_keys", "secret_keys", "empty_keys",
    ):
        assert key in d


# --- CLI tests ---

class _NS:
    def __init__(self, file, json_out=False, secret_pattern=None):
        self.file = file
        self.json = json_out
        self.secret_pattern = secret_pattern


def test_cmd_summarize_returns_0(tmp_path):
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nBAZ=qux\n")
    assert cmd_summarize(_NS(str(f))) == 0


def test_cmd_summarize_missing_file_returns_2(tmp_path):
    assert cmd_summarize(_NS(str(tmp_path / "missing.env"))) == 2


def test_cmd_summarize_json_output(tmp_path, capsys):
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nSECRET_KEY=xyz\n")
    rc = cmd_summarize(_NS(str(f), json_out=True))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert data["key_count"] == 2


def test_cmd_summarize_extra_secret_pattern(tmp_path, capsys):
    f = tmp_path / ".env"
    f.write_text("MY_TOKEN=abc\nFOO=bar\n")
    rc = cmd_summarize(_NS(str(f), json_out=True, secret_pattern=[r"MY_TOKEN"]))
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "MY_TOKEN" in data["secret_keys"]
