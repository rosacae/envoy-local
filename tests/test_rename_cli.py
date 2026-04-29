"""Tests for rename_cli.cmd_rename."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.rename_cli import cmd_rename


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("OLD_KEY=hello\nOTHER=world\n")
    return p


def _ns(file: str, old_key: str, new_key: str, force: bool = False, audit: bool = False) -> argparse.Namespace:
    return argparse.Namespace(
        file=file,
        old_key=old_key,
        new_key=new_key,
        force=force,
        audit=audit,
        audit_dir=None,
    )


def test_cmd_rename_returns_0_on_success(env_file: Path) -> None:
    rc = cmd_rename(_ns(str(env_file), "OLD_KEY", "NEW_KEY"))
    assert rc == 0


def test_cmd_rename_key_appears_in_file(env_file: Path) -> None:
    cmd_rename(_ns(str(env_file), "OLD_KEY", "NEW_KEY"))
    content = env_file.read_text()
    assert "NEW_KEY" in content
    assert "OLD_KEY" not in content


def test_cmd_rename_other_keys_preserved(env_file: Path) -> None:
    cmd_rename(_ns(str(env_file), "OLD_KEY", "NEW_KEY"))
    content = env_file.read_text()
    assert "OTHER=world" in content


def test_cmd_rename_returns_1_when_key_missing(env_file: Path) -> None:
    rc = cmd_rename(_ns(str(env_file), "DOES_NOT_EXIST", "NEW_KEY"))
    assert rc == 1


def test_cmd_rename_returns_1_when_file_missing(tmp_path: Path) -> None:
    rc = cmd_rename(_ns(str(tmp_path / "missing.env"), "A", "B"))
    assert rc == 1


def test_cmd_rename_returns_2_on_conflict_without_force(env_file: Path) -> None:
    # Both keys already present — renaming OLD_KEY -> OTHER should conflict.
    rc = cmd_rename(_ns(str(env_file), "OLD_KEY", "OTHER", force=False))
    assert rc == 2


def test_cmd_rename_force_resolves_conflict(env_file: Path) -> None:
    rc = cmd_rename(_ns(str(env_file), "OLD_KEY", "OTHER", force=True))
    assert rc == 0
    content = env_file.read_text()
    assert "OLD_KEY" not in content
    # After force-rename the value of OLD_KEY should be under OTHER.
    assert "OTHER" in content


def test_cmd_rename_audit_creates_log(env_file: Path, tmp_path: Path) -> None:
    audit_dir = tmp_path / "audit"
    ns = argparse.Namespace(
        file=str(env_file),
        old_key="OLD_KEY",
        new_key="NEW_KEY",
        force=False,
        audit=True,
        audit_dir=str(audit_dir),
    )
    rc = cmd_rename(ns)
    assert rc == 0
    assert audit_dir.exists()
    logs = list(audit_dir.glob("*.jsonl"))
    assert len(logs) == 1
