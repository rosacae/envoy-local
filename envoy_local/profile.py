"""Profile support: named env file variants (e.g. dev, staging, prod)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

_PROFILE_MANIFEST = ".envoy_profiles.json"


@dataclass
class Profile:
    name: str
    path: str  # relative or absolute path to the .env file
    description: str = ""

    def to_dict(self) -> dict:
        return {"name": self.name, "path": self.path, "description": self.description}

    @staticmethod
    def from_dict(d: dict) -> "Profile":
        return Profile(name=d["name"], path=d["path"], description=d.get("description", ""))


@dataclass
class ProfileManifest:
    profiles: Dict[str, Profile] = field(default_factory=dict)
    active: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "active": self.active,
            "profiles": {k: v.to_dict() for k, v in self.profiles.items()},
        }

    @staticmethod
    def from_dict(d: dict) -> "ProfileManifest":
        profiles = {k: Profile.from_dict(v) for k, v in d.get("profiles", {}).items()}
        return ProfileManifest(profiles=profiles, active=d.get("active"))


def _manifest_path(base_dir: Path) -> Path:
    return base_dir / _PROFILE_MANIFEST


def load_manifest(base_dir: Path) -> ProfileManifest:
    p = _manifest_path(base_dir)
    if not p.exists():
        return ProfileManifest()
    return ProfileManifest.from_dict(json.loads(p.read_text()))


def save_manifest(base_dir: Path, manifest: ProfileManifest) -> None:
    _manifest_path(base_dir).write_text(json.dumps(manifest.to_dict(), indent=2))


def add_profile(base_dir: Path, name: str, path: str, description: str = "") -> Profile:
    manifest = load_manifest(base_dir)
    profile = Profile(name=name, path=path, description=description)
    manifest.profiles[name] = profile
    save_manifest(base_dir, manifest)
    return profile


def remove_profile(base_dir: Path, name: str) -> bool:
    manifest = load_manifest(base_dir)
    if name not in manifest.profiles:
        return False
    del manifest.profiles[name]
    if manifest.active == name:
        manifest.active = None
    save_manifest(base_dir, manifest)
    return True


def set_active(base_dir: Path, name: str) -> bool:
    manifest = load_manifest(base_dir)
    if name not in manifest.profiles:
        return False
    manifest.active = name
    save_manifest(base_dir, manifest)
    return True


def get_active_profile(base_dir: Path) -> Optional[Profile]:
    manifest = load_manifest(base_dir)
    if manifest.active is None:
        return None
    return manifest.profiles.get(manifest.active)


def list_profiles(base_dir: Path) -> List[Profile]:
    return list(load_manifest(base_dir).profiles.values())
