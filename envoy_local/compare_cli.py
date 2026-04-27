"""CLI command: envoy-local compare <left> <right>"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from envoy_local.compare import compare_env_files, CompareResult
from envoy_local.redactor import Redactor, RedactionConfig


def _print_text(result: CompareResult, redactor: Optional[Redactor], show_equal: bool) -> None:
    sections = [
        ("LEFT ONLY", result.left_only()),
        ("RIGHT ONLY", result.right_only()),
        ("CHANGED", result.changed()),
    ]
    if show_equal:
        sections.append(("EQUAL", result.equal()))

    for label, entries in sections:
        if not entries:
            continue
        print(f"--- {label} ---")
        for e in entries:
            d = e.to_dict(redactor)
            left = d["left"] if d["left"] is not None else "<absent>"
            right = d["right"] if d["right"] is not None else "<absent>"
            if label == "LEFT ONLY":
                print(f"  {e.key}={left}")
            elif label == "RIGHT ONLY":
                print(f"  {e.key}={right}")
            elif label == "CHANGED":
                print(f"  {e.key}: {left!r} -> {right!r}")
            else:
                print(f"  {e.key}={left}")


def cmd_compare(ns: argparse.Namespace) -> int:
    left_path = Path(ns.left)
    right_path = Path(ns.right)

    if not left_path.exists():
        print(f"error: left file not found: {left_path}")
        return 2
    if not right_path.exists():
        print(f"error: right file not found: {right_path}")
        return 2

    result = compare_env_files(left_path, right_path)

    redactor: Optional[Redactor] = None
    if getattr(ns, "redact", False):
        redactor = Redactor(RedactionConfig())

    if getattr(ns, "format", "text") == "json":
        output = [e.to_dict(redactor) for e in result.entries]
        if not getattr(ns, "show_equal", False):
            output = [d for d in output if d["status"] != "equal"]
        print(json.dumps(output, indent=2))
    else:
        _print_text(result, redactor, show_equal=getattr(ns, "show_equal", False))

    return 1 if result.has_differences else 0


def build_compare_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("compare", help="Compare two .env files")
    p.add_argument("left", help="First .env file")
    p.add_argument("right", help="Second .env file")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--redact", action="store_true", help="Redact secret values")
    p.add_argument("--show-equal", action="store_true", help="Also show equal keys")
    p.set_defaults(func=cmd_compare)
