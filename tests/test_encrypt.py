"""Tests for envoy_local.encrypt."""
from __future__ import annotations

import pytest

from envoy_local.encrypt import (
    PREFIX,
    EncryptResult,
    decrypt_value,
    encrypt_value,
    is_encrypted,
    maybe_decrypt,
)
from envoy_local.vault import Vault


@pytest.fixture()
def key() -> bytes:
    return Vault.generate_key()


def test_is_encrypted_true_for_prefixed(key):
    blob = encrypt_value("secret", key)
    assert is_encrypted(blob)


def test_is_encrypted_false_for_plain():
    assert not is_encrypted("plaintext")
    assert not is_encrypted("")


def test_encrypt_value_starts_with_prefix(key):
    result = encrypt_value("hello", key)
    assert result.startswith(PREFIX)


def test_roundtrip_returns_original_plaintext(key):
    plaintext = "super-secret-value"
    encrypted = encrypt_value(plaintext, key)
    assert decrypt_value(encrypted, key) == plaintext


def test_different_nonces_produce_different_ciphertexts(key):
    a = encrypt_value("same", key)
    b = encrypt_value("same", key)
    assert a != b


def test_decrypt_raises_on_wrong_key(key):
    other_key = Vault.generate_key()
    encrypted = encrypt_value("secret", key)
    with pytest.raises(Exception):
        decrypt_value(encrypted, other_key)


def test_decrypt_raises_if_not_prefixed(key):
    with pytest.raises(ValueError, match="enc:"):
        decrypt_value("notencrypted", key)


def test_maybe_decrypt_decrypts_when_key_provided(key):
    encrypted = encrypt_value("value", key)
    res = maybe_decrypt(encrypted, key)
    assert res.value == "value"
    assert res.was_encrypted is True


def test_maybe_decrypt_passthrough_when_no_key(key):
    encrypted = encrypt_value("value", key)
    res = maybe_decrypt(encrypted, None)
    assert res.value == encrypted
    assert res.was_encrypted is False


def test_maybe_decrypt_plain_value_unchanged(key):
    res = maybe_decrypt("plain", key)
    assert res.value == "plain"
    assert res.was_encrypted is False
