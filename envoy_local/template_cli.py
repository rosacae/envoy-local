"""CLI commands for template rendering."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_local.parser import parse_env_file
from envoy_local.template import list_placeholders, render_template_from_parse_result
from envoy_local.vault_integration import inject_vault_secrets


def cmd_template_render(args: argparse.Namespace) -> int:
    """Render a template file substituting values from an .env file."""
    template_path = Path(args.template)
    env_path = Path(args.env_file)

    if not template_path.exists():
        print(f"error: template file not found: {template_path}", file=sys.stderr)
        return 2
    if not env_path.exists():
        print(f"error: env file not found: {env_path}", file=sys.stderr)
        return 2

    template = template_path.read_text(encoding="utf-8")
    result = parse_env_file(env_path)

    if args.vault:
        vault_path = Path(args.vault)
        key_path = Path(args.vault_key) if args.vault_key else None
        result = inject_vault_secrets(result, vault_path, key_path)

    render = render_template_from_parse_result(template, result)

    if render.missing and not args.allow_missing:
        for key in render.missing:
            print(f"error: unresolved placeholder: {{{{{key}}}}}", file=sys.stderr)
        return 1

    output = Path(args.output) if args.output else None
    if output:
        output.write_text(render.text, encoding="utf-8")
    else:
        print(render.text, end="")

    return 0


def cmd_template_list(args: argparse.Namespace) -> int:
    """List all {{PLACEHOLDER}} names found in a template file."""
    template_path = Path(args.template)
    if not template_path.exists():
        print(f"error: template file not found: {template_path}", file=sys.stderr)
        return 2

    template = template_path.read_text(encoding="utf-8")
    placeholders = list_placeholders(template)
    for name in placeholders:
        print(name)
    return 0
