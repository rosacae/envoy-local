"""Audit integration for patch operations."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .patch import PatchOptions, PatchResult, patch_env_file
from .audit import record


def patch_with_audit(
    path: Path,
    options: PatchOptions,
    frozen_keys: Optional[list[str]] = None,
    log_dir: Optional[Path] = None,
    actor: str = "envoy-local",
) -> PatchResult:
    """Run patch_env_file and record an audit entry for every mutation."""
    result = patch_env_file(path, options, frozen_keys=frozen_keys)

    if not result.ok:
        return result

    audit_dir = log_dir or path.parent

    for key in result.added:
        record(
            path=path,
            action="patch:add",
            key=key,
            detail=f"value set to {options.upsert.get(key, '')!r}",
            log_dir=audit_dir,
            actor=actor,
        )

    for key in result.updated:
        record(
            path=path,
            action="patch:update",
            key=key,
            detail=f"value updated to {options.upsert.get(key, '')!r}",
            log_dir=audit_dir,
            actor=actor,
        )

    for key in result.deleted:
        record(
            path=path,
            action="patch:delete",
            key=key,
            detail="key removed",
            log_dir=audit_dir,
            actor=actor,
        )

    return result
