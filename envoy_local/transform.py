"""Key/value transformation pass: uppercase keys, trim whitespace, prefix injection."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envoy_local.parser import EnvEntry, ParseResult


@dataclass
class TransformOptions:
    uppercase_keys: bool = False
    strip_values: bool = False
    prefix: str = ""
    suffix: str = ""
    remove_prefix: str = ""


@dataclass
class TransformResult:
    entries: List[EnvEntry] = field(default_factory=list)
    changed: int = 0
    skipped: int = 0

    def summary(self) -> str:
        return f"transformed={self.changed} skipped={self.skipped}"


def _transform_entry(entry: EnvEntry, opts: TransformOptions) -> tuple[EnvEntry, bool]:
    """Return (new_entry, was_changed)."""
    if entry.key is None:
        return entry, False

    key = entry.key
    value = entry.value or ""
    changed = False

    if opts.uppercase_keys and key != key.upper():
        key = key.upper()
        changed = True

    if opts.remove_prefix and key.startswith(opts.remove_prefix):
        key = key[len(opts.remove_prefix):]
        changed = True

    if opts.prefix and not key.startswith(opts.prefix):
        key = opts.prefix + key
        changed = True

    if opts.suffix and not key.endswith(opts.suffix):
        key = key + opts.suffix
        changed = True

    if opts.strip_values and value != value.strip():
        value = value.strip()
        changed = True

    new_entry = EnvEntry(
        key=key,
        value=value,
        comment=entry.comment,
        raw=entry.raw,
    )
    return new_entry, changed


def transform_entries(
    parse_result: ParseResult,
    opts: Optional[TransformOptions] = None,
) -> TransformResult:
    if opts is None:
        opts = TransformOptions()

    result = TransformResult()
    for entry in parse_result.entries:
        new_entry, changed = _transform_entry(entry, opts)
        result.entries.append(new_entry)
        if changed:
            result.changed += 1
        else:
            result.skipped += 1
    return result
