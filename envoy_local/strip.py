"""Strip keys from a .env file by name or pattern."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .parser import ParseResult, parse_env_file
from .serializer import entries_to_text, write_env_file


@dataclass
class StripResult:
    removed: List[str] = field(default_factory=list)
    kept: int = 0
    skipped: int = 0  # keys matched by pattern but already absent
    written: bool = False

    @property
    def ok(self) -> bool:
        return self.written

    def summary(self) -> str:
        parts = [f"removed={len(self.removed)}", f"kept={self.kept}"]
        if self.skipped:
            parts.append(f"skipped={self.skipped}")
        return ", ".join(parts)


def strip_keys(
    path: Path,
    keys: Optional[List[str]] = None,
    pattern: Optional[str] = None,
    dry_run: bool = False,
) -> StripResult:
    """Remove matching keys from *path* and write the result in-place.

    At least one of *keys* or *pattern* must be supplied.
    When *dry_run* is True the file is not modified.
    """
    if not keys and not pattern:
        raise ValueError("supply at least one of 'keys' or 'pattern'")

    if not path.exists():
        raise FileNotFoundError(f"{path} does not exist")

    compiled: Optional[re.Pattern] = re.compile(pattern) if pattern else None
    key_set = set(keys or [])

    result_obj = parse_env_file(path)
    kept_entries = []
    removed: List[str] = []

    for entry in result_obj.entries:
        if entry.key is None:
            kept_entries.append(entry)
            continue

        matched = entry.key in key_set or (
            compiled is not None and compiled.search(entry.key) is not None
        )
        if matched:
            removed.append(entry.key)
        else:
            kept_entries.append(entry)

    result = StripResult(
        removed=removed,
        kept=sum(1 for e in kept_entries if e.key is not None),
    )

    if not dry_run:
        text = entries_to_text(kept_entries)
        write_env_file(path, text)
        result.written = True

    return result
