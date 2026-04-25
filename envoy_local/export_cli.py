"""CLI command: envoy-local export — export .env to shell/json/yaml/docker formats."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional

from envoy_local.env_export import ExportFormat, export_entries
from envoy_local.parser import parse_env_file
from envoy_local.redactor import RedactionConfig, Redactor


def cmd_export(ns: argparse.Namespace) -> int:
    source = Path(ns.file)
    if not source.exists():
        print(f"error: file not found: {source}", file=sys.stderr)
        return 2

    try:
        fmt = ExportFormat(ns.format)
    except ValueError:
        valid = ", ".join(f.value for f in ExportFormat)
        print(f"error: invalid format '{ns.format}'. Choose from: {valid}", file=sys.stderr)
        return 2

    result = parse_env_file(source)
    if result.errors:
        for err in result.errors:
            print(f"warning: {err}", file=sys.stderr)

    redactor: Optional[Redactor] = None
    if getattr(ns, "redact", False):
        cfg = RedactionConfig(
            secret_patterns=ns.secret_patterns if ns.secret_patterns else None
        )
        redactor = Redactor(cfg)

    output = export_entries(result, fmt, redactor)

    if ns.output:
        out_path = Path(ns.output)
        out_path.write_text(output + "\n", encoding="utf-8")
        print(f"exported {len([e for e in result.entries if e.key])} entries to {out_path}")
    else:
        print(output)

    return 0


def build_export_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("export", help="Export .env entries to another format")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--format", "-f",
        default="shell",
        help="Output format: shell, json, yaml, docker (default: shell)",
    )
    p.add_argument("--output", "-o", default=None, help="Write output to file instead of stdout")
    p.add_argument("--redact", action="store_true", help="Redact secret values")
    p.add_argument(
        "--secret-patterns",
        nargs="*",
        default=None,
        metavar="PATTERN",
        help="Additional key patterns to treat as secrets",
    )
    p.set_defaults(func=cmd_export)
