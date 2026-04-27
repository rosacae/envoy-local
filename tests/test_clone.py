"""Tests for envoy_local.clone"""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy_local.clone import CloneOptions, clone_env_file
from envoy_local.parser import parse_env_file
from envoy_local.encrypt import generate_key, is_encrypted


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    f = tmp_path / "source.env"
    f.write_text(
        "APP_NAME=myapp\n"
        "SECRET_KEY=supersecret\n"
        "DATABASE_URL=postgres://localhost/db\n"
        "# a comment\n"
    )
    return f


def test_clone_creates_destination(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest.env"
    result = clone_env_file(source, dest)
    assert dest.exists()
    assert result.skipped is False
    assert result.total == 4  # 3 entries + 1 comment/blank


def test_clone_content_matches_source(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest.env"
    clone_env_file(source, dest)
    src_dict = {e.key: e.value for e in parse_env_file(source).entries if e.key}
    dst_dict = {e.key: e.value for e in parse_env_file(dest).entries if e.key}
    assert src_dict == dst_dict


def test_clone_redacts_secrets(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest.env"
    opts = CloneOptions(redact_secrets=True, redact_placeholder="***")
    result = clone_env_file(source, dest, opts)
    entries = {e.key: e.value for e in parse_env_file(dest).entries if e.key}
    assert entries["SECRET_KEY"] == "***"
    assert entries["APP_NAME"] == "myapp"  # non-secret untouched
    assert result.redacted >= 1


def test_clone_skips_when_dest_exists_no_overwrite(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest.env"
    dest.write_text("EXISTING=1\n")
    result = clone_env_file(source, dest)
    assert result.skipped is True
    assert dest.read_text() == "EXISTING=1\n"  # untouched


def test_clone_overwrites_when_flag_set(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest.env"
    dest.write_text("EXISTING=1\n")
    opts = CloneOptions(overwrite=True)
    result = clone_env_file(source, dest, opts)
    assert result.skipped is False
    entries = {e.key: e.value for e in parse_env_file(dest).entries if e.key}
    assert "APP_NAME" in entries


def test_clone_encrypts_plain_values(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest.env"
    key = generate_key()
    opts = CloneOptions(encrypt_key=key)
    result = clone_env_file(source, dest, opts)
    entries = {e.key: e.value for e in parse_env_file(dest).entries if e.key}
    assert all(is_encrypted(v) for v in entries.values() if v)
    assert result.encrypted >= 1


def test_clone_summary_no_skip(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest.env"
    result = clone_env_file(source, dest)
    summary = result.summary()
    assert str(dest) in summary
    assert "Cloned" in summary


def test_clone_summary_skipped(source: Path, tmp_path: Path) -> None:
    dest = tmp_path / "dest.env"
    dest.write_text("X=1\n")
    result = clone_env_file(source, dest)
    assert "Skipped" in result.summary()
