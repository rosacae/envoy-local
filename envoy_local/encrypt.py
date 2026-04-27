"""Field-level encryption for .env values using the vault key."""
from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Optional

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PREFIX = "enc:"
_NONCE_BYTES = 12


@dataclass
class EncryptResult:
    value: str
    was_encrypted: bool


def is_encrypted(value: str) -> bool:
    """Return True if value looks like an encrypted blob."""
    return value.startswith(PREFIX)


def encrypt_value(plaintext: str, key: bytes) -> str:
    """Encrypt *plaintext* and return a prefixed base64 string."""
    aesgcm = AESGCM(key)
    nonce = os.urandom(_NONCE_BYTES)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode(), None)
    blob = base64.urlsafe_b64encode(nonce + ciphertext).decode()
    return f"{PREFIX}{blob}"


def decrypt_value(encrypted: str, key: bytes) -> str:
    """Decrypt an encrypted blob and return the plaintext."""
    if not is_encrypted(encrypted):
        raise ValueError(f"Value does not start with '{PREFIX}': {encrypted!r}")
    blob = base64.urlsafe_b64decode(encrypted[len(PREFIX):])
    nonce, ciphertext = blob[:_NONCE_BYTES], blob[_NONCE_BYTES:]
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, None).decode()


def maybe_decrypt(value: str, key: Optional[bytes]) -> EncryptResult:
    """Decrypt *value* if it is encrypted and *key* is provided."""
    if is_encrypted(value) and key is not None:
        return EncryptResult(value=decrypt_value(value, key), was_encrypted=True)
    return EncryptResult(value=value, was_encrypted=False)
