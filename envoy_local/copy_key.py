"""copy_key: copy a key (optionally renamed) from one .env file to another."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .parser import parse_env_file, EnvEntry
from .serializer import write_env_file, merge_entries
from .redactor import Redactor, RedactionConfig


@dataclass
class CopyKeyResult:
    ok: bool
    source_key: str
    dest_key: str
    value: Optional[str]
    skipped: bool
    message: str

    def summary(self) -> str:
        return self.message


def copy_key(
    source_path: Path,
    dest_path: Path,
    key: str,
    *,
    dest_key: Optional[str] = None,
    overwrite: bool = False,
    redact: bool = False,
    redaction_config: Optional[RedactionConfig] = None,
) -> CopyKeyResult:
    """Copy *key* from *source_path* into *dest_path*.

    Parameters
    ----------
    source_path:  file to read the key from.
    dest_path:    file to write the key into (created if absent).
    key:          key name in the source file.
    dest_key:     key name to use in the destination (defaults to *key*).
    overwrite:    replace the key if it already exists in the destination.
    redact:       if True the value is replaced with an empty string when
                  the key is detected as a secret.
    redaction_config: custom redaction settings (uses defaults when None).
    """
    target_key = dest_key or key

    if not source_path.exists():
        return CopyKeyResult(
            ok=False, source_key=key, dest_key=target_key, value=None,
            skipped=True, message=f"Source file not found: {source_path}"
        )

    src_result = parse_env_file(source_path)
    src_dict = {e.key: e for e in src_result.entries if e.key}

    if key not in src_dict:
        return CopyKeyResult(
            ok=False, source_key=key, dest_key=target_key, value=None,
            skipped=True, message=f"Key '{key}' not found in {source_path}"
        )

    src_entry: EnvEntry = src_dict[key]
    value = src_entry.value or ""

    if redact:
        cfg = redaction_config or RedactionConfig()
        redactor = Redactor(cfg)
        if redactor.is_secret(key):
            value = ""

    dest_entries = []
    if dest_path.exists():
        dest_result = parse_env_file(dest_path)
        dest_entries = dest_result.entries

    dest_dict = {e.key: e for e in dest_entries if e.key}

    if target_key in dest_dict and not overwrite:
        return CopyKeyResult(
            ok=True, source_key=key, dest_key=target_key, value=value,
            skipped=True,
            message=f"Key '{target_key}' already exists in destination (use overwrite=True to replace)"
        )

    new_entry = EnvEntry(
        key=target_key,
        value=value,
        comment=src_entry.comment,
        original_line=f"{target_key}={value}",
    )
    merged = merge_entries(dest_entries, [new_entry], overwrite=overwrite)
    write_env_file(dest_path, merged)

    action = "overwrote" if (target_key in dest_dict and overwrite) else "added"
    return CopyKeyResult(
        ok=True, source_key=key, dest_key=target_key, value=value,
        skipped=False,
        message=f"Key '{key}' {action} as '{target_key}' in {dest_path}"
    )
