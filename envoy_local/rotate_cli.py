"""CLI command for key rotation."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.rotate import rotate_file
from envoy_local.vault_cli import _resolve_key


def cmd_rotate(ns: argparse.Namespace) -> int:
    """Entry point for ``envoy rotate``."""
    env_path = Path(ns.file)
    if not env_path.exists():
        print(f"error: file not found: {env_path}")
        return 2

    try:
        old_key = _resolve_key(ns.old_key)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load old key — {exc}")
        return 2

    try:
        new_key = _resolve_key(ns.new_key)
    except Exception as exc:  # noqa: BLE001
        print(f"error: could not load new key — {exc}")
        return 2

    if old_key == new_key:
        print("error: old and new keys are identical — nothing to do")
        return 1

    dry_run: bool = getattr(ns, "dry_run", False)
    result = rotate_file(env_path, old_key, new_key, dry_run=dry_run)

    for key in result.rotated:
        print(f"  rotated  {key}")
    for key in result.skipped:
        print(f"  skipped  {key}")
    for msg in result.errors:
        print(f"  error    {msg}")

    print(result.summary())
    if dry_run:
        print("(dry-run — file not modified)")

    return 0 if result.ok else 1


def build_rotate_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("rotate", help="Re-encrypt ENC[] values with a new key")
    p.add_argument("file", help="Path to the .env file")
    p.add_argument("--old-key", required=True, metavar="HEX_OR_FILE",
                   help="Current encryption key (hex string or @path)")
    p.add_argument("--new-key", required=True, metavar="HEX_OR_FILE",
                   help="Replacement encryption key (hex string or @path)")
    p.add_argument("--dry-run", action="store_true",
                   help="Show what would change without writing the file")
    p.set_defaults(func=cmd_rotate)
