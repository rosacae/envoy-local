"""Tag management for .env entries — attach labels to keys for filtering and grouping."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json
from typing import Dict, List, Optional


_TAG_FILE = ".envoy_tags.json"


@dataclass
class TagManifest:
    tags: Dict[str, List[str]] = field(default_factory=dict)  # key -> [tag, ...]

    def to_dict(self) -> dict:
        return {"tags": self.tags}

    @staticmethod
    def from_dict(data: dict) -> "TagManifest":
        return TagManifest(tags=data.get("tags", {}))


def _tag_path(base_dir: Path) -> Path:
    return base_dir / _TAG_FILE


def load_tags(base_dir: Path) -> TagManifest:
    p = _tag_path(base_dir)
    if not p.exists():
        return TagManifest()
    return TagManifest.from_dict(json.loads(p.read_text()))


def _save_tags(base_dir: Path, manifest: TagManifest) -> None:
    _tag_path(base_dir).write_text(json.dumps(manifest.to_dict(), indent=2))


def add_tag(base_dir: Path, key: str, tag: str) -> bool:
    """Add *tag* to *key*.  Returns True if the tag was newly added."""
    manifest = load_tags(base_dir)
    existing = manifest.tags.setdefault(key, [])
    if tag in existing:
        return False
    existing.append(tag)
    _save_tags(base_dir, manifest)
    return True


def remove_tag(base_dir: Path, key: str, tag: str) -> bool:
    """Remove *tag* from *key*.  Returns True if the tag existed."""
    manifest = load_tags(base_dir)
    existing = manifest.tags.get(key, [])
    if tag not in existing:
        return False
    existing.remove(tag)
    if not existing:
        manifest.tags.pop(key, None)
    _save_tags(base_dir, manifest)
    return True


def keys_for_tag(manifest: TagManifest, tag: str) -> List[str]:
    """Return all keys that carry *tag*."""
    return [k for k, tags in manifest.tags.items() if tag in tags]


def tags_for_key(manifest: TagManifest, key: str) -> List[str]:
    """Return all tags attached to *key*."""
    return list(manifest.tags.get(key, []))
