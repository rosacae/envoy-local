"""Tests for envoy_local.profile_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.profile import add_profile, load_manifest, set_active
from envoy_local.profile_cli import (
    cmd_profile_add,
    cmd_profile_list,
    cmd_profile_remove,
    cmd_profile_show,
    cmd_profile_use,
)


def _ns(base_dir: Path, **kwargs) -> argparse.Namespace:
    return argparse.Namespace(base_dir=str(base_dir), **kwargs)


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_cmd_profile_add_returns_0(base_dir):
    ns = _ns(base_dir, name="dev", path=".env.dev", description="Dev env")
    assert cmd_profile_add(ns) == 0


def test_cmd_profile_add_persists(base_dir):
    ns = _ns(base_dir, name="dev", path=".env.dev", description="")
    cmd_profile_add(ns)
    manifest = load_manifest(base_dir)
    assert "dev" in manifest.profiles


def test_cmd_profile_remove_returns_0(base_dir):
    add_profile(base_dir, "dev", ".env.dev")
    ns = _ns(base_dir, name="dev")
    assert cmd_profile_remove(ns) == 0


def test_cmd_profile_remove_returns_1_when_missing(base_dir):
    ns = _ns(base_dir, name="ghost")
    assert cmd_profile_remove(ns) == 1


def test_cmd_profile_use_returns_0(base_dir):
    add_profile(base_dir, "prod", ".env.prod")
    ns = _ns(base_dir, name="prod")
    assert cmd_profile_use(ns) == 0


def test_cmd_profile_use_returns_1_when_missing(base_dir):
    ns = _ns(base_dir, name="nowhere")
    assert cmd_profile_use(ns) == 1


def test_cmd_profile_list_returns_0_with_profiles(base_dir, capsys):
    add_profile(base_dir, "dev", ".env.dev")
    add_profile(base_dir, "prod", ".env.prod")
    ns = _ns(base_dir)
    assert cmd_profile_list(ns) == 0
    out = capsys.readouterr().out
    assert "dev" in out
    assert "prod" in out


def test_cmd_profile_list_shows_active_marker(base_dir, capsys):
    add_profile(base_dir, "dev", ".env.dev")
    set_active(base_dir, "dev")
    ns = _ns(base_dir)
    cmd_profile_list(ns)
    out = capsys.readouterr().out
    assert "(active)" in out


def test_cmd_profile_list_empty(base_dir, capsys):
    ns = _ns(base_dir)
    assert cmd_profile_list(ns) == 0
    out = capsys.readouterr().out
    assert "No profiles" in out


def test_cmd_profile_show_returns_0_when_active(base_dir, capsys):
    add_profile(base_dir, "staging", ".env.staging")
    set_active(base_dir, "staging")
    ns = _ns(base_dir)
    assert cmd_profile_show(ns) == 0
    out = capsys.readouterr().out
    assert "staging" in out


def test_cmd_profile_show_returns_1_when_no_active(base_dir):
    ns = _ns(base_dir)
    assert cmd_profile_show(ns) == 1
