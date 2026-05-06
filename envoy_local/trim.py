"""Trim keys from an env file that match a given list or pattern."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envoy_local.parser import ParseResult, EnvEntry, parse_env_file
from envoy_local.serializer import entries_to_text, write_env_file


@dataclass
class TrimResult:
    ok: bool
    trimmed: List[str] = field(default_factory=list)
    kept: int = 0
    error: Optional[str] = None

    def summary(self) -> str:
        if not self.ok:
            return f"error: {self.error}"
        return (
            f"trimmed {len(self.trimmed)} key(s), kept {self.kept}"
        )


def trim_keys(
    path: Path,
    keys: Optional[List[str]] = None,
    pattern: Optional[str] = None,
    dry_run: bool = False,
) -> TrimResult:
    """Remove entries whose key appears in *keys* or matches *pattern*.

    At least one of *keys* or *pattern* must be provided.
    Comments and blank lines are preserved unless their adjacent key is removed.
    """
    if not keys and not pattern:
        return TrimResult(ok=False, error="no keys or pattern provided")

    if not path.exists():
        return TrimResult(ok=False, error=f"file not found: {path}")

    result: ParseResult = parse_env_file(path)

    key_set = set(keys or [])
    compiled: Optional[re.Pattern] = None
    if pattern:
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            return TrimResult(ok=False, error=f"invalid pattern: {exc}")

    def _should_trim(entry: EnvEntry) -> bool:
        if entry.key is None:
            return False
        if entry.key in key_set:
            return True
        if compiled and compiled.search(entry.key):
            return True
        return False

    trimmed_keys: List[str] = []
    kept_entries: List[EnvEntry] = []

    for entry in result.entries:
        if _should_trim(entry):
            assert entry.key is not None
            trimmed_keys.append(entry.key)
        else:
            kept_entries.append(entry)

    if not dry_run:
        text = entries_to_text(kept_entries)
        write_env_file(path, text)

    kept_count = sum(1 for e in kept_entries if e.key is not None)
    return TrimResult(ok=True, trimmed=trimmed_keys, kept=kept_count)
