"""CLI commands for inject feature."""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from .inject import inject_keys


def _parse_pair(raw: str) -> tuple[str, str]:
    """Parse a KEY=VALUE string, raising ArgumentTypeError on bad format."""
    if "=" not in raw:
        raise argparse.ArgumentTypeError(
            f"Expected KEY=VALUE, got: {raw!r}"
        )
    key, _, value = raw.partition("=")
    key = key.strip()
    if not key:
        raise argparse.ArgumentTypeError(f"Empty key in pair: {raw!r}")
    return key, value


def cmd_inject(ns: argparse.Namespace) -> int:
    """Inject key=value pairs into a .env file.

    Returns:
        0 on success, 1 on error.
    """
    path = Path(ns.file)
    pairs_raw: List[str] = ns.pairs

    try:
        pairs = dict(_parse_pair(p) for p in pairs_raw)
    except argparse.ArgumentTypeError as exc:
        print(f"[inject] error: {exc}")
        return 1

    result = inject_keys(
        path,
        pairs,
        overwrite=not ns.no_overwrite,
        create=not ns.no_create,
    )

    if not result.ok:
        print(f"[inject] error: {result.error}")
        return 1

    print(f"[inject] {result.summary()}")
    return 0


def build_inject_parser(sub: argparse._SubParsersAction) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    p = sub.add_parser("inject", help="Inject key=value pairs into a .env file")
    p.add_argument("file", help="Target .env file")
    p.add_argument(
        "pairs",
        nargs="+",
        metavar="KEY=VALUE",
        help="One or more KEY=VALUE pairs to inject",
    )
    p.add_argument(
        "--no-overwrite",
        action="store_true",
        default=False,
        help="Skip keys that already exist",
    )
    p.add_argument(
        "--no-create",
        action="store_true",
        default=False,
        help="Fail if the target file does not exist",
    )
    p.set_defaults(func=cmd_inject)
    return p
