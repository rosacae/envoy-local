"""Tests for promote_with_audit integration."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_local.promote import PromoteOptions
from envoy_local.promote_audit import promote_with_audit
from envoy_local.audit import load_log, _audit_path


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    p = tmp_path / "source.env"
    p.write_text("DB_HOST=localhost\nDB_PASS=secret\nDEBUG=true\n")
    return p


@pytest.fixture()
def target(tmp_path: Path) -> Path:
    p = tmp_path / "target.env"
    p.write_text("DEBUG=false\n")
    return p


def test_promote_with_audit_returns_promote_result(source: Path, target: Path, tmp_path: Path) -> None:
    opts = PromoteOptions(overwrite=False, redact_secrets=False)
    result = promote_with_audit(source, target, opts, log_dir=tmp_path)
    # Two keys not present in target should be added
    assert result.added >= 1


def test_promote_with_audit_creates_log_file(source: Path, target: Path, tmp_path: Path) -> None:
    opts = PromoteOptions(overwrite=False, redact_secrets=False)
    promote_with_audit(source, target, opts, log_dir=tmp_path)
    log_file = _audit_path(tmp_path)
    assert log_file.exists()


def test_promote_with_audit_log_entry_has_operation(source: Path, target: Path, tmp_path: Path) -> None:
    opts = PromoteOptions(overwrite=False, redact_secrets=False)
    promote_with_audit(source, target, opts, log_dir=tmp_path)
    entries = load_log(tmp_path)
    assert len(entries) == 1
    assert entries[0].operation == "promote"


def test_promote_with_audit_log_entry_target_matches(source: Path, target: Path, tmp_path: Path) -> None:
    opts = PromoteOptions(overwrite=False, redact_secrets=False)
    promote_with_audit(source, target, opts, log_dir=tmp_path)
    entries = load_log(tmp_path)
    assert entries[0].target == str(target)


def test_promote_with_audit_detail_contains_counts(source: Path, target: Path, tmp_path: Path) -> None:
    opts = PromoteOptions(overwrite=False, redact_secrets=False)
    result = promote_with_audit(source, target, opts, log_dir=tmp_path)
    entries = load_log(tmp_path)
    detail = entries[0].detail
    assert detail["added"] == result.added
    assert detail["skipped"] == result.skipped


def test_promote_with_audit_default_log_dir_is_target_parent(source: Path, tmp_path: Path) -> None:
    sub = tmp_path / "subdir"
    sub.mkdir()
    target = sub / "target.env"
    target.write_text("")
    opts = PromoteOptions(overwrite=True, redact_secrets=False)
    promote_with_audit(source, target, opts)  # no log_dir supplied
    log_file = _audit_path(sub)
    assert log_file.exists()


def test_promote_with_audit_actor_stored(source: Path, target: Path, tmp_path: Path) -> None:
    opts = PromoteOptions(overwrite=False, redact_secrets=False)
    promote_with_audit(source, target, opts, log_dir=tmp_path, actor="ci-bot")
    entries = load_log(tmp_path)
    assert entries[0].actor == "ci-bot"


def test_promote_with_audit_multiple_calls_append(source: Path, target: Path, tmp_path: Path) -> None:
    opts = PromoteOptions(overwrite=False, redact_secrets=False)
    promote_with_audit(source, target, opts, log_dir=tmp_path)
    promote_with_audit(source, target, opts, log_dir=tmp_path)
    entries = load_log(tmp_path)
    assert len(entries) == 2
