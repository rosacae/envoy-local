"""Apply default values to missing or empty keys in a parsed env file."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.parser import EnvEntry, ParseResult
from envoy_local.serializer import write_env_file


@dataclass
class DefaultsResult:
    applied: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    entries: List[EnvEntry] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return True

    def summary(self) -> str:
        parts = []
        if self.applied:
            parts.append(f"applied {len(self.applied)} default(s): {', '.join(self.applied)}")
        if self.skipped:
            parts.append(f"skipped {len(self.skipped)} already-set key(s): {', '.join(self.skipped)}")
        if not parts:
            return "no defaults to apply"
        return "; ".join(parts)


def apply_defaults(
    result: ParseResult,
    defaults: Dict[str, str],
    *,
    overwrite_empty: bool = True,
    env_file: Optional[str] = None,
) -> DefaultsResult:
    """Merge *defaults* into *result*, optionally writing back to *env_file*.

    Args:
        result: Parsed entries from an env file.
        defaults: Mapping of key -> default value.
        overwrite_empty: If True, replace existing keys whose value is empty
            string with the provided default.
        env_file: If given, write the updated entries back to this path.

    Returns:
        DefaultsResult describing what changed.
    """
    existing: Dict[str, int] = {}
    for idx, entry in enumerate(result.entries):
        if entry.key:
            existing[entry.key] = idx

    entries = list(result.entries)
    applied: List[str] = []
    skipped: List[str] = []

    for key, default_value in defaults.items():
        if key in existing:
            idx = existing[key]
            current_value = entries[idx].value or ""
            if overwrite_empty and current_value == "":
                entries[idx] = EnvEntry(
                    key=key,
                    value=default_value,
                    comment=entries[idx].comment,
                    raw=f"{key}={default_value}",
                )
                applied.append(key)
            else:
                skipped.append(key)
        else:
            entries.append(
                EnvEntry(
                    key=key,
                    value=default_value,
                    comment=None,
                    raw=f"{key}={default_value}",
                )
            )
            applied.append(key)

    if env_file and applied:
        write_env_file(env_file, entries)

    return DefaultsResult(applied=applied, skipped=skipped, entries=entries)
