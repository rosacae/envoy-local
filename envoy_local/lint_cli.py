"""CLI command for linting .env files."""
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from .lint import lint_env_file


def cmd_lint(ns: Namespace) -> int:
    """
    Lint one or more .env files and report issues.

    ns.files  : list[str]  – paths to .env files
    ns.format : str        – 'text' (default) or 'json'
    ns.strict : bool       – exit 1 on warnings too (always True here)
    """
    paths = [Path(f) for f in ns.files]
    fmt = getattr(ns, "format", "text")
    all_ok = True

    results = []
    for path in paths:
        try:
            result = lint_env_file(path)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}")
            return 2
        results.append(result)
        if not result.ok:
            all_ok = False

    if fmt == "json":
        print(json.dumps([r.to_dict() for r in results], indent=2))
    else:
        for result in results:
            if result.ok:
                print(f"OK  {result.path}")
            else:
                print(f"FAIL {result.path}")
                for issue in result.issues:
                    loc = f"line {issue.line_number}"
                    key_part = f" [{issue.key}]" if issue.key else ""
                    print(f"  {issue.code}{key_part} ({loc}): {issue.message}")

    return 0 if all_ok else 1
