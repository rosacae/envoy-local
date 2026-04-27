"""Tests for envoy_local.rotate."""
from __future__ import annotations

from pathlib import Path

import pytest

from envoy_local.encrypt import encrypt_value, decrypt_value, generate_key
from envoy_local.rotate import rotate_file, RotateResult


@pytest.fixture()
def old_key() -> bytes:
    return generate_key()


@pytest.fixture()
def new_key() -> bytes:
    return generate_key()


@pytest.fixture()
def env_file(tmp_path: Path, old_key: bytes) -> Path:
    secret = encrypt_value("s3cr3t", old_key)
    plain = "not-encrypted"
    content = f"SECRET={secret}\nPLAIN={plain}\n# comment line\n"
    p = tmp_path / ".env"
    p.write_text(content)
    return p


def test_rotate_re_encrypts_with_new_key(
    env_file: Path, old_key: bytes, new_key: bytes
) -> None:
    result = rotate_file(env_path=env_file, old_key=old_key, new_key=new_key)
    assert result.ok
    assert "SECRET" in result.rotated
    # Verify new ciphertext decrypts correctly with new key
    from envoy_local.parser import parse_env_file
    entries = {e.key: e.value for e in parse_env_file(env_file).entries if e.key}
    assert decrypt_value(entries["SECRET"], new_key) == "s3cr3t"


def test_rotate_skips_plain_values(
    env_file: Path, old_key: bytes, new_key: bytes
) -> None:
    result = rotate_file(env_path=env_file, old_key=old_key, new_key=new_key)
    assert "PLAIN" in result.skipped


def test_rotate_dry_run_does_not_modify_file(
    env_file: Path, old_key: bytes, new_key: bytes
) -> None:
    original = env_file.read_text()
    result = rotate_file(env_path=env_file, old_key=old_key, new_key=new_key, dry_run=True)
    assert result.ok
    assert env_file.read_text() == original


def test_rotate_wrong_old_key_reports_error(
    env_file: Path, new_key: bytes
) -> None:
    wrong_key = generate_key()
    result = rotate_file(env_path=env_file, old_key=wrong_key, new_key=new_key)
    assert not result.ok
    assert len(result.errors) == 1
    assert "SECRET" in result.errors[0]


def test_rotate_result_summary_contains_counts(
    env_file: Path, old_key: bytes, new_key: bytes
) -> None:
    result = rotate_file(env_path=env_file, old_key=old_key, new_key=new_key)
    summary = result.summary()
    assert "1" in summary  # 1 rotated
    assert "Rotated" in summary
