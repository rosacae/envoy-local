"""Scope support: restrict env entries to a named scope (e.g. 'test', 'prod')."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set
import json

SCOPE_FILE = ".envoy_scopes.json"


@dataclass
class ScopeManifest:
    scopes: Dict[str, Set[str]] = field(default_factory=dict)  # scope -> set of keys

    def to_dict(self) -> dict:
        return {k: sorted(v) for k, v in self.scopes.items()}

    @staticmethod
    def from_dict(data: dict) -> "ScopeManifest":
        return ScopeManifest(scopes={k: set(v) for k, v in data.items()})


def _scope_path(base_dir: Path) -> Path:
    return base_dir / SCOPE_FILE


def load_scopes(base_dir: Path) -> ScopeManifest:
    p = _scope_path(base_dir)
    if not p.exists():
        return ScopeManifest()
    return ScopeManifest.from_dict(json.loads(p.read_text()))


def _save(base_dir: Path, manifest: ScopeManifest) -> None:
    _scope_path(base_dir).write_text(json.dumps(manifest.to_dict(), indent=2))


def add_key_to_scope(base_dir: Path, scope: str, key: str) -> bool:
    """Add key to scope. Returns True if newly added, False if already present."""
    manifest = load_scopes(base_dir)
    bucket = manifest.scopes.setdefault(scope, set())
    if key in bucket:
        return False
    bucket.add(key)
    _save(base_dir, manifest)
    return True


def remove_key_from_scope(base_dir: Path, scope: str, key: str) -> bool:
    """Remove key from scope. Returns True if removed, False if not found."""
    manifest = load_scopes(base_dir)
    bucket = manifest.scopes.get(scope, set())
    if key not in bucket:
        return False
    bucket.discard(key)
    if not bucket:
        del manifest.scopes[scope]
    _save(base_dir, manifest)
    return True


def keys_in_scope(base_dir: Path, scope: str) -> Set[str]:
    return load_scopes(base_dir).scopes.get(scope, set())


def list_scopes(base_dir: Path) -> List[str]:
    return sorted(load_scopes(base_dir).scopes.keys())


def filter_entries_by_scope(entries, base_dir: Path, scope: str):
    """Return only entries whose key belongs to the given scope."""
    allowed = keys_in_scope(base_dir, scope)
    return [e for e in entries if getattr(e, "key", None) in allowed]
