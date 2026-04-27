"""Main CLI entry point for envoy-local.

Wires together all sub-commands into a single `envoy` executable.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envoy_local.audit_cli import cmd_audit_log
from envoy_local.compare_cli import build_compare_parser, cmd_compare
from envoy_local.diff_cli import cmd_diff
from envoy_local.export_cli import build_export_parser, cmd_export
from envoy_local.interpolate_cli import build_interpolate_parser, cmd_interpolate
from envoy_local.lint_cli import cmd_lint
from envoy_local.profile_cli import (
    cmd_profile_add,
    cmd_profile_list,
    cmd_profile_remove,
    cmd_profile_show,
    cmd_profile_use,
)
from envoy_local.schema_cli import build_schema_parser, cmd_schema_validate
from envoy_local.snapshot_cli import (
    cmd_snapshot_create,
    cmd_snapshot_list,
    cmd_snapshot_show,
)
from envoy_local.template_cli import cmd_template_list, cmd_template_render
from envoy_local.vault_cli import (
    cmd_vault_delete,
    cmd_vault_get,
    cmd_vault_init,
    cmd_vault_list,
    cmd_vault_put,
)


def build_parser() -> argparse.ArgumentParser:
    """Construct the top-level argument parser with all sub-commands attached."""
    parser = argparse.ArgumentParser(
        prog="envoy",
        description="Manage and sync local .env files with secret redaction support.",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    # ── diff ──────────────────────────────────────────────────────────────────
    p_diff = sub.add_parser("diff", help="Show diff between two .env files.")
    p_diff.add_argument("source", help="Source .env file.")
    p_diff.add_argument("target", help="Target .env file.")
    p_diff.add_argument("--redact", action="store_true", help="Redact secret values.")
    p_diff.add_argument("--json", dest="as_json", action="store_true", help="JSON output.")
    p_diff.set_defaults(func=cmd_diff)

    # ── lint ──────────────────────────────────────────────────────────────────
    p_lint = sub.add_parser("lint", help="Lint a .env file for common issues.")
    p_lint.add_argument("file", help="Path to .env file.")
    p_lint.add_argument("--json", dest="as_json", action="store_true", help="JSON output.")
    p_lint.set_defaults(func=cmd_lint)

    # ── export ────────────────────────────────────────────────────────────────
    build_export_parser(sub)

    # ── compare ───────────────────────────────────────────────────────────────
    build_compare_parser(sub)

    # ── interpolate ───────────────────────────────────────────────────────────
    build_interpolate_parser(sub)

    # ── schema ────────────────────────────────────────────────────────────────
    build_schema_parser(sub)

    # ── snapshot ──────────────────────────────────────────────────────────────
    p_snap = sub.add_parser("snapshot", help="Manage .env snapshots.")
    snap_sub = p_snap.add_subparsers(dest="snapshot_cmd", metavar="<subcommand>")

    p_snap_create = snap_sub.add_parser("create", help="Create a new snapshot.")
    p_snap_create.add_argument("file", help="Path to .env file.")
    p_snap_create.add_argument("--snap-dir", default=".snapshots", help="Snapshot directory.")
    p_snap_create.add_argument("--label", default=None, help="Optional label.")
    p_snap_create.set_defaults(func=cmd_snapshot_create)

    p_snap_list = snap_sub.add_parser("list", help="List available snapshots.")
    p_snap_list.add_argument("file", help="Path to .env file.")
    p_snap_list.add_argument("--snap-dir", default=".snapshots", help="Snapshot directory.")
    p_snap_list.set_defaults(func=cmd_snapshot_list)

    p_snap_show = snap_sub.add_parser("show", help="Show contents of a snapshot.")
    p_snap_show.add_argument("file", help="Path to .env file.")
    p_snap_show.add_argument("--snap-dir", default=".snapshots", help="Snapshot directory.")
    p_snap_show.add_argument("--index", type=int, default=-1, help="Snapshot index (default: latest).")
    p_snap_show.set_defaults(func=cmd_snapshot_show)

    # ── template ──────────────────────────────────────────────────────────────
    p_tmpl = sub.add_parser("template", help="Render or list template placeholders.")
    tmpl_sub = p_tmpl.add_subparsers(dest="template_cmd", metavar="<subcommand>")

    p_tmpl_render = tmpl_sub.add_parser("render", help="Render a template with .env values.")
    p_tmpl_render.add_argument("template", help="Template file.")
    p_tmpl_render.add_argument("env", help=".env file to use for substitution.")
    p_tmpl_render.add_argument("--output", "-o", default=None, help="Output file (default: stdout).")
    p_tmpl_render.set_defaults(func=cmd_template_render)

    p_tmpl_list = tmpl_sub.add_parser("list", help="List placeholders in a template.")
    p_tmpl_list.add_argument("template", help="Template file.")
    p_tmpl_list.set_defaults(func=cmd_template_list)

    # ── vault ─────────────────────────────────────────────────────────────────
    p_vault = sub.add_parser("vault", help="Manage the encrypted secret vault.")
    vault_sub = p_vault.add_subparsers(dest="vault_cmd", metavar="<subcommand>")

    vault_sub.add_parser("init", help="Initialise a new vault and generate a key.").set_defaults(func=cmd_vault_init)

    p_vput = vault_sub.add_parser("put", help="Store a secret in the vault.")
    p_vput.add_argument("key", help="Secret name.")
    p_vput.add_argument("value", help="Secret value.")
    p_vput.set_defaults(func=cmd_vault_put)

    p_vget = vault_sub.add_parser("get", help="Retrieve a secret from the vault.")
    p_vget.add_argument("key", help="Secret name.")
    p_vget.set_defaults(func=cmd_vault_get)

    p_vdel = vault_sub.add_parser("delete", help="Delete a secret from the vault.")
    p_vdel.add_argument("key", help="Secret name.")
    p_vdel.set_defaults(func=cmd_vault_delete)

    vault_sub.add_parser("list", help="List all secret keys in the vault.").set_defaults(func=cmd_vault_list)

    # ── audit ─────────────────────────────────────────────────────────────────
    p_audit = sub.add_parser("audit", help="View the audit log.")
    p_audit.add_argument("--log-dir", default=".audit", help="Audit log directory.")
    p_audit.add_argument("--json", dest="as_json", action="store_true", help="JSON output.")
    p_audit.set_defaults(func=cmd_audit_log)

    # ── profile ───────────────────────────────────────────────────────────────
    p_prof = sub.add_parser("profile", help="Manage named .env profiles.")
    prof_sub = p_prof.add_subparsers(dest="profile_cmd", metavar="<subcommand>")

    p_padd = prof_sub.add_parser("add", help="Add a profile.")
    p_padd.add_argument("name", help="Profile name.")
    p_padd.add_argument("file", help="Path to .env file for this profile.")
    p_padd.set_defaults(func=cmd_profile_add)

    p_prm = prof_sub.add_parser("remove", help="Remove a profile.")
    p_prm.add_argument("name", help="Profile name.")
    p_prm.set_defaults(func=cmd_profile_remove)

    p_puse = prof_sub.add_parser("use", help="Switch to a profile.")
    p_puse.add_argument("name", help="Profile name.")
    p_puse.set_defaults(func=cmd_profile_use)

    prof_sub.add_parser("list", help="List all profiles.").set_defaults(func=cmd_profile_list)

    p_pshow = prof_sub.add_parser("show", help="Show contents of a profile.")
    p_pshow.add_argument("name", help="Profile name.")
    p_pshow.set_defaults(func=cmd_profile_show)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Entry point for the `envoy` CLI.

    Returns the exit code so tests can inspect it without calling sys.exit.
    """
    parser = build_parser()
    ns = parser.parse_args(argv)

    if not ns.command:
        parser.print_help()
        return 0

    if not hasattr(ns, "func"):
        # Sub-command group chosen but no sub-command given
        parser.parse_args([ns.command, "--help"])
        return 0

    return ns.func(ns)  # type: ignore[no-any-return]


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
