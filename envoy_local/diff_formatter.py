"""Render DiffResult as human-readable or machine-readable output."""
from __future__ import annotations

from typing import List

from envoy_local.diff import DiffEntry, DiffResult
from envoy_local.redactor import Redactor

_STATUS_SYMBOL = {
    "added": "+",
    "removed": "-",
    "changed": "~",
    "unchanged": " ",
}

_STATUS_COLOR = {
    "added": "\033[32m",
    "removed": "\033[31m",
    "changed": "\033[33m",
    "unchanged": "\033[0m",
}
_RESET = "\033[0m"


def _maybe_redact(value: str | None, key: str, redactor: Redactor | None) -> str:
    if value is None:
        return ""
    if redactor and redactor.config.is_secret(key):
        return redactor.redact(value)
    return value


def format_diff(
    result: DiffResult,
    redactor: Redactor | None = None,
    color: bool = True,
    show_unchanged: bool = False,
) -> str:
    lines: List[str] = []
    for entry in result.entries:
        if entry.status == "unchanged" and not show_unchanged:
            continue

        symbol = _STATUS_SYMBOL[entry.status]
        color_code = _STATUS_COLOR[entry.status] if color else ""
        reset = _RESET if color else ""

        if entry.status == "added":
            val = _maybe_redact(entry.new_value, entry.key, redactor)
            lines.append(f"{color_code}{symbol} {entry.key}={val}{reset}")
        elif entry.status == "removed":
            val = _maybe_redact(entry.old_value, entry.key, redactor)
            lines.append(f"{color_code}{symbol} {entry.key}={val}{reset}")
        elif entry.status == "changed":
            old = _maybe_redact(entry.old_value, entry.key, redactor)
            new = _maybe_redact(entry.new_value, entry.key, redactor)
            lines.append(f"{color_code}{symbol} {entry.key}: {old} -> {new}{reset}")
        else:
            val = _maybe_redact(entry.old_value, entry.key, redactor)
            lines.append(f"{color_code}{symbol} {entry.key}={val}{reset}")

    header = f"# {result.summary()}"
    return "\n".join([header] + lines) if lines else header


def format_diff_json(result: DiffResult, redactor: Redactor | None = None) -> list:
    """Return diff as a list of dicts suitable for JSON serialisation."""
    out = []
    for entry in result.entries:
        out.append(
            {
                "key": entry.key,
                "status": entry.status,
                "old_value": _maybe_redact(entry.old_value, entry.key, redactor),
                "new_value": _maybe_redact(entry.new_value, entry.key, redactor),
            }
        )
    return out
