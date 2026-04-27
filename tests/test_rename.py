"""Tests for envoy_local.rename."""
from pathlib import Path

import pytest

from envoy_local.rename import rename_key


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPP_SECRET=hunter2\n")
    return p


def test_rename_modifies_key(env_file: Path) -> None:
    result = rename_key([env_file], old_key="DB_HOST", new_key="DATABASE_HOST")
    assert result.ok
    assert env_file in result.files_modified
    content = env_file.read_text()
    assert "DATABASE_HOST=localhost" in content
    assert "DB_HOST" not in content


def test_rename_preserves_other_keys(env_file: Path) -> None:
    rename_key([env_file], old_key="DB_HOST", new_key="DATABASE_HOST")
    content = env_file.read_text()
    assert "DB_PORT=5432" in content
    assert "APP_SECRET=hunter2" in content


def test_rename_skips_when_key_missing(env_file: Path) -> None:
    result = rename_key([env_file], old_key="NONEXISTENT", new_key="WHATEVER")
    assert not result.ok
    assert env_file in result.files_skipped
    # File unchanged
    assert "DB_HOST=localhost" in env_file.read_text()


def test_rename_skips_missing_file(tmp_path: Path) -> None:
    ghost = tmp_path / "ghost.env"
    result = rename_key([ghost], old_key="KEY", new_key="NEW_KEY")
    assert not result.ok
    assert ghost in result.files_skipped


def test_rename_dry_run_does_not_write(env_file: Path) -> None:
    original = env_file.read_text()
    result = rename_key([env_file], old_key="DB_HOST", new_key="DATABASE_HOST", dry_run=True)
    assert result.ok
    assert env_file in result.files_modified
    assert env_file.read_text() == original  # unchanged on disk


def test_rename_multiple_files(tmp_path: Path) -> None:
    f1 = tmp_path / "a.env"
    f2 = tmp_path / "b.env"
    f3 = tmp_path / "c.env"
    f1.write_text("OLD_KEY=value1\n")
    f2.write_text("OLD_KEY=value2\nOTHER=x\n")
    f3.write_text("UNRELATED=yes\n")

    result = rename_key([f1, f2, f3], old_key="OLD_KEY", new_key="NEW_KEY")

    assert f1 in result.files_modified
    assert f2 in result.files_modified
    assert f3 in result.files_skipped
    assert "NEW_KEY=value1" in f1.read_text()
    assert "NEW_KEY=value2" in f2.read_text()


def test_summary_contains_key_names(env_file: Path) -> None:
    result = rename_key([env_file], old_key="DB_HOST", new_key="DATABASE_HOST")
    summary = result.summary()
    assert "DB_HOST" in summary
    assert "DATABASE_HOST" in summary


def test_summary_mentions_skipped_file(tmp_path: Path, env_file: Path) -> None:
    ghost = tmp_path / "ghost.env"
    result = rename_key([env_file, ghost], old_key="DB_HOST", new_key="DATABASE_HOST")
    summary = result.summary()
    assert str(ghost) in summary
