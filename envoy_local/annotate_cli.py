"""CLI commands for annotate feature."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy_local.annotate import annotate_entries
from envoy_local.parser import parse_env_file
from envoy_local.serializer import write_env_file


def _parse_pair(pair: str) -> tuple[str, str]:
    if "=" not in pair:
        raise argparse.ArgumentTypeError(
            f"Annotation must be KEY=comment, got: {pair!r}"
        )
    key, _, comment = pair.partition("=")
    return key.strip(), comment.strip()


def cmd_annotate(ns: argparse.Namespace) -> int:
    src = Path(ns.file)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 2

    parse_result = parse_env_file(src)

    # Build annotations dict from --set pairs or --from-json file.
    annotations: dict[str, str] = {}
    if ns.set:
        for pair in ns.set:
            try:
                k, v = _parse_pair(pair)
                annotations[k] = v
            except argparse.ArgumentTypeError as exc:
                print(f"error: {exc}", file=sys.stderr)
                return 2

    if ns.from_json:
        json_path = Path(ns.from_json)
        if not json_path.exists():
            print(f"error: annotations file not found: {json_path}", file=sys.stderr)
            return 2
        try:
            annotations.update(json.loads(json_path.read_text()))
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON: {exc}", file=sys.stderr)
            return 2

    if not annotations:
        print("error: no annotations provided (use --set or --from-json)", file=sys.stderr)
        return 2

    result = annotate_entries(parse_result, annotations, overwrite=not ns.no_overwrite)

    out_path = Path(ns.output) if ns.output else src
    write_env_file(out_path, result.entries)

    print(result.summary())
    return 0


def build_annotate_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("annotate", help="Attach inline comments to .env keys")
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--set", metavar="KEY=comment", action="append",
        help="Annotation pair (repeatable)",
    )
    p.add_argument("--from-json", metavar="FILE", help="JSON file mapping key -> comment")
    p.add_argument("--output", "-o", metavar="FILE", help="Output file (default: overwrite input)")
    p.add_argument(
        "--no-overwrite", action="store_true",
        help="Skip keys that already have an inline comment",
    )
    p.set_defaults(func=cmd_annotate)
