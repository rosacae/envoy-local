"""Apply a set of key-value patches to an env file (add, update, delete)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from .parser import ParseResult, parse_env_file
from .serializer import write_env_file
from .freeze_integration import guard_frozen


@dataclass
class PatchOptions:
    upsert: Dict[str, str] = field(default_factory=dict)   # key -> new value
    delete: List[str] = field(default_factory=list)         # keys to remove
    overwrite_existing: bool = True


@dataclass
class PatchResult:
    ok: bool
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    deleted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    frozen_blocked: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"added={len(self.added)}")
        if self.updated:
            parts.append(f"updated={len(self.updated)}")
        if self.deleted:
            parts.append(f"deleted={len(self.deleted)}")
        if self.skipped:
            parts.append(f"skipped={len(self.skipped)}")
        if self.frozen_blocked:
            parts.append(f"frozen_blocked={len(self.frozen_blocked)}")
        return ", ".join(parts) if parts else "no changes"


def patch_env_file(
    path: Path,
    options: PatchOptions,
    frozen_keys: Optional[List[str]] = None,
) -> PatchResult:
    if not path.exists():
        return PatchResult(ok=False, error=f"file not found: {path}")

    frozen_keys = frozen_keys or []
    result = parse_env_file(path)
    entries = list(result.entries)
    existing_keys = {e.key: i for i, e in enumerate(entries) if e.key}

    patch_result = PatchResult(ok=True)

    # Handle upserts
    for key, value in options.upsert.items():
        if key in frozen_keys:
            patch_result.frozen_blocked.append(key)
            continue
        if key in existing_keys:
            if options.overwrite_existing:
                entries[existing_keys[key]] = entries[existing_keys[key]].__class__(
                    key=key,
                    value=value,
                    comment=entries[existing_keys[key]].comment,
                    raw=f"{key}={value}",
                )
                patch_result.updated.append(key)
            else:
                patch_result.skipped.append(key)
        else:
            from .parser import EnvEntry
            entries.append(EnvEntry(key=key, value=value, comment=None, raw=f"{key}={value}"))
            patch_result.added.append(key)

    # Handle deletes
    delete_set = set(options.delete)
    new_entries = []
    for entry in entries:
        if entry.key and entry.key in delete_set:
            if entry.key in frozen_keys:
                patch_result.frozen_blocked.append(entry.key)
                new_entries.append(entry)
            else:
                patch_result.deleted.append(entry.key)
        else:
            new_entries.append(entry)

    from .parser import ParseResult as PR
    write_env_file(path, PR(entries=new_entries, errors=result.errors))
    return patch_result
