"""Parser for .env files with support for comments, quoted values, and multiline strings."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

ENV_LINE_RE = re.compile(
    r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?P<value>.*)$"
)
COMMENT_RE = re.compile(r"^\s*#.*$")


@dataclass
class EnvEntry:
    key: str
    value: str
    raw_line: str
    line_number: int
    is_quoted: bool = False


@dataclass
class ParseResult:
    entries: list[EnvEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def as_dict(self) -> dict[str, str]:
        return {e.key: e.value for e in self.entries}


def _strip_quotes(value: str) -> tuple[str, bool]:
    """Remove surrounding quotes from a value if present."""
    for quote in ('"', "'"):
        if value.startswith(quote) and value.endswith(quote) and len(value) >= 2:
            return value[1:-1], True
    return value, False


def _strip_inline_comment(value: str) -> str:
    """Remove inline comments from unquoted values."""
    idx = value.find(" #")
    if idx != -1:
        return value[:idx].rstrip()
    return value


def parse_env_lines(lines: Iterator[str]) -> ParseResult:
    result = ParseResult()
    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n")
        if not line.strip() or COMMENT_RE.match(line):
            continue
        m = ENV_LINE_RE.match(line.strip())
        if not m:
            result.errors.append(f"Line {lineno}: cannot parse '{line.strip()}'")
            continue
        key = m.group("key")
        raw_value = m.group("value").strip()
        value, is_quoted = _strip_quotes(raw_value)
        if not is_quoted:
            value = _strip_inline_comment(value)
        result.entries.append(
            EnvEntry(key=key, value=value, raw_line=line, line_number=lineno, is_quoted=is_quoted)
        )
    return result


def parse_env_file(path: Path) -> ParseResult:
    """Parse a .env file from disk."""
    if not path.exists():
        raise FileNotFoundError(f".env file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return parse_env_lines(iter(fh))
