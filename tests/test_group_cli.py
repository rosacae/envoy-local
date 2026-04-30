"""Tests for envoy_local.group_cli."""
from __future__ import annotations

import json
import argparse
from pathlib import Path

import pytest

from envoy_local.group_cli import cmd_group, build_group_parser


ENV_CONTENT = "DB_HOST=localhost\nDB_PORT=5432\nAWS_KEY=abc\nAPP_NAME=myapp\n"


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(ENV_CONTENT)
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": "",
        "separator": "_",
        "prefixes": None,
        "mapping": None,
        "format": "text",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_group_returns_0(env_file, capsys):
    rc = cmd_group(_ns(file=str(env_file)))
    assert rc == 0


def test_cmd_group_text_output_contains_groups(env_file, capsys):
    cmd_group(_ns(file=str(env_file)))
    out = capsys.readouterr().out
    assert "[DB]" in out
    assert "[AWS]" in out


def test_cmd_group_json_output_is_valid(env_file, capsys):
    rc = cmd_group(_ns(file=str(env_file), format="json"))
    assert rc == 0
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "groups" in data
    assert "DB" in data["groups"]


def test_cmd_group_with_prefixes_filter(env_file, capsys):
    cmd_group(_ns(file=str(env_file), prefixes="DB", format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "DB" in data["groups"]
    assert "AWS" not in data["groups"]


def test_cmd_group_with_mapping(env_file, capsys):
    mapping = json.dumps({"infra": ["DB_HOST", "DB_PORT"]})
    cmd_group(_ns(file=str(env_file), mapping=mapping, format="json"))
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "infra" in data["groups"]


def test_cmd_group_missing_file_returns_2(tmp_path, capsys):
    rc = cmd_group(_ns(file=str(tmp_path / "missing.env")))
    assert rc == 2


def test_cmd_group_bad_mapping_json_returns_2(env_file, capsys):
    rc = cmd_group(_ns(file=str(env_file), mapping="{not valid json}"))
    assert rc == 2


def test_build_group_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_group_parser(sub)
    ns = parser.parse_args(["group", "somefile.env"])
    assert ns.file == "somefile.env"
    assert ns.separator == "_"
