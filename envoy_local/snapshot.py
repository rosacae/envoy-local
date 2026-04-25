"""Snapshot support: capture and restore .env file states."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from envoy_local.parser import ParseResult, parse_env_file
from envoy_local.serializer import entries_to_text, write_env_file

DEFAULT_SNAPSHOT_DIR = Path(".envoy_snapshots")


@dataclass
class Snapshot:
    label: str
    source_path: str
    created_at: str
    entries: Dict[str, str]  # key -> raw value

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "source_path": self.source_path,
            "created_at": self.created_at,
            "entries": self.entries,
        }

    @staticmethod
    def from_dict(data: dict) -> "Snapshot":
        return Snapshot(
            label=data["label"],
            source_path=data["source_path"],
            created_at=data["created_at"],
            entries=data["entries"],
        )


def _snapshot_path(snapshot_dir: Path, label: str) -> Path:
    safe_label = label.replace(os.sep, "_").replace(" ", "_")
    return snapshot_dir / f"{safe_label}.json"


def create_snapshot(
    env_path: Path,
    label: Optional[str] = None,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> Snapshot:
    """Parse *env_path* and persist a snapshot under *label*."""
    result: ParseResult = parse_env_file(env_path)
    entries = {e.key: e.raw_value for e in result.entries}
    ts = datetime.now(timezone.utc).isoformat()
    effective_label = label or ts
    snap = Snapshot(
        label=effective_label,
        source_path=str(env_path),
        created_at=ts,
        entries=entries,
    )
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    _snapshot_path(snapshot_dir, effective_label).write_text(
        json.dumps(snap.to_dict(), indent=2), encoding="utf-8"
    )
    return snap


def load_snapshot(label: str, snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> Snapshot:
    """Load a previously saved snapshot by *label*."""
    path = _snapshot_path(snapshot_dir, label)
    if not path.exists():
        raise FileNotFoundError(f"Snapshot '{label}' not found at {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return Snapshot.from_dict(data)


def list_snapshots(snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR) -> List[str]:
    """Return sorted list of snapshot labels available in *snapshot_dir*."""
    if not snapshot_dir.exists():
        return []
    return sorted(p.stem for p in snapshot_dir.glob("*.json"))


def restore_snapshot(
    label: str,
    target_path: Optional[Path] = None,
    snapshot_dir: Path = DEFAULT_SNAPSHOT_DIR,
) -> Path:
    """Write snapshot entries back to a .env file.

    Uses *target_path* when provided, otherwise restores to the original path.
    Returns the path written.
    """
    snap = load_snapshot(label, snapshot_dir)
    out_path = target_path or Path(snap.source_path)
    lines = [f"{k}={v}" for k, v in snap.entries.items()]
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path
