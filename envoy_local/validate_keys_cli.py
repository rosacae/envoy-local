"""CLI command for key-name validation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy_local.parser import parse_env_file
from envoy_local.validate_keys import validate_key_names


def cmd_validate_keys(ns: argparse.Namespace) -> int:
    """Validate key names in a .env file.

    Returns:
        0 – all keys valid
        1 – one or more violations found
        2 – file not found or unreadable
    """
    path = Path(ns.file)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    result = parse_env_file(path)
    validation = validate_key_names(
        result,
        allow_lowercase=getattr(ns, "allow_lowercase", False),
        check_reserved=not getattr(ns, "no_reserved_check", False),
    )

    if getattr(ns, "json", False):
        print(json.dumps(validation.to_dict(), indent=2))
    else:
        if validation.ok:
            print(f"OK — all key names in '{path}' are valid.")
        else:
            print(f"Found {len(validation.violations)} violation(s) in '{path}':")
            for v in validation.violations:
                print(f"  [{v.key}] {v.reason}")

    return 0 if validation.ok else 1


def build_validate_keys_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser(
        "validate-keys",
        help="Check that all key names follow naming conventions",
    )
    p.add_argument("file", help="Path to the .env file")
    p.add_argument(
        "--allow-lowercase",
        action="store_true",
        default=False,
        help="Do not flag lowercase key names",
    )
    p.add_argument(
        "--no-reserved-check",
        action="store_true",
        default=False,
        help="Skip check for reserved shell variable names",
    )
    p.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output results as JSON",
    )
    p.set_defaults(func=cmd_validate_keys)
