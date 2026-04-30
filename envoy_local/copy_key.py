"""copy_key: copy a single key from one .env file to another."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envoy_local.parser import parse_env_file, EnvEntry
from envoy_local.serializer import write_env_file, merge_entries


@dataclass
class CopyKeyResult:
    ok: bool
    message: str
    source_key: str
    dest_key: str
    source_file: Path
    dest_file: Path
    skipped: bool = False

    def summary(self) -> str:
        if self.skipped:
            return (
                f"skipped: '{self.dest_key}' already exists in {self.dest_file}"
            )
        return (
            f"copied '{self.source_key}' -> '{self.dest_key}' "
            f"from {self.source_file} to {self.dest_file}"
        )


def copy_key(
    source: Path,
    dest: Path,
    key: str,
    dest_key: Optional[str] = None,
    overwrite: bool = False,
) -> CopyKeyResult:
    """Copy *key* from *source* .env to *dest* .env.

    Parameters
    ----------
    source:    Path to the source .env file.
    dest:      Path to the destination .env file (created if absent).
    key:       Key name to read from *source*.
    dest_key:  Key name to write in *dest*. Defaults to *key*.
    overwrite: If False and the key already exists in *dest*, abort.
    """
    resolved_dest_key = dest_key or key

    src_result = parse_env_file(source)
    src_dict = {e.key: e for e in src_result.entries if e.key}

    if key not in src_dict:
        return CopyKeyResult(
            ok=False,
            message=f"key '{key}' not found in {source}",
            source_key=key,
            dest_key=resolved_dest_key,
            source_file=source,
            dest_file=dest,
        )

    src_entry: EnvEntry = src_dict[key]

    # Load existing destination entries (or start empty).
    if dest.exists():
        dst_result = parse_env_file(dest)
        dst_entries = list(dst_result.entries)
    else:
        dst_entries = []

    dst_keys = {e.key for e in dst_entries if e.key}

    if resolved_dest_key in dst_keys and not overwrite:
        return CopyKeyResult(
            ok=False,
            message=f"key '{resolved_dest_key}' already exists in {dest}",
            source_key=key,
            dest_key=resolved_dest_key,
            source_file=source,
            dest_file=dest,
            skipped=True,
        )

    # Build the new entry (rename key if needed).
    new_entry = EnvEntry(
        key=resolved_dest_key,
        value=src_entry.value,
        comment=src_entry.comment,
        original_line=None,
    )

    incoming = [new_entry]
    merged = merge_entries(dst_entries, incoming, overwrite=overwrite)
    write_env_file(dest, merged)

    return CopyKeyResult(
        ok=True,
        message="ok",
        source_key=key,
        dest_key=resolved_dest_key,
        source_file=source,
        dest_file=dest,
    )
