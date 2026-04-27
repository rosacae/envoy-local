"""Pin management: lock specific env keys to fixed values that survive syncs."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


PIN_FILE_NAME = ".env.pins"


@dataclass
class PinManifest:
    """Maps key names to pinned values."""
    pins: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {"pins": self.pins}

    @classmethod
    def from_dict(cls, data: dict) -> "PinManifest":
        return cls(pins=dict(data.get("pins", {})))


def _pin_path(directory: Path) -> Path:
    return directory / PIN_FILE_NAME


def load_pins(directory: Path) -> PinManifest:
    path = _pin_path(directory)
    if not path.exists():
        return PinManifest()
    data = json.loads(path.read_text(encoding="utf-8"))
    return PinManifest.from_dict(data)


def save_pins(directory: Path, manifest: PinManifest) -> None:
    path = _pin_path(directory)
    path.write_text(json.dumps(manifest.to_dict(), indent=2), encoding="utf-8")


def pin_key(directory: Path, key: str, value: str) -> PinManifest:
    manifest = load_pins(directory)
    manifest.pins[key] = value
    save_pins(directory, manifest)
    return manifest


def unpin_key(directory: Path, key: str) -> bool:
    """Remove a pin. Returns True if the key was pinned, False otherwise."""
    manifest = load_pins(directory)
    if key not in manifest.pins:
        return False
    del manifest.pins[key]
    save_pins(directory, manifest)
    return True


def apply_pins(entries: List, manifest: PinManifest) -> List:
    """Return a new list of EnvEntry objects with pinned values applied."""
    from envoy_local.parser import EnvEntry  # avoid circular at module level
    result = []
    for entry in entries:
        if entry.key and entry.key in manifest.pins:
            result.append(EnvEntry(
                key=entry.key,
                value=manifest.pins[entry.key],
                comment=entry.comment,
                raw=entry.raw,
            ))
        else:
            result.append(entry)
    return result


def list_pins(directory: Path) -> Dict[str, str]:
    return load_pins(directory).pins
