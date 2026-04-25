"""Diff utilities for comparing .env files and showing changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.parser import EnvEntry, ParseResult


@dataclass
class DiffEntry:
    key: str
    status: str  # 'added' | 'removed' | 'changed' | 'unchanged'
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    @property
    def is_changed(self) -> bool:
        return self.status != "unchanged"


@dataclass
class DiffResult:
    entries: List[DiffEntry] = field(default_factory=list)

    @property
    def added(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "added"]

    @property
    def removed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "removed"]

    @property
    def changed(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "changed"]

    @property
    def unchanged(self) -> List[DiffEntry]:
        return [e for e in self.entries if e.status == "unchanged"]

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"+{len(self.added)} added")
        if self.removed:
            parts.append(f"-{len(self.removed)} removed")
        if self.changed:
            parts.append(f"~{len(self.changed)} changed")
        if not parts:
            return "No changes"
        return ", ".join(parts)


def diff_env(source: ParseResult, target: ParseResult) -> DiffResult:
    """Compare two ParseResult objects and return a DiffResult."""
    source_dict: Dict[str, str] = {
        e.key: (e.value or "") for e in source.entries if e.key
    }
    target_dict: Dict[str, str] = {
        e.key: (e.value or "") for e in target.entries if e.key
    }

    all_keys = sorted(set(source_dict) | set(target_dict))
    entries: List[DiffEntry] = []

    for key in all_keys:
        in_source = key in source_dict
        in_target = key in target_dict

        if in_source and not in_target:
            entries.append(DiffEntry(key=key, status="removed", old_value=source_dict[key]))
        elif in_target and not in_source:
            entries.append(DiffEntry(key=key, status="added", new_value=target_dict[key]))
        elif source_dict[key] != target_dict[key]:
            entries.append(
                DiffEntry(
                    key=key,
                    status="changed",
                    old_value=source_dict[key],
                    new_value=target_dict[key],
                )
            )
        else:
            entries.append(
                DiffEntry(key=key, status="unchanged", old_value=source_dict[key], new_value=target_dict[key])
            )

    return DiffResult(entries=entries)
