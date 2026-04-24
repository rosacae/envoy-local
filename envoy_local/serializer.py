"""Serialize EnvEntry objects back to .env file format."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from envoy_local.parser import EnvEntry


def entry_to_line(entry: EnvEntry) -> str:
    """Convert an EnvEntry to a .env formatted line."""
    value = entry.value
    if entry.is_quoted:
        value = f'"{value}"'
    return f"{entry.key}={value}"


def entries_to_text(entries: Sequence[EnvEntry]) -> str:
    """Render a list of EnvEntry objects as .env file text."""
    lines = [entry_to_line(e) for e in entries]
    return "\n".join(lines) + ("\n" if lines else "")


def write_env_file(path: Path, entries: Sequence[EnvEntry], overwrite: bool = False) -> None:
    """Write entries to a .env file.

    Args:
        path: Destination file path.
        entries: Sequence of EnvEntry objects to write.
        overwrite: If False and file exists, raise FileExistsError.
    """
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"File already exists: {path}. Pass overwrite=True to replace it."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    text = entries_to_text(entries)
    path.write_text(text, encoding="utf-8")


def merge_entries(
    base: Sequence[EnvEntry],
    override: Sequence[EnvEntry],
) -> list[EnvEntry]:
    """Merge two entry lists; override values win on duplicate keys."""
    merged: dict[str, EnvEntry] = {e.key: e for e in base}
    for entry in override:
        merged[entry.key] = entry
    return list(merged.values())
