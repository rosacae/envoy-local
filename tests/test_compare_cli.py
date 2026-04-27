"""Tests for envoy_local.compare_cli"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy_local.compare_cli import cmd_compare, build_compare_parser


@pytest.fixture()
def left_file(tmp_path: Path) -> Path:
    f = tmp_path / "left.env"
    f.write_text("APP=myapp\nDB_HOST=localhost\nSECRET_KEY=abc\n")
    return f


@pytest.fixture()
def right_file(tmp_path: Path) -> Path:
    f = tmp_path / "right.env"
    f.write_text("APP=myapp\nDB_HOST=remote\nAPI_TOKEN=tok\n")
    return f


def _ns(left: str, right: str, **kwargs) -> argparse.Namespace:
    defaults = {"format": "text", "redact": False, "show_equal": False}
    defaults.update(kwargs)
    return argparse.Namespace(left=left, right=right, **defaults)


def test_cmd_compare_returns_1_when_differences(left_file, right_file):
    rc = cmd_compare(_ns(str(left_file), str(right_file)))
    assert rc == 1


def test_cmd_compare_returns_0_when_identical(tmp_path: Path):
    f = tmp_path / "same.env"
    f.write_text("FOO=bar\n")
    rc = cmd_compare(_ns(str(f), str(f)))
    assert rc == 0


def test_cmd_compare_returns_2_on_missing_left(right_file):
    rc = cmd_compare(_ns("/nonexistent/left.env", str(right_file)))
    assert rc == 2


def test_cmd_compare_returns_2_on_missing_right(left_file):
    rc = cmd_compare(_ns(str(left_file), "/nonexistent/right.env"))
    assert rc == 2


def test_cmd_compare_json_output(left_file, right_file, capsys):
    rc = cmd_compare(_ns(str(left_file), str(right_file), format="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    statuses = {d["key"]: d["status"] for d in data}
    assert statuses["DB_HOST"] == "changed"
    assert statuses["SECRET_KEY"] == "left_only"
    assert statuses["API_TOKEN"] == "right_only"
    # equal keys excluded by default
    assert "APP" not in statuses


def test_cmd_compare_json_show_equal_includes_equal(left_file, right_file, capsys):
    cmd_compare(_ns(str(left_file), str(right_file), format="json", show_equal=True))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    statuses = {d["key"]: d["status"] for d in data}
    assert statuses.get("APP") == "equal"


def test_build_compare_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_compare_parser(sub)
    ns = parser.parse_args(["compare", "a.env", "b.env", "--format", "json"])
    assert ns.left == "a.env"
    assert ns.right == "b.env"
    assert ns.format == "json"
