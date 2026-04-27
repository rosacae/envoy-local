"""Integration helpers: apply pins when loading or writing env files."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from envoy_local.parser import EnvEntry, parse_env_file
from envoy_local.pin import load_pins, apply_pins, PinManifest
from envoy_local.serializer import entries_to_text, write_env_file


def load_with_pins(
    env_path: Path,
    pin_dir: Optional[Path] = None,
) -> List[EnvEntry]:
    """Parse an env file and apply any pins found in pin_dir (defaults to env file's directory)."""
    result = parse_env_file(env_path)
    directory = pin_dir if pin_dir is not None else env_path.parent
    manifest = load_pins(directory)
    if not manifest.pins:
        return result.entries
    return apply_pins(result.entries, manifest)


def write_with_pins(
    env_path: Path,
    entries: List[EnvEntry],
    pin_dir: Optional[Path] = None,
) -> None:
    """Apply pins to entries then write the env file."""
    directory = pin_dir if pin_dir is not None else env_path.parent
    manifest = load_pins(directory)
    pinned = apply_pins(entries, manifest) if manifest.pins else entries
    write_env_file(env_path, pinned)


def pinned_keys_in_file(
    env_path: Path,
    pin_dir: Optional[Path] = None,
) -> List[str]:
    """Return a list of keys present in the env file that are currently pinned."""
    result = parse_env_file(env_path)
    directory = pin_dir if pin_dir is not None else env_path.parent
    manifest = load_pins(directory)
    env_keys = {e.key for e in result.entries if e.key}
    return [k for k in manifest.pins if k in env_keys]
