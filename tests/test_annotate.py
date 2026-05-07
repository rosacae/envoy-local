"""Tests for envoy_local.annotate."""
from __future__ import annotations

import pytest

from envoy_local.parser import ParseResult, EnvEntry
from envoy_local.annotate import annotate_entries, AnnotateResult


def _make_result(*lines: tuple[str | None, str | None, str | None]) -> ParseResult:
    """Build a minimal ParseResult from (key, value, comment) tuples."""
    entries = [
        EnvEntry(key=k, value=v, comment=c, raw=f"{k}={v}" if k else (c or ""))
        for k, v, c in lines
    ]
    return ParseResult(entries=entries, errors=[])


def test_annotate_adds_comment_to_matching_key():
    pr = _make_result(("DB_HOST", "localhost", None))
    result = annotate_entries(pr, {"DB_HOST": "database hostname"})
    assert result.annotated == ["DB_HOST"]
    assert result.entries[0].comment == "database hostname"


def test_annotate_multiple_keys():
    pr = _make_result(
        ("DB_HOST", "localhost", None),
        ("DB_PORT", "5432", None),
        ("SECRET", "abc", None),
    )
    result = annotate_entries(pr, {"DB_HOST": "host", "DB_PORT": "port"})
    assert set(result.annotated) == {"DB_HOST", "DB_PORT"}
    assert result.skipped == ["SECRET"]


def test_annotate_overwrites_existing_comment_by_default():
    pr = _make_result(("API_URL", "https://x.com", "old comment"))
    result = annotate_entries(pr, {"API_URL": "new comment"})
    assert result.entries[0].comment == "new comment"
    assert "API_URL" in result.annotated


def test_annotate_no_overwrite_keeps_existing_comment():
    pr = _make_result(("API_URL", "https://x.com", "keep me"))
    result = annotate_entries(pr, {"API_URL": "ignored"}, overwrite=False)
    assert result.entries[0].comment == "keep me"
    assert "API_URL" not in result.annotated


def test_annotate_preserves_comment_entries():
    pr = _make_result(
        (None, None, "# section header"),
        ("KEY", "val", None),
    )
    result = annotate_entries(pr, {"KEY": "desc"})
    assert result.entries[0].comment == "# section header"
    assert result.entries[1].comment == "desc"


def test_annotate_skipped_keys_listed():
    pr = _make_result(("ALPHA", "1", None), ("BETA", "2", None))
    result = annotate_entries(pr, {"ALPHA": "first"})
    assert result.skipped == ["BETA"]


def test_annotate_empty_annotations_returns_all_skipped():
    pr = _make_result(("X", "1", None), ("Y", "2", None))
    result = annotate_entries(pr, {})
    assert result.annotated == []
    assert set(result.skipped) == {"X", "Y"}


def test_annotate_summary_message():
    pr = _make_result(("A", "1", None), ("B", "2", None))
    result = annotate_entries(pr, {"A": "note"})
    summary = result.summary()
    assert "1 annotated" in summary
    assert "1 keys not in map" in summary


def test_annotate_ok_always_true():
    pr = _make_result(("K", "v", None))
    result = annotate_entries(pr, {})
    assert result.ok() is True
