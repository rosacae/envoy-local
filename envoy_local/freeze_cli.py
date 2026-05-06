"""CLI commands for freeze/unfreeze key management."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.freeze import freeze_key, unfreeze_key, frozen_keys


def cmd_freeze_add(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.dir) if ns.dir else Path.cwd()
    added = freeze_key(ns.key, base_dir)
    if added:
        print(f"Frozen: {ns.key}")
        return 0
    print(f"Already frozen: {ns.key}")
    return 0


def cmd_freeze_remove(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.dir) if ns.dir else Path.cwd()
    removed = unfreeze_key(ns.key, base_dir)
    if removed:
        print(f"Unfrozen: {ns.key}")
        return 0
    print(f"Key not frozen: {ns.key}")
    return 1


def cmd_freeze_list(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.dir) if ns.dir else Path.cwd()
    keys = frozen_keys(base_dir)
    if not keys:
        print("No frozen keys.")
        return 0
    for k in keys:
        print(k)
    return 0


def build_freeze_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("freeze", help="Manage frozen (locked) keys")
    p.add_argument("--dir", default=None, help="Base directory for freeze manifest")
    fsub = p.add_subparsers(dest="freeze_cmd")

    add_p = fsub.add_parser("add", help="Freeze a key")
    add_p.add_argument("key", help="Key to freeze")
    add_p.set_defaults(func=cmd_freeze_add)

    rm_p = fsub.add_parser("remove", help="Unfreeze a key")
    rm_p.add_argument("key", help="Key to unfreeze")
    rm_p.set_defaults(func=cmd_freeze_remove)

    ls_p = fsub.add_parser("list", help="List frozen keys")
    ls_p.set_defaults(func=cmd_freeze_list)
