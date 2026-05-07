"""CLI handler for the `resolve` command."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from envoy_local.resolve import resolve_env_file


def _parse_pair(pair: str) -> tuple[str, str]:
    if "=" not in pair:
        raise argparse.ArgumentTypeError(f"context pair must be KEY=VALUE, got: {pair!r}")
    k, _, v = pair.partition("=")
    return k.strip(), v.strip()


def cmd_resolve(ns: argparse.Namespace) -> int:
    """Resolve variable references in a .env file."""
    source = Path(ns.file)
    output: Optional[Path] = Path(ns.output) if getattr(ns, "output", None) else None
    extra: dict[str, str] = {}
    for pair in getattr(ns, "context", []) or []:
        try:
            k, v = _parse_pair(pair)
            extra[k] = v
        except argparse.ArgumentTypeError as exc:
            print(f"[resolve] {exc}")
            return 2

    allow_partial: bool = not getattr(ns, "strict", False)

    result = resolve_env_file(
        source=source,
        output=output,
        extra_context=extra or None,
        allow_partial=allow_partial,
    )

    if not result.ok:
        print(f"[resolve] error: {result.error}")
        return 2

    print(f"[resolve] {result.summary()}")
    return 0


def build_resolve_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("resolve", help="resolve variable references inside a .env file")
    p.add_argument("file", help="path to the .env file")
    p.add_argument("-o", "--output", default=None, help="write resolved output to this file (default: in-place)")
    p.add_argument(
        "-c",
        "--context",
        metavar="KEY=VALUE",
        action="append",
        help="extra context values for resolution (repeatable)",
    )
    p.add_argument(
        "--strict",
        action="store_true",
        default=False,
        help="fail if any reference cannot be resolved",
    )
    p.set_defaults(func=cmd_resolve)
    return p
