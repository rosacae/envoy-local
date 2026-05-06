"""Tests for envoy_local.patch_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.patch_cli import cmd_patch, build_patch_parser
from envoy_local.parser import parse_env_file


@pytest.fixture
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("FOO=bar\nBAZ=qux\n")
    return f


def _ns(env_file: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(
        file=str(env_file),
        set=None,
        delete=None,
        no_overwrite=False,
        ignore_frozen=True,
        verbose=False,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _keys(path: Path) -> dict[str, str]:
    result = parse_env_file(path)
    return {e.key: e.value for e in result.entries if e.key}


def test_cmd_patch_returns_0_on_success(env_file: Path) -> None:
    ns = _ns(env_file, set=["NEW=val"])
    assert cmd_patch(ns) == 0


def test_cmd_patch_adds_key(env_file: Path) -> None:
    ns = _ns(env_file, set=["ADDED=hello"])
    cmd_patch(ns)
    assert _keys(env_file).get("ADDED") == "hello"


def test_cmd_patch_updates_key(env_file: Path) -> None:
    ns = _ns(env_file, set=["FOO=updated"])
    cmd_patch(ns)
    assert _keys(env_file)["FOO"] == "updated"


def test_cmd_patch_deletes_key(env_file: Path) -> None:
    ns = _ns(env_file, delete=["BAZ"])
    cmd_patch(ns)
    assert "BAZ" not in _keys(env_file)


def test_cmd_patch_returns_2_on_missing_file(tmp_path: Path) -> None:
    ns = _ns(tmp_path / "missing.env", set=["X=1"])
    assert cmd_patch(ns) == 2


def test_cmd_patch_returns_2_on_bad_set_pair(env_file: Path) -> None:
    ns = _ns(env_file, set=["NOEQUALSSIGN"])
    assert cmd_patch(ns) == 2


def test_cmd_patch_no_overwrite_skips_existing(env_file: Path) -> None:
    ns = _ns(env_file, set=["FOO=changed"], no_overwrite=True)
    cmd_patch(ns)
    assert _keys(env_file)["FOO"] == "bar"


def test_build_patch_parser_registers_subcommand() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_patch_parser(sub)
    args = parser.parse_args(["patch", "some.env", "--set", "K=V"])
    assert args.file == "some.env"
    assert args.set == ["K=V"]
