"""Tests for envoy_local.schema_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy_local.schema_cli import cmd_schema_validate, build_schema_parser


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("PORT=8080\nENV=prod\n")
    return p


@pytest.fixture()
def schema_file(tmp_path: Path) -> Path:
    p = tmp_path / "schema.json"
    p.write_text(
        json.dumps({
            "allow_extra": True,
            "fields": {
                "PORT": {"required": True, "pattern": r"\d+"},
                "ENV": {"allowed_values": ["dev", "staging", "prod"]},
            },
        })
    )
    return p


def _ns(env_file: str, schema_file: str, fmt: str = "text") -> argparse.Namespace:
    return argparse.Namespace(env_file=env_file, schema_file=schema_file, format=fmt)


def test_cmd_validate_returns_0_when_valid(env_file, schema_file):
    rc = cmd_schema_validate(_ns(str(env_file), str(schema_file)))
    assert rc == 0


def test_cmd_validate_returns_1_when_violations(tmp_path, schema_file):
    bad_env = tmp_path / ".env"
    bad_env.write_text("PORT=not-a-number\n")
    rc = cmd_schema_validate(_ns(str(bad_env), str(schema_file)))
    assert rc == 1


def test_cmd_validate_returns_2_on_missing_env(tmp_path, schema_file):
    rc = cmd_schema_validate(_ns(str(tmp_path / "missing.env"), str(schema_file)))
    assert rc == 2


def test_cmd_validate_returns_2_on_missing_schema(env_file, tmp_path):
    rc = cmd_schema_validate(_ns(str(env_file), str(tmp_path / "missing.json")))
    assert rc == 2


def test_cmd_validate_json_output_valid(env_file, schema_file, capsys):
    rc = cmd_schema_validate(_ns(str(env_file), str(schema_file), fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["ok"] is True
    assert data["violations"] == []
    assert rc == 0


def test_cmd_validate_json_output_violations(tmp_path, schema_file, capsys):
    bad_env = tmp_path / ".env"
    bad_env.write_text("ENV=invalid_value\n")
    rc = cmd_schema_validate(_ns(str(bad_env), str(schema_file), fmt="json"))
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["ok"] is False
    assert len(data["violations"]) >= 1
    assert rc == 1


def test_build_schema_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_schema_parser(sub)
    ns = parser.parse_args(["schema-validate", "a.env", "schema.json"])
    assert ns.env_file == "a.env"
    assert ns.schema_file == "schema.json"
    assert ns.format == "text"
