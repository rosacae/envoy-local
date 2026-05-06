"""Utilities for filtering parsed env entries by scope."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from envoy_local.parser import EnvEntry, ParseResult
from envoy_local.scope import keys_in_scope, load_scopes


def filter_parse_result_by_scope(
    result: ParseResult, base_dir: Path, scope: str
) -> ParseResult:
    """Return a new ParseResult containing only entries in the given scope.

    Comment and blank entries are preserved as-is.
    """
    allowed = keys_in_scope(base_dir, scope)
    filtered: List[EnvEntry] = []
    for entry in result.entries:
        if entry.key is None:  # comment or blank line
            filtered.append(entry)
        elif entry.key in allowed:
            filtered.append(entry)
    return ParseResult(entries=filtered)


def scope_coverage(
    result: ParseResult, base_dir: Path, scope: str
) -> Dict[str, bool]:
    """Return a mapping of scope keys -> whether they are present in the parse result."""
    allowed = keys_in_scope(base_dir, scope)
    present = {e.key for e in result.entries if e.key is not None}
    return {k: k in present for k in sorted(allowed)}


def missing_from_scope(
    result: ParseResult, base_dir: Path, scope: str
) -> List[str]:
    """Return scope keys that are not present in the parsed entries."""
    coverage = scope_coverage(result, base_dir, scope)
    return [k for k, found in coverage.items() if not found]


def extra_outside_scope(
    result: ParseResult, base_dir: Path, scope: str
) -> List[str]:
    """Return keys present in the file but not assigned to the scope."""
    allowed = keys_in_scope(base_dir, scope)
    return [
        e.key
        for e in result.entries
        if e.key is not None and e.key not in allowed
    ]
