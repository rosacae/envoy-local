"""Tests for envoy_local.vault and envoy_local.vault_cli."""

from __future__ import annotations

import json
import os
import pytest
from pathlib import Path

from envoy_local.vault import Vault, generate_key, DEFAULT_VAULT_PATH
from envoy_local.vault_cli import (
    cmd_vault_init,
    cmd_vault_put,
    cmd_vault_get,
    cmd_vault_delete,
    cmd_vault_list,
    ENV_KEY_VAR,
)


@pytest.fixture()
def vault_key() -> bytes:
    return generate_key()


@pytest.fixture()
def unlocked_vault(tmp_path, vault_key):
    v = Vault(path=tmp_path / ".vault")
    v.unlock(vault_key)
    return v


def test_generate_key_returns_bytes():
    key = generate_key()
    assert isinstance(key, bytes)
    assert len(key) > 0


def test_put_and_get_roundtrip(unlocked_vault):
    unlocked_vault.put("DB_PASSWORD", "s3cr3t")
    assert unlocked_vault.get("DB_PASSWORD") == "s3cr3t"


def test_get_missing_key_returns_none(unlocked_vault):
    assert unlocked_vault.get("NONEXISTENT") is None


def test_delete_existing_key(unlocked_vault):
    unlocked_vault.put("API_KEY", "abc123")
    result = unlocked_vault.delete("API_KEY")
    assert result is True
    assert unlocked_vault.get("API_KEY") is None


def test_delete_missing_key_returns_false(unlocked_vault):
    assert unlocked_vault.delete("GHOST") is False


def test_list_keys(unlocked_vault):
    unlocked_vault.put("KEY_A", "1")
    unlocked_vault.put("KEY_B", "2")
    keys = unlocked_vault.list_keys()
    assert set(keys) == {"KEY_A", "KEY_B"}


def test_vault_persists_to_disk(tmp_path, vault_key):
    path = tmp_path / ".vault"
    v1 = Vault(path=path)
    v1.unlock(vault_key)
    v1.put("SECRET", "value")

    v2 = Vault(path=path)
    v2.unlock(vault_key)
    assert v2.get("SECRET") == "value"


def test_vault_locked_raises(tmp_path):
    v = Vault(path=tmp_path / ".vault")
    with pytest.raises(RuntimeError, match="locked"):
        v.put("K", "V")


def test_cmd_vault_init_creates_file(tmp_path):
    path = tmp_path / ".vault"
    key_str = cmd_vault_init(vault_path=path)
    assert path.exists()
    data = json.loads(path.read_text())
    assert "secrets" in data
    assert isinstance(key_str, str)


def test_cmd_put_get_via_env(tmp_path, vault_key, monkeypatch):
    monkeypatch.setenv(ENV_KEY_VAR, vault_key.decode())
    path = tmp_path / ".vault"
    cmd_vault_init(vault_path=path)
    cmd_vault_put("TOKEN", "mytoken", vault_path=path)
    result = cmd_vault_get("TOKEN", vault_path=path)
    assert result == "mytoken"


def test_cmd_list_and_delete(tmp_path, vault_key, monkeypatch):
    monkeypatch.setenv(ENV_KEY_VAR, vault_key.decode())
    path = tmp_path / ".vault"
    cmd_vault_init(vault_path=path)
    cmd_vault_put("A", "1", vault_path=path)
    cmd_vault_put("B", "2", vault_path=path)
    assert set(cmd_vault_list(vault_path=path)) == {"A", "B"}
    cmd_vault_delete("A", vault_path=path)
    assert cmd_vault_list(vault_path=path) == ["B"]


def test_cmd_missing_env_key_raises(tmp_path, monkeypatch):
    """Ensure commands raise when the encryption key env var is not set."""
    monkeypatch.delenv(ENV_KEY_VAR, raising=False)
    path = tmp_path / ".vault"
    cmd_vault_init(vault_path=path)
    with pytest.raises((KeyError, RuntimeError, ValueError)):
        cmd_vault_get("SOME_KEY", vault_path=path)
