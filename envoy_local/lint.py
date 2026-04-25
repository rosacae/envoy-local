"""Lint .env files for common issues."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from .parser import ParseResult, parse_env_file


@dataclass
class LintIssue:
    line_number: int
    key: str | None
    code: str
    message: str

    def to_dict(self) -> dict:
        return {
            "line": self.line_number,
            "key": self.key,
            "code": self.code,
            "message": self.message,
        }


@dataclass
class LintResult:
    path: Path
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.issues) == 0

    def to_dict(self) -> dict:
        return {
            "path": str(self.path),
            "ok": self.ok,
            "issues": [i.to_dict() for i in self.issues],
        }


def lint_parse_result(path: Path, result: ParseResult) -> LintResult:
    lint = LintResult(path=path)
    seen_keys: dict[str, int] = {}

    for entry in result.entries:
        lineno = entry.line_number
        key = entry.key

        # Duplicate keys
        if key in seen_keys:
            lint.issues.append(LintIssue(
                line_number=lineno,
                key=key,
                code="DUPLICATE_KEY",
                message=f"Key '{key}' already defined on line {seen_keys[key]}",
            ))
        else:
            seen_keys[key] = lineno

        # Empty value warning
        if entry.value == "":
            lint.issues.append(LintIssue(
                line_number=lineno,
                key=key,
                code="EMPTY_VALUE",
                message=f"Key '{key}' has an empty value",
            ))

        # Key naming convention (should be UPPER_SNAKE_CASE)
        if key and not key.replace("_", "").isupper():
            lint.issues.append(LintIssue(
                line_number=lineno,
                key=key,
                code="KEY_CASE",
                message=f"Key '{key}' is not UPPER_SNAKE_CASE",
            ))

    # Invalid lines
    for lineno, raw in result.invalid_lines:
        lint.issues.append(LintIssue(
            line_number=lineno,
            key=None,
            code="INVALID_LINE",
            message=f"Could not parse line: {raw!r}",
        ))

    return lint


def lint_env_file(path: Path) -> LintResult:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    result = parse_env_file(path)
    return lint_parse_result(path, result)
