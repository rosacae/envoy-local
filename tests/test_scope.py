"""Tests for envoy_local.scope."""
from pathlib import Path
import json
import pytest

from envoy_local.scope import (
    load_scopes,
    add_key_to_scope,
    remove_key_from_scope,
    keys_in_scope,
    list_scopes,
    filter_entries_by_scope,
    SCOPE_FILE,
)
from envoy_local.parser import EnvEntry


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_scopes_returns_empty_when_no_file(base_dir):
    manifest = load_scopes(base_dir)
    assert manifest.scopes == {}


def test_add_key_creates_scope_file(base_dir):
    add_key_to_scope(base_dir, "prod", "DB_URL")
    assert (base_dir / SCOPE_FILE).exists()


def test_add_key_returns_true_when_new(base_dir):
    result = add_key_to_scope(base_dir, "prod", "DB_URL")
    assert result is True


def test_add_key_returns_false_when_duplicate(base_dir):
    add_key_to_scope(base_dir, "prod", "DB_URL")
    result = add_key_to_scope(base_dir, "prod", "DB_URL")
    assert result is False


def test_keys_in_scope_roundtrip(base_dir):
    add_key_to_scope(base_dir, "test", "API_KEY")
    add_key_to_scope(base_dir, "test", "SECRET")
    assert keys_in_scope(base_dir, "test") == {"API_KEY", "SECRET"}


def test_remove_key_returns_true_when_present(base_dir):
    add_key_to_scope(base_dir, "prod", "DB_URL")
    result = remove_key_from_scope(base_dir, "prod", "DB_URL")
    assert result is True


def test_remove_key_returns_false_when_absent(base_dir):
    result = remove_key_from_scope(base_dir, "prod", "MISSING")
    assert result is False


def test_remove_last_key_deletes_scope(base_dir):
    add_key_to_scope(base_dir, "prod", "DB_URL")
    remove_key_from_scope(base_dir, "prod", "DB_URL")
    assert "prod" not in list_scopes(base_dir)


def test_list_scopes_returns_sorted_names(base_dir):
    add_key_to_scope(base_dir, "staging", "X")
    add_key_to_scope(base_dir, "prod", "Y")
    assert list_scopes(base_dir) == ["prod", "staging"]


def test_filter_entries_by_scope(base_dir):
    add_key_to_scope(base_dir, "prod", "DB_URL")
    entries = [
        EnvEntry(key="DB_URL", value="postgres://", comment=None, raw="DB_URL=postgres://"),
        EnvEntry(key="DEBUG", value="true", comment=None, raw="DEBUG=true"),
        EnvEntry(key=None, value=None, comment="# header", raw="# header"),
    ]
    filtered = filter_entries_by_scope(entries, base_dir, "prod")
    keys = [e.key for e in filtered if e.key is not None]
    assert keys == ["DB_URL"]


def test_filter_entries_preserves_comments(base_dir):
    add_key_to_scope(base_dir, "prod", "DB_URL")
    entries = [
        EnvEntry(key=None, value=None, comment="# top", raw="# top"),
        EnvEntry(key="DB_URL", value="x", comment=None, raw="DB_URL=x"),
    ]
    filtered = filter_entries_by_scope(entries, base_dir, "prod")
    assert len(filtered) == 2
