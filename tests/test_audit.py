"""Tests for envoy_local.audit and envoy_local.audit_cli."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_local.audit import AuditEntry, load_log, record
from envoy_local.audit_cli import cmd_audit_log


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path / "audit"


def test_record_creates_file(log_dir: Path) -> None:
    record("sync", ".env", ["FOO", "BAR"], log_dir)
    assert (log_dir / "audit.jsonl").exists()


def test_record_returns_entry(log_dir: Path) -> None:
    entry = record("put", "vault", ["SECRET"], log_dir, note="manual")
    assert isinstance(entry, AuditEntry)
    assert entry.operation == "put"
    assert entry.target == "vault"
    assert entry.keys == ["SECRET"]
    assert entry.note == "manual"


def test_multiple_records_appended(log_dir: Path) -> None:
    record("sync", ".env", ["A"], log_dir)
    record("delete", ".env", ["B"], log_dir)
    entries = load_log(log_dir)
    assert len(entries) == 2
    assert entries[0].operation == "sync"
    assert entries[1].operation == "delete"


def test_load_log_empty_when_no_file(log_dir: Path) -> None:
    assert load_log(log_dir) == []


def test_audit_entry_roundtrip() -> None:
    entry = AuditEntry(
        timestamp="2024-01-01T00:00:00+00:00",
        operation="sync",
        target=".env",
        keys=["X"],
        note="test",
    )
    restored = AuditEntry.from_dict(entry.to_dict())
    assert restored.timestamp == entry.timestamp
    assert restored.keys == ["X"]
    assert restored.note == "test"


def test_cmd_audit_log_text_output(log_dir: Path, capsys: pytest.CaptureFixture) -> None:
    record("sync", ".env", ["FOO"], log_dir)
    code = cmd_audit_log(log_dir=log_dir, output_format="text")
    assert code == 0
    out = capsys.readouterr().out
    assert "sync" in out
    assert "FOO" in out


def test_cmd_audit_log_json_output(log_dir: Path, capsys: pytest.CaptureFixture) -> None:
    record("put", "vault", ["BAR"], log_dir)
    code = cmd_audit_log(log_dir=log_dir, output_format="json")
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert data[0]["operation"] == "put"


def test_cmd_audit_log_filter(log_dir: Path, capsys: pytest.CaptureFixture) -> None:
    record("sync", ".env", ["A"], log_dir)
    record("delete", ".env", ["B"], log_dir)
    code = cmd_audit_log(log_dir=log_dir, operation_filter="delete")
    assert code == 0
    out = capsys.readouterr().out
    assert "delete" in out
    assert "sync" not in out


def test_cmd_audit_log_limit(log_dir: Path, capsys: pytest.CaptureFixture) -> None:
    for i in range(5):
        record("sync", ".env", [f"K{i}"], log_dir)
    code = cmd_audit_log(log_dir=log_dir, limit=2)
    assert code == 0
    out = capsys.readouterr().out
    assert out.count("sync") == 2


def test_cmd_audit_log_no_entries(log_dir: Path, capsys: pytest.CaptureFixture) -> None:
    code = cmd_audit_log(log_dir=log_dir)
    assert code == 0
    assert "No audit entries" in capsys.readouterr().out
