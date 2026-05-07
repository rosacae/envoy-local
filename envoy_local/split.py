"""Split a .env file into multiple files based on key prefix groups."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import ParseResult, EnvEntry, parse_env_text
from .serializer import entries_to_text, write_env_file


@dataclass
class SplitResult:
    ok: bool
    files_written: List[Path] = field(default_factory=list)
    ungrouped_count: int = 0
    error: Optional[str] = None

    def summary(self) -> str:
        if not self.ok:
            return f"split failed: {self.error}"
        parts = [f"wrote {len(self.files_written)} file(s)"]
        if self.ungrouped_count:
            parts.append(f"{self.ungrouped_count} ungrouped entry(ies) skipped")
        return ", ".join(parts)


def _prefix_of(key: str, prefixes: List[str]) -> Optional[str]:
    """Return the first matching prefix for *key*, or None."""
    for prefix in prefixes:
        if key.startswith(prefix):
            return prefix
    return None


def split_env_file(
    source: Path,
    output_dir: Path,
    prefixes: List[str],
    *,
    strip_prefix: bool = False,
    overwrite: bool = False,
) -> SplitResult:
    """Split *source* into per-prefix files inside *output_dir*.

    Each key whose name starts with one of *prefixes* lands in a file named
    ``<prefix_lower>.env`` (trailing underscores stripped from the filename).
    Keys that match no prefix are counted as ungrouped and not written.
    """
    if not source.exists():
        return SplitResult(ok=False, error=f"source file not found: {source}")

    text = source.read_text(encoding="utf-8")
    result: ParseResult = parse_env_text(text)

    groups: Dict[str, List[EnvEntry]] = {p: [] for p in prefixes}
    ungrouped = 0

    for entry in result.entries:
        if entry.key is None:
            continue
        matched = _prefix_of(entry.key, prefixes)
        if matched is None:
            ungrouped += 1
            continue
        if strip_prefix:
            entry = EnvEntry(
                key=entry.key[len(matched):],
                value=entry.value,
                comment=entry.comment,
                raw=entry.raw,
            )
        groups[matched].append(entry)

    output_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    for prefix, entries in groups.items():
        if not entries:
            continue
        filename = prefix.rstrip("_").lower() + ".env"
        dest = output_dir / filename
        if dest.exists() and not overwrite:
            return SplitResult(
                ok=False,
                error=f"destination already exists (use overwrite=True): {dest}",
            )
        write_env_file(dest, entries)
        written.append(dest)

    return SplitResult(ok=True, files_written=written, ungrouped_count=ungrouped)
