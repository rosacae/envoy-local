"""CLI entry point for the reorder command."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .reorder import reorder_env_file


def cmd_reorder(ns: argparse.Namespace) -> int:
    """Reorder keys in a .env file.

    Returns 0 on success, 2 on file-not-found, 1 on other errors.
    """
    path = Path(ns.file)
    output = Path(ns.output) if getattr(ns, "output", None) else None
    key_order: List[str] = ns.keys

    if not key_order:
        print("error: at least one key must be specified in --keys")
        return 1

    result = reorder_env_file(path, key_order, output=output)

    if not result.ok:
        print(f"error: {result.error}")
        return 2

    print(result.summary())

    if result.unmatched_keys and not getattr(ns, "quiet", False):
        print("warning: keys not found in file: " + ", ".join(result.unmatched_keys))

    return 0


def build_reorder_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("reorder", help="Reorder keys in a .env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--keys",
        nargs="+",
        required=True,
        metavar="KEY",
        help="Desired key order (remaining keys are appended)",
    )
    p.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write result to FILE instead of modifying in place",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress warnings about unmatched keys",
    )
    p.set_defaults(func=cmd_reorder)
    return p
