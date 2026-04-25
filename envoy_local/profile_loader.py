"""Load env entries for the active (or named) profile."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

from envoy_local.parser import ParseResult, parse_env_file
from envoy_local.profile import Profile, get_active_profile, load_manifest


class ProfileLoadError(Exception):
    """Raised when a profile env file cannot be loaded."""


def resolve_profile_path(profile: Profile, base_dir: Path) -> Path:
    """Return absolute path for a profile's env file."""
    p = Path(profile.path)
    if p.is_absolute():
        return p
    return (base_dir / p).resolve()


def load_profile_entries(
    base_dir: Path,
    profile_name: Optional[str] = None,
) -> ParseResult:
    """Parse and return env entries for the given (or active) profile.

    Raises ProfileLoadError if the profile or its file is missing.
    """
    manifest = load_manifest(base_dir)

    if profile_name is not None:
        profile = manifest.profiles.get(profile_name)
        if profile is None:
            raise ProfileLoadError(f"Profile '{profile_name}' not found.")
    else:
        if manifest.active is None:
            raise ProfileLoadError("No active profile set.")
        profile = manifest.profiles.get(manifest.active)
        if profile is None:
            raise ProfileLoadError(f"Active profile '{manifest.active}' missing from manifest.")

    env_path = resolve_profile_path(profile, base_dir)
    if not env_path.exists():
        raise ProfileLoadError(f"Env file not found: {env_path}")

    return parse_env_file(env_path)


def load_profile_as_dict(
    base_dir: Path,
    profile_name: Optional[str] = None,
) -> Dict[str, str]:
    """Convenience wrapper returning a plain key->value dict."""
    from envoy_local.parser import as_dict

    result = load_profile_entries(base_dir, profile_name)
    return as_dict(result)
