"""CLI commands for the strip feature."""
from __future__ import annotations

import argparse
from pathlib import Path

from .strip import strip_keys


def cmd_strip(ns: argparse.Namespace) -> int:
    """Remove one or more keys from a .env file."""
    path = Path(ns.file)
    if not path.exists():
        print(f"error: file not found: {path}")
        return 2

    keys = ns.keys or []
    pattern = getattr(ns, "pattern", None)

    if not keys and not pattern:
        print("error: provide at least one key or --pattern")
        return 2

    try:
        result = strip_keys(
            path,
            keys=keys or None,
            pattern=pattern or None,
            dry_run=ns.dry_run,
        )
    except Exception as exc:  # pragma: no cover
        print(f"error: {exc}")
        return 1

    if ns.dry_run:
        if result.removed:
            print("Would remove: " + ", ".join(result.removed))
        else:
            print("No matching keys found.")
        return 0

    if result.removed:
        print("Removed: " + ", ".join(result.removed))
    else:
        print("No matching keys found.")

    return 0


def build_strip_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("strip", help="Remove keys from a .env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("keys", nargs="*", help="Key names to remove")
    p.add_argument(
        "--pattern",
        metavar="REGEX",
        help="Remove keys whose names match this regular expression",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would be removed without modifying the file",
    )
    p.set_defaults(func=cmd_strip)
    return p
