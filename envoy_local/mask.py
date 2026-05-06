"""Mask: partially obscure env values for safe display."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from envoy_local.parser import EnvEntry, ParseResult


@dataclass
class MaskOptions:
    visible_chars: int = 4
    mask_char: str = "*"
    mask_all: bool = False
    only_secrets: bool = True


@dataclass
class MaskResult:
    entries: List[EnvEntry]
    masked_count: int

    def summary(self) -> str:
        return f"Masked {self.masked_count} value(s)."


def _mask_value(value: str, opts: MaskOptions) -> str:
    """Return a masked representation of *value*."""
    if not value:
        return value
    if opts.mask_all or len(value) <= opts.visible_chars:
        return opts.mask_char * max(len(value), 6)
    visible = value[: opts.visible_chars]
    return visible + opts.mask_char * (len(value) - opts.visible_chars)


def mask_entries(
    result: ParseResult,
    opts: Optional[MaskOptions] = None,
    secret_keys: Optional[List[str]] = None,
) -> MaskResult:
    """Return a new list of EnvEntry with sensitive values masked.

    Args:
        result: Parsed .env file.
        opts: Masking options.
        secret_keys: Explicit list of keys to mask regardless of heuristics.
                     When *opts.only_secrets* is False every valued entry is masked.
    """
    if opts is None:
        opts = MaskOptions()
    secret_keys_set = set(secret_keys or [])

    masked_count = 0
    out: List[EnvEntry] = []
    for entry in result.entries:
        if entry.key is None or entry.value is None:
            out.append(entry)
            continue

        should_mask = (
            not opts.only_secrets
            or entry.key in secret_keys_set
        )
        if should_mask:
            new_entry = EnvEntry(
                key=entry.key,
                value=_mask_value(entry.value, opts),
                comment=entry.comment,
                raw=entry.raw,
            )
            out.append(new_entry)
            masked_count += 1
        else:
            out.append(entry)

    return MaskResult(entries=out, masked_count=masked_count)
