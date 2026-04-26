"""CLI commands for schema validation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envoy_local.parser import parse_env_file
from envoy_local.schema import EnvSchema, validate_schema


def cmd_schema_validate(ns: argparse.Namespace) -> int:
    """Validate an .env file against a schema file.

    Returns 0 if valid, 1 if violations found, 2 on file errors.
    """
    env_path = Path(ns.env_file)
    schema_path = Path(ns.schema_file)

    if not env_path.exists():
        print(f"error: env file not found: {env_path}", file=sys.stderr)
        return 2
    if not schema_path.exists():
        print(f"error: schema file not found: {schema_path}", file=sys.stderr)
        return 2

    try:
        schema = EnvSchema.load(str(schema_path))
    except (json.JSONDecodeError, KeyError) as exc:
        print(f"error: invalid schema file: {exc}", file=sys.stderr)
        return 2

    parse_result = parse_env_file(str(env_path))
    entries = {e.key: e.value for e in parse_result.entries if e.key}

    result = validate_schema(entries, schema)

    if ns.format == "json":
        output = {
            "ok": result.ok,
            "violations": [v.to_dict() for v in result.violations],
        }
        print(json.dumps(output, indent=2))
    else:
        if result.ok:
            print("schema validation passed — no violations found")
        else:
            print(f"schema validation failed — {len(result.violations)} violation(s):")
            for v in result.violations:
                print(f"  [{v.key}] {v.message}")

    return 0 if result.ok else 1


def build_schema_parser(sub: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = sub.add_parser("schema-validate", help="Validate .env file against a JSON schema")
    p.add_argument("env_file", help="Path to the .env file")
    p.add_argument("schema_file", help="Path to the JSON schema file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )
    p.set_defaults(func=cmd_schema_validate)
