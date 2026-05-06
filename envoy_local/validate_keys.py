"""Key name validation utilities for .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
import re

from envoy_local.parser import ParseResult, EnvEntry

_VALID_KEY_RE = re.compile(r'^[A-Z_][A-Z0-9_]*$')
_RESERVED_PREFIXES = ("BASH_", "IFS", "PATH", "PS1", "PS2", "HOME", "USER")


@dataclass
class KeyViolation:
    key: str
    reason: str

    def to_dict(self) -> dict:
        return {"key": self.key, "reason": self.reason}


@dataclass
class KeyValidationResult:
    violations: List[KeyViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "violations": [v.to_dict() for v in self.violations],
        }


def validate_key_names(
    result: ParseResult,
    *,
    allow_lowercase: bool = False,
    check_reserved: bool = True,
) -> KeyValidationResult:
    """Validate all key names in a ParseResult.

    Args:
        result: Parsed .env entries.
        allow_lowercase: If True, lowercase keys are not flagged.
        check_reserved: If True, keys that shadow shell reserved names are flagged.

    Returns:
        KeyValidationResult with any violations found.
    """
    violations: List[KeyViolation] = []

    for entry in result.entries:
        key = entry.key
        if key is None:
            continue

        if not allow_lowercase and not _VALID_KEY_RE.match(key):
            violations.append(
                KeyViolation(
                    key=key,
                    reason=(
                        f"Key '{key}' must match [A-Z_][A-Z0-9_]* "
                        "(uppercase letters, digits, underscores only)"
                    ),
                )
            )
            continue

        if check_reserved:
            for prefix in _RESERVED_PREFIXES:
                if key == prefix.rstrip("_") or key.startswith(prefix):
                    violations.append(
                        KeyViolation(
                            key=key,
                            reason=f"Key '{key}' shadows a reserved shell name '{prefix.rstrip('_')}'",
                        )
                    )
                    break

    return KeyValidationResult(violations=violations)
