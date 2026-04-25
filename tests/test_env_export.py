"""Tests for envoy_local.env_export."""
from __future__ import annotations

import json
import textwrap

import pytest

from envoy_local.env_export import (
    ExportFormat,
    export_docker,
    export_entries,
    export_json,
    export_shell,
    export_yaml,
)
from envoy_local.parser import EnvEntry, ParseResult
from envoy_local.redactor import RedactionConfig, Redactor


def _result(*pairs: tuple[str, str]) -> ParseResult:
    entries = [EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}") for k, v in pairs]
    return ParseResult(entries=entries, errors=[])


# ---------------------------------------------------------------------------
# shell
# ---------------------------------------------------------------------------

def test_export_shell_basic():
    r = _result(("FOO", "bar"), ("BAZ", "qux"))
    out = export_shell(r.entries)
    assert 'export FOO="bar"' in out
    assert 'export BAZ="qux"' in out


def test_export_shell_escapes_double_quotes():
    r = _result(("MSG", 'say "hello"'))
    out = export_shell(r.entries)
    assert 'export MSG="say \\"hello\\""' in out


def test_export_shell_skips_keyless_entries():
    entries = [EnvEntry(key="", value="", comment="# comment", raw="# comment")]
    out = export_shell(entries)
    assert out == ""


# ---------------------------------------------------------------------------
# json
# ---------------------------------------------------------------------------

def test_export_json_valid_json():
    r = _result(("A", "1"), ("B", "2"))
    out = export_json(r.entries)
    data = json.loads(out)
    assert data == {"A": "1", "B": "2"}


def test_export_json_empty():
    out = export_json([])
    assert json.loads(out) == {}


# ---------------------------------------------------------------------------
# yaml
# ---------------------------------------------------------------------------

def test_export_yaml_simple_values():
    r = _result(("HOST", "localhost"), ("PORT", "5432"))
    out = export_yaml(r.entries)
    assert "HOST: localhost" in out
    assert "PORT: 5432" in out


def test_export_yaml_quotes_special_chars():
    r = _result(("URL", "http://example.com:8080"))
    out = export_yaml(r.entries)
    assert 'URL: "http://example.com:8080"' in out


# ---------------------------------------------------------------------------
# docker
# ---------------------------------------------------------------------------

def test_export_docker_format():
    r = _result(("X", "1"), ("Y", "2"))
    out = export_docker(r.entries)
    assert "--env X=1" in out
    assert "--env Y=2" in out


# ---------------------------------------------------------------------------
# redaction
# ---------------------------------------------------------------------------

def test_export_redacts_secrets():
    cfg = RedactionConfig()
    redactor = Redactor(cfg)
    r = _result(("API_KEY", "supersecret"), ("HOST", "localhost"))
    out = export_shell(r.entries, redactor=redactor)
    assert "supersecret" not in out
    assert "localhost" in out


# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------

def test_export_entries_dispatches_json():
    r = _result(("K", "v"))
    out = export_entries(r, ExportFormat.JSON)
    assert json.loads(out) == {"K": "v"}


def test_export_entries_dispatches_shell():
    r = _result(("K", "v"))
    out = export_entries(r, ExportFormat.SHELL)
    assert 'export K="v"' in out
