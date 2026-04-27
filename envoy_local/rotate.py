"""Key rotation: re-encrypt all ENC[] values in a .env file with a new key."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from envoy_local.encrypt import is_encrypted, encrypt_value, decrypt_value
from envoy_local.parser import parse_env_file, EnvEntry
from envoy_local.serializer import entries_to_text, write_env_file


@dataclass
class RotateResult:
    rotated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> str:
        return (
            f"Rotated {len(self.rotated)} key(s), "
            f"skipped {len(self.skipped)}, "
            f"errors {len(self.errors)}."
        )


def rotate_file(
    path: Path,
    old_key: bytes,
    new_key: bytes,
    *,
    dry_run: bool = False,
) -> RotateResult:
    """Re-encrypt every ENC[] value in *path* from old_key to new_key."""
    result = RotateResult()

    parse_result = parse_env_file(path)
    updated: List[EnvEntry] = []

    for entry in parse_result.entries:
        if entry.key is None or not is_encrypted(entry.value or ""):
            updated.append(entry)
            if entry.key:
                result.skipped.append(entry.key)
            continue

        try:
            plaintext = decrypt_value(entry.value, old_key)  # type: ignore[arg-type]
            new_cipher = encrypt_value(plaintext, new_key)
            updated.append(
                EnvEntry(
                    key=entry.key,
                    value=new_cipher,
                    comment=entry.comment,
                    raw=entry.raw,
                )
            )
            result.rotated.append(entry.key)
        except Exception as exc:  # noqa: BLE001
            result.errors.append(f"{entry.key}: {exc}")
            updated.append(entry)

    if not dry_run and result.ok:
        write_env_file(path, entries_to_text(updated))

    return result
