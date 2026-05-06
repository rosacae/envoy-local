"""CLI commands for tag management."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.tag import add_tag, remove_tag, load_tags, keys_for_tag, tags_for_key


def cmd_tag_add(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.env_file).parent
    added = add_tag(base_dir, ns.key, ns.tag)
    if added:
        print(f"Tagged {ns.key!r} with {ns.tag!r}")
    else:
        print(f"{ns.key!r} already has tag {ns.tag!r}")
    return 0


def cmd_tag_remove(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.env_file).parent
    removed = remove_tag(base_dir, ns.key, ns.tag)
    if removed:
        print(f"Removed tag {ns.tag!r} from {ns.key!r}")
    else:
        print(f"{ns.key!r} did not have tag {ns.tag!r}")
        return 1
    return 0


def cmd_tag_list(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.env_file).parent
    manifest = load_tags(base_dir)
    if ns.key:
        tags = tags_for_key(manifest, ns.key)
        if tags:
            print("  ".join(tags))
        else:
            print(f"No tags for {ns.key!r}")
    elif ns.tag:
        keys = keys_for_tag(manifest, ns.tag)
        if keys:
            print("  ".join(keys))
        else:
            print(f"No keys tagged with {ns.tag!r}")
    else:
        if not manifest.tags:
            print("No tags defined.")
        for key, tags in sorted(manifest.tags.items()):
            print(f"{key}: {', '.join(tags)}")
    return 0


def build_tag_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("tag", help="Manage key tags")
    sp = p.add_subparsers(dest="tag_cmd", required=True)

    add_p = sp.add_parser("add", help="Add a tag to a key")
    add_p.add_argument("env_file")
    add_p.add_argument("key")
    add_p.add_argument("tag")
    add_p.set_defaults(func=cmd_tag_add)

    rm_p = sp.add_parser("remove", help="Remove a tag from a key")
    rm_p.add_argument("env_file")
    rm_p.add_argument("key")
    rm_p.add_argument("tag")
    rm_p.set_defaults(func=cmd_tag_remove)

    ls_p = sp.add_parser("list", help="List tags")
    ls_p.add_argument("env_file")
    ls_p.add_argument("--key", default="", help="Show tags for a specific key")
    ls_p.add_argument("--tag", default="", help="Show keys for a specific tag")
    ls_p.set_defaults(func=cmd_tag_list)
