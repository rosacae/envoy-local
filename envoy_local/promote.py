"""Promote env entries from one environment profile to another with optional redaction."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envoy_local.parser import ParseResult, parse_env_file
from envoy_local.redactor import Redactor, RedactionConfig
from envoy_local.serializer import merge_entries, write_env_file


@dataclass
class PromoteOptions:
    overwrite: bool = False
    redact_secrets: bool = False
    dry_run: bool = False
    keys: Optional[List[str]] = None  # None means all keys


@dataclass
class PromoteResult:
    promoted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    redacted: List[str] = field(default_factory=list)
    dry_run: bool = False

    def summary(self) -> str:
        lines = [
            f"Promoted : {len(self.promoted)}",
            f"Skipped  : {len(self.skipped)}",
            f"Redacted : {len(self.redacted)}",
        ]
        if self.dry_run:
            lines.insert(0, "[dry-run] No files were written.")
        return "\n".join(lines)


def promote_env(
    source: Path,
    target: Path,
    options: PromoteOptions,
) -> PromoteResult:
    """Copy selected entries from *source* into *target*, respecting PromoteOptions."""
    src_result: ParseResult = parse_env_file(source)
    tgt_result: ParseResult = parse_env_file(target) if target.exists() else ParseResult(entries=[])

    existing_keys = {e.key for e in tgt_result.entries if e.key}

    redactor: Optional[Redactor] = None
    if options.redact_secrets:
        redactor = Redactor(RedactionConfig())

    result = PromoteResult(dry_run=options.dry_run)
    new_entries = list(tgt_result.entries)

    for entry in src_result.entries:
        if not entry.key:
            continue
        if options.keys is not None and entry.key not in options.keys:
            continue
        if entry.key in existing_keys and not options.overwrite:
            result.skipped.append(entry.key)
            continue

        promoted_entry = entry
        if redactor and redactor.is_secret(entry.key):
            from dataclasses import replace as dc_replace
            promoted_entry = dc_replace(entry, value="***REDACTED***")
            result.redacted.append(entry.key)

        # Replace or append
        new_entries = [e for e in new_entries if e.key != entry.key]
        new_entries.append(promoted_entry)
        result.promoted.append(entry.key)

    if not options.dry_run:
        from envoy_local.serializer import entries_to_text
        target.write_text(entries_to_text(new_entries))

    return result
