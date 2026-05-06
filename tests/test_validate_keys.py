"""Tests for envoy_local.validate_keys and validate_keys_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.validate_keys import validate_key_names, KeyValidationResult
from envoy_local.validate_keys_cli import cmd_validate_keys


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse(text: str):
    return parse_env_text(text)


# ---------------------------------------------------------------------------
# validate_key_names unit tests
# ---------------------------------------------------------------------------

def test_valid_uppercase_keys_produce_no_violations():
    result = _parse("DB_HOST=localhost\nDB_PORT=5432\n")
    vr = validate_key_names(result)
    assert vr.ok
    assert vr.violations == []


def test_lowercase_key_is_flagged_by_default():
    result = _parse("db_host=localhost\n")
    vr = validate_key_names(result)
    assert not vr.ok
    assert any(v.key == "db_host" for v in vr.violations)


def test_lowercase_key_allowed_when_flag_set():
    result = _parse("db_host=localhost\n")
    vr = validate_key_names(result, allow_lowercase=True)
    assert vr.ok


def test_key_starting_with_digit_is_flagged():
    result = _parse("1BADKEY=value\n")
    vr = validate_key_names(result)
    assert not vr.ok
    assert any(v.key == "1BADKEY" for v in vr.violations)


def test_reserved_prefix_is_flagged():
    result = _parse("PATH=/usr/bin\n")
    vr = validate_key_names(result, check_reserved=True)
    assert not vr.ok
    assert any(v.key == "PATH" for v in vr.violations)


def test_reserved_check_skipped_when_disabled():
    result = _parse("PATH=/usr/bin\n")
    vr = validate_key_names(result, check_reserved=False)
    assert vr.ok


def test_comment_lines_are_ignored():
    result = _parse("# this is a comment\nVALID_KEY=yes\n")
    vr = validate_key_names(result)
    assert vr.ok


def test_to_dict_structure():
    result = _parse("bad_key=x\n")
    vr = validate_key_names(result)
    d = vr.to_dict()
    assert "ok" in d
    assert "violations" in d
    assert isinstance(d["violations"], list)
    assert d["violations"][0]["key"] == "bad_key"


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("GOOD_KEY=hello\nBAD_key=world\n")
    return p


def _ns(file: str, allow_lowercase: bool = False, no_reserved_check: bool = False, use_json: bool = False):
    ns = argparse.Namespace(
        file=file,
        allow_lowercase=allow_lowercase,
        no_reserved_check=no_reserved_check,
        json=use_json,
    )
    return ns


def test_cmd_validate_keys_returns_1_on_violations(env_file: Path):
    assert cmd_validate_keys(_ns(str(env_file))) == 1


def test_cmd_validate_keys_returns_0_when_clean(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("CLEAN_KEY=ok\nANOTHER=yes\n")
    assert cmd_validate_keys(_ns(str(p))) == 0


def test_cmd_validate_keys_returns_2_on_missing_file(tmp_path: Path):
    assert cmd_validate_keys(_ns(str(tmp_path / "missing.env"))) == 2


def test_cmd_validate_keys_json_output_is_valid(env_file: Path, capsys):
    cmd_validate_keys(_ns(str(env_file), use_json=True))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "ok" in data
    assert "violations" in data


def test_cmd_validate_keys_allow_lowercase_passes(tmp_path: Path):
    p = tmp_path / ".env"
    p.write_text("lower_key=value\n")
    assert cmd_validate_keys(_ns(str(p), allow_lowercase=True)) == 0
