"""Secret redaction utilities for .env values."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

DEFAULT_SECRET_PATTERNS: list[str] = [
    r"(?i)(password|passwd|secret|token|api[_-]?key|auth|credential|private[_-]?key)",
]

REDACTED_PLACEHOLDER = "**REDACTED**"


@dataclass
class RedactionConfig:
    patterns: list[str] = None  # type: ignore[assignment]
    placeholder: str = REDACTED_PLACEHOLDER
    min_value_length: int = 3

    def __post_init__(self) -> None:
        if self.patterns is None:
            self.patterns = list(DEFAULT_SECRET_PATTERNS)
        self._compiled = [re.compile(p) for p in self.patterns]

    def is_secret(self, key: str) -> bool:
        return any(r.search(key) for r in self._compiled)


class Redactor:
    def __init__(self, config: RedactionConfig | None = None) -> None:
        self.config = config or RedactionConfig()

    def redact_value(self, key: str, value: str) -> str:
        """Return redacted placeholder if key matches a secret pattern."""
        if len(value) < self.config.min_value_length:
            return value
        if self.config.is_secret(key):
            return self.config.placeholder
        return value

    def redact_dict(self, env: dict[str, str]) -> dict[str, str]:
        """Return a new dict with secret values replaced."""
        return {k: self.redact_value(k, v) for k, v in env.items()}

    def redact_entries(self, entries: Sequence) -> list:
        """Return a list of EnvEntry objects with secret values replaced (shallow copy)."""
        from envoy_local.parser import EnvEntry  # local import to avoid cycles

        result = []
        for entry in entries:
            if self.config.is_secret(entry.key) and len(entry.value) >= self.config.min_value_length:
                result.append(
                    EnvEntry(
                        key=entry.key,
                        value=self.config.placeholder,
                        raw_line=entry.raw_line,
                        line_number=entry.line_number,
                        is_quoted=entry.is_quoted,
                    )
                )
            else:
                result.append(entry)
        return result
