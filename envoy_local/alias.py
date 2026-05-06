"""Key aliasing: map one or more source keys to a new alias name."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.parser import EnvEntry, ParseResult
from envoy_local.serializer import write_env_file


@dataclass
class AliasResult:
    created: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    missing_sources: List[str] = field(default_factory=list)
    entries: List[EnvEntry] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing_sources) == 0

    def summary(self) -> str:
        parts = []
        if self.created:
            parts.append(f"created: {', '.join(self.created)}")
        if self.skipped:
            parts.append(f"skipped: {', '.join(self.skipped)}")
        if self.missing_sources:
            parts.append(f"missing sources: {', '.join(self.missing_sources)}")
        return "; ".join(parts) if parts else "no changes"


def alias_keys(
    result: ParseResult,
    mapping: Dict[str, str],
    overwrite: bool = False,
    output_path: Optional[str] = None,
) -> AliasResult:
    """Add alias entries derived from existing keys.

    Args:
        result: Parsed .env file.
        mapping: Dict of {alias_name: source_key}.
        overwrite: If True, overwrite an existing alias key.
        output_path: If given, write the modified file back to disk.

    Returns:
        AliasResult describing what was created / skipped / missing.
    """
    existing: Dict[str, EnvEntry] = {
        e.key: e for e in result.entries if e.key is not None
    }
    entries = list(result.entries)
    ar = AliasResult(entries=entries)

    for alias, source in mapping.items():
        if source not in existing:
            ar.missing_sources.append(source)
            continue

        source_value = existing[source].value or ""

        if alias in existing and not overwrite:
            ar.skipped.append(alias)
            continue

        new_entry = EnvEntry(
            key=alias,
            value=source_value,
            comment=None,
            original_line=f"{alias}={source_value}",
        )

        if alias in existing:
            # replace in-place
            entries = [
                new_entry if (e.key == alias) else e for e in entries
            ]
        else:
            entries.append(new_entry)

        existing[alias] = new_entry
        ar.created.append(alias)

    ar.entries = entries

    if output_path:
        write_env_file(output_path, entries)

    return ar
