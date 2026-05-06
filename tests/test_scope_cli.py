"""Tests for envoy_local.scope_cli."""
from pathlib import Path
import argparse
import pytest

from envoy_local.scope_cli import cmd_scope_add, cmd_scope_remove, cmd_scope_list
from envoy_local.scope import keys_in_scope, add_key_to_scope


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"dir": ".", "scope": "prod", "key": "DB_URL"}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_scope_add_returns_0(base_dir):
    ns = _ns(dir=str(base_dir))
    assert cmd_scope_add(ns) == 0


def test_cmd_scope_add_persists(base_dir):
    ns = _ns(dir=str(base_dir), scope="prod", key="API_KEY")
    cmd_scope_add(ns)
    assert "API_KEY" in keys_in_scope(base_dir, "prod")


def test_cmd_scope_add_duplicate_returns_0(base_dir, capsys):
    ns = _ns(dir=str(base_dir))
    cmd_scope_add(ns)
    rc = cmd_scope_add(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "already" in out


def test_cmd_scope_remove_returns_0_when_present(base_dir):
    add_key_to_scope(base_dir, "prod", "DB_URL")
    ns = _ns(dir=str(base_dir))
    assert cmd_scope_remove(ns) == 0


def test_cmd_scope_remove_returns_1_when_absent(base_dir):
    ns = _ns(dir=str(base_dir))
    assert cmd_scope_remove(ns) == 1


def test_cmd_scope_list_no_scope_arg(base_dir, capsys):
    add_key_to_scope(base_dir, "staging", "X")
    add_key_to_scope(base_dir, "prod", "Y")
    ns = _ns(dir=str(base_dir), scope=None)
    rc = cmd_scope_list(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "prod" in out
    assert "staging" in out


def test_cmd_scope_list_with_scope_arg(base_dir, capsys):
    add_key_to_scope(base_dir, "prod", "DB_URL")
    add_key_to_scope(base_dir, "prod", "SECRET")
    ns = _ns(dir=str(base_dir), scope="prod")
    rc = cmd_scope_list(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "DB_URL" in out
    assert "SECRET" in out


def test_cmd_scope_list_empty_scope_prints_message(base_dir, capsys):
    ns = _ns(dir=str(base_dir), scope="nonexistent")
    rc = cmd_scope_list(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "empty" in out or "does not exist" in out
