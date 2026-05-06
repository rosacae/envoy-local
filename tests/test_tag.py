"""Tests for envoy_local.tag and envoy_local.tag_filter."""
from __future__ import annotations

from pathlib import Path
import pytest

from envoy_local.tag import (
    add_tag,
    remove_tag,
    load_tags,
    keys_for_tag,
    tags_for_key,
    TagManifest,
)
from envoy_local.tag_filter import entries_with_tag, entries_without_tag, annotate_entry
from envoy_local.parser import EnvEntry


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_tags_returns_empty_when_no_file(base_dir: Path) -> None:
    manifest = load_tags(base_dir)
    assert manifest.tags == {}


def test_add_tag_creates_file(base_dir: Path) -> None:
    add_tag(base_dir, "API_KEY", "secret")
    assert (base_dir / ".envoy_tags.json").exists()


def test_add_tag_returns_true_when_new(base_dir: Path) -> None:
    assert add_tag(base_dir, "API_KEY", "secret") is True


def test_add_tag_returns_false_when_duplicate(base_dir: Path) -> None:
    add_tag(base_dir, "API_KEY", "secret")
    assert add_tag(base_dir, "API_KEY", "secret") is False


def test_add_multiple_tags_to_same_key(base_dir: Path) -> None:
    add_tag(base_dir, "DB_URL", "infra")
    add_tag(base_dir, "DB_URL", "required")
    tags = tags_for_key(load_tags(base_dir), "DB_URL")
    assert set(tags) == {"infra", "required"}


def test_remove_tag_returns_true_when_existed(base_dir: Path) -> None:
    add_tag(base_dir, "API_KEY", "secret")
    assert remove_tag(base_dir, "API_KEY", "secret") is True


def test_remove_tag_returns_false_when_missing(base_dir: Path) -> None:
    assert remove_tag(base_dir, "API_KEY", "secret") is False


def test_remove_tag_cleans_up_empty_key(base_dir: Path) -> None:
    add_tag(base_dir, "API_KEY", "secret")
    remove_tag(base_dir, "API_KEY", "secret")
    manifest = load_tags(base_dir)
    assert "API_KEY" not in manifest.tags


def test_keys_for_tag_returns_correct_keys(base_dir: Path) -> None:
    add_tag(base_dir, "A", "infra")
    add_tag(base_dir, "B", "infra")
    add_tag(base_dir, "C", "secret")
    manifest = load_tags(base_dir)
    assert set(keys_for_tag(manifest, "infra")) == {"A", "B"}


def _entry(key: str, value: str = "val") -> EnvEntry:
    return EnvEntry(key=key, value=value, comment="", raw=f"{key}={value}")


def test_entries_with_tag_filters_correctly(base_dir: Path) -> None:
    add_tag(base_dir, "SECRET_KEY", "secret")
    entries = [_entry("SECRET_KEY"), _entry("PUBLIC_URL")]
    result = entries_with_tag(entries, "secret", base_dir)
    assert len(result) == 1
    assert result[0].key == "SECRET_KEY"


def test_entries_without_tag_excludes_tagged(base_dir: Path) -> None:
    add_tag(base_dir, "SECRET_KEY", "secret")
    entries = [_entry("SECRET_KEY"), _entry("PUBLIC_URL")]
    result = entries_without_tag(entries, "secret", base_dir)
    assert len(result) == 1
    assert result[0].key == "PUBLIC_URL"


def test_annotate_entry_appends_tags() -> None:
    manifest = TagManifest(tags={"API_KEY": ["secret", "required"]})
    entry = _entry("API_KEY", "abc123")
    line = annotate_entry(entry, manifest)
    assert "secret" in line
    assert "required" in line


def test_annotate_entry_no_tags_returns_plain() -> None:
    manifest = TagManifest()
    entry = _entry("PLAIN", "value")
    line = annotate_entry(entry, manifest)
    assert line == "PLAIN=value"
