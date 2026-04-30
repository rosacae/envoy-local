"""set_key.py — add or update a single key in an .env file."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from envoy_local.parser import parse_env_file, EnvEntry
from envoy_local.serializer import write_env_file


@dataclass
class SetKeyResult:
    ok: bool
    key: str
    previous_value: Optional[str]
    new_value: str
    created: bool          # True when key did not exist before
    error: Optional[str] = None

    def summary(self) -> str:
        if not self.ok:
            return f"error: {self.error}"
        action = "created" if self.created else "updated"
        if self.created:
            return f"{action}: {self.key}={self.new_value}"
        return f"{action}: {self.key}  ({self.previous_value!r} -> {self.new_value!r})"


def set_key(
    path: Path,
    key: str,
    value: str,
    *,
    create_missing: bool = True,
    quote: bool = False,
) -> SetKeyResult:
    """Set *key* to *value* in the env file at *path*.

    Parameters
    ----------
    path:            Path to the target .env file.
    key:             The variable name to set.
    value:           The new value.
    create_missing:  When True (default) the key is appended if absent.
                     When False the function returns ok=False if not found.
    quote:           Wrap the value in double-quotes when writing.
    """
    if not path.exists():
        if not create_missing:
            return SetKeyResult(
                ok=False, key=key, previous_value=None,
                new_value=value, created=False,
                error=f"file not found: {path}",
            )
        path.touch()

    result = parse_env_file(path)
    entries: list[EnvEntry] = list(result.entries)

    written_value = f'"{value}"' if quote else value
    previous: Optional[str] = None
    found = False

    for i, entry in enumerate(entries):
        if entry.key == key:
            previous = entry.value
            entries[i] = EnvEntry(
                key=key,
                value=written_value,
                comment=entry.comment,
                raw=f"{key}={written_value}",
            )
            found = True
            break

    if not found:
        if not create_missing:
            return SetKeyResult(
                ok=False, key=key, previous_value=None,
                new_value=value, created=False,
                error=f"key not found: {key}",
            )
        entries.append(
            EnvEntry(key=key, value=written_value, comment=None,
                     raw=f"{key}={written_value}")
        )

    write_env_file(path, entries)
    return SetKeyResult(
        ok=True, key=key, previous_value=previous,
        new_value=value, created=not found,
    )
