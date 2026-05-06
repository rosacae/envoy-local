"""Integration helpers: filter out frozen keys from write operations."""
from __future__ import annotations

from pathlib import Path
from typing import List

from envoy_local.freeze import load_frozen
from envoy_local.parser import EnvEntry


def filter_frozen_entries(
    entries: List[EnvEntry],
    base_dir: Path,
) -> tuple[List[EnvEntry], List[str]]:
    """Return (allowed_entries, skipped_keys) after removing frozen keys."""
    manifest = load_frozen(base_dir)
    frozen = set(manifest.frozen)
    allowed: List[EnvEntry] = []
    skipped: List[str] = []
    for entry in entries:
        if entry.key and entry.key in frozen:
            skipped.append(entry.key)
        else:
            allowed.append(entry)
    return allowed, skipped


def guard_frozen(
    key: str,
    base_dir: Path,
) -> bool:
    """Return True if the key is frozen (i.e. the operation should be blocked)."""
    manifest = load_frozen(base_dir)
    return key in set(manifest.frozen)
