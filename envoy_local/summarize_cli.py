"""CLI command: envoy summarize — print a summary of an .env file."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy_local.parser import parse_env_file
from envoy_local.redactor import RedactionConfig
from envoy_local.summarize import summarize_parse_result


def cmd_summarize(ns: argparse.Namespace) -> int:
    path = Path(ns.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    result = parse_env_file(path)
    cfg = RedactionConfig(
        extra_patterns=list(ns.secret_pattern) if ns.secret_pattern else []
    )
    summary = summarize_parse_result(result, cfg)

    if ns.json:
        print(json.dumps(summary.to_dict(), indent=2))
        return 0

    print(f"File          : {path}")
    print(f"Total lines   : {summary.total_lines}")
    print(f"Keys          : {summary.key_count}")
    print(f"Empty values  : {summary.empty_value_count}")
    print(f"Secrets       : {summary.secret_count}")
    print(f"Comments      : {summary.comment_count}")
    print(f"Blank lines   : {summary.blank_line_count}")

    if summary.duplicate_keys:
        print(f"Duplicates    : {', '.join(summary.duplicate_keys)}")
    if summary.empty_keys:
        print(f"Empty keys    : {', '.join(summary.empty_keys)}")
    if summary.secret_keys:
        print(f"Secret keys   : {', '.join(summary.secret_keys)}")

    return 0


def build_summarize_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("summarize", help="Print a summary of an .env file")
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--json", action="store_true", default=False, help="Output as JSON"
    )
    p.add_argument(
        "--secret-pattern",
        metavar="PATTERN",
        action="append",
        help="Additional regex pattern to treat as secret (repeatable)",
    )
    p.set_defaults(func=cmd_summarize)
