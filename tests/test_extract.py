"""Tests for envoy_local.extract."""
from pathlib import Path

import pytest

from envoy_local.extract import extract_keys
from envoy_local.parser import parse_env_file


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "APP_HOST=localhost\n"
        "APP_PORT=8080\n"
        "DB_HOST=db.local\n"
        "DB_PASSWORD=secret\n"
        "DEBUG=true\n"
    )
    return p


def test_extract_by_explicit_keys(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out.env"
    result = extract_keys(env_file, dest, keys=["APP_HOST", "APP_PORT"])
    assert result.ok
    assert set(result.extracted) == {"APP_HOST", "APP_PORT"}
    parsed = parse_env_file(dest)
    keys = [e.key for e in parsed.entries if e.key]
    assert keys == ["APP_HOST", "APP_PORT"]


def test_extract_by_pattern(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "db.env"
    result = extract_keys(env_file, dest, pattern=r"^DB_")
    assert result.ok
    assert set(result.extracted) == {"DB_HOST", "DB_PASSWORD"}
    parsed = parse_env_file(dest)
    keys = [e.key for e in parsed.entries if e.key]
    assert set(keys) == {"DB_HOST", "DB_PASSWORD"}


def test_extract_keys_and_pattern_union(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "mixed.env"
    result = extract_keys(env_file, dest, keys=["DEBUG"], pattern=r"^APP_")
    assert result.ok
    assert set(result.extracted) == {"APP_HOST", "APP_PORT", "DEBUG"}


def test_extract_skipped_keys_reported(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out.env"
    result = extract_keys(env_file, dest, keys=["APP_HOST"])
    assert "DB_HOST" in result.skipped
    assert "DB_PASSWORD" in result.skipped


def test_extract_missing_source(tmp_path: Path) -> None:
    result = extract_keys(tmp_path / "ghost.env", tmp_path / "out.env", keys=["X"])
    assert not result.ok
    assert "source file not found" in result.error


def test_extract_no_keys_or_pattern_is_error(env_file: Path, tmp_path: Path) -> None:
    result = extract_keys(env_file, tmp_path / "out.env")
    assert not result.ok
    assert "pattern" in result.error


def test_extract_dest_exists_no_overwrite(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out.env"
    dest.write_text("EXISTING=1\n")
    result = extract_keys(env_file, dest, keys=["APP_HOST"])
    assert not result.ok
    assert "already exists" in result.error


def test_extract_dest_exists_with_overwrite(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out.env"
    dest.write_text("EXISTING=1\n")
    result = extract_keys(env_file, dest, keys=["APP_HOST"], overwrite=True)
    assert result.ok
    parsed = parse_env_file(dest)
    keys = [e.key for e in parsed.entries if e.key]
    assert keys == ["APP_HOST"]


def test_extract_summary_contains_counts(env_file: Path, tmp_path: Path) -> None:
    dest = tmp_path / "out.env"
    result = extract_keys(env_file, dest, keys=["APP_HOST", "APP_PORT"])
    summary = result.summary()
    assert "2" in summary
    assert "extracted" in summary
