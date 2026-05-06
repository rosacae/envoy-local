"""Tests for envoy_local.typecheck."""
import pytest

from envoy_local.parser import parse_lines
from envoy_local.typecheck import (
    TypeCheckResult,
    TypeViolation,
    typecheck_entries,
    KNOWN_TYPES,
)


def _parse(text: str):
    return parse_lines(text.strip().splitlines())


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def test_known_types_includes_primitives():
    assert "int" in KNOWN_TYPES
    assert "float" in KNOWN_TYPES
    assert "bool" in KNOWN_TYPES
    assert "str" in KNOWN_TYPES
    assert "url" in KNOWN_TYPES
    assert "email" in KNOWN_TYPES


# ---------------------------------------------------------------------------
# int
# ---------------------------------------------------------------------------

def test_valid_int_passes():
    result = _parse("PORT=8080")
    tc = typecheck_entries(result, {"PORT": "int"})
    assert tc.ok
    assert tc.checked == 1


def test_invalid_int_is_violation():
    result = _parse("PORT=abc")
    tc = typecheck_entries(result, {"PORT": "int"})
    assert not tc.ok
    assert len(tc.violations) == 1
    assert tc.violations[0].key == "PORT"
    assert tc.violations[0].expected_type == "int"


# ---------------------------------------------------------------------------
# float
# ---------------------------------------------------------------------------

def test_valid_float_passes():
    result = _parse("RATIO=3.14")
    tc = typecheck_entries(result, {"RATIO": "float"})
    assert tc.ok


def test_invalid_float_is_violation():
    result = _parse("RATIO=not_a_float")
    tc = typecheck_entries(result, {"RATIO": "float"})
    assert not tc.ok


# ---------------------------------------------------------------------------
# bool
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("val", ["true", "false", "1", "0", "yes", "no", "True", "False"])
def test_valid_bool_passes(val):
    result = _parse(f"FLAG={val}")
    tc = typecheck_entries(result, {"FLAG": "bool"})
    assert tc.ok


def test_invalid_bool_is_violation():
    result = _parse("FLAG=maybe")
    tc = typecheck_entries(result, {"FLAG": "bool"})
    assert not tc.ok


# ---------------------------------------------------------------------------
# url
# ---------------------------------------------------------------------------

def test_valid_url_passes():
    result = _parse("ENDPOINT=https://example.com/api")
    tc = typecheck_entries(result, {"ENDPOINT": "url"})
    assert tc.ok


def test_invalid_url_is_violation():
    result = _parse("ENDPOINT=not-a-url")
    tc = typecheck_entries(result, {"ENDPOINT": "url"})
    assert not tc.ok


# ---------------------------------------------------------------------------
# email
# ---------------------------------------------------------------------------

def test_valid_email_passes():
    result = _parse("ADMIN=admin@example.com")
    tc = typecheck_entries(result, {"ADMIN": "email"})
    assert tc.ok


def test_invalid_email_is_violation():
    result = _parse("ADMIN=not-an-email")
    tc = typecheck_entries(result, {"ADMIN": "email"})
    assert not tc.ok


# ---------------------------------------------------------------------------
# str (always passes)
# ---------------------------------------------------------------------------

def test_str_type_always_passes():
    result = _parse("ANYTHING=whatever 123 !@#")
    tc = typecheck_entries(result, {"ANYTHING": "str"})
    assert tc.ok


# ---------------------------------------------------------------------------
# edge cases
# ---------------------------------------------------------------------------

def test_missing_key_skipped():
    result = _parse("OTHER=value")
    tc = typecheck_entries(result, {"PORT": "int"})
    assert tc.ok
    assert tc.checked == 0


def test_unknown_type_skipped():
    result = _parse("X=hello")
    tc = typecheck_entries(result, {"X": "uuid"})
    assert tc.ok
    assert tc.checked == 0


def test_multiple_violations_collected():
    result = _parse("PORT=abc\nRATIO=xyz")
    tc = typecheck_entries(result, {"PORT": "int", "RATIO": "float"})
    assert not tc.ok
    assert len(tc.violations) == 2


def test_to_dict_structure():
    result = _parse("PORT=bad")
    tc = typecheck_entries(result, {"PORT": "int"})
    d = tc.to_dict()
    assert d["ok"] is False
    assert d["checked"] == 1
    assert isinstance(d["violations"], list)
    v = d["violations"][0]
    assert v["key"] == "PORT"
    assert v["expected_type"] == "int"
