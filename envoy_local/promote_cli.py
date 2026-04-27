"""CLI commands for the promote feature."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.promote import PromoteOptions, promote_env


def cmd_promote(ns: argparse.Namespace) -> int:
    source = Path(ns.source)
    target = Path(ns.target)

    if not source.exists():
        print(f"[error] Source file not found: {source}")
        return 2

    if not target.exists() and not ns.dry_run:
        # Create an empty target so promote can write into it
        target.touch()

    keys = ns.keys.split(",") if ns.keys else None

    options = PromoteOptions(
        overwrite=ns.overwrite,
        redact_secrets=ns.redact,
        dry_run=ns.dry_run,
        keys=keys,
    )

    result = promote_env(source, target, options)
    print(result.summary())

    if result.promoted:
        print("\nPromoted keys:")
        for k in result.promoted:
            tag = " [redacted]" if k in result.redacted else ""
            print(f"  + {k}{tag}")

    if result.skipped:
        print("\nSkipped keys (already exist):")
        for k in result.skipped:
            print(f"  ~ {k}")

    return 0


def build_promote_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("promote", help="Promote env entries from source to target file")
    p.add_argument("source", help="Source .env file")
    p.add_argument("target", help="Target .env file")
    p.add_argument("--overwrite", action="store_true", help="Overwrite existing keys in target")
    p.add_argument("--redact", action="store_true", help="Redact secret values before writing")
    p.add_argument("--dry-run", action="store_true", dest="dry_run", help="Preview without writing")
    p.add_argument("--keys", default=None, help="Comma-separated list of keys to promote")
    p.set_defaults(func=cmd_promote)
