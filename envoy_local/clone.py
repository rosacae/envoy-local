"""Clone an env file to a new location, with optional redaction and encryption."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .parser import ParseResult, parse_env_file
from .redactor import Redactor, RedactionConfig
from .serializer import entries_to_text, write_env_file
from .encrypt import is_encrypted, encrypt_value


@dataclass
class CloneOptions:
    redact_secrets: bool = False
    redact_placeholder: str = "REDACTED"
    encrypt_key: Optional[bytes] = None
    overwrite: bool = False


@dataclass
class CloneResult:
    source: Path
    destination: Path
    total: int
    redacted: int
    encrypted: int
    skipped: bool  # True when destination existed and overwrite=False

    def summary(self) -> str:
        if self.skipped:
            return f"Skipped: {self.destination} already exists."
        parts = [f"Cloned {self.total} entries from {self.source} → {self.destination}"]
        if self.redacted:
            parts.append(f"{self.redacted} redacted")
        if self.encrypted:
            parts.append(f"{self.encrypted} encrypted")
        return "; ".join(parts) + "."


def clone_env_file(
    source: Path,
    destination: Path,
    options: Optional[CloneOptions] = None,
) -> CloneResult:
    """Copy *source* to *destination*, applying optional redaction / encryption."""
    if options is None:
        options = CloneOptions()

    if destination.exists() and not options.overwrite:
        result = parse_env_file(source)
        return CloneResult(
            source=source,
            destination=destination,
            total=len(result.entries),
            redacted=0,
            encrypted=0,
            skipped=True,
        )

    result: ParseResult = parse_env_file(source)
    redactor = Redactor(RedactionConfig()) if options.redact_secrets else None

    redacted_count = 0
    encrypted_count = 0
    entries = []

    for entry in result.entries:
        if entry.key is None:
            entries.append(entry)
            continue

        value = entry.value or ""

        if options.redact_secrets and redactor and redactor.is_secret(entry.key):
            value = options.redact_placeholder
            redacted_count += 1
        elif options.encrypt_key and not is_encrypted(value):
            value = encrypt_value(value, options.encrypt_key)
            encrypted_count += 1

        entries.append(entry.__class__(key=entry.key, value=value, comment=entry.comment, raw=entry.raw))

    write_env_file(destination, entries)

    return CloneResult(
        source=source,
        destination=destination,
        total=len(entries),
        redacted=redacted_count,
        encrypted=encrypted_count,
        skipped=False,
    )
