"""Integration tests for the diff CLI command."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy_local.diff_cli import cmd_diff


@pytest.fixture()
def env_a(tmp_path: Path) -> Path:
    p = tmp_path / ".env.a"
    p.write_text(textwrap.dedent("""\
        APP=myapp
        SECRET_KEY=oldsecret
        REMOVED=bye
    """))
    return p


@pytest.fixture()
def env_b(tmp_path: Path) -> Path:
    p = tmp_path / ".env.b"
    p.write_text(textwrap.dedent("""\
        APP=myapp
        SECRET_KEY=newsecret
        ADDED=hi
    """))
    return p


def test_cmd_diff_returns_1_when_changes(env_a, env_b, capsys):
    rc = cmd_diff(str(env_a), str(env_b), color=False)
    assert rc == 1


def test_cmd_diff_returns_0_when_no_changes(env_a, tmp_path, capsys):
    env_c = tmp_path / ".env.c"
    env_c.write_text(env_a.read_text())
    rc = cmd_diff(str(env_a), str(env_c), color=False)
    assert rc == 0


def test_cmd_diff_returns_2_on_missing_source(env_b, capsys):
    rc = cmd_diff("/nonexistent/.env", str(env_b), color=False)
    assert rc == 2


def test_cmd_diff_returns_2_on_missing_target(env_a, capsys):
    rc = cmd_diff(str(env_a), "/nonexistent/.env", color=False)
    assert rc == 2


def test_cmd_diff_output_contains_diff_markers(env_a, env_b, capsys):
    cmd_diff(str(env_a), str(env_b), color=False)
    captured = capsys.readouterr()
    assert "ADDED" in captured.out
    assert "REMOVED" in captured.out


def test_cmd_diff_json_output(env_a, env_b, capsys):
    import json
    cmd_diff(str(env_a), str(env_b), color=False, output_format="json")
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert any(item["key"] == "ADDED" for item in data)


def test_cmd_diff_redacts_secrets_in_output(env_a, env_b, capsys):
    cmd_diff(str(env_a), str(env_b), color=False, redact=True)
    captured = capsys.readouterr()
    assert "oldsecret" not in captured.out
    assert "newsecret" not in captured.out
