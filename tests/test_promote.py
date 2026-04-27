"""Tests for envoy_local.promote and envoy_local.promote_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.promote import PromoteOptions, promote_env
from envoy_local.promote_cli import cmd_promote


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    f = tmp_path / "source.env"
    f.write_text("DB_HOST=localhost\nDB_PASSWORD=s3cr3t\nAPP_ENV=staging\n")
    return f


@pytest.fixture()
def target(tmp_path: Path) -> Path:
    f = tmp_path / "target.env"
    f.write_text("APP_ENV=production\n")
    return f


def test_promote_adds_new_keys(source: Path, target: Path) -> None:
    opts = PromoteOptions()
    result = promote_env(source, target, opts)
    assert "DB_HOST" in result.promoted
    assert "DB_PASSWORD" in result.promoted
    # APP_ENV already exists and overwrite is False
    assert "APP_ENV" in result.skipped


def test_promote_overwrites_when_flag_set(source: Path, target: Path) -> None:
    opts = PromoteOptions(overwrite=True)
    result = promote_env(source, target, opts)
    assert "APP_ENV" in result.promoted
    assert "APP_ENV" not in result.skipped
    content = target.read_text()
    assert "APP_ENV=staging" in content


def test_promote_redacts_secrets(source: Path, target: Path) -> None:
    opts = PromoteOptions(overwrite=True, redact_secrets=True)
    result = promote_env(source, target, opts)
    assert "DB_PASSWORD" in result.redacted
    content = target.read_text()
    assert "***REDACTED***" in content
    assert "s3cr3t" not in content


def test_promote_dry_run_does_not_write(source: Path, target: Path) -> None:
    original = target.read_text()
    opts = PromoteOptions(dry_run=True)
    result = promote_env(source, target, opts)
    assert result.dry_run is True
    assert target.read_text() == original


def test_promote_specific_keys_only(source: Path, target: Path) -> None:
    opts = PromoteOptions(keys=["DB_HOST"])
    result = promote_env(source, target, opts)
    assert "DB_HOST" in result.promoted
    assert "DB_PASSWORD" not in result.promoted
    assert "DB_PASSWORD" not in result.skipped


def test_promote_creates_target_if_missing(tmp_path: Path, source: Path) -> None:
    new_target = tmp_path / "new_target.env"
    assert not new_target.exists()
    opts = PromoteOptions()
    ns = argparse.Namespace(
        source=str(source),
        target=str(new_target),
        overwrite=False,
        redact=False,
        dry_run=False,
        keys=None,
    )
    rc = cmd_promote(ns)
    assert rc == 0
    assert new_target.exists()


def test_cmd_promote_missing_source(tmp_path: Path) -> None:
    ns = argparse.Namespace(
        source=str(tmp_path / "nope.env"),
        target=str(tmp_path / "target.env"),
        overwrite=False,
        redact=False,
        dry_run=False,
        keys=None,
    )
    rc = cmd_promote(ns)
    assert rc == 2


def test_summary_contains_counts(source: Path, target: Path) -> None:
    opts = PromoteOptions()
    result = promote_env(source, target, opts)
    summary = result.summary()
    assert "Promoted" in summary
    assert "Skipped" in summary
