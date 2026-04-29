"""CLI commands for renaming keys in .env files."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.rename import rename_key
from envoy_local.audit import record


def cmd_rename(ns: argparse.Namespace) -> int:
    """Rename a key in an .env file.

    Returns:
        0  – key renamed successfully
        1  – key not found or file missing
        2  – new key already exists (use --force to overwrite)
    """
    env_path = Path(ns.file)

    if not env_path.exists():
        print(f"error: file not found: {env_path}")
        return 1

    result = rename_key(
        env_path,
        old_key=ns.old_key,
        new_key=ns.new_key,
        force=getattr(ns, "force", False),
    )

    if not result.ok:
        print(f"error: {result.summary()}")
        return 2 if result.conflict else 1

    if getattr(ns, "audit", False):
        record(
            operation="rename",
            target=str(env_path),
            detail=f"{ns.old_key} -> {ns.new_key}",
            audit_dir=Path(ns.audit_dir) if getattr(ns, "audit_dir", None) else None,
        )

    print(result.summary())
    return 0


def build_rename_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("rename", help="Rename a key inside an .env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("old_key", help="Existing key name")
    p.add_argument("new_key", help="New key name")
    p.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Overwrite new_key if it already exists",
    )
    p.add_argument(
        "--audit",
        action="store_true",
        default=False,
        help="Record the operation in the audit log",
    )
    p.add_argument(
        "--audit-dir",
        default=None,
        metavar="DIR",
        help="Directory for audit log (default: .envoy_audit)",
    )
    p.set_defaults(func=cmd_rename)
    return p
