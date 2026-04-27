"""CLI commands for cascade env loading."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy_local.cascade import CascadeOptions, cascade_env_files
from envoy_local.serializer import entries_to_text


def cmd_cascade(
    ns: argparse.Namespace,
    out=sys.stdout,
    err=sys.stderr,
) -> int:
    """Merge FILES in order (later overrides earlier) and print the result."""
    files = [Path(f) for f in ns.files]
    if not files:
        err.write("cascade: at least one file required\n")
        return 2

    options = CascadeOptions(
        files=files,
        ignore_missing=getattr(ns, "ignore_missing", False),
    )

    try:
        result = cascade_env_files(options)
    except FileNotFoundError as exc:
        err.write(f"cascade: {exc}\n")
        return 2

    fmt = getattr(ns, "format", "env")

    if fmt == "json":
        out.write(json.dumps(result.as_dict(), indent=2))
        out.write("\n")
    else:
        text = entries_to_text(result.entries)
        out.write(text)
        if text and not text.endswith("\n"):
            out.write("\n")

    if getattr(ns, "summary", False):
        err.write(result.summary() + "\n")

    return 0


def build_cascade_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "cascade",
        help="merge multiple .env files in priority order (later files win)",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="FILE",
        help=".env files to merge, in ascending priority order",
    )
    p.add_argument(
        "--ignore-missing",
        action="store_true",
        default=False,
        help="silently skip files that do not exist",
    )
    p.add_argument(
        "--format",
        choices=["env", "json"],
        default="env",
        help="output format (default: env)",
    )
    p.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="print a summary line to stderr",
    )
    p.set_defaults(func=cmd_cascade)
