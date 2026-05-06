"""Normalize .env file values: quote values with spaces, strip trailing whitespace, etc."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envoy_local.parser import EnvEntry, ParseResult
from envoy_local.serializer import write_env_file


@dataclass
class NormalizeResult:
    changed: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    total: int = 0
    written: bool = False

    @property
    def ok(self) -> bool:
        return True

    def summary(self) -> str:
        parts = []
        if self.changed:
            parts.append(f"{len(self.changed)} key(s) normalized")
        if self.skipped:
            parts.append(f"{len(self.skipped)} key(s) unchanged")
        if not parts:
            return "Nothing to normalize."
        return ", ".join(parts) + f" (of {self.total} total)."


def _normalize_value(value: str) -> str:
    """Apply normalization rules to a single value string."""
    # Strip surrounding whitespace
    normalized = value.strip()
    # If value contains spaces and is not already quoted, wrap in double quotes
    if " " in normalized and not (
        (normalized.startswith('"') and normalized.endswith('"'))
        or (normalized.startswith("'") and normalized.endswith("'"))
    ):
        inner = normalized.replace('"', '\\"')
        normalized = f'"{inner}"'
    return normalized


def normalize_env_file(
    parse_result: ParseResult,
    output_path: Optional[str] = None,
    *,
    source_path: Optional[str] = None,
) -> NormalizeResult:
    """Normalize all keyed entries in *parse_result*.

    If *output_path* is given the result is written to disk.
    If *output_path* is None but *source_path* is given, the source file is
    overwritten in-place.
    """
    result = NormalizeResult()
    updated: List[EnvEntry] = []

    for entry in parse_result.entries:
        if entry.key is None:
            updated.append(entry)
            continue

        result.total += 1
        new_value = _normalize_value(entry.value or "")
        if new_value != (entry.value or ""):
            updated.append(
                EnvEntry(
                    key=entry.key,
                    value=new_value,
                    comment=entry.comment,
                    raw=entry.raw,
                )
            )
            result.changed.append(entry.key)
        else:
            updated.append(entry)
            result.skipped.append(entry.key)

    dest = output_path or source_path
    if dest:
        write_env_file(dest, updated)
        result.written = True

    return result
