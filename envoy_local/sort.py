"""Sort keys in a .env file alphabetically or by custom order."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from envoy_local.parser import EnvEntry, ParseResult, parse_env_text
from envoy_local.serializer import entries_to_text, write_env_file


@dataclass
class SortResult:
    ok: bool
    source: str
    original_count: int
    sorted_count: int
    error: Optional[str] = None

    def summary(self) -> str:
        if not self.ok:
            return f"sort failed: {self.error}"
        return (
            f"sorted {self.sorted_count} key(s) in '{self.source}'"
        )


def _entry_sort_key(entry: EnvEntry, reverse: bool) -> tuple:
    """Return a sort key for an entry; comments/blanks sort to their natural position."""
    if entry.key is None:
        # blank lines and comments bubble to top when not reversed, bottom otherwise
        return (1, "") if not reverse else (0, "")
    return (0, entry.key.lower()) if not reverse else (1, entry.key.lower())


def sort_env_file(
    source: Path,
    *,
    dest: Optional[Path] = None,
    reverse: bool = False,
    comments_first: bool = True,
) -> SortResult:
    """Sort entries in *source* and write result to *dest* (defaults to *source*).

    Args:
        source: Path to the .env file to sort.
        dest: Optional output path; overwrites source when omitted.
        reverse: Sort in descending order when True.
        comments_first: Keep comment/blank lines before keyed entries when True.
    """
    if not source.exists():
        return SortResult(
            ok=False,
            source=str(source),
            original_count=0,
            sorted_count=0,
            error=f"file not found: {source}",
        )

    raw = source.read_text(encoding="utf-8")
    result: ParseResult = parse_env_text(raw)

    keyed = [e for e in result.entries if e.key is not None]
    non_keyed = [e for e in result.entries if e.key is None]

    keyed_sorted = sorted(keyed, key=lambda e: e.key.lower(), reverse=reverse)

    if comments_first:
        ordered = non_keyed + keyed_sorted
    else:
        ordered = keyed_sorted + non_keyed

    out_path = dest if dest is not None else source
    write_env_file(out_path, ordered)

    return SortResult(
        ok=True,
        source=str(source),
        original_count=len(result.entries),
        sorted_count=len(keyed_sorted),
    )
