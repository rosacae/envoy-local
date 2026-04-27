"""CLI command: envoy-local clone"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from .clone import CloneOptions, clone_env_file
from .encrypt import _load_key  # reuse existing key-loading helper if present


def _load_key_safe(key_path: Optional[str]) -> Optional[bytes]:
    """Return raw key bytes or None when no path given."""
    if not key_path:
        return None
    path = Path(key_path)
    if not path.exists():
        return None
    return path.read_bytes().strip()


def cmd_clone(ns: argparse.Namespace) -> int:
    source = Path(ns.source)
    destination = Path(ns.destination)

    if not source.exists():
        print(f"Error: source file not found: {source}")
        return 2

    encrypt_key = _load_key_safe(getattr(ns, "key", None))

    options = CloneOptions(
        redact_secrets=getattr(ns, "redact", False),
        redact_placeholder=getattr(ns, "placeholder", "REDACTED"),
        encrypt_key=encrypt_key,
        overwrite=getattr(ns, "overwrite", False),
    )

    result = clone_env_file(source, destination, options)
    print(result.summary())
    return 0


def build_clone_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("clone", help="Clone an .env file to a new location")
    p.add_argument("source", help="Source .env file")
    p.add_argument("destination", help="Destination path")
    p.add_argument(
        "--redact",
        action="store_true",
        default=False,
        help="Redact secret-looking values in the clone",
    )
    p.add_argument(
        "--placeholder",
        default="REDACTED",
        help="Placeholder text used when --redact is set (default: REDACTED)",
    )
    p.add_argument(
        "--key",
        default=None,
        metavar="KEY_FILE",
        help="Path to encryption key file; encrypts plain values in the clone",
    )
    p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite destination if it already exists",
    )
    p.set_defaults(func=cmd_clone)
