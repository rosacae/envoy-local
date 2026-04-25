"""Audit log for tracking env file operations (sync, put, delete, etc.)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


@dataclass
class AuditEntry:
    timestamp: str
    operation: str
    target: str
    keys: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "target": self.target,
            "keys": self.keys,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            timestamp=data["timestamp"],
            operation=data["operation"],
            target=data["target"],
            keys=data.get("keys", []),
            note=data.get("note"),
        )


def _audit_path(log_dir: Path) -> Path:
    return log_dir / "audit.jsonl"


def record(
    operation: str,
    target: str,
    keys: List[str],
    log_dir: Path,
    note: Optional[str] = None,
) -> AuditEntry:
    """Append a new audit entry to the JSONL log and return it."""
    entry = AuditEntry(
        timestamp=datetime.now(timezone.utc).isoformat(),
        operation=operation,
        target=target,
        keys=keys,
        note=note,
    )
    log_dir.mkdir(parents=True, exist_ok=True)
    with _audit_path(log_dir).open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry.to_dict()) + "\n")
    return entry


def load_log(log_dir: Path) -> List[AuditEntry]:
    """Read all audit entries from the JSONL log file."""
    path = _audit_path(log_dir)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(AuditEntry.from_dict(json.loads(line)))
    return entries
