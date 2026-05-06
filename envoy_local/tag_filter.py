"""Filter parsed env entries by tag membership."""
from __future__ import annotations

from pathlib import Path
from typing import List, Sequence

from envoy_local.parser import EnvEntry
from envoy_local.tag import load_tags, keys_for_tag, TagManifest


def entries_with_tag(
    entries: Sequence[EnvEntry],
    tag: str,
    base_dir: Path,
) -> List[EnvEntry]:
    """Return only entries whose key carries *tag*."""
    manifest = load_tags(base_dir)
    tagged = set(keys_for_tag(manifest, tag))
    return [e for e in entries if e.key and e.key in tagged]


def entries_without_tag(
    entries: Sequence[EnvEntry],
    tag: str,
    base_dir: Path,
) -> List[EnvEntry]:
    """Return entries whose key does *not* carry *tag* (comments/blanks pass through)."""
    manifest = load_tags(base_dir)
    tagged = set(keys_for_tag(manifest, tag))
    return [e for e in entries if not e.key or e.key not in tagged]


def annotate_entry(
    entry: EnvEntry,
    manifest: TagManifest,
) -> str:
    """Return a display line for *entry* with its tags appended as a comment."""
    tags = manifest.tags.get(entry.key or "", [])
    base = f"{entry.key}={entry.value}" if entry.key else (entry.raw or "")
    if tags:
        return f"{base}  # [{', '.join(tags)}]"
    return base
