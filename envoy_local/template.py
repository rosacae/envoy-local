"""Template rendering: substitute {{VAR}} placeholders with env values."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envoy_local.parser import ParseResult

_PLACEHOLDER_RE = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


@dataclass
class RenderResult:
    text: str
    resolved: List[str] = field(default_factory=list)
    missing: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.missing) == 0


def render_template(template: str, env: Dict[str, str]) -> RenderResult:
    """Replace {{KEY}} placeholders in *template* using *env* mapping."""
    resolved: List[str] = []
    missing: List[str] = []

    def _replace(match: re.Match) -> str:
        key = match.group(1)
        if key in env:
            resolved.append(key)
            return env[key]
        missing.append(key)
        return match.group(0)  # leave placeholder intact

    rendered = _PLACEHOLDER_RE.sub(_replace, template)
    return RenderResult(text=rendered, resolved=resolved, missing=missing)


def render_template_from_parse_result(
    template: str,
    result: ParseResult,
    override: Optional[Dict[str, str]] = None,
) -> RenderResult:
    """Convenience wrapper that accepts a *ParseResult* from the parser."""
    from envoy_local.parser import as_dict

    env = as_dict(result)
    if override:
        env.update(override)
    return render_template(template, env)


def list_placeholders(template: str) -> List[str]:
    """Return unique placeholder names found in *template*, preserving order."""
    seen: dict[str, None] = {}
    for match in _PLACEHOLDER_RE.finditer(template):
        seen[match.group(1)] = None
    return list(seen)
