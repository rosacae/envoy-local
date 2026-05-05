"""CLI commands for the transform feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_local.parser import parse_env_file
from envoy_local.serializer import write_env_file
from envoy_local.transform import TransformOptions, transform_entries


def cmd_transform(ns: argparse.Namespace) -> int:
    src = Path(ns.file)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 2

    parse_result = parse_env_file(src)
    if not parse_result.ok:
        print(f"error: could not parse {src}", file=sys.stderr)
        return 2

    opts = TransformOptions(
        uppercase_keys=getattr(ns, "uppercase", False),
        strip_values=getattr(ns, "strip_values", False),
        prefix=getattr(ns, "prefix", "") or "",
        suffix=getattr(ns, "suffix", "") or "",
        remove_prefix=getattr(ns, "remove_prefix", "") or "",
    )

    result = transform_entries(parse_result, opts)

    dest = Path(ns.output) if getattr(ns, "output", None) else src
    write_env_file(dest, result.entries)

    if not getattr(ns, "quiet", False):
        print(result.summary())

    return 0


def build_transform_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("transform", help="Transform keys and values in a .env file")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("-o", "--output", help="Output file (defaults to in-place)")
    p.add_argument("--uppercase", action="store_true", help="Uppercase all keys")
    p.add_argument("--strip-values", action="store_true", help="Strip whitespace from values")
    p.add_argument("--prefix", default="", help="Add prefix to all keys")
    p.add_argument("--suffix", default="", help="Add suffix to all keys")
    p.add_argument("--remove-prefix", default="", metavar="PREFIX", help="Remove prefix from keys")
    p.add_argument("-q", "--quiet", action="store_true", help="Suppress summary output")
    p.set_defaults(func=cmd_transform)
