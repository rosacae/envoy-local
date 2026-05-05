"""Extract a subset of keys from an env file into a new file."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envoy_local.parser import ParseResult, EnvEntry
from envoy_local.serializer import write_env_file


@dataclass
class ExtractResult:
    ok: bool
    extracted: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)
    error: Optional[str] = None

    def summary(self) -> str:
        if not self.ok:
            return f"error: {self.error}"
        return (
            f"extracted {len(self.extracted)} key(s), "
            f"skipped {len(self.skipped)} key(s)"
        )


def extract_keys(
    source: Path,
    dest: Path,
    keys: Optional[List[str]] = None,
    pattern: Optional[str] = None,
    overwrite: bool = False,
) -> ExtractResult:
    """Extract matching keys from *source* and write them to *dest*.

    At least one of *keys* or *pattern* must be provided.  When both are
    given the union of matches is used.
    """
    if not keys and not pattern:
        return ExtractResult(ok=False, error="provide at least one key or a pattern")

    if not source.exists():
        return ExtractResult(ok=False, error=f"source file not found: {source}")

    if dest.exists() and not overwrite:
        return ExtractResult(ok=False, error=f"destination already exists: {dest}")

    from envoy_local.parser import parse_env_file

    parsed: ParseResult = parse_env_file(source)

    key_set = set(keys or [])
    compiled = re.compile(pattern) if pattern else None

    extracted: List[EnvEntry] = []
    extracted_names: List[str] = []
    skipped: List[str] = []

    for entry in parsed.entries:
        if entry.key is None:
            # preserve blank lines / comments as-is
            continue
        matched = entry.key in key_set or (compiled is not None and compiled.search(entry.key))
        if matched:
            extracted.append(entry)
            extracted_names.append(entry.key)
        else:
            skipped.append(entry.key)

    write_env_file(dest, extracted)
    return ExtractResult(ok=True, extracted=extracted_names, skipped=skipped)
