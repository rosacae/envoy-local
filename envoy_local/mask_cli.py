"""CLI commands for the mask feature."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_local.mask import MaskOptions, mask_entries
from envoy_local.parser import parse_env_file
from envoy_local.redactor import RedactionConfig, Redactor
from envoy_local.serializer import entries_to_text


def build_mask_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("mask", help="Print .env file with secret values masked")
    p.add_argument("file", help="Path to .env file")
    p.add_argument(
        "--visible",
        type=int,
        default=4,
        metavar="N",
        help="Number of leading characters to keep visible (default: 4)",
    )
    p.add_argument(
        "--mask-all",
        action="store_true",
        help="Mask every value, not just detected secrets",
    )
    p.add_argument(
        "--char",
        default="*",
        metavar="C",
        help="Character used for masking (default: *)",
    )
    p.add_argument(
        "--key",
        action="append",
        dest="keys",
        metavar="KEY",
        help="Explicit key to mask (repeatable)",
    )


def cmd_mask(ns: argparse.Namespace) -> int:
    path = Path(ns.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    result = parse_env_file(path)
    if not result.ok:
        print(f"error: could not parse {path}", file=sys.stderr)
        return 2

    # Collect secret keys via redactor heuristics
    redactor = Redactor(RedactionConfig())
    heuristic_secrets = [
        e.key for e in result.entries if e.key and redactor.is_secret(e.key)
    ]
    explicit_keys = list(ns.keys or [])
    secret_keys = list(set(heuristic_secrets + explicit_keys))

    opts = MaskOptions(
        visible_chars=ns.visible,
        mask_char=ns.char,
        mask_all=ns.mask_all,
        only_secrets=not ns.mask_all,
    )
    mask_result = mask_entries(result, opts=opts, secret_keys=secret_keys)
    print(entries_to_text(mask_result.entries), end="")
    print(f"# masked {mask_result.masked_count} value(s)", file=sys.stderr)
    return 0
