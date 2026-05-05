"""Tests for envoy_local.sort."""
from pathlib import Path

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.sort import sort_env_file


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text(
        "ZEBRA=1\n"
        "APPLE=2\n"
        "MANGO=3\n"
        "# a comment\n"
        "BANANA=4\n",
        encoding="utf-8",
    )
    return p


def _keys(path: Path) -> list[str]:
    result = parse_env_text(path.read_text(encoding="utf-8"))
    return [e.key for e in result.entries if e.key is not None]


def test_sort_returns_ok(env_file: Path) -> None:
    result = sort_env_file(env_file)
    assert result.ok is True


def test_sort_orders_keys_alphabetically(env_file: Path) -> None:
    sort_env_file(env_file)
    assert _keys(env_file) == ["APPLE", "BANANA", "MANGO", "ZEBRA"]


def test_sort_reverse_orders_keys_descending(env_file: Path) -> None:
    sort_env_file(env_file, reverse=True)
    assert _keys(env_file) == ["ZEBRA", "MANGO", "BANANA", "APPLE"]


def test_sort_reports_sorted_count(env_file: Path) -> None:
    result = sort_env_file(env_file)
    assert result.sorted_count == 4


def test_sort_writes_to_dest_not_source(tmp_path: Path, env_file: Path) -> None:
    dest = tmp_path / "sorted.env"
    sort_env_file(env_file, dest=dest)
    # source should be untouched
    assert _keys(env_file) == ["ZEBRA", "APPLE", "MANGO", "BANANA"]
    # dest should be sorted
    assert _keys(dest) == ["APPLE", "BANANA", "MANGO", "ZEBRA"]


def test_sort_missing_file_returns_error(tmp_path: Path) -> None:
    result = sort_env_file(tmp_path / "missing.env")
    assert result.ok is False
    assert "not found" in (result.error or "")


def test_sort_summary_ok(env_file: Path) -> None:
    result = sort_env_file(env_file)
    assert "sorted" in result.summary()
    assert "4" in result.summary()


def test_sort_summary_error(tmp_path: Path) -> None:
    result = sort_env_file(tmp_path / "ghost.env")
    assert "sort failed" in result.summary()


def test_sort_comments_first_by_default(env_file: Path) -> None:
    sort_env_file(env_file)
    lines = env_file.read_text(encoding="utf-8").splitlines()
    comment_idx = next(i for i, l in enumerate(lines) if l.startswith("#"))
    first_key_idx = next(i for i, l in enumerate(lines) if "=" in l)
    assert comment_idx < first_key_idx


def test_sort_single_entry_file(tmp_path: Path) -> None:
    p = tmp_path / ".env"
    p.write_text("ONLY=value\n", encoding="utf-8")
    result = sort_env_file(p)
    assert result.ok is True
    assert result.sorted_count == 1
    assert _keys(p) == ["ONLY"]
