"""Tests for envoy_local.profile."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envoy_local.profile import (
    Profile,
    ProfileManifest,
    add_profile,
    get_active_profile,
    list_profiles,
    load_manifest,
    remove_profile,
    save_manifest,
    set_active,
)


@pytest.fixture
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def test_load_manifest_returns_empty_when_no_file(base_dir):
    manifest = load_manifest(base_dir)
    assert manifest.profiles == {}
    assert manifest.active is None


def test_add_profile_creates_manifest_file(base_dir):
    add_profile(base_dir, "dev", ".env.dev", "Development")
    manifest_file = base_dir / ".envoy_profiles.json"
    assert manifest_file.exists()


def test_add_profile_roundtrip(base_dir):
    add_profile(base_dir, "dev", ".env.dev", "Development")
    manifest = load_manifest(base_dir)
    assert "dev" in manifest.profiles
    assert manifest.profiles["dev"].path == ".env.dev"
    assert manifest.profiles["dev"].description == "Development"


def test_add_multiple_profiles(base_dir):
    add_profile(base_dir, "dev", ".env.dev")
    add_profile(base_dir, "prod", ".env.prod", "Production")
    profiles = list_profiles(base_dir)
    names = [p.name for p in profiles]
    assert "dev" in names
    assert "prod" in names


def test_remove_profile_returns_true(base_dir):
    add_profile(base_dir, "dev", ".env.dev")
    result = remove_profile(base_dir, "dev")
    assert result is True
    assert "dev" not in {p.name for p in list_profiles(base_dir)}


def test_remove_missing_profile_returns_false(base_dir):
    result = remove_profile(base_dir, "nonexistent")
    assert result is False


def test_set_active_returns_true_for_existing(base_dir):
    add_profile(base_dir, "staging", ".env.staging")
    result = set_active(base_dir, "staging")
    assert result is True
    manifest = load_manifest(base_dir)
    assert manifest.active == "staging"


def test_set_active_returns_false_for_missing(base_dir):
    result = set_active(base_dir, "ghost")
    assert result is False


def test_get_active_profile_returns_none_when_not_set(base_dir):
    add_profile(base_dir, "dev", ".env.dev")
    assert get_active_profile(base_dir) is None


def test_get_active_profile_returns_profile(base_dir):
    add_profile(base_dir, "dev", ".env.dev")
    set_active(base_dir, "dev")
    profile = get_active_profile(base_dir)
    assert profile is not None
    assert profile.name == "dev"


def test_remove_active_profile_clears_active(base_dir):
    add_profile(base_dir, "dev", ".env.dev")
    set_active(base_dir, "dev")
    remove_profile(base_dir, "dev")
    manifest = load_manifest(base_dir)
    assert manifest.active is None


def test_profile_to_dict_and_from_dict():
    p = Profile(name="test", path=".env.test", description="Test env")
    d = p.to_dict()
    restored = Profile.from_dict(d)
    assert restored.name == p.name
    assert restored.path == p.path
    assert restored.description == p.description
