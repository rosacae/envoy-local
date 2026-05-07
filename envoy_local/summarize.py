"""Summarize an .env file: key count, empty values, secrets, comments, etc."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envoy_local.parser import ParseResult, EnvEntry
from envoy_local.redactor import RedactionConfig, Redactor


@dataclass
class SummarizeResult:
    total_lines: int = 0
    key_count: int = 0
    empty_value_count: int = 0
    secret_count: int = 0
    comment_count: int = 0
    blank_line_count: int = 0
    duplicate_keys: List[str] = field(default_factory=list)
    secret_keys: List[str] = field(default_factory=list)
    empty_keys: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_lines": self.total_lines,
            "key_count": self.key_count,
            "empty_value_count": self.empty_value_count,
            "secret_count": self.secret_count,
            "comment_count": self.comment_count,
            "blank_line_count": self.blank_line_count,
            "duplicate_keys": self.duplicate_keys,
            "secret_keys": self.secret_keys,
            "empty_keys": self.empty_keys,
        }


def summarize_parse_result(
    result: ParseResult,
    redaction_config: RedactionConfig | None = None,
) -> SummarizeResult:
    cfg = redaction_config or RedactionConfig()
    redactor = Redactor(cfg)

    summary = SummarizeResult()
    summary.total_lines = len(result.entries)

    seen_keys: dict[str, int] = {}

    for entry in result.entries:
        if entry.key is None:
            raw = entry.raw or ""
            stripped = raw.strip()
            if stripped.startswith("#"):
                summary.comment_count += 1
            else:
                summary.blank_line_count += 1
            continue

        summary.key_count += 1
        seen_keys[entry.key] = seen_keys.get(entry.key, 0) + 1

        if not entry.value:
            summary.empty_value_count += 1
            summary.empty_keys.append(entry.key)

        if redactor.is_secret(entry.key):
            summary.secret_count += 1
            summary.secret_keys.append(entry.key)

    summary.duplicate_keys = [k for k, count in seen_keys.items() if count > 1]
    return summary
