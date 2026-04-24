"""Tests for parser, redactor, and serializer modules."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envoy_local.parser import parse_env_lines, parse_env_file, EnvEntry
from envoy_local.redactor import Redactor, RedactionConfig
from envoy_local.serializer import entry_to_line, entries_to_text, write_env_file, merge_entries


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

SAMPLE_ENV = textwrap.dedent("""\
    # This is a comment
    APP_NAME=envoy-local
    DEBUG=true
    DATABASE_URL="postgres://user:pass@localhost/db"
    SECRET_KEY=supersecret123
    EMPTY=
    INLINE=hello # world
""")


def _lines(text: str):
    return iter(text.splitlines(keepends=True))


def test_parse_basic_entries():
    result = parse_env_lines(_lines(SAMPLE_ENV))
    assert result.errors == []
    d = result.as_dict
    assert d["APP_NAME"] == "envoy-local"
    assert d["DEBUG"] == "true"
    assert d["EMPTY"] == ""


def test_parse_quoted_value():
    result = parse_env_lines(_lines(SAMPLE_ENV))
    entry = next(e for e in result.entries if e.key == "DATABASE_URL")
    assert entry.is_quoted is True
    assert "postgres://" in entry.value


def test_parse_inline_comment_stripped():
    result = parse_env_lines(_lines(SAMPLE_ENV))
    d = result.as_dict
    assert d["INLINE"] == "hello"


def test_parse_invalid_line():
    result = parse_env_lines(iter(["NOT VALID LINE\n"]))
    assert len(result.errors) == 1


def test_parse_env_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_env_file(tmp_path / "missing.env")


def test_parse_env_file_roundtrip(tmp_path):
    env_file = tmp_path / ".env"
    env_file.write_text(SAMPLE_ENV, encoding="utf-8")
    result = parse_env_file(env_file)
    assert "APP_NAME" in result.as_dict


# ---------------------------------------------------------------------------
# Redactor tests
# ---------------------------------------------------------------------------

def test_redact_secret_key():
    r = Redactor()
    assert r.redact_value("SECRET_KEY", "abc123") == "**REDACTED**"


def test_redact_non_secret_key():
    r = Redactor()
    assert r.redact_value("APP_NAME", "envoy") == "envoy"


def test_redact_short_value_not_redacted():
    r = Redactor()
    assert r.redact_value("SECRET_KEY", "ab") == "ab"


def test_redact_dict():
    r = Redactor()
    env = {"APP_NAME": "envoy", "API_KEY": "tok_abc123", "DEBUG": "true"}
    out = r.redact_dict(env)
    assert out["APP_NAME"] == "envoy"
    assert out["API_KEY"] == "**REDACTED**"


def test_custom_placeholder():
    cfg = RedactionConfig(placeholder="***")
    r = Redactor(cfg)
    assert r.redact_value("PASSWORD", "hunter2") == "***"


# ---------------------------------------------------------------------------
# Serializer tests
# ---------------------------------------------------------------------------

def test_entry_to_line_unquoted():
    e = EnvEntry(key="FOO", value="bar", raw_line="FOO=bar", line_number=1)
    assert entry_to_line(e) == "FOO=bar"


def test_entry_to_line_quoted():
    e = EnvEntry(key="URL", value="http://x", raw_line='URL="http://x"', line_number=1, is_quoted=True)
    assert entry_to_line(e) == 'URL="http://x"'


def test_entries_to_text():
    entries = [
        EnvEntry(key="A", value="1", raw_line="A=1", line_number=1),
        EnvEntry(key="B", value="2", raw_line="B=2", line_number=2),
    ]
    text = entries_to_text(entries)
    assert text == "A=1\nB=2\n"


def test_write_env_file(tmp_path):
    entries = [EnvEntry(key="X", value="y", raw_line="X=y", line_number=1)]
    dest = tmp_path / "out.env"
    write_env_file(dest, entries)
    assert dest.read_text() == "X=y\n"


def test_write_env_file_no_overwrite(tmp_path):
    dest = tmp_path / "out.env"
    dest.write_text("existing")
    entries = [EnvEntry(key="X", value="y", raw_line="X=y", line_number=1)]
    with pytest.raises(FileExistsError):
        write_env_file(dest, entries, overwrite=False)


def test_merge_entries_override():
    base = [EnvEntry(key="A", value="1", raw_line="A=1", line_number=1)]
    override = [EnvEntry(key="A", value="99", raw_line="A=99", line_number=1)]
    merged = merge_entries(base, override)
    assert len(merged) == 1
    assert merged[0].value == "99"
