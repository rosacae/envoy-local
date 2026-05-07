"""Annotate .env entries with inline comments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.parser import EnvEntry, ParseResult
from envoy_local.serializer import entry_to_line


@dataclass
class AnnotateResult:
    entries: List[EnvEntry]
    annotated: List[str]  # keys that received a new/updated comment
    skipped: List[str]    # keys not found in annotations map

    def ok(self) -> bool:
        return True

    def summary(self) -> str:
        parts = [f"{len(self.annotated)} annotated"]
        if self.skipped:
            parts.append(f"{len(self.skipped)} keys not in map (skipped)")
        return ", ".join(parts)


def annotate_entries(
    parse_result: ParseResult,
    annotations: Dict[str, str],
    overwrite: bool = True,
) -> AnnotateResult:
    """Attach inline comments to matching entries.

    Args:
        parse_result: Parsed .env entries.
        annotations:  Mapping of key -> comment text (without leading ``#``).
        overwrite:    When *True* replace an existing inline comment;
                      when *False* leave entries that already have a comment.

    Returns:
        AnnotateResult with updated entries and accounting lists.
    """
    annotated: List[str] = []
    skipped: List[str] = []
    updated: List[EnvEntry] = []

    for entry in parse_result.entries:
        if entry.key is None or entry.key not in annotations:
            # Preserve comments/blanks and non-annotated keys as-is.
            if entry.key is not None and entry.key not in annotations:
                skipped.append(entry.key)
            updated.append(entry)
            continue

        comment_text = annotations[entry.key].strip()
        if entry.comment and not overwrite:
            updated.append(entry)
            continue

        new_entry = EnvEntry(
            key=entry.key,
            value=entry.value,
            comment=comment_text,
            raw=entry.raw,
        )
        updated.append(new_entry)
        annotated.append(entry.key)

    return AnnotateResult(entries=updated, annotated=annotated, skipped=skipped)
