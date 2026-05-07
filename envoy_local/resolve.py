"""Resolve all variable references in a .env file using its own entries as context."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envoy_local.parser import ParseResult, EnvEntry, parse_env_file
from envoy_local.interpolate import InterpolateResult, replace_brace, replace_bare
from envoy_local.serializer import write_env_file


@dataclass
class ResolveResult:
    ok: bool
    entries: list[EnvEntry] = field(default_factory=list)
    resolved_keys: list[str] = field(default_factory=list)
    unresolved_keys: list[str] = field(default_factory=list)
    error: Optional[str] = None

    def summary(self) -> str:
        if not self.ok:
            return f"error: {self.error}"
        parts = []
        if self.resolved_keys:
            parts.append(f"resolved {len(self.resolved_keys)} key(s): {', '.join(self.resolved_keys)}")
        if self.unresolved_keys:
            parts.append(f"unresolved {len(self.unresolved_keys)} key(s): {', '.join(self.unresolved_keys)}")
        if not parts:
            return "no references to resolve"
        return "; ".join(parts)


def resolve_env_file(
    source: Path,
    output: Optional[Path] = None,
    extra_context: Optional[dict[str, str]] = None,
    allow_partial: bool = True,
) -> ResolveResult:
    """Resolve variable references inside *source* using its own values.

    If *output* is None the file is resolved in-place.
    *extra_context* values are merged in (source file takes precedence).
    When *allow_partial* is False, any unresolved reference causes failure.
    """
    if not source.exists():
        return ResolveResult(ok=False, error=f"file not found: {source}")

    parse_result: ParseResult = parse_env_file(source)
    if not parse_result.ok:
        return ResolveResult(ok=False, error=parse_result.error)

    context: dict[str, str] = dict(extra_context or {})
    # Build initial context from keyed entries
    for entry in parse_result.entries:
        if entry.key:
            context[entry.key] = entry.value or ""

    resolved_keys: list[str] = []
    unresolved_keys: list[str] = []
    new_entries: list[EnvEntry] = []

    for entry in parse_result.entries:
        if not entry.key or not entry.value:
            new_entries.append(entry)
            continue

        result: InterpolateResult = replace_brace(
            replace_bare(InterpolateResult(ok=True, entries=[entry], unresolved=[]), context),
            context,
        )
        resolved_entry = result.entries[0] if result.entries else entry
        new_entries.append(resolved_entry)

        if resolved_entry.value != entry.value:
            resolved_keys.append(entry.key)
            context[entry.key] = resolved_entry.value or ""
        elif result.unresolved:
            unresolved_keys.append(entry.key)

    if unresolved_keys and not allow_partial:
        return ResolveResult(
            ok=False,
            error=f"unresolved references in keys: {', '.join(unresolved_keys)}",
        )

    dest = output or source
    write_env_file(dest, new_entries)

    return ResolveResult(
        ok=True,
        entries=new_entries,
        resolved_keys=resolved_keys,
        unresolved_keys=unresolved_keys,
    )
