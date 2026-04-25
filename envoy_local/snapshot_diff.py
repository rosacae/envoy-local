"""Compare a current .env file against a previously saved snapshot."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy_local.diff import DiffResult, compute_diff
from envoy_local.parser import parse_env_file
from envoy_local.snapshot import Snapshot, load_snapshot, list_snapshots


def diff_against_snapshot(
    env_path: Path,
    snapshot_id: Optional[str] = None,
    snap_dir: Optional[Path] = None,
) -> tuple[DiffResult, Snapshot]:
    """Return a DiffResult comparing *env_path* to a snapshot.

    If *snapshot_id* is None the most-recent snapshot for *env_path* is used.
    Raises FileNotFoundError when the env file or snapshot cannot be found.
    Raises ValueError when no snapshots exist for the given file.
    """
    if not env_path.exists():
        raise FileNotFoundError(f"Env file not found: {env_path}")

    if snapshot_id is not None:
        snap = load_snapshot(snapshot_id, snap_dir=snap_dir)
        if snap is None:
            raise FileNotFoundError(f"Snapshot not found: {snapshot_id}")
    else:
        snaps = list_snapshots(env_path, snap_dir=snap_dir)
        if not snaps:
            raise ValueError(f"No snapshots found for: {env_path}")
        snap = snaps[-1]  # most recent

    current_entries = parse_env_file(env_path).entries
    snapshot_entries = [
        entry
        for entry in (
            __import__("envoy_local.parser", fromlist=["EnvEntry"]).EnvEntry(
                key=k, value=v, comment=None, raw=f"{k}={v}"
            )
            for k, v in snap.data.items()
        )
    ]

    # Build parsed entries from snapshot dict directly
    from envoy_local.parser import EnvEntry

    snap_entries = [
        EnvEntry(key=k, value=v, comment=None, raw=f"{k}={v}")
        for k, v in snap.data.items()
    ]

    result = compute_diff(snap_entries, current_entries)
    return result, snap
