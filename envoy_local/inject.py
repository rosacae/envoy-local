"""Inject key-value pairs into an existing .env file from CLI args or a dict."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import ParseResult, parse_env_file
from .serializer import entries_to_text, merge_entries, write_env_file
from .parser import EnvEntry


@dataclass
class InjectResult:
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"added: {', '.join(self.added)}")
        if self.updated:
            parts.append(f"updated: {', '.join(self.updated)}")
        if self.skipped:
            parts.append(f"skipped: {', '.join(self.skipped)}")
        return "; ".join(parts) if parts else "no changes"


def inject_keys(
    path: Path,
    pairs: Dict[str, str],
    *,
    overwrite: bool = True,
    create: bool = True,
) -> InjectResult:
    """Inject key=value pairs into *path*.

    Args:
        path: Target .env file.
        pairs: Mapping of key -> value to inject.
        overwrite: When False, existing keys are skipped.
        create: When True, create the file if it does not exist.
    """
    if not pairs:
        return InjectResult()

    if not path.exists():
        if not create:
            return InjectResult(error=f"File not found: {path}")
        existing: List[EnvEntry] = []
    else:
        result: ParseResult = parse_env_file(path)
        existing = list(result.entries)

    existing_keys = {e.key for e in existing if e.key}

    added: List[str] = []
    updated: List[str] = []
    skipped: List[str] = []

    incoming: List[EnvEntry] = []
    for key, value in pairs.items():
        if key in existing_keys:
            if overwrite:
                updated.append(key)
                incoming.append(EnvEntry(key=key, value=value))
            else:
                skipped.append(key)
        else:
            added.append(key)
            incoming.append(EnvEntry(key=key, value=value))

    if not incoming:
        return InjectResult(added=added, updated=updated, skipped=skipped)

    merged = merge_entries(existing, incoming, overwrite=overwrite)
    write_env_file(path, entries_to_text(merged))

    return InjectResult(added=added, updated=updated, skipped=skipped)
