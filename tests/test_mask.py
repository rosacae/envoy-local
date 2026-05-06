"""Tests for envoy_local.mask."""
from __future__ import annotations

import textwrap

import pytest

from envoy_local.mask import MaskOptions, mask_entries, _mask_value
from envoy_local.parser import parse_env_text


def _parse(text: str):
    return parse_env_text(textwrap.dedent(text))


# ---------------------------------------------------------------------------
# _mask_value unit tests
# ---------------------------------------------------------------------------

def test_mask_value_hides_tail():
    opts = MaskOptions(visible_chars=3, mask_char="*")
    assert _mask_value("abcdefgh", opts) == "abc*****"


def test_mask_value_short_string_fully_masked():
    opts = MaskOptions(visible_chars=4, mask_char="*")
    result = _mask_value("abc", opts)
    assert "*" in result
    assert "abc" not in result


def test_mask_value_mask_all_hides_everything():
    opts = MaskOptions(visible_chars=4, mask_char="#", mask_all=True)
    result = _mask_value("mysecret", opts)
    assert all(c == "#" for c in result)


def test_mask_value_empty_returns_empty():
    opts = MaskOptions()
    assert _mask_value("", opts) == ""


# ---------------------------------------------------------------------------
# mask_entries integration tests
# ---------------------------------------------------------------------------

def test_mask_entries_masks_explicit_key():
    result = _parse("""\
        API_KEY=supersecretvalue
        PORT=8080
    """)
    mr = mask_entries(result, secret_keys=["API_KEY"])
    values = {e.key: e.value for e in mr.entries if e.key}
    assert values["PORT"] == "8080"
    assert values["API_KEY"] != "supersecretvalue"
    assert "supe" in values["API_KEY"]
    assert mr.masked_count == 1


def test_mask_entries_mask_all_option():
    result = _parse("""\
        FOO=hello
        BAR=world
    """)
    opts = MaskOptions(mask_all=True, only_secrets=False)
    mr = mask_entries(result, opts=opts)
    for entry in mr.entries:
        if entry.key and entry.value:
            assert "*" in entry.value
    assert mr.masked_count == 2


def test_mask_entries_preserves_comments():
    result = _parse("""\
        # a comment
        SECRET=abc123
    """)
    mr = mask_entries(result, secret_keys=["SECRET"])
    comment_entries = [e for e in mr.entries if e.key is None]
    assert len(comment_entries) == 1


def test_mask_entries_no_keys_no_masking():
    result = _parse("""\
        PLAIN=value
    """)
    mr = mask_entries(result, secret_keys=[])
    assert mr.masked_count == 0
    assert mr.entries[0].value == "value"


def test_mask_entries_custom_char():
    result = _parse("TOKEN=abcdefghij")
    opts = MaskOptions(visible_chars=2, mask_char="-")
    mr = mask_entries(result, opts=opts, secret_keys=["TOKEN"])
    val = mr.entries[0].value
    assert val.startswith("ab")
    assert "-" in val


def test_mask_result_summary():
    result = _parse("KEY=val")
    mr = mask_entries(result, secret_keys=["KEY"])
    assert "1" in mr.summary()
