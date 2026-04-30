"""Tests for copy_key_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.copy_key_cli import cmd_copy_key, build_copy_key_parser


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    f = tmp_path / "source.env"
    f.write_text("API_KEY=abc123\nDEBUG=true\n")
    return f


@pytest.fixture()
def dest(tmp_path: Path) -> Path:
    return tmp_path / "dest.env"


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(dest_key=None, overwrite=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_copy_key_returns_0_on_success(source: Path, dest: Path) -> None:
    ns = _ns(source=str(source), dest=str(dest), key="API_KEY")
    assert cmd_copy_key(ns) == 0


def test_cmd_copy_key_key_appears_in_dest(source: Path, dest: Path) -> None:
    ns = _ns(source=str(source), dest=str(dest), key="API_KEY")
    cmd_copy_key(ns)
    assert "API_KEY=abc123" in dest.read_text()


def test_cmd_copy_key_with_dest_key(source: Path, dest: Path) -> None:
    ns = _ns(source=str(source), dest=str(dest), key="API_KEY", dest_key="NEW_KEY")
    rc = cmd_copy_key(ns)
    assert rc == 0
    text = dest.read_text()
    assert "NEW_KEY=abc123" in text
    assert "API_KEY" not in text


def test_cmd_copy_key_missing_source(tmp_path: Path, dest: Path) -> None:
    ns = _ns(source=str(tmp_path / "nope.env"), dest=str(dest), key="API_KEY")
    assert cmd_copy_key(ns) == 2


def test_cmd_copy_key_missing_key_returns_1(source: Path, dest: Path) -> None:
    ns = _ns(source=str(source), dest=str(dest), key="MISSING_KEY")
    assert cmd_copy_key(ns) == 1


def test_cmd_copy_key_no_overwrite_returns_1_when_exists(source: Path, dest: Path) -> None:
    dest.write_text("API_KEY=old\n")
    ns = _ns(source=str(source), dest=str(dest), key="API_KEY", overwrite=False)
    assert cmd_copy_key(ns) == 1


def test_cmd_copy_key_overwrite_succeeds(source: Path, dest: Path) -> None:
    dest.write_text("API_KEY=old\n")
    ns = _ns(source=str(source), dest=str(dest), key="API_KEY", overwrite=True)
    assert cmd_copy_key(ns) == 0
    assert "API_KEY=abc123" in dest.read_text()


def test_build_copy_key_parser_registers_subcommand() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_copy_key_parser(sub)
    args = parser.parse_args(["copy-key", "src.env", "dst.env", "MY_KEY"])
    assert args.key == "MY_KEY"
    assert args.dest_key is None
    assert args.overwrite is False
