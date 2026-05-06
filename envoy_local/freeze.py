"""Freeze: lock specific keys so they cannot be modified by sync/merge operations."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class FreezeManifest:
    frozen: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"frozen": sorted(self.frozen)}

    @classmethod
    def from_dict(cls, data: dict) -> "FreezeManifest":
        return cls(frozen=list(data.get("frozen", [])))


def _freeze_path(base_dir: Path) -> Path:
    return base_dir / ".envoy_frozen.json"


def load_frozen(base_dir: Path) -> FreezeManifest:
    path = _freeze_path(base_dir)
    if not path.exists():
        return FreezeManifest()
    data = json.loads(path.read_text(encoding="utf-8"))
    return FreezeManifest.from_dict(data)


def _save(manifest: FreezeManifest, base_dir: Path) -> None:
    path = _freeze_path(base_dir)
    path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")


def freeze_key(key: str, base_dir: Path) -> bool:
    """Add key to frozen set. Returns True if newly frozen, False if already frozen."""
    manifest = load_frozen(base_dir)
    if key in manifest.frozen:
        return False
    manifest.frozen.append(key)
    _save(manifest, base_dir)
    return True


def unfreeze_key(key: str, base_dir: Path) -> bool:
    """Remove key from frozen set. Returns True if removed, False if not present."""
    manifest = load_frozen(base_dir)
    if key not in manifest.frozen:
        return False
    manifest.frozen.remove(key)
    _save(manifest, base_dir)
    return True


def is_frozen(key: str, base_dir: Path) -> bool:
    return key in load_frozen(base_dir).frozen


def frozen_keys(base_dir: Path) -> List[str]:
    return sorted(load_frozen(base_dir).frozen)
