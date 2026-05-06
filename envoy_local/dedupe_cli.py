"""CLI entry-points for the dedupe command."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.dedupe import dedupe_env_file


def build_dedupe_parser(sub: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser(
        "dedupe",
        help="remove duplicate keys from a .env file",
    )
    p.add_argument("file", type=Path, help="target .env file")
    p.add_argument(
        "--keep",
        choices=["first", "last"],
        default="last",
        help="which occurrence to keep when a key appears multiple times (default: last)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="report duplicates without modifying the file",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="suppress output",
    )
    return p


def cmd_dedupe(ns: argparse.Namespace) -> int:
    result = dedupe_env_file(
        ns.file,
        keep=ns.keep,
        dry_run=ns.dry_run,
    )

    if not result.ok:
        print(f"error: {result.error}")
        return 2

    if not ns.quiet:
        print(result.summary())

    return 1 if result.removed else 0
