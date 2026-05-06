"""CLI commands for the alias feature."""
from __future__ import annotations

import argparse
import sys
from typing import List

from envoy_local.alias import alias_keys
from envoy_local.parser import parse_env_file


def _parse_pair(raw: str):
    """Parse 'ALIAS=SOURCE' pair."""
    if "=" not in raw:
        raise argparse.ArgumentTypeError(
            f"Invalid alias mapping {raw!r}. Expected ALIAS=SOURCE_KEY."
        )
    alias, source = raw.split("=", 1)
    return alias.strip(), source.strip()


def cmd_alias(ns: argparse.Namespace) -> int:
    parsed = parse_env_file(ns.file)
    if not parsed.ok:
        print(f"error: cannot parse {ns.file}", file=sys.stderr)
        return 2

    mapping = {}
    for raw in ns.mapping:
        try:
            alias, source = _parse_pair(raw)
        except argparse.ArgumentTypeError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        mapping[alias] = source

    result = alias_keys(
        parsed,
        mapping,
        overwrite=ns.overwrite,
        output_path=ns.file if not ns.dry_run else None,
    )

    for alias in result.created:
        print(f"created alias: {alias} -> {mapping[alias]}")
    for alias in result.skipped:
        print(f"skipped (already exists): {alias}")
    for src in result.missing_sources:
        print(f"warning: source key not found: {src}", file=sys.stderr)

    if result.missing_sources:
        return 1
    return 0


def build_alias_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:
    p = sub.add_parser("alias", help="Create alias keys derived from existing keys")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "mapping",
        nargs="+",
        metavar="ALIAS=SOURCE",
        help="One or more alias=source_key pairs",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite the alias key if it already exists",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Preview changes without writing to disk",
    )
    p.set_defaults(func=cmd_alias)
    return p
