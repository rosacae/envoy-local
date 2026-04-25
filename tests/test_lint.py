"""Tests for envoy_local.lint and envoy_local.lint_cli."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy_local.lint import LintIssue, LintResult, lint_env_file, lint_parse_result
from envoy_local.parser import parse_env_text


def _lint(text: str, path: Path | None = None) -> LintResult:
    result = parse_env_text(text)
    return lint_parse_result(path or Path(".env"), result)


def test_lint_clean_file_is_ok():
    lr = _lint("DB_HOST=localhost\nDB_PORT=5432\n")
    assert lr.ok
    assert lr.issues == []


def test_lint_detects_duplicate_key():
    lr = _lint("API_KEY=abc\nAPI_KEY=xyz\n")
    codes = [i.code for i in lr.issues]
    assert "DUPLICATE_KEY" in codes


def test_lint_detects_empty_value():
    lr = _lint("SECRET=\n")
    codes = [i.code for i in lr.issues]
    assert "EMPTY_VALUE" in codes


def test_lint_detects_lowercase_key():
    lr = _lint("database_url=postgres://localhost/db\n")
    codes = [i.code for i in lr.issues]
    assert "KEY_CASE" in codes


def test_lint_uppercase_key_no_case_issue():
    lr = _lint("DATABASE_URL=postgres://localhost/db\n")
    codes = [i.code for i in lr.issues]
    assert "KEY_CASE" not in codes


def test_lint_invalid_line_reported():
    lr = _lint("VALID=1\nthis is not valid\n")
    codes = [i.code for i in lr.issues]
    assert "INVALID_LINE" in codes


def test_lint_multiple_issues_same_entry():
    # lowercase key AND empty value
    lr = _lint("my_key=\n")
    codes = [i.code for i in lr.issues]
    assert "KEY_CASE" in codes
    assert "EMPTY_VALUE" in codes


def test_lint_to_dict_structure():
    lr = _lint("API_KEY=abc\nAPI_KEY=xyz\n")
    d = lr.to_dict()
    assert "path" in d
    assert "ok" in d
    assert "issues" in d
    assert isinstance(d["issues"], list)
    issue = d["issues"][0]
    assert {"line", "key", "code", "message"} <= issue.keys()


def test_lint_env_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        lint_env_file(tmp_path / "missing.env")


def test_lint_env_file_from_disk(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\nDB_HOST=other\n")
    lr = lint_env_file(env)
    assert not lr.ok
    assert any(i.code == "DUPLICATE_KEY" for i in lr.issues)


# --- CLI tests ---

from argparse import Namespace
from envoy_local.lint_cli import cmd_lint


def _ns(files, fmt="text"):
    return Namespace(files=files, format=fmt)


def test_cmd_lint_returns_0_on_clean(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("DB_HOST=localhost\n")
    assert cmd_lint(_ns([str(env)])) == 0


def test_cmd_lint_returns_1_on_issues(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("bad_key=value\n")
    assert cmd_lint(_ns([str(env)])) == 1


def test_cmd_lint_returns_2_on_missing_file(tmp_path: Path):
    assert cmd_lint(_ns([str(tmp_path / "nope.env")])) == 2


def test_cmd_lint_json_output(tmp_path: Path, capsys):
    env = tmp_path / ".env"
    env.write_text("DB=ok\nDB=dup\n")
    ret = cmd_lint(_ns([str(env)], fmt="json"))
    captured = capsys.readouterr()
    import json
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["ok"] is False
    assert ret == 1
