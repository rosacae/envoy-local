"""Tests for envoy_local.interpolate."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy_local.interpolate import interpolate
from envoy_local.interpolate_cli import cmd_interpolate
from envoy_local.parser import parse_env_text


def _parse(text: str):
    return parse_env_text(textwrap.dedent(text))


# ---------------------------------------------------------------------------
# interpolate() unit tests
# ---------------------------------------------------------------------------

def test_brace_reference_resolved():
    pr = _parse("BASE=/app\nFULL=${BASE}/bin\n")
    result = interpolate(pr)
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["FULL"] == "/app/bin"
    assert result.ok


def test_bare_reference_resolved():
    pr = _parse("HOST=localhost\nURL=http://$HOST:8080\n")
    result = interpolate(pr)
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["URL"] == "http://localhost:8080"


def test_unresolved_reference_kept_intact():
    pr = _parse("URL=http://${HOST}/path\n")
    result = interpolate(pr)
    values = {e.key: e.value for e in result.entries if e.key}
    assert "${HOST}" in values["URL"]
    assert "HOST" in result.unresolved
    assert not result.ok


def test_extra_context_provides_resolution():
    pr = _parse("FULL=${BASE}/bin\n")
    result = interpolate(pr, extra_context={"BASE": "/usr"})
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["FULL"] == "/usr/bin"
    assert result.ok


def test_chained_references():
    pr = _parse("A=hello\nB=${A}_world\nC=${B}!\n")
    result = interpolate(pr)
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["B"] == "hello_world"
    assert values["C"] == "hello_world!"


def test_no_references_unchanged():
    pr = _parse("FOO=bar\nBAZ=qux\n")
    result = interpolate(pr)
    values = {e.key: e.value for e in result.entries if e.key}
    assert values["FOO"] == "bar"
    assert values["BAZ"] == "qux"
    assert result.ok


def test_entries_without_key_passed_through():
    pr = _parse("# just a comment\nFOO=bar\n")
    result = interpolate(pr)
    assert len(result.entries) == len(pr.entries)


# ---------------------------------------------------------------------------
# cmd_interpolate CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text("BASE=/app\nFULL=${BASE}/bin\n")
    return f


def test_cmd_interpolate_returns_0(env_file: Path, capsys):
    import argparse
    ns = argparse.Namespace(file=str(env_file), output=None, strict=False, ignore_missing=False)
    rc = cmd_interpolate(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "/app/bin" in out


def test_cmd_interpolate_missing_file_returns_2(tmp_path: Path):
    import argparse
    ns = argparse.Namespace(
        file=str(tmp_path / "missing.env"), output=None, strict=False, ignore_missing=False
    )
    assert cmd_interpolate(ns) == 2


def test_cmd_interpolate_strict_unresolved_returns_1(tmp_path: Path):
    import argparse
    f = tmp_path / ".env"
    f.write_text("URL=http://${HOST}/path\n")
    ns = argparse.Namespace(file=str(f), output=None, strict=True, ignore_missing=False)
    assert cmd_interpolate(ns) == 1


def test_cmd_interpolate_writes_output_file(env_file: Path, tmp_path: Path):
    import argparse
    out = tmp_path / "result.env"
    ns = argparse.Namespace(file=str(env_file), output=str(out), strict=False, ignore_missing=False)
    rc = cmd_interpolate(ns)
    assert rc == 0
    assert out.exists()
    assert "/app/bin" in out.read_text()
