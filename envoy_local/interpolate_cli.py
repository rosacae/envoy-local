"""CLI command: envoy-local interpolate

Reads a .env file, resolves $VAR / ${VAR} references within values,
and writes the result to stdout or an output file.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_local.interpolate import interpolate
from envoy_local.parser import parse_env_file
from envoy_local.serializer import entries_to_text, write_env_file


def cmd_interpolate(ns: argparse.Namespace) -> int:
    src = Path(ns.file)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 2

    parse_result = parse_env_file(src)
    result = interpolate(parse_result)

    if not result.ok and not ns.ignore_missing:
        for key in result.unresolved:
            print(f"warning: unresolved variable: ${key}", file=sys.stderr)
        if ns.strict:
            print("error: unresolved variables in strict mode", file=sys.stderr)
            return 1

    text = entries_to_text(result.entries)

    if ns.output:
        out = Path(ns.output)
        write_env_file(out, result.entries)
        print(f"written to {out}")
    else:
        sys.stdout.write(text)

    return 0


def build_interpolate_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser(
        "interpolate",
        help="Resolve $VAR references within a .env file",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("-o", "--output", metavar="FILE", help="Write result to FILE instead of stdout")
    p.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if any variable cannot be resolved",
    )
    p.add_argument(
        "--ignore-missing",
        action="store_true",
        help="Suppress warnings for unresolved variables",
    )
    p.set_defaults(func=cmd_interpolate)
