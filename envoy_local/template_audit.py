"""Record template render events to the audit log."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from envoy_local.audit import record
from envoy_local.template import RenderResult


def audit_render(
    template_path: Path,
    env_path: Path,
    render: RenderResult,
    audit_dir: Optional[Path] = None,
    actor: str = "envoy-local",
) -> None:
    """Write a render event to the audit log.

    Records which template was rendered, which env file was used, how many
    placeholders were resolved, and which keys (if any) were missing.
    """
    detail_parts = [
        f"template={template_path.name}",
        f"env={env_path.name}",
        f"resolved={len(render.resolved)}",
    ]
    if render.missing:
        detail_parts.append(f"missing={','.join(render.missing)}")

    event = "template_render" if render.ok else "template_render_incomplete"
    detail = " ".join(detail_parts)

    record(
        event=event,
        detail=detail,
        actor=actor,
        log_dir=audit_dir,
    )
