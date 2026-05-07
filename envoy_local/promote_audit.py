"""Audit integration for promote operations."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy_local.promote import PromoteOptions, PromoteResult, promote_env
from envoy_local.audit import record


def promote_with_audit(
    source: Path,
    target: Path,
    options: PromoteOptions,
    log_dir: Optional[Path] = None,
    actor: str = "envoy-local",
) -> PromoteResult:
    """Run promote_env and record an audit entry for the operation.

    Parameters
    ----------
    source:
        Path to the source .env file.
    target:
        Path to the destination .env file.
    options:
        Promote configuration (overwrite, redact, etc.).
    log_dir:
        Directory where the audit log is stored.  Defaults to the
        parent directory of *target*.
    actor:
        Free-form label stored in the audit entry.

    Returns
    -------
    PromoteResult
        The result returned by :func:`promote_env`, unchanged.
    """
    result = promote_env(source, target, options)

    resolved_log_dir = log_dir if log_dir is not None else target.parent

    detail = {
        "source": str(source),
        "target": str(target),
        "added": result.added,
        "overwritten": result.overwritten,
        "skipped": result.skipped,
        "redacted": result.redacted,
        "overwrite_flag": options.overwrite,
        "redact_flag": options.redact_secrets,
    }

    record(
        operation="promote",
        target=str(target),
        detail=detail,
        log_dir=resolved_log_dir,
        actor=actor,
    )

    return result
