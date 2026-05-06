"""Value type coercion utilities for env entries."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from envoy_local.parser import EnvEntry, ParseResult


@dataclass
class CoerceResult:
    entries: List[EnvEntry]
    changed: List[str]
    skipped: List[str]
    ok: bool = True
    error: Optional[str] = None

    def summary(self) -> str:
        if not self.ok:
            return f"error: {self.error}"
        return (
            f"{len(self.changed)} coerced, "
            f"{len(self.skipped)} skipped"
        )


def _coerce_value(raw: str, target_type: str) -> Optional[str]:
    """Attempt to coerce *raw* to *target_type*.

    Returns the coerced string representation, or None if the
    conversion is not possible / not needed.
    """
    stripped = raw.strip()
    if target_type == "bool":
        if stripped.lower() in ("1", "true", "yes", "on"):
            return "true"
        if stripped.lower() in ("0", "false", "no", "off"):
            return "false"
        return None
    if target_type == "int":
        try:
            int(stripped)
            return str(int(stripped))
        except ValueError:
            return None
    if target_type == "float":
        try:
            float(stripped)
            return str(float(stripped))
        except ValueError:
            return None
    if target_type == "str":
        return stripped
    return None


def coerce_entries(
    result: ParseResult,
    type_map: dict[str, str],
) -> CoerceResult:
    """Coerce entry values according to *type_map* (key -> target_type).

    Supported target types: ``bool``, ``int``, ``float``, ``str``.
    Entries whose key is not in *type_map* are passed through unchanged.
    """
    out: List[EnvEntry] = []
    changed: List[str] = []
    skipped: List[str] = []

    for entry in result.entries:
        if entry.key is None or entry.key not in type_map:
            out.append(entry)
            continue

        target = type_map[entry.key]
        coerced = _coerce_value(entry.value or "", target)
        if coerced is None:
            skipped.append(entry.key)
            out.append(entry)
        elif coerced != (entry.value or ""):
            changed.append(entry.key)
            out.append(
                EnvEntry(
                    key=entry.key,
                    value=coerced,
                    comment=entry.comment,
                    raw=entry.raw,
                )
            )
        else:
            out.append(entry)

    return CoerceResult(entries=out, changed=changed, skipped=skipped)
