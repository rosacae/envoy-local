"""Detect and remove duplicate keys from a .env file."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envoy_local.parser import ParseResult, EnvEntry, parse_env_file
from envoy_local.serializer import entries_to_text, write_env_file


@dataclass
class DedupeResult:
    removed: List[str] = field(default_factory=list)
    kept: List[EnvEntry] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        if not self.ok:
            return f"error: {self.error}"
        if not self.removed:
            return "no duplicate keys found"
        keys = ", ".join(self.removed)
        return f"removed {len(self.removed)} duplicate(s): {keys}"


def dedupe_env_file(
    path: Path,
    *,
    keep: str = "last",
    dry_run: bool = False,
) -> DedupeResult:
    """Remove duplicate keys from *path*, keeping either the first or last
    occurrence depending on *keep* ('first' | 'last').

    When *dry_run* is True the file is not written.
    """
    if not path.exists():
        return DedupeResult(error=f"file not found: {path}")

    result: ParseResult = parse_env_file(path)

    seen: dict[str, int] = {}
    for idx, entry in enumerate(result.entries):
        if entry.key:
            seen[entry.key] = idx

    if keep == "first":
        # re-scan to keep first index
        seen_first: dict[str, int] = {}
        for idx, entry in enumerate(result.entries):
            if entry.key and entry.key not in seen_first:
                seen_first[entry.key] = idx
        seen = seen_first

    kept_indices = set(seen.values())
    removed_keys: List[str] = []
    kept_entries: List[EnvEntry] = []

    for idx, entry in enumerate(result.entries):
        if entry.key and idx not in kept_indices:
            removed_keys.append(entry.key)
        else:
            kept_entries.append(entry)

    if removed_keys and not dry_run:
        write_env_file(path, entries_to_text(kept_entries))

    return DedupeResult(removed=removed_keys, kept=kept_entries)
