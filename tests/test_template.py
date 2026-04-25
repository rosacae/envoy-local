"""Unit tests for envoy_local.template."""
from __future__ import annotations

import pytest

from envoy_local.parser import ParseResult, EnvEntry
from envoy_local.template import (
    RenderResult,
    list_placeholders,
    render_template,
    render_template_from_parse_result,
)


# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------

def test_render_basic_substitution():
    result = render_template("Hello, {{NAME}}!", {"NAME": "World"})
    assert result.text == "Hello, World!"
    assert result.resolved == ["NAME"]
    assert result.missing == []
    assert result.ok


def test_render_multiple_placeholders():
    tmpl = "{{A}} + {{B}} = {{C}}"
    env = {"A": "1", "B": "2", "C": "3"}
    result = render_template(tmpl, env)
    assert result.text == "1 + 2 = 3"
    assert set(result.resolved) == {"A", "B", "C"}


def test_render_missing_placeholder_left_intact():
    result = render_template("url={{BASE_URL}}/path", {})
    assert "{{BASE_URL}}" in result.text
    assert result.missing == ["BASE_URL"]
    assert not result.ok


def test_render_placeholder_with_spaces():
    result = render_template("{{ KEY }}", {"KEY": "value"})
    assert result.text == "value"


def test_render_same_placeholder_twice():
    result = render_template("{{X}} and {{X}}", {"X": "42"})
    assert result.text == "42 and 42"
    # resolved may contain duplicates — that's fine; missing should be empty
    assert result.ok


def test_render_no_placeholders():
    result = render_template("no placeholders here", {"A": "1"})
    assert result.text == "no placeholders here"
    assert result.resolved == []
    assert result.missing == []


# ---------------------------------------------------------------------------
# render_template_from_parse_result
# ---------------------------------------------------------------------------

def _make_parse_result(*pairs: tuple) -> ParseResult:
    entries = [EnvEntry(key=k, raw_value=v, comment=None) for k, v in pairs]
    return ParseResult(entries=entries, invalid_lines=[])


def test_render_from_parse_result():
    pr = _make_parse_result(("HOST", "localhost"), ("PORT", "5432"))
    result = render_template_from_parse_result("{{HOST}}:{{PORT}}", pr)
    assert result.text == "localhost:5432"


def test_render_from_parse_result_with_override():
    pr = _make_parse_result(("HOST", "localhost"))
    result = render_template_from_parse_result("{{HOST}}:{{PORT}}", pr, override={"PORT": "9999"})
    assert result.text == "localhost:9999"


# ---------------------------------------------------------------------------
# list_placeholders
# ---------------------------------------------------------------------------

def test_list_placeholders_unique_ordered():
    tmpl = "{{A}} {{B}} {{A}} {{C}}"
    assert list_placeholders(tmpl) == ["A", "B", "C"]


def test_list_placeholders_empty():
    assert list_placeholders("no vars here") == []
