"""CLI commands for grouping env keys."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy_local.group import group_by_prefix, group_by_mapping
from envoy_local.parser import parse_env_file


def cmd_group(ns: argparse.Namespace) -> int:
    src = Path(ns.file)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 2

    result = parse_env_file(src)

    if ns.mapping:
        try:
            raw: dict = json.loads(ns.mapping)
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON mapping: {exc}", file=sys.stderr)
            return 2
        grouped = group_by_mapping(result, raw)
    else:
        prefixes = ns.prefixes.split(",") if ns.prefixes else None
        grouped = group_by_prefix(
            result,
            separator=ns.separator,
            prefixes=prefixes,
        )

    if ns.format == "json":
        print(json.dumps(grouped.to_dict(), indent=2))
    else:
        for group_name, entries in grouped.groups.items():
            print(f"[{group_name}]")
            for e in entries:
                print(f"  {e.key}={e.value}")
        if grouped.ungrouped:
            print("[ungrouped]")
            for e in grouped.ungrouped:
                label = e.key if e.key else "(comment/blank)"
                print(f"  {label}")

    return 0


def build_group_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("group", help="Group env keys by prefix or mapping")
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--separator",
        default="_",
        help="Prefix separator character (default: _)",
    )
    p.add_argument(
        "--prefixes",
        default=None,
        help="Comma-separated list of prefixes to group by",
    )
    p.add_argument(
        "--mapping",
        default=None,
        help='JSON object mapping group names to lists of keys, e.g. \'{"db":["DB_HOST"]}\' ',
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_group)
