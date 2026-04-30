"""Tests for envoy_local.merge."""
from __future__ import annotations

from pathlib import Path
import pytest

from envoy_local.merge import MergeOptions, merge_env_files


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_merge_combines_disjoint_keys(base_dir: Path) -> None:
    a = _write(base_dir / "a.env", "FOO=1\nBAR=2\n")
    b = _write(base_dir / "b.env", "BAZ=3\n")
    result = merge_env_files(MergeOptions(sources=[a, b]))
    assert result.ok
    keys = [e.key for e in result.merged if e.key]
    assert keys == ["FOO", "BAR", "BAZ"]


def test_merge_later_file_wins_by_default(base_dir: Path) -> None:
    a = _write(base_dir / "a.env", "FOO=original\n")
    b = _write(base_dir / "b.env", "FOO=overridden\n")
    result = merge_env_files(MergeOptions(sources=[a, b]))
    assert result.ok
    values = {e.key: e.value for e in result.merged if e.key}
    assert values["FOO"] == "overridden"
    assert "FOO" in result.conflicts


def test_merge_no_overwrite_keeps_first(base_dir: Path) -> None:
    a = _write(base_dir / "a.env", "FOO=first\n")
    b = _write(base_dir / "b.env", "FOO=second\n")
    result = merge_env_files(MergeOptions(sources=[a, b], overwrite=False))
    assert result.ok
    values = {e.key: e.value for e in result.merged if e.key}
    assert values["FOO"] == "first"
    assert "FOO" in result.conflicts


def test_merge_writes_output_file(base_dir: Path) -> None:
    a = _write(base_dir / "a.env", "X=1\n")
    b = _write(base_dir / "b.env", "Y=2\n")
    out = base_dir / "merged.env"
    result = merge_env_files(MergeOptions(sources=[a, b], output=out))
    assert result.ok
    assert out.exists()
    text = out.read_text()
    assert "X=1" in text
    assert "Y=2" in text


def test_merge_dry_run_does_not_write(base_dir: Path) -> None:
    a = _write(base_dir / "a.env", "X=1\n")
    out = base_dir / "merged.env"
    merge_env_files(MergeOptions(sources=[a], output=out, dry_run=True))
    assert not out.exists()


def test_merge_missing_source_returns_error(base_dir: Path) -> None:
    result = merge_env_files(MergeOptions(sources=[base_dir / "missing.env"]))
    assert not result.ok
    assert "not found" in result.error


def test_merge_no_sources_returns_error() -> None:
    result = merge_env_files(MergeOptions(sources=[]))
    assert not result.ok


def test_merge_summary_contains_key_count(base_dir: Path) -> None:
    a = _write(base_dir / "a.env", "A=1\nB=2\n")
    b = _write(base_dir / "b.env", "C=3\n")
    result = merge_env_files(MergeOptions(sources=[a, b]))
    assert "3" in result.summary()


def test_merge_three_sources_correct_order(base_dir: Path) -> None:
    a = _write(base_dir / "a.env", "A=1\n")
    b = _write(base_dir / "b.env", "B=2\n")
    c = _write(base_dir / "c.env", "C=3\n")
    result = merge_env_files(MergeOptions(sources=[a, b, c]))
    keys = [e.key for e in result.merged if e.key]
    assert keys == ["A", "B", "C"]
