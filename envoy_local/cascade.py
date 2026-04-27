"""Cascade loading: merge multiple .env files in priority order.

Later files in the list take precedence over earlier ones.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

from envoy_local.parser import ParseResult, EnvEntry, parse_env_file
from envoy_local.serializer import merge_entries


@dataclass
class CascadeOptions:
    files: List[Path]
    ignore_missing: bool = False


@dataclass
class CascadeResult:
    entries: List[EnvEntry]
    loaded: List[Path] = field(default_factory=list)
    skipped: List[Path] = field(default_factory=list)

    def as_dict(self) -> Dict[str, str]:
        return {
            e.key: (e.value or "")
            for e in self.entries
            if e.key is not None
        }

    def summary(self) -> str:
        loaded = ", ".join(str(p) for p in self.loaded)
        skipped = ", ".join(str(p) for p in self.skipped)
        parts = [f"loaded={loaded or 'none'}"]
        if skipped:
            parts.append(f"skipped={skipped}")
        parts.append(f"keys={len(self.as_dict())}")
        return " ".join(parts)


def cascade_env_files(options: CascadeOptions) -> CascadeResult:
    """Merge env files left-to-right; later files override earlier ones."""
    accumulated: List[EnvEntry] = []
    loaded: List[Path] = []
    skipped: List[Path] = []

    for path in options.files:
        if not path.exists():
            if options.ignore_missing:
                skipped.append(path)
                continue
            raise FileNotFoundError(f"Cascade source not found: {path}")

        result: ParseResult = parse_env_file(path)
        # merge_entries keeps keys from *override* when duplicate
        accumulated = merge_entries(
            base=accumulated,
            override=result.entries,
            overwrite=True,
        )
        loaded.append(path)

    return CascadeResult(entries=accumulated, loaded=loaded, skipped=skipped)
