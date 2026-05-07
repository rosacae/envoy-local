"""Tests for envoy_local.resolve and envoy_local.resolve_cli."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy_local.resolve import resolve_env_file
from envoy_local.resolve_cli import cmd_resolve, build_resolve_parser
from envoy_local.parser import parse_env_file


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "BASE_URL=https://example.com\n"
        "API_URL=${BASE_URL}/api\n"
        "PLAIN=hello\n"
    )
    return p


def test_resolve_replaces_brace_reference(env_file: Path) -> None:
    result = resolve_env_file(env_file)
    assert result.ok
    assert "API_URL" in result.resolved_keys


def test_resolve_value_is_expanded(env_file: Path) -> None:
    resolve_env_file(env_file)
    pr = parse_env_file(env_file)
    d = {e.key: e.value for e in pr.entries if e.key}
    assert d["API_URL"] == "https://example.com/api"


def test_resolve_plain_key_not_in_resolved(env_file: Path) -> None:
    result = resolve_env_file(env_file)
    assert "PLAIN" not in result.resolved_keys


def test_resolve_missing_file_returns_error(tmp_path: Path) -> None:
    result = resolve_env_file(tmp_path / "missing.env")
    assert not result.ok
    assert "not found" in result.error


def test_resolve_writes_to_output_file(env_file: Path, tmp_path: Path) -> None:
    out = tmp_path / "resolved.env"
    result = resolve_env_file(env_file, output=out)
    assert result.ok
    assert out.exists()
    content = out.read_text()
    assert "https://example.com/api" in content


def test_resolve_extra_context_used(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("FULL_URL=${HOST}/path\n")
    result = resolve_env_file(p, extra_context={"HOST": "http://localhost"})
    assert result.ok
    assert "FULL_URL" in result.resolved_keys
    pr = parse_env_file(p)
    d = {e.key: e.value for e in pr.entries if e.key}
    assert d["FULL_URL"] == "http://localhost/path"


def test_resolve_strict_fails_on_unresolved(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("URL=${UNDEFINED_VAR}/path\n")
    result = resolve_env_file(p, allow_partial=False)
    assert not result.ok
    assert "unresolved" in result.error


def test_resolve_partial_allows_unresolved(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("URL=${UNDEFINED_VAR}/path\n")
    result = resolve_env_file(p, allow_partial=True)
    assert result.ok
    assert "URL" in result.unresolved_keys


# --- CLI tests ---


@pytest.fixture()
def _ns_base(env_file: Path) -> object:
    import argparse
    ns = argparse.Namespace(file=str(env_file), output=None, context=None, strict=False)
    return ns


def test_cmd_resolve_returns_0(env_file: Path, _ns_base: object) -> None:
    assert cmd_resolve(_ns_base) == 0  # type: ignore[arg-type]


def test_cmd_resolve_missing_file_returns_2(tmp_path: Path) -> None:
    import argparse
    ns = argparse.Namespace(file=str(tmp_path / "no.env"), output=None, context=None, strict=False)
    assert cmd_resolve(ns) == 2


def test_cmd_resolve_strict_returns_2_on_unresolved(tmp_path: Path) -> None:
    import argparse
    p = tmp_path / ".env"
    p.write_text("URL=${NOPE}\n")
    ns = argparse.Namespace(file=str(p), output=None, context=None, strict=True)
    assert cmd_resolve(ns) == 2


def test_build_resolve_parser_registers_subcommand() -> None:
    import argparse
    root = argparse.ArgumentParser()
    sub = root.add_subparsers()
    build_resolve_parser(sub)
    args = root.parse_args(["resolve", "some.env"])
    assert args.file == "some.env"
