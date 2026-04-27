"""CLI commands for pin management."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.pin import pin_key, unpin_key, list_pins


def cmd_pin_set(args: argparse.Namespace) -> int:
    directory = Path(args.dir) if args.dir else Path.cwd()
    manifest = pin_key(directory, args.key, args.value)
    print(f"Pinned {args.key}={args.value!r} in {directory}")
    return 0


def cmd_pin_remove(args: argparse.Namespace) -> int:
    directory = Path(args.dir) if args.dir else Path.cwd()
    removed = unpin_key(directory, args.key)
    if removed:
        print(f"Unpinned {args.key!r} from {directory}")
        return 0
    print(f"Key {args.key!r} was not pinned.")
    return 1


def cmd_pin_list(args: argparse.Namespace) -> int:
    directory = Path(args.dir) if args.dir else Path.cwd()
    pins = list_pins(directory)
    if not pins:
        print("No pins defined.")
        return 0
    for key, value in sorted(pins.items()):
        print(f"{key}={value}")
    return 0


def build_pin_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("pin", help="Manage pinned env values")
    pin_sub = p.add_subparsers(dest="pin_cmd", required=True)

    ps = pin_sub.add_parser("set", help="Pin a key to a value")
    ps.add_argument("key")
    ps.add_argument("value")
    ps.add_argument("--dir", default=None)
    ps.set_defaults(func=cmd_pin_set)

    pr = pin_sub.add_parser("remove", help="Remove a pin")
    pr.add_argument("key")
    pr.add_argument("--dir", default=None)
    pr.set_defaults(func=cmd_pin_remove)

    pl = pin_sub.add_parser("list", help="List all pins")
    pl.add_argument("--dir", default=None)
    pl.set_defaults(func=cmd_pin_list)
