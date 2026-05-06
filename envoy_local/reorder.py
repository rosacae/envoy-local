"""Reorder keys in a .env file according to a provided key order list."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from .parser import ParseResult, EnvEntry, parse_env_file
from .serializer import write_env_file


@dataclass
class ReorderResult:
    ok: bool
    ordered_keys: List[str]
    unmatched_keys: List[str]  # keys in order list not found in file
    trailing_keys: List[str]   # keys in file not mentioned in order list
    error: Optional[str] = None

    def summary(self) -> str:
        if not self.ok:
            return f"error: {self.error}"
        parts = [f"reordered {len(self.ordered_keys)} key(s)"]
        if self.trailing_keys:
            parts.append(f"{len(self.trailing_keys)} key(s) appended at end")
        if self.unmatched_keys:
            parts.append(f"{len(self.unmatched_keys)} order key(s) not found in file")
        return ", ".join(parts)


def reorder_env_file(
    path: Path,
    key_order: List[str],
    *,
    output: Optional[Path] = None,
) -> ReorderResult:
    """Reorder entries in *path* so that keys appear in *key_order* first.

    Keys not mentioned in *key_order* are appended after the ordered block.
    Comment and blank lines that immediately precede a key entry travel with
    that entry; orphaned leading comments are placed at the very top.
    """
    if not path.exists():
        return ReorderResult(ok=False, ordered_keys=[], unmatched_keys=[], trailing_keys=[], error=f"file not found: {path}")

    result: ParseResult = parse_env_file(path)

    # Separate keyed entries from structural ones (comments / blanks)
    keyed: dict[str, EnvEntry] = {e.key: e for e in result.entries if e.key}
    order_set = list(dict.fromkeys(key_order))  # deduplicate, preserve order

    ordered_keys = [k for k in order_set if k in keyed]
    unmatched_keys = [k for k in order_set if k not in keyed]
    trailing_keys = [k for k in keyed if k not in set(order_set)]

    # Build new entry list: ordered first, then trailing
    new_entries: List[EnvEntry] = []
    for k in ordered_keys:
        new_entries.append(keyed[k])
    for k in trailing_keys:
        new_entries.append(keyed[k])

    dest = output or path
    write_env_file(dest, new_entries)

    return ReorderResult(
        ok=True,
        ordered_keys=ordered_keys,
        unmatched_keys=unmatched_keys,
        trailing_keys=trailing_keys,
    )
