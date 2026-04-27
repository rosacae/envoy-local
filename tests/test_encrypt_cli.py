"""Tests for envoy_local.encrypt_cli."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from envoy_local.encrypt import decrypt_value, encrypt_value, is_encrypted
from envoy_local.encrypt_cli import cmd_decrypt_value, cmd_encrypt_file, cmd_encrypt_value
from envoy_local.vault import Vault


@pytest.fixture()
def key() -> bytes:
    return Vault.generate_key()


def _ns(key: bytes, **kwargs) -> argparse.Namespace:
    defaults = {"key_b64": None, "key_file": None, "output": None}
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    # Patch _resolve_key by injecting the raw key directly
    import envoy_local.encrypt_cli as mod
    mod._resolve_key = lambda _ns: key  # type: ignore[attr-defined]
    return ns


def test_cmd_encrypt_value_returns_0(key, capsys):
    ns = _ns(key, value="mysecret")
    rc = cmd_encrypt_value(ns)
    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert is_encrypted(out)


def test_cmd_encrypt_decrypt_roundtrip(key, capsys):
    ns_enc = _ns(key, value="roundtrip")
    cmd_encrypt_value(ns_enc)
    encrypted = capsys.readouterr().out.strip()

    ns_dec = _ns(key, value=encrypted)
    rc = cmd_decrypt_value(ns_dec)
    assert rc == 0
    assert capsys.readouterr().out.strip() == "roundtrip"


def test_cmd_decrypt_fails_on_plain_text(key, capsys):
    ns = _ns(key, value="plaintext")
    rc = cmd_decrypt_value(ns)
    assert rc == 1


def test_cmd_encrypt_file_encrypts_secrets(key, tmp_path, capsys):
    env_file = tmp_path / ".env"
    env_file.write_text("API_KEY=topsecret\nDEBUG=true\n")
    out_file = tmp_path / ".env.enc"

    ns = _ns(key, file=str(env_file), output=str(out_file))
    rc = cmd_encrypt_file(ns)
    assert rc == 0

    content = out_file.read_text()
    assert "enc:" in content        # API_KEY encrypted
    assert "DEBUG=true" in content  # non-secret left alone


def test_cmd_encrypt_file_missing_returns_2(key, tmp_path):
    ns = _ns(key, file=str(tmp_path / "missing.env"), output=None)
    rc = cmd_encrypt_file(ns)
    assert rc == 2
