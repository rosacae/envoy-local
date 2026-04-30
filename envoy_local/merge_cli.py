"""CLI commands for the merge feature."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import List

from envoy_local.merge import MergeOptions, merge_env_files


def cmd_merge(ns: argparse.Namespace) -> int:
    sources: List[Path] = [Path(s) for s in ns.sources]
    output: Path | None = Path(ns.output) if ns.output else None

    options = MergeOptions(
        sources=sources,
        output=output,
        overwrite=not ns.no_overwrite,
        keep_comments=not ns.strip_comments,
        dry_run=ns.dry_run,
    )

    result = merge_env_files(options)

    if not result.ok:
        print(f"error: {result.error}")
        return 2

    if ns.json:
        data = {
            "ok": result.ok,
            "summary": result.summary(),
            "conflicts": result.conflicts,
            "merged_keys": [e.key for e in result.merged if e.key],
        }
        print(json.dumps(data, indent=2))
    else:
        print(result.summary())
        if result.conflicts:
            print("conflicts resolved (last-wins):", ", ".join(result.conflicts))
        if ns.dry_run:
            from envoy_local.serializer import entries_to_text
            print("--- dry run output ---")
            print(entries_to_text(result.merged))

    return 0


def build_merge_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("merge", help="merge multiple .env files into one")
    p.add_argument("sources", nargs="+", metavar="FILE", help="source .env files (in priority order)")
    p.add_argument("-o", "--output", metavar="FILE", help="write merged result to this file")
    p.add_argument("--no-overwrite", action="store_true", help="keep first occurrence on conflict")
    p.add_argument("--strip-comments", action="store_true", help="omit comment and blank lines")
    p.add_argument("--dry-run", action="store_true", help="print result without writing")
    p.add_argument("--json", action="store_true", help="output as JSON")
    p.set_defaults(func=cmd_merge)
    return p
