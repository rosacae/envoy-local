"""Merge multiple .env files into a single output, with configurable conflict resolution."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from envoy_local.parser import ParseResult, EnvEntry, parse_env_file
from envoy_local.serializer import entries_to_text, write_env_file


@dataclass
class MergeOptions:
    sources: List[Path]
    output: Optional[Path] = None
    overwrite: bool = True          # later files win on conflict
    keep_comments: bool = True
    dry_run: bool = False


@dataclass
class MergeResult:
    merged: List[EnvEntry] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    source_counts: List[int] = field(default_factory=list)
    ok: bool = True
    error: str = ""

    def summary(self) -> str:
        total = len([e for e in self.merged if e.key])
        parts = [f"merged {total} keys from {len(self.source_counts)} files"]
        if self.conflicts:
            parts.append(f"{len(self.conflicts)} conflict(s) resolved")
        return "; ".join(parts)


def merge_env_files(options: MergeOptions) -> MergeResult:
    result = MergeResult()

    if not options.sources:
        result.ok = False
        result.error = "no source files provided"
        return result

    seen: dict[str, EnvEntry] = {}
    ordered_keys: list[str] = []
    extra_entries: list[EnvEntry] = []  # comments / blanks

    for path in options.sources:
        if not path.exists():
            result.ok = False
            result.error = f"source file not found: {path}"
            return result

        pr: ParseResult = parse_env_file(path)
        result.source_counts.append(len([e for e in pr.entries if e.key]))

        for entry in pr.entries:
            if not entry.key:
                if options.keep_comments:
                    extra_entries.append(entry)
                continue
            if entry.key in seen:
                result.conflicts.append(entry.key)
                if options.overwrite:
                    seen[entry.key] = entry
            else:
                seen[entry.key] = entry
                ordered_keys.append(entry.key)

    merged: list[EnvEntry] = []
    if options.keep_comments and extra_entries:
        merged.extend(extra_entries[:1])  # leading comments
    for key in ordered_keys:
        merged.append(seen[key])

    result.merged = merged

    if not options.dry_run and options.output:
        write_env_file(options.output, merged)

    return result
