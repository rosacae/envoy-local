"""CLI commands for field-level encryption of .env values."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envoy_local.encrypt import decrypt_value, encrypt_value, is_encrypted
from envoy_local.vault import Vault
from envoy_local.vault_cli import _resolve_key


def cmd_encrypt_value(ns: argparse.Namespace) -> int:
    """Encrypt a plain-text value and print the result."""
    key = _resolve_key(ns)
    if key is None:
        print("error: no vault key available", file=sys.stderr)
        return 2
    result = encrypt_value(ns.value, key)
    print(result)
    return 0


def cmd_decrypt_value(ns: argparse.Namespace) -> int:
    """Decrypt an encrypted value and print the plaintext."""
    key = _resolve_key(ns)
    if key is None:
        print("error: no vault key available", file=sys.stderr)
        return 2
    if not is_encrypted(ns.value):
        print(f"error: value is not encrypted (must start with 'enc:')", file=sys.stderr)
        return 1
    try:
        plaintext = decrypt_value(ns.value, key)
    except Exception as exc:  # noqa: BLE001
        print(f"error: decryption failed — {exc}", file=sys.stderr)
        return 1
    print(plaintext)
    return 0


def cmd_encrypt_file(ns: argparse.Namespace) -> int:
    """Re-write a .env file encrypting every secret value in place."""
    from envoy_local.parser import parse_env_file
    from envoy_local.redactor import RedactionConfig, Redactor
    from envoy_local.serializer import entries_to_text, write_env_file

    src = Path(ns.file)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 2
    key = _resolve_key(ns)
    if key is None:
        print("error: no vault key available", file=sys.stderr)
        return 2

    result = parse_env_file(src)
    cfg = RedactionConfig()
    redactor = Redactor(cfg)
    updated = []
    count = 0
    for entry in result.entries:
        if entry.key and redactor.is_secret(entry.key) and entry.value and not is_encrypted(entry.value):
            entry = entry.__class__(
                key=entry.key,
                value=encrypt_value(entry.value, key),
                comment=entry.comment,
                raw=entry.raw,
            )
            count += 1
        updated.append(entry)

    out = Path(ns.output) if ns.output else src
    write_env_file(out, entries_to_text(updated))
    print(f"encrypted {count} field(s) → {out}")
    return 0
