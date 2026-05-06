"""Sanitize .env values by trimming whitespace, normalizing line endings,
and optionally removing non-printable characters."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional
import re

from envoy_local.parser import EnvEntry, ParseResult


@dataclass
class SanitizeOptions:
    strip_whitespace: bool = True
    remove_non_printable: bool = True
    normalize_quotes: bool = False  # strip surrounding quotes and re-add none


@dataclass
class SanitizeResult:
    entries: List[EnvEntry] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    total: int = 0

    def ok(self) -> bool:
        return True

    def summary(self) -> str:
        return (
            f"Sanitized {self.total} entries; "
            f"{len(self.changed)} value(s) modified."
        )


_NON_PRINTABLE_RE = re.compile(r"[^\x09\x0A\x0D\x20-\x7E]")


def _sanitize_value(
    value: Optional[str],
    opts: SanitizeOptions,
) -> Optional[str]:
    if value is None:
        return value
    result = value
    if opts.strip_whitespace:
        result = result.strip()
    if opts.remove_non_printable:
        result = _NON_PRINTABLE_RE.sub("", result)
    if opts.normalize_quotes:
        # strip surrounding single or double quotes
        if len(result) >= 2 and result[0] in ('"', "'") and result[-1] == result[0]:
            result = result[1:-1]
    return result


def sanitize_entries(
    parse_result: ParseResult,
    opts: Optional[SanitizeOptions] = None,
) -> SanitizeResult:
    if opts is None:
        opts = SanitizeOptions()

    out_entries: List[EnvEntry] = []
    changed: List[str] = []

    for entry in parse_result.entries:
        if entry.key is None or entry.value is None:
            out_entries.append(entry)
            continue

        new_value = _sanitize_value(entry.value, opts)
        if new_value != entry.value:
            changed.append(entry.key)
            entry = EnvEntry(
                key=entry.key,
                value=new_value,
                comment=entry.comment,
                raw=entry.raw,
            )
        out_entries.append(entry)

    return SanitizeResult(
        entries=out_entries,
        changed=changed,
        total=len([e for e in out_entries if e.key is not None]),
    )
