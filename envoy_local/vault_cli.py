"""CLI helpers for vault operations used by the main CLI entry point."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from envoy_local.vault import Vault, generate_key, DEFAULT_VAULT_PATH

ENV_KEY_VAR = "ENVOY_VAULT_KEY"


def _resolve_key() -> bytes:
    """Read vault key from environment variable."""
    raw = os.environ.get(ENV_KEY_VAR)
    if not raw:
        raise EnvironmentError(
            f"Vault key not set. Export {ENV_KEY_VAR} with a valid Fernet key."
        )
    return raw.encode()


def cmd_vault_init(vault_path: Path = DEFAULT_VAULT_PATH) -> str:
    """Generate a new vault key and print it. Does not store the key."""
    key = generate_key()
    vault_path.write_text('{"secrets": {}}', encoding="utf-8")
    return key.decode()


def cmd_vault_put(key: str, value: str, vault_path: Path = DEFAULT_VAULT_PATH) -> None:
    vault = Vault(path=vault_path)
    vault.unlock(_resolve_key())
    vault.put(key, value)


def cmd_vault_get(key: str, vault_path: Path = DEFAULT_VAULT_PATH) -> Optional[str]:
    vault = Vault(path=vault_path)
    vault.unlock(_resolve_key())
    return vault.get(key)


def cmd_vault_delete(key: str, vault_path: Path = DEFAULT_VAULT_PATH) -> bool:
    vault = Vault(path=vault_path)
    vault.unlock(_resolve_key())
    return vault.delete(key)


def cmd_vault_list(vault_path: Path = DEFAULT_VAULT_PATH) -> list[str]:
    vault = Vault(path=vault_path)
    vault.unlock(_resolve_key())
    return vault.list_keys()
