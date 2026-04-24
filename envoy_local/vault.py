"""Vault module for storing and retrieving encrypted secrets."""

from __future__ import annotations

import base64
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

try:
    from cryptography.fernet import Fernet, InvalidToken
except ImportError:  # pragma: no cover
    raise ImportError("cryptography package is required: pip install cryptography")


DEFAULT_VAULT_PATH = Path(".envoy_vault")


@dataclass
class VaultEntry:
    key: str
    encrypted_value: str  # base64-encoded ciphertext


@dataclass
class Vault:
    path: Path = field(default_factory=lambda: DEFAULT_VAULT_PATH)
    _fernet: Optional[Fernet] = field(default=None, init=False, repr=False)
    _store: Dict[str, str] = field(default_factory=dict, init=False, repr=False)

    def unlock(self, key: bytes) -> None:
        """Unlock the vault with a Fernet key."""
        self._fernet = Fernet(key)
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self._store = raw.get("secrets", {})

    def _save(self) -> None:
        self.path.write_text(
            json.dumps({"secrets": self._store}, indent=2), encoding="utf-8"
        )

    def _require_unlocked(self) -> Fernet:
        if self._fernet is None:
            raise RuntimeError("Vault is locked. Call unlock() first.")
        return self._fernet

    def put(self, key: str, value: str) -> None:
        fernet = self._require_unlocked()
        encrypted = fernet.encrypt(value.encode()).decode()
        self._store[key] = encrypted
        self._save()

    def get(self, key: str) -> Optional[str]:
        fernet = self._require_unlocked()
        encrypted = self._store.get(key)
        if encrypted is None:
            return None
        try:
            return fernet.decrypt(encrypted.encode()).decode()
        except InvalidToken:
            raise ValueError(f"Failed to decrypt value for key '{key}': invalid token.")

    def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            self._save()
            return True
        return False

    def list_keys(self) -> list[str]:
        self._require_unlocked()
        return list(self._store.keys())


def generate_key() -> bytes:
    """Generate a new Fernet key."""
    return Fernet.generate_key()
