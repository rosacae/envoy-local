"""Tests for envoy_local.dedupe."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy_local.dedupe import dedupe_env_file


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "APP_KEY=first\n"
        "DEBUG=true\n"
        "APP_KEY=second\n"
        "PORT=8080\n"
        "DEBUG=false\n",
        encoding="utf-8",
    )
    return p


def _keys(path: Path) -> list[str]:
    from envoy_local.parser import parse_env_file

    return [e.key for e in parse_env_file(path).entries if e.key]


def _values(path: Path) -> dict[str, str]:
    from envoy_local.parser import parse_env_file

    return {e.key: e.value for e in parse_env_file(path).entries if e.key}


# ---------------------------------------------------------------------------


def test_dedupe_detects_duplicates(env_file: Path) -> None:
    result = dedupe_env_file(env_file, dry_run=True)
    assert result.ok
    assert set(result.removed) == {"APP_KEY", "DEBUG"}


def test_dedupe_keep_last_is_default(env_file: Path) -> None:
    result = dedupe_env_file(env_file)
    vals = _values(env_file)
    assert vals["APP_KEY"] == "second"
    assert vals["DEBUG"] == "false"


def test_dedupe_keep_first(env_file: Path) -> None:
    result = dedupe_env_file(env_file, keep="first")
    vals = _values(env_file)
    assert vals["APP_KEY"] == "first"
    assert vals["DEBUG"] == "true"


def test_dedupe_preserves_non_duplicate_keys(env_file: Path) -> None:
    dedupe_env_file(env_file)
    keys = _keys(env_file)
    assert "PORT" in keys


def test_dedupe_removes_correct_count(env_file: Path) -> None:
    result = dedupe_env_file(env_file)
    assert len(result.removed) == 2


def test_dedupe_dry_run_does_not_modify_file(env_file: Path) -> None:
    original = env_file.read_text()
    dedupe_env_file(env_file, dry_run=True)
    assert env_file.read_text() == original


def test_dedupe_no_duplicates_returns_empty_removed(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("FOO=1\nBAR=2\n", encoding="utf-8")
    result = dedupe_env_file(p)
    assert result.removed == []


def test_dedupe_missing_file_returns_error(tmp_path: Path) -> None:
    result = dedupe_env_file(tmp_path / "missing.env")
    assert not result.ok
    assert "not found" in result.error  # type: ignore[operator]


def test_dedupe_summary_lists_keys(env_file: Path) -> None:
    result = dedupe_env_file(env_file, dry_run=True)
    summary = result.summary()
    assert "APP_KEY" in summary or "DEBUG" in summary


def test_dedupe_summary_clean_file(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("ONLY=one\n", encoding="utf-8")
    result = dedupe_env_file(p)
    assert "no duplicate" in result.summary()
