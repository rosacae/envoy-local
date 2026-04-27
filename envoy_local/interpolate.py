"""Variable interpolation for .env files.

Supports ${VAR} and $VAR style references within values,
resolving them from the same parse result or a provided context dict.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.parser import EnvEntry, ParseResult

_BRACE_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_BARE_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolateResult:
    entries: List[EnvEntry]
    unresolved: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.unresolved) == 0


def _resolve_value(value: str, context: Dict[str, str]) -> tuple[str, List[str]]:
    """Return (resolved_value, list_of_missing_keys)."""
    missing: List[str] = []

    def replace_brace(m: re.Match) -> str:
        key = m.group(1)
        if key in context:
            return context[key]
        missing.append(key)
        return m.group(0)

    def replace_bare(m: re.Match) -> str:
        key = m.group(1)
        if key in context:
            return context[key]
        missing.append(key)
        return m.group(0)

    result = _BRACE_RE.sub(replace_brace, value)
    result = _BARE_RE.sub(replace_bare, result)
    return result, missing


def interpolate(
    parse_result: ParseResult,
    extra_context: Optional[Dict[str, str]] = None,
) -> InterpolateResult:
    """Interpolate variable references in all entries of *parse_result*.

    Variables are resolved from the entries themselves (in order) plus
    any values supplied in *extra_context*.
    """
    context: Dict[str, str] = dict(extra_context or {})
    resolved_entries: List[EnvEntry] = []
    all_missing: List[str] = []

    for entry in parse_result.entries:
        if entry.key is None or entry.value is None:
            resolved_entries.append(entry)
            continue

        new_value, missing = _resolve_value(entry.value, context)
        all_missing.extend(m for m in missing if m not in all_missing)

        new_entry = EnvEntry(
            key=entry.key,
            value=new_value,
            comment=entry.comment,
            raw=entry.raw,
        )
        resolved_entries.append(new_entry)
        context[entry.key] = new_value

    return InterpolateResult(entries=resolved_entries, unresolved=all_missing)
