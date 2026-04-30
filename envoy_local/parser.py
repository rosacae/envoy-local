"""Parser for .env files.

This file is the canonical version — reproduced here to add
``parse_env_text`` as a public helper used by group.py and its tests.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class EnvEntry:
    key: Optional[str]
    value: Optional[str]
    comment: Optional[str] = None
    raw: str = ""


@dataclass
class ParseResult:
    entries: List[EnvEntry] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


def as_dict(result: ParseResult) -> dict:
    return {
        e.key: e.value
        for e in result.entries
        if e.key is not None
    }


_QUOTE_RE = re.compile(r'^(["\'])(.*?)\1$', re.DOTALL)
_INLINE_COMMENT_RE = re.compile(r'(?<!\\)\s+#.*$')


def _strip_quotes(value: str) -> str:
    m = _QUOTE_RE.match(value)
    if m:
        return m.group(2)
    return value


def _strip_inline_comment(value: str) -> str:
    if value and value[0] in ('"', "'"):
        return value
    return _INLINE_COMMENT_RE.sub("", value)


def _parse_line(line: str, lineno: int, errors: List[str]) -> EnvEntry:
    raw = line
    stripped = line.strip()

    if not stripped or stripped.startswith("#"):
        return EnvEntry(key=None, value=None, comment=stripped or None, raw=raw)

    if "=" not in stripped:
        errors.append(f"line {lineno}: no '=' found: {stripped!r}")
        return EnvEntry(key=None, value=None, raw=raw)

    key, _, rest = stripped.partition("=")
    key = key.strip()
    rest = rest.strip()
    rest = _strip_inline_comment(rest)
    value = _strip_quotes(rest)

    return EnvEntry(key=key, value=value, raw=raw)


def parse_env_text(text: str) -> ParseResult:
    result = ParseResult()
    for lineno, line in enumerate(text.splitlines(), start=1):
        entry = _parse_line(line, lineno, result.errors)
        result.entries.append(entry)
    return result


def parse_env_file(path: Path) -> ParseResult:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        r = ParseResult()
        r.errors.append(f"file not found: {path}")
        return r
    return parse_env_text(text)
