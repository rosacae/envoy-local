"""Tests for envoy_local.reorder and envoy_local.reorder_cli."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy_local.reorder import reorder_env_file
from envoy_local.reorder_cli import cmd_reorder
from envoy_local.parser import parse_env_file


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text(textwrap.dedent("""\
        ALPHA=1
        BETA=2
        GAMMA=3
        DELTA=4
    """))
    return f


def _keys(path: Path):
    return [e.key for e in parse_env_file(path).entries if e.key]


# ---------------------------------------------------------------------------
# reorder_env_file
# ---------------------------------------------------------------------------

def test_reorder_returns_ok(env_file: Path):
    result = reorder_env_file(env_file, ["GAMMA", "ALPHA", "BETA", "DELTA"])
    assert result.ok


def test_reorder_applies_key_order(env_file: Path):
    reorder_env_file(env_file, ["GAMMA", "ALPHA", "BETA", "DELTA"])
    assert _keys(env_file) == ["GAMMA", "ALPHA", "BETA", "DELTA"]


def test_reorder_trailing_keys_appended(env_file: Path):
    reorder_env_file(env_file, ["DELTA", "ALPHA"])
    keys = _keys(env_file)
    assert keys[0] == "DELTA"
    assert keys[1] == "ALPHA"
    # BETA and GAMMA must still be present after the ordered block
    assert set(keys[2:]) == {"BETA", "GAMMA"}


def test_reorder_reports_trailing_keys(env_file: Path):
    result = reorder_env_file(env_file, ["DELTA", "ALPHA"])
    assert set(result.trailing_keys) == {"BETA", "GAMMA"}


def test_reorder_reports_unmatched_keys(env_file: Path):
    result = reorder_env_file(env_file, ["ZETA", "ALPHA"])
    assert "ZETA" in result.unmatched_keys


def test_reorder_missing_file_returns_error(tmp_path: Path):
    result = reorder_env_file(tmp_path / "missing.env", ["A"])
    assert not result.ok
    assert result.error is not None


def test_reorder_writes_to_output_file(env_file: Path, tmp_path: Path):
    out = tmp_path / "out.env"
    reorder_env_file(env_file, ["BETA", "ALPHA"], output=out)
    assert out.exists()
    keys = _keys(out)
    assert keys[0] == "BETA"
    assert keys[1] == "ALPHA"


def test_reorder_original_unchanged_when_output_specified(env_file: Path, tmp_path: Path):
    original_keys = _keys(env_file)
    out = tmp_path / "out.env"
    reorder_env_file(env_file, ["DELTA", "GAMMA"], output=out)
    assert _keys(env_file) == original_keys


# ---------------------------------------------------------------------------
# cmd_reorder
# ---------------------------------------------------------------------------

def _ns(env_file: Path, keys, output=None, quiet=False):
    import argparse
    ns = argparse.Namespace(file=str(env_file), keys=keys, output=output, quiet=quiet)
    return ns


def test_cmd_reorder_returns_0(env_file: Path):
    assert cmd_reorder(_ns(env_file, ["BETA", "ALPHA"])) == 0


def test_cmd_reorder_missing_file_returns_2(tmp_path: Path):
    assert cmd_reorder(_ns(tmp_path / "nope.env", ["A"])) == 2


def test_cmd_reorder_no_keys_returns_1(env_file: Path):
    assert cmd_reorder(_ns(env_file, [])) == 1
