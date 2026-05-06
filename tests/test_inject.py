"""Tests for envoy_local.inject and envoy_local.inject_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.inject import inject_keys
from envoy_local.inject_cli import cmd_inject
from envoy_local.parser import parse_env_file


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nBAZ=qux\n")
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = {"no_overwrite": False, "no_create": False}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# --- inject_keys unit tests ---

def test_inject_adds_new_key(env_file: Path) -> None:
    result = inject_keys(env_file, {"NEW_KEY": "hello"})
    assert result.ok
    assert "NEW_KEY" in result.added
    parsed = parse_env_file(env_file).as_dict()
    assert parsed["NEW_KEY"] == "hello"


def test_inject_updates_existing_key(env_file: Path) -> None:
    result = inject_keys(env_file, {"FOO": "newval"})
    assert result.ok
    assert "FOO" in result.updated
    assert parse_env_file(env_file).as_dict()["FOO"] == "newval"


def test_inject_skips_existing_when_no_overwrite(env_file: Path) -> None:
    result = inject_keys(env_file, {"FOO": "changed"}, overwrite=False)
    assert result.ok
    assert "FOO" in result.skipped
    assert parse_env_file(env_file).as_dict()["FOO"] == "bar"


def test_inject_creates_file_when_missing(tmp_path: Path) -> None:
    target = tmp_path / "new.env"
    result = inject_keys(target, {"KEY": "val"}, create=True)
    assert result.ok
    assert target.exists()
    assert parse_env_file(target).as_dict()["KEY"] == "val"


def test_inject_returns_error_when_no_create_and_missing(tmp_path: Path) -> None:
    target = tmp_path / "ghost.env"
    result = inject_keys(target, {"KEY": "val"}, create=False)
    assert not result.ok
    assert "not found" in result.error.lower()


def test_inject_empty_pairs_is_noop(env_file: Path) -> None:
    before = env_file.read_text()
    result = inject_keys(env_file, {})
    assert result.ok
    assert env_file.read_text() == before


def test_inject_preserves_existing_keys(env_file: Path) -> None:
    inject_keys(env_file, {"EXTRA": "1"})
    d = parse_env_file(env_file).as_dict()
    assert d["FOO"] == "bar"
    assert d["BAZ"] == "qux"
    assert d["EXTRA"] == "1"


# --- cmd_inject CLI tests ---

def test_cmd_inject_returns_0(env_file: Path) -> None:
    ns = _ns(file=str(env_file), pairs=["NEWK=newv"])
    assert cmd_inject(ns) == 0


def test_cmd_inject_key_appears_in_file(env_file: Path) -> None:
    ns = _ns(file=str(env_file), pairs=["CLI_KEY=cli_val"])
    cmd_inject(ns)
    assert parse_env_file(env_file).as_dict()["CLI_KEY"] == "cli_val"


def test_cmd_inject_bad_pair_returns_1(env_file: Path) -> None:
    ns = _ns(file=str(env_file), pairs=["NOEQUALSSIGN"])
    assert cmd_inject(ns) == 1


def test_cmd_inject_missing_file_no_create_returns_1(tmp_path: Path) -> None:
    ns = _ns(file=str(tmp_path / "nope.env"), pairs=["K=v"], no_create=True)
    assert cmd_inject(ns) == 1
