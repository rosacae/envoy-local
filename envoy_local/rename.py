"""Rename a key across one or more .env files."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from envoy_local.parser import ParseResult, parse_env_file
from envoy_local.serializer import entries_to_text, write_env_file


@dataclass
class RenameResult:
    old_key: str
    new_key: str
    files_modified: List[Path]
    files_skipped: List[Path]  # key not found

    @property
    def ok(self) -> bool:
        return len(self.files_modified) > 0

    def summary(self) -> str:
        parts = []
        if self.files_modified:
            paths = ", ".join(str(p) for p in self.files_modified)
            parts.append(f"Renamed '{self.old_key}' -> '{self.new_key}' in: {paths}")
        if self.files_skipped:
            paths = ", ".join(str(p) for p in self.files_skipped)
            parts.append(f"Key '{self.old_key}' not found in: {paths}")
        return "\n".join(parts) if parts else "Nothing changed."


def rename_key(
    files: List[Path],
    old_key: str,
    new_key: str,
    dry_run: bool = False,
) -> RenameResult:
    """Rename *old_key* to *new_key* in each file that contains it.

    If *dry_run* is True the files are not written.
    """
    modified: List[Path] = []
    skipped: List[Path] = []

    for path in files:
        if not path.exists():
            skipped.append(path)
            continue

        result: ParseResult = parse_env_file(path)
        found = False
        new_entries = []
        for entry in result.entries:
            if entry.key == old_key:
                from envoy_local.parser import EnvEntry
                new_entries.append(
                    EnvEntry(
                        key=new_key,
                        value=entry.value,
                        comment=entry.comment,
                        raw=entry.raw,
                    )
                )
                found = True
            else:
                new_entries.append(entry)

        if not found:
            skipped.append(path)
            continue

        if not dry_run:
            text = entries_to_text(new_entries)
            write_env_file(path, text)

        modified.append(path)

    return RenameResult(
        old_key=old_key,
        new_key=new_key,
        files_modified=modified,
        files_skipped=skipped,
    )
