"""Tests for envoy_local.syncer — sync_env_files behaviour."""

from pathlib import Path

import pytest

from envoy_local.syncer import SyncOptions, sync_env_files
from envoy_local.redactor import RedactionConfig


@pytest.fixture()
def tmp_source(tmp_path: Path) -> Path:
    p = tmp_path / "source.env"
    p.write_text(
        "APP_NAME=myapp\n"
        "SECRET_KEY=supersecret\n"
        "DEBUG=true\n"
        "# a comment\n"
        "DATABASE_PASSWORD=hunter2\n"
    )
    return p


@pytest.fixture()
def tmp_target(tmp_path: Path) -> Path:
    p = tmp_path / "target.env"
    p.write_text("APP_NAME=existing\nEXISTING_VAR=keep\n")
    return p


def test_sync_adds_new_keys(tmp_source: Path, tmp_path: Path) -> None:
    target = tmp_path / "new_target.env"
    opts = SyncOptions(redact_secrets=False)
    result = sync_env_files(tmp_source, target, opts)
    assert "APP_NAME" in result.added
    assert "DEBUG" in result.added
    assert target.exists()


def test_sync_skips_existing_keys(tmp_source: Path, tmp_target: Path) -> None:
    opts = SyncOptions(redact_secrets=False, overwrite_existing=False)
    result = sync_env_files(tmp_source, tmp_target, opts)
    assert "APP_NAME" in result.skipped
    content = tmp_target.read_text()
    assert "APP_NAME=existing" in content


def test_sync_overwrites_when_flag_set(tmp_source: Path, tmp_target: Path) -> None:
    opts = SyncOptions(redact_secrets=False, overwrite_existing=True)
    result = sync_env_files(tmp_source, tmp_target, opts)
    assert "APP_NAME" in result.overwritten
    content = tmp_target.read_text()
    assert "APP_NAME=myapp" in content


def test_sync_redacts_secrets(tmp_source: Path, tmp_path: Path) -> None:
    target = tmp_path / "redacted.env"
    cfg = RedactionConfig(secret_patterns=["SECRET", "PASSWORD"])
    opts = SyncOptions(redact_secrets=True, redaction_config=cfg)
    result = sync_env_files(tmp_source, target, opts)
    assert "SECRET_KEY" in result.redacted
    assert "DATABASE_PASSWORD" in result.redacted
    content = target.read_text()
    assert "supersecret" not in content
    assert "hunter2" not in content


def test_sync_dry_run_does_not_write(tmp_source: Path, tmp_path: Path) -> None:
    target = tmp_path / "dry.env"
    opts = SyncOptions(redact_secrets=False, dry_run=True)
    result = sync_env_files(tmp_source, target, opts)
    assert result.added  # changes detected
    assert not target.exists()  # but file not written


def test_sync_result_summary(tmp_source: Path, tmp_target: Path) -> None:
    opts = SyncOptions(redact_secrets=False)
    result = sync_env_files(tmp_source, tmp_target, opts)
    assert "added" in result.summary or "skipped" in result.summary


def test_sync_no_changes_summary() -> None:
    from envoy_local.syncer import SyncResult
    r = SyncResult()
    assert r.summary == "no changes"
