"""CLI commands for diffing .env files."""
from __future__ import annotations

import json
from pathlib import Path

from envoy_local.diff import diff_env
from envoy_local.diff_formatter import format_diff, format_diff_json
from envoy_local.parser import parse_env_file
from envoy_local.redactor import Redactor, RedactionConfig


def cmd_diff(
    source_path: str,
    target_path: str,
    *,
    redact: bool = True,
    color: bool = True,
    show_unchanged: bool = False,
    output_format: str = "text",
) -> int:
    """Compare two .env files and print the diff.

    Returns 0 if no changes, 1 if changes exist, 2 on error.
    """
    source = Path(source_path)
    target = Path(target_path)

    if not source.exists():
        print(f"Error: source file not found: {source}")
        return 2
    if not target.exists():
        print(f"Error: target file not found: {target}")
        return 2

    source_result = parse_env_file(source)
    target_result = parse_env_file(target)

    result = diff_env(source_result, target_result)

    redactor: Redactor | None = None
    if redact:
        redactor = Redactor(RedactionConfig())

    if output_format == "json":
        data = format_diff_json(result, redactor=redactor)
        print(json.dumps(data, indent=2))
    else:
        print(format_diff(result, redactor=redactor, color=color, show_unchanged=show_unchanged))

    return 1 if result.has_changes else 0
