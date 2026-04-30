"""Tests for envoy_local.strip and envoy_local.strip_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.strip import strip_keys
from envoy_local.strip_cli import cmd_strip


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    f = tmp_path / ".env"
    f.write_text(
        "APP_NAME=myapp\n"
        "DB_HOST=localhost\n"
        "DB_PORT=5432\n"
        "SECRET_KEY=abc123\n"
        "# a comment\n"
        "DEBUG=true\n"
    )
    return f


def test_strip_removes_single_key(env_file: Path) -> None:
    result = strip_keys(env_file, keys=["DB_PORT"])
    assert "DB_PORT" in result.removed
    assert len(result.removed) == 1
    assert result.written is True
    assert "DB_PORT" not in env_file.read_text()


def test_strip_removes_multiple_keys(env_file: Path) -> None:
    result = strip_keys(env_file, keys=["DB_HOST", "DB_PORT"])
    assert set(result.removed) == {"DB_HOST", "DB_PORT"}
    text = env_file.read_text()
    assert "DB_HOST" not in text
    assert "DB_PORT" not in text
    assert "APP_NAME" in text


def test_strip_by_pattern(env_file: Path) -> None:
    result = strip_keys(env_file, pattern=r"^DB_")
    assert set(result.removed) == {"DB_HOST", "DB_PORT"}
    text = env_file.read_text()
    assert "DB_" not in text


def test_strip_preserves_comments(env_file: Path) -> None:
    strip_keys(env_file, keys=["DEBUG"])
    assert "# a comment" in env_file.read_text()


def test_strip_no_match_returns_empty_removed(env_file: Path) -> None:
    result = strip_keys(env_file, keys=["NONEXISTENT"])
    assert result.removed == []
    assert result.written is True


def test_strip_dry_run_does_not_modify_file(env_file: Path) -> None:
    original = env_file.read_text()
    result = strip_keys(env_file, keys=["APP_NAME"], dry_run=True)
    assert result.written is False
    assert env_file.read_text() == original
    assert "APP_NAME" in result.removed


def test_strip_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        strip_keys(tmp_path / "missing.env", keys=["KEY"])


def test_strip_no_keys_or_pattern_raises(env_file: Path) -> None:
    with pytest.raises(ValueError):
        strip_keys(env_file)


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(file="", keys=[], pattern=None, dry_run=False)
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_strip_returns_0_on_success(env_file: Path) -> None:
    ns = _ns(file=str(env_file), keys=["DEBUG"])
    assert cmd_strip(ns) == 0


def test_cmd_strip_returns_2_on_missing_file(tmp_path: Path) -> None:
    ns = _ns(file=str(tmp_path / "nope.env"), keys=["X"])
    assert cmd_strip(ns) == 2


def test_cmd_strip_returns_2_without_keys_or_pattern(env_file: Path) -> None:
    ns = _ns(file=str(env_file))
    assert cmd_strip(ns) == 2


def test_cmd_strip_dry_run_prints_would_remove(env_file: Path, capsys) -> None:
    ns = _ns(file=str(env_file), keys=["SECRET_KEY"], dry_run=True)
    code = cmd_strip(ns)
    assert code == 0
    out = capsys.readouterr().out
    assert "SECRET_KEY" in out
    assert "SECRET_KEY" in env_file.read_text()  # file unchanged
