"""Type-checking for env entry values against declared types."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from envoy_local.parser import EnvEntry, ParseResult


KNOWN_TYPES = {"str", "int", "float", "bool", "url", "email"}

_URL_RE = re.compile(
    r"^https?://[^\s/$.?#].[^\s]*$", re.IGNORECASE
)
_EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$", re.IGNORECASE
)


@dataclass
class TypeViolation:
    key: str
    value: str
    expected_type: str
    reason: str

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "expected_type": self.expected_type,
            "reason": self.reason,
        }


@dataclass
class TypeCheckResult:
    violations: List[TypeViolation] = field(default_factory=list)
    checked: int = 0

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "checked": self.checked,
            "violations": [v.to_dict() for v in self.violations],
        }


def _check_value(value: str, expected: str) -> Optional[str]:
    """Return a reason string if value fails the type check, else None."""
    if expected == "int":
        try:
            int(value)
        except ValueError:
            return f"cannot convert {value!r} to int"
    elif expected == "float":
        try:
            float(value)
        except ValueError:
            return f"cannot convert {value!r} to float"
    elif expected == "bool":
        if value.lower() not in {"true", "false", "1", "0", "yes", "no"}:
            return f"{value!r} is not a recognised boolean"
    elif expected == "url":
        if not _URL_RE.match(value):
            return f"{value!r} is not a valid URL"
    elif expected == "email":
        if not _EMAIL_RE.match(value):
            return f"{value!r} is not a valid email address"
    # "str" always passes
    return None


def typecheck_entries(
    result: ParseResult,
    type_map: dict,  # {key: expected_type}
) -> TypeCheckResult:
    """Validate entry values against the provided type_map."""
    violations: List[TypeViolation] = []
    checked = 0

    entry_map = {e.key: e for e in result.entries if e.key}

    for key, expected in type_map.items():
        if expected not in KNOWN_TYPES:
            continue
        entry: Optional[EnvEntry] = entry_map.get(key)
        if entry is None or entry.value is None:
            continue
        reason = _check_value(entry.value, expected)
        checked += 1
        if reason:
            violations.append(
                TypeViolation(
                    key=key,
                    value=entry.value,
                    expected_type=expected,
                    reason=reason,
                )
            )

    return TypeCheckResult(violations=violations, checked=checked)
