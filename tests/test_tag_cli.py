"""Tests for envoy_local.tag_cli."""
from __future__ import annotations

import argparse
from pathlib import Path
import pytest

from envoy_local.tag_cli import cmd_tag_add, cmd_tag_remove, cmd_tag_list
from envoy_local.tag import load_tags


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("API_KEY=secret\nDB_URL=postgres://localhost/db\n")
    return p


def _ns(env_file: Path, **kwargs: object) -> argparse.Namespace:
    return argparse.Namespace(env_file=str(env_file), **kwargs)


def test_cmd_tag_add_returns_0(env_file: Path) -> None:
    ns = _ns(env_file, key="API_KEY", tag="secret")
    assert cmd_tag_add(ns) == 0


def test_cmd_tag_add_persists(env_file: Path) -> None:
    ns = _ns(env_file, key="API_KEY", tag="secret")
    cmd_tag_add(ns)
    manifest = load_tags(env_file.parent)
    assert "secret" in manifest.tags.get("API_KEY", [])


def test_cmd_tag_add_duplicate_returns_0(env_file: Path) -> None:
    ns = _ns(env_file, key="API_KEY", tag="secret")
    cmd_tag_add(ns)
    assert cmd_tag_add(ns) == 0


def test_cmd_tag_remove_returns_0_when_present(env_file: Path) -> None:
    add_ns = _ns(env_file, key="API_KEY", tag="secret")
    cmd_tag_add(add_ns)
    rm_ns = _ns(env_file, key="API_KEY", tag="secret")
    assert cmd_tag_remove(rm_ns) == 0


def test_cmd_tag_remove_returns_1_when_absent(env_file: Path) -> None:
    ns = _ns(env_file, key="API_KEY", tag="ghost")
    assert cmd_tag_remove(ns) == 1


def test_cmd_tag_list_all_returns_0(env_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cmd_tag_add(_ns(env_file, key="API_KEY", tag="secret"))
    cmd_tag_add(_ns(env_file, key="DB_URL", tag="infra"))
    ns = _ns(env_file, key="", tag="")
    assert cmd_tag_list(ns) == 0
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "DB_URL" in out


def test_cmd_tag_list_by_key(env_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cmd_tag_add(_ns(env_file, key="API_KEY", tag="secret"))
    ns = _ns(env_file, key="API_KEY", tag="")
    cmd_tag_list(ns)
    out = capsys.readouterr().out
    assert "secret" in out


def test_cmd_tag_list_by_tag(env_file: Path, capsys: pytest.CaptureFixture[str]) -> None:
    cmd_tag_add(_ns(env_file, key="API_KEY", tag="required"))
    cmd_tag_add(_ns(env_file, key="DB_URL", tag="required"))
    ns = _ns(env_file, key="", tag="required")
    cmd_tag_list(ns)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "DB_URL" in out
