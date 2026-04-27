"""Tests for envoy_local.cascade and envoy_local.cascade_cli."""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path

import pytest

from envoy_local.cascade import CascadeOptions, cascade_env_files
from envoy_local.cascade_cli import cmd_cascade


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


# ---------------------------------------------------------------------------
# cascade_env_files
# ---------------------------------------------------------------------------

def test_cascade_single_file(base_dir):
    f = _write(base_dir / "a.env", "FOO=1\nBAR=2\n")
    result = cascade_env_files(CascadeOptions(files=[f]))
    assert result.as_dict() == {"FOO": "1", "BAR": "2"}
    assert f in result.loaded


def test_cascade_later_file_overrides(base_dir):
    a = _write(base_dir / "a.env", "FOO=base\nSHARED=a\n")
    b = _write(base_dir / "b.env", "SHARED=b\nEXTRA=yes\n")
    result = cascade_env_files(CascadeOptions(files=[a, b]))
    d = result.as_dict()
    assert d["FOO"] == "base"
    assert d["SHARED"] == "b"
    assert d["EXTRA"] == "yes"


def test_cascade_three_files_priority(base_dir):
    a = _write(base_dir / "a.env", "KEY=a\n")
    b = _write(base_dir / "b.env", "KEY=b\n")
    c = _write(base_dir / "c.env", "KEY=c\n")
    result = cascade_env_files(CascadeOptions(files=[a, b, c]))
    assert result.as_dict()["KEY"] == "c"


def test_cascade_missing_file_raises(base_dir):
    missing = base_dir / "ghost.env"
    with pytest.raises(FileNotFoundError):
        cascade_env_files(CascadeOptions(files=[missing]))


def test_cascade_ignore_missing_skips_file(base_dir):
    present = _write(base_dir / "real.env", "X=1\n")
    missing = base_dir / "ghost.env"
    result = cascade_env_files(
        CascadeOptions(files=[missing, present], ignore_missing=True)
    )
    assert result.as_dict() == {"X": "1"}
    assert missing in result.skipped
    assert present in result.loaded


def test_cascade_summary_contains_key_count(base_dir):
    f = _write(base_dir / "a.env", "A=1\nB=2\n")
    result = cascade_env_files(CascadeOptions(files=[f]))
    assert "keys=2" in result.summary()


# ---------------------------------------------------------------------------
# cmd_cascade
# ---------------------------------------------------------------------------

def _ns(files, fmt="env", ignore_missing=False, summary=False):
    ns = argparse.Namespace()
    ns.files = [str(f) for f in files]
    ns.format = fmt
    ns.ignore_missing = ignore_missing
    ns.summary = summary
    return ns


def test_cmd_cascade_returns_0_on_success(base_dir):
    f = _write(base_dir / "a.env", "FOO=bar\n")
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_cascade(_ns([f]), out=out, err=err)
    assert rc == 0
    assert "FOO=bar" in out.getvalue()


def test_cmd_cascade_json_format(base_dir):
    f = _write(base_dir / "a.env", "FOO=bar\n")
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_cascade(_ns([f], fmt="json"), out=out, err=err)
    assert rc == 0
    data = json.loads(out.getvalue())
    assert data["FOO"] == "bar"


def test_cmd_cascade_returns_2_on_missing(base_dir):
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_cascade(_ns([base_dir / "nope.env"]), out=out, err=err)
    assert rc == 2


def test_cmd_cascade_returns_2_no_files():
    out, err = io.StringIO(), io.StringIO()
    rc = cmd_cascade(_ns([]), out=out, err=err)
    assert rc == 2


def test_cmd_cascade_summary_written_to_stderr(base_dir):
    f = _write(base_dir / "a.env", "K=v\n")
    out, err = io.StringIO(), io.StringIO()
    cmd_cascade(_ns([f], summary=True), out=out, err=err)
    assert "keys=" in err.getvalue()
