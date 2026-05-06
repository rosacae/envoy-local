"""Filter entries from a parsed .env file by key pattern, value pattern, or presence of a value."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envoy_local.parser import EnvEntry, ParseResult


@dataclass
class FilterOptions:
    key_pattern: Optional[str] = None        # regex applied to key
    value_pattern: Optional[str] = None      # regex applied to value
    only_empty: bool = False                 # keep entries whose value is empty
    only_set: bool = False                   # keep entries whose value is non-empty
    invert: bool = False                     # invert the match


@dataclass
class FilterResult:
    matched: List[EnvEntry] = field(default_factory=list)
    skipped: List[EnvEntry] = field(default_factory=list)
    total: int = 0

    def summary(self) -> str:
        return (
            f"{len(self.matched)} matched, "
            f"{len(self.skipped)} skipped "
            f"(of {self.total} entries)"
        )

    def to_dict(self) -> dict:
        return {
            "matched": [e.key for e in self.matched if e.key],
            "skipped": [e.key for e in self.skipped if e.key],
            "total": self.total,
        }


def _entry_matches(entry: EnvEntry, opts: FilterOptions) -> bool:
    """Return True if *entry* satisfies all active filter criteria."""
    # Comments and blank lines are never matched by value/key filters
    if entry.key is None:
        return False

    if opts.key_pattern:
        if not re.search(opts.key_pattern, entry.key):
            return False

    value = entry.value or ""

    if opts.value_pattern:
        if not re.search(opts.value_pattern, value):
            return False

    if opts.only_empty and value != "":
        return False

    if opts.only_set and value == "":
        return False

    return True


def filter_entries(result: ParseResult, opts: FilterOptions) -> FilterResult:
    """Filter *result* entries according to *opts*."""
    matched: List[EnvEntry] = []
    skipped: List[EnvEntry] = []

    for entry in result.entries:
        # Structural entries (comments / blanks) go straight to skipped
        if entry.key is None:
            skipped.append(entry)
            continue

        hit = _entry_matches(entry, opts)
        if opts.invert:
            hit = not hit

        if hit:
            matched.append(entry)
        else:
            skipped.append(entry)

    return FilterResult(
        matched=matched,
        skipped=skipped,
        total=len(result.entries),
    )
