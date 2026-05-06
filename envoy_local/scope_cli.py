"""CLI commands for scope management."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.scope import (
    add_key_to_scope,
    remove_key_from_scope,
    keys_in_scope,
    list_scopes,
)


def cmd_scope_add(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.dir)
    added = add_key_to_scope(base_dir, ns.scope, ns.key)
    if added:
        print(f"Added '{ns.key}' to scope '{ns.scope}'.")
    else:
        print(f"'{ns.key}' already in scope '{ns.scope}'.")
    return 0


def cmd_scope_remove(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.dir)
    removed = remove_key_from_scope(base_dir, ns.scope, ns.key)
    if removed:
        print(f"Removed '{ns.key}' from scope '{ns.scope}'.")
    else:
        print(f"'{ns.key}' not found in scope '{ns.scope}'.")
        return 1
    return 0


def cmd_scope_list(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.dir)
    if ns.scope:
        keys = sorted(keys_in_scope(base_dir, ns.scope))
        if not keys:
            print(f"Scope '{ns.scope}' is empty or does not exist.")
        else:
            for k in keys:
                print(k)
    else:
        scopes = list_scopes(base_dir)
        if not scopes:
            print("No scopes defined.")
        else:
            for s in scopes:
                print(s)
    return 0


def build_scope_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser("scope", help="Manage key scopes")
    sp = p.add_subparsers(dest="scope_cmd", required=True)

    add_p = sp.add_parser("add", help="Add a key to a scope")
    add_p.add_argument("scope")
    add_p.add_argument("key")
    add_p.add_argument("--dir", default=".")
    add_p.set_defaults(func=cmd_scope_add)

    rm_p = sp.add_parser("remove", help="Remove a key from a scope")
    rm_p.add_argument("scope")
    rm_p.add_argument("key")
    rm_p.add_argument("--dir", default=".")
    rm_p.set_defaults(func=cmd_scope_remove)

    ls_p = sp.add_parser("list", help="List scopes or keys in a scope")
    ls_p.add_argument("scope", nargs="?", default=None)
    ls_p.add_argument("--dir", default=".")
    ls_p.set_defaults(func=cmd_scope_list)
