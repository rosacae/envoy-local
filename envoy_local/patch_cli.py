"""CLI commands for patch: apply key-value patches to an env file."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List

from .patch import PatchOptions, patch_env_file
from .freeze import load_frozen


def _parse_pair(s: str) -> tuple[str, str]:
    if "=" not in s:
        raise argparse.ArgumentTypeError(f"Expected KEY=VALUE, got: {s!r}")
    k, _, v = s.partition("=")
    return k.strip(), v


def cmd_patch(ns: argparse.Namespace) -> int:
    path = Path(ns.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    upsert: dict[str, str] = {}
    for pair in ns.set or []:
        try:
            k, v = _parse_pair(pair)
            upsert[k] = v
        except argparse.ArgumentTypeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    frozen_keys: List[str] = []
    if not ns.ignore_frozen:
        manifest = load_frozen(path.parent)
        frozen_keys = list(manifest.keys)

    options = PatchOptions(
        upsert=upsert,
        delete=list(ns.delete or []),
        overwrite_existing=not ns.no_overwrite,
    )

    result = patch_env_file(path, options, frozen_keys=frozen_keys)

    if not result.ok:
        print(f"error: {result.error}", file=sys.stderr)
        return 2

    if ns.verbose:
        if result.added:
            print(f"added: {', '.join(result.added)}")
        if result.updated:
            print(f"updated: {', '.join(result.updated)}")
        if result.deleted:
            print(f"deleted: {', '.join(result.deleted)}")
        if result.skipped:
            print(f"skipped: {', '.join(result.skipped)}")
        if result.frozen_blocked:
            print(f"frozen (blocked): {', '.join(result.frozen_blocked)}")

    print(result.summary())
    return 0


def build_patch_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser("patch", help="Apply key-value patches to an env file")
    p.add_argument("file", help="Target .env file")
    p.add_argument("--set", metavar="KEY=VALUE", action="append",
                   help="Set a key (can be repeated)")
    p.add_argument("--delete", metavar="KEY", action="append",
                   help="Delete a key (can be repeated)")
    p.add_argument("--no-overwrite", action="store_true",
                   help="Skip keys that already exist")
    p.add_argument("--ignore-frozen", action="store_true",
                   help="Apply patches even to frozen keys")
    p.add_argument("--verbose", "-v", action="store_true")
    p.set_defaults(func=cmd_patch)
    return p
