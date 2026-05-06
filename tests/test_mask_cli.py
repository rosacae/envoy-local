"""Tests for envoy_local.mask_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.mask_cli import cmd_mask, build_mask_parser


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "API_KEY=supersecretvalue\n"
        "DB_PASSWORD=hunter2\n"
        "PORT=9000\n"
    )
    return p


def _ns(env_file: Path, **kwargs) -> argparse.Namespace:
    defaults = dict(
        file=str(env_file),
        visible=4,
        char="*",
        mask_all=False,
        keys=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_mask_returns_0(env_file: Path) -> None:
    assert cmd_mask(_ns(env_file)) == 0


def test_cmd_mask_missing_file(tmp_path: Path) -> None:
    ns = _ns(tmp_path / "missing.env")
    assert cmd_mask(ns) == 2


def test_cmd_mask_output_hides_secret(env_file: Path, capsys) -> None:
    cmd_mask(_ns(env_file, keys=["API_KEY"]))
    out = capsys.readouterr().out
    assert "supersecretvalue" not in out
    assert "API_KEY" in out


def test_cmd_mask_plain_key_unchanged(env_file: Path, capsys) -> None:
    cmd_mask(_ns(env_file, keys=["API_KEY"]))
    out = capsys.readouterr().out
    assert "PORT=9000" in out


def test_cmd_mask_mask_all_hides_port(env_file: Path, capsys) -> None:
    cmd_mask(_ns(env_file, mask_all=True))
    out = capsys.readouterr().out
    assert "9000" not in out


def test_cmd_mask_custom_visible(env_file: Path, capsys) -> None:
    cmd_mask(_ns(env_file, keys=["API_KEY"], visible=2))
    out = capsys.readouterr().out
    # Only first 2 chars of value should be visible
    assert "su" in out
    assert "supersecretvalue" not in out


def test_build_mask_parser_registers_subcommand() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    build_mask_parser(sub)
    ns = parser.parse_args(["mask", "some.env"])
    assert ns.file == "some.env"
