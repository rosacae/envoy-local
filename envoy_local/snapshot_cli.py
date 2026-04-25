"""CLI commands for snapshot management."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy_local.snapshot import create_snapshot, load_snapshot, list_snapshots


def cmd_snapshot_create(args: argparse.Namespace) -> int:
    """Create a snapshot of the given .env file."""
    env_path = Path(args.env_file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}", file=sys.stderr)
        return 2

    snap_dir = Path(args.snap_dir) if args.snap_dir else None
    snapshot = create_snapshot(env_path, snap_dir=snap_dir, label=args.label)
    print(f"snapshot created: {snapshot.snapshot_id}")
    if args.verbose:
        print(json.dumps(snapshot.to_dict(), indent=2))
    return 0


def cmd_snapshot_list(args: argparse.Namespace) -> int:
    """List all snapshots for a given .env file."""
    env_path = Path(args.env_file)
    snap_dir = Path(args.snap_dir) if args.snap_dir else None
    snapshots = list_snapshots(env_path, snap_dir=snap_dir)

    if not snapshots:
        print("no snapshots found.")
        return 0

    for snap in snapshots:
        label_part = f"  [{snap.label}]" if snap.label else ""
        print(f"{snap.snapshot_id}  {snap.created_at}{label_part}")
    return 0


def cmd_snapshot_show(args: argparse.Namespace) -> int:
    """Print the contents of a specific snapshot."""
    env_path = Path(args.env_file)
    snap_dir = Path(args.snap_dir) if args.snap_dir else None
    snapshot = load_snapshot(args.snapshot_id, env_path, snap_dir=snap_dir)

    if snapshot is None:
        print(f"error: snapshot not found: {args.snapshot_id}", file=sys.stderr)
        return 2

    print(json.dumps(snapshot.to_dict(), indent=2))
    return 0
