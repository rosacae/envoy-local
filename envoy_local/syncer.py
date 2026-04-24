"""Sync .env files between a source and target, preserving comments and redacting secrets."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from envoy_local.parser import ParseResult, parse_env_file
from envoy_local.redactor import Redactor, RedactionConfig
from envoy_local.serializer import merge_entries, write_env_file


@dataclass
class SyncOptions:
    redact_secrets: bool = True
    overwrite_existing: bool = False
    dry_run: bool = False
    redaction_config: RedactionConfig = field(default_factory=RedactionConfig)


@dataclass
class SyncResult:
    added: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    redacted: list[str] = field(default_factory=list)
    overwritten: list[str] = field(default_factory=list)

    @property
    def summary(self) -> str:
        parts = []
        if self.added:
            parts.append(f"{len(self.added)} added")
        if self.overwritten:
            parts.append(f"{len(self.overwritten)} overwritten")
        if self.skipped:
            parts.append(f"{len(self.skipped)} skipped")
        if self.redacted:
            parts.append(f"{len(self.redacted)} redacted")
        return ", ".join(parts) if parts else "no changes"


def sync_env_files(
    source: Path,
    target: Path,
    options: Optional[SyncOptions] = None,
) -> SyncResult:
    """Sync entries from source .env into target .env.

    New keys from source are added to target. Existing keys in target are
    skipped unless overwrite_existing is True. Secret values are redacted
    when redact_secrets is True.
    """
    if options is None:
        options = SyncOptions()

    source_result: ParseResult = parse_env_file(source)
    target_result: ParseResult = parse_env_file(target) if target.exists() else ParseResult(entries=[])

    redactor = Redactor(options.redaction_config) if options.redact_secrets else None

    existing_keys = {e.key for e in target_result.entries if e.key is not None}
    result = SyncResult()

    incoming = []
    for entry in source_result.entries:
        if entry.key is None:
            # comment or blank line — skip
            continue

        if entry.key in existing_keys:
            if options.overwrite_existing:
                result.overwritten.append(entry.key)
                incoming.append(entry)
            else:
                result.skipped.append(entry.key)
            continue

        if redactor and redactor.is_secret(entry.key):
            entry = entry.__class__(
                key=entry.key,
                value="",
                comment=entry.comment,
                raw=entry.raw,
            )
            result.redacted.append(entry.key)
        else:
            result.added.append(entry.key)

        incoming.append(entry)

    if not options.dry_run and incoming:
        merged = merge_entries(target_result.entries, incoming, overwrite=options.overwrite_existing)
        write_env_file(target, merged)

    return result
