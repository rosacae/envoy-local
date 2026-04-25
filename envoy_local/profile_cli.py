"""CLI commands for profile management."""
from __future__ import annotations

import argparse
from pathlib import Path

from envoy_local.profile import (
    add_profile,
    get_active_profile,
    list_profiles,
    load_manifest,
    remove_profile,
    set_active,
)


def cmd_profile_add(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.base_dir) if hasattr(ns, "base_dir") and ns.base_dir else Path.cwd()
    profile = add_profile(base_dir, ns.name, ns.path, getattr(ns, "description", ""))
    print(f"Profile '{profile.name}' added -> {profile.path}")
    return 0


def cmd_profile_remove(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.base_dir) if hasattr(ns, "base_dir") and ns.base_dir else Path.cwd()
    removed = remove_profile(base_dir, ns.name)
    if not removed:
        print(f"Profile '{ns.name}' not found.")
        return 1
    print(f"Profile '{ns.name}' removed.")
    return 0


def cmd_profile_use(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.base_dir) if hasattr(ns, "base_dir") and ns.base_dir else Path.cwd()
    ok = set_active(base_dir, ns.name)
    if not ok:
        print(f"Profile '{ns.name}' not found.")
        return 1
    print(f"Active profile set to '{ns.name}'.")
    return 0


def cmd_profile_list(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.base_dir) if hasattr(ns, "base_dir") and ns.base_dir else Path.cwd()
    manifest = load_manifest(base_dir)
    profiles = list_profiles(base_dir)
    if not profiles:
        print("No profiles defined.")
        return 0
    for p in profiles:
        active_marker = " (active)" if p.name == manifest.active else ""
        desc = f" - {p.description}" if p.description else ""
        print(f"  {p.name}{active_marker}: {p.path}{desc}")
    return 0


def cmd_profile_show(ns: argparse.Namespace) -> int:
    base_dir = Path(ns.base_dir) if hasattr(ns, "base_dir") and ns.base_dir else Path.cwd()
    profile = get_active_profile(base_dir)
    if profile is None:
        print("No active profile.")
        return 1
    print(f"Active profile: {profile.name} -> {profile.path}")
    if profile.description:
        print(f"  Description: {profile.description}")
    return 0
