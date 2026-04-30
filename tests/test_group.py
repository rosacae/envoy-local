"""Tests for envoy_local.group."""
from __future__ import annotations

import pytest

from envoy_local.parser import parse_env_text
from envoy_local.group import group_by_prefix, group_by_mapping, GroupResult


ENV_TEXT = """DB_HOST=localhost
DB_PORT=5432
AWS_KEY=abc
AWS_SECRET=xyz
APP_NAME=myapp
PLAIN=value
# a comment
"""


@pytest.fixture
def parsed():
    return parse_env_text(ENV_TEXT)


def test_group_by_prefix_creates_groups(parsed):
    gr = group_by_prefix(parsed)
    assert "DB" in gr.groups
    assert "AWS" in gr.groups
    assert "APP" in gr.groups


def test_group_by_prefix_correct_entries(parsed):
    gr = group_by_prefix(parsed)
    keys = [e.key for e in gr.groups["DB"]]
    assert keys == ["DB_HOST", "DB_PORT"]


def test_group_by_prefix_ungrouped_has_plain(parsed):
    gr = group_by_prefix(parsed)
    ungrouped_keys = [e.key for e in gr.ungrouped if e.key]
    assert "PLAIN" in ungrouped_keys


def test_group_by_prefix_comments_are_ungrouped(parsed):
    gr = group_by_prefix(parsed)
    # comment entry has key=None
    assert any(e.key is None for e in gr.ungrouped)


def test_group_by_prefix_with_explicit_prefixes(parsed):
    gr = group_by_prefix(parsed, prefixes=["DB"])
    assert "DB" in gr.groups
    assert "AWS" not in gr.groups
    # AWS entries should be ungrouped
    ungrouped_keys = [e.key for e in gr.ungrouped if e.key]
    assert "AWS_KEY" in ungrouped_keys


def test_group_by_prefix_custom_separator(parsed):
    text = "DB.HOST=localhost\nDB.PORT=5432\nOTHER=x\n"
    result = parse_env_text(text)
    gr = group_by_prefix(result, separator=".")
    assert "DB" in gr.groups
    assert len(gr.groups["DB"]) == 2


def test_group_by_mapping(parsed):
    mapping = {"database": ["DB_HOST", "DB_PORT"], "cloud": ["AWS_KEY", "AWS_SECRET"]}
    gr = group_by_mapping(parsed, mapping)
    assert "database" in gr.groups
    assert "cloud" in gr.groups
    db_keys = [e.key for e in gr.groups["database"]]
    assert "DB_HOST" in db_keys
    assert "DB_PORT" in db_keys


def test_group_by_mapping_unmapped_keys_are_ungrouped(parsed):
    mapping = {"database": ["DB_HOST"]}
    gr = group_by_mapping(parsed, mapping)
    ungrouped_keys = [e.key for e in gr.ungrouped if e.key]
    assert "APP_NAME" in ungrouped_keys
    assert "PLAIN" in ungrouped_keys


def test_group_result_to_dict(parsed):
    gr = group_by_prefix(parsed)
    d = gr.to_dict()
    assert "groups" in d
    assert "ungrouped" in d
    assert isinstance(d["groups"], dict)
    assert isinstance(d["ungrouped"], list)


def test_empty_file_produces_empty_groups():
    from envoy_local.parser import parse_env_text
    result = parse_env_text("")
    gr = group_by_prefix(result)
    assert gr.groups == {}
