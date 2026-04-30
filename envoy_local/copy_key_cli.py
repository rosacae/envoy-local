"""CLI commands for copy_key: copy a key from one .env file to another."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.copy_key import copy_key, CopyKeyResult


def cmd_copy_key(ns: argparse.Namespace) -> int:
    """Entry point for `envoy copy-key`."""
    source = Path(ns.source)
    dest = Path(ns.dest)

    if not source.exists():
        print(f"error: source file not found: {source}")
        return 2

    result: CopyKeyResult = copy_key(
        source=source,
        dest=dest,
        key=ns.key,
        dest_key=ns.dest_key,
        overwrite=ns.overwrite,
    )

    if not result.ok:
        print(f"error: {result.message}")
        return 1

    print(result.summary())
    return 0


def build_copy_key_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser(
        "copy-key",
        help="Copy a key from one .env file to another",
    )
    p.add_argument("source", help="Source .env file")
    p.add_argument("dest", help="Destination .env file")
    p.add_argument("key", help="Key to copy from source")
    p.add_argument(
        "--dest-key",
        default=None,
        metavar="NAME",
        help="Key name to use in destination (defaults to same as source key)",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the key in destination if it already exists",
    )
    p.set_defaults(func=cmd_copy_key)
