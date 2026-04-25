"""CLI commands for viewing the envoy-local audit log."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from envoy_local.audit import load_log

_DEFAULT_LOG_DIR = Path(".envoy/audit")


def cmd_audit_log(
    log_dir: Optional[Path] = None,
    output_format: str = "text",
    operation_filter: Optional[str] = None,
    limit: Optional[int] = None,
) -> int:
    """Print audit log entries.  Returns 0 on success, 1 on error."""
    resolved_dir = log_dir or _DEFAULT_LOG_DIR
    try:
        entries = load_log(resolved_dir)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not read audit log: {exc}")
        return 1

    if operation_filter:
        entries = [e for e in entries if e.operation == operation_filter]

    if not entries:
        print("No audit entries found.")
        return 0

    if limit is not None:
        entries = entries[-limit:]

    if output_format == "json":
        print(json.dumps([e.to_dict() for e in entries], indent=2))
    else:
        for e in entries:
            keys_str = ", ".join(e.keys) if e.keys else "—"
            note_str = f"  # {e.note}" if e.note else ""
            print(f"[{e.timestamp}] {e.operation:12s} {e.target}  keys=[{keys_str}]{note_str}")

    return 0
