"""Integration between the vault and the env parser/serializer.

Allows injecting vault secrets into parsed env entries before writing.
"""

from __future__ import annotations

from typing import List, Optional

from envoy_local.parser import EnvEntry
from envoy_local.vault import Vault

VAULT_REF_PREFIX = "vault:"


def is_vault_ref(value: str) -> bool:
    """Return True if value is a vault reference like 'vault:MY_KEY'."""
    return value.strip().startswith(VAULT_REF_PREFIX)


def resolve_vault_ref(value: str) -> str:
    """Extract the vault key name from a vault reference string."""
    return value.strip()[len(VAULT_REF_PREFIX):]


def inject_vault_secrets(
    entries: List[EnvEntry],
    vault: Vault,
    *,
    raise_on_missing: bool = False,
) -> List[EnvEntry]:
    """Return a new list of EnvEntry with vault references resolved.

    Entries whose value is a vault reference (e.g. ``vault:DB_PASSWORD``) will
    have their value replaced with the decrypted secret from the vault.  If the
    vault does not contain the referenced key the original reference string is
    kept (or an error raised when *raise_on_missing* is True).
    """
    resolved: List[EnvEntry] = []
    for entry in entries:
        if entry.value is not None and is_vault_ref(entry.value):
            vault_key = resolve_vault_ref(entry.value)
            secret: Optional[str] = vault.get(vault_key)
            if secret is None:
                if raise_on_missing:
                    raise KeyError(
                        f"Vault has no entry for '{vault_key}' "
                        f"(referenced by env key '{entry.key}')."
                    )
                resolved.append(entry)
            else:
                resolved.append(
                    EnvEntry(
                        key=entry.key,
                        value=secret,
                        comment=entry.comment,
                        raw_line=entry.raw_line,
                    )
                )
        else:
            resolved.append(entry)
    return resolved
