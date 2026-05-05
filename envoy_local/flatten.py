"""Flatten nested prefix groups into a single env dict with optional prefix stripping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.parser import EnvEntry, ParseResult


@dataclass
class FlattenResult:
    entries: List[EnvEntry] = field(default_factory=list)
    stripped_prefixes: List[str] = field(default_factory=list)
    skipped: int = 0

    def ok(self) -> bool:
        return True

    def summary(self) -> str:
        parts = [f"{len(self.entries)} entries flattened"]
        if self.stripped_prefixes:
            quoted = ", ".join(f"{p!r}" for p in self.stripped_prefixes)
            parts.append(f"prefixes stripped: {quoted}")
        if self.skipped:
            parts.append(f"{self.skipped} skipped (no key)")
        return "; ".join(parts)


def flatten_env(
    result: ParseResult,
    strip_prefixes: Optional[List[str]] = None,
    separator: str = "__",
) -> FlattenResult:
    """Return entries with optional prefix stripping and separator normalisation.

    When *strip_prefixes* is given every key whose prefix matches (case-sensitive)
    has that prefix (and the following separator) removed.  Keys that have no
    ``key`` (blank lines / comments) are passed through unchanged but counted as
    skipped for reporting purposes.
    """
    strip_prefixes = strip_prefixes or []
    out_entries: List[EnvEntry] = []
    used_prefixes: set = set()
    skipped = 0

    for entry in result.entries:
        if not entry.key:
            skipped += 1
            out_entries.append(entry)
            continue

        new_key = entry.key
        for prefix in strip_prefixes:
            token = prefix + separator
            if entry.key.startswith(token):
                new_key = entry.key[len(token):]
                used_prefixes.add(prefix)
                break

        if new_key != entry.key:
            entry = EnvEntry(
                key=new_key,
                value=entry.value,
                comment=entry.comment,
                raw=entry.raw,
            )

        out_entries.append(entry)

    return FlattenResult(
        entries=out_entries,
        stripped_prefixes=sorted(used_prefixes),
        skipped=skipped,
    )


def flatten_to_dict(
    result: ParseResult,
    strip_prefixes: Optional[List[str]] = None,
    separator: str = "__",
) -> Dict[str, str]:
    """Convenience wrapper that returns a plain key→value mapping."""
    flat = flatten_env(result, strip_prefixes=strip_prefixes, separator=separator)
    return {e.key: (e.value or "") for e in flat.entries if e.key}
