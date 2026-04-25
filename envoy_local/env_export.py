"""Export .env entries to various formats (shell export, JSON, YAML, Docker)."""
from __future__ import annotations

import json
from enum import Enum
from typing import List, Optional

from envoy_local.parser import EnvEntry, ParseResult
from envoy_local.redactor import Redactor


class ExportFormat(str, Enum):
    SHELL = "shell"
    JSON = "json"
    YAML = "yaml"
    DOCKER = "docker"


def _maybe_redact(entry: EnvEntry, redactor: Optional[Redactor]) -> str:
    if redactor and redactor.is_secret(entry.key):
        return redactor.redact(entry.value)
    return entry.value


def export_shell(entries: List[EnvEntry], redactor: Optional[Redactor] = None) -> str:
    """Emit 'export KEY=VALUE' lines suitable for shell sourcing."""
    lines = []
    for e in entries:
        if not e.key:
            continue
        value = _maybe_redact(e, redactor)
        escaped = value.replace('"', '\\"')
        lines.append(f'export {e.key}="{escaped}"')
    return "\n".join(lines)


def export_json(entries: List[EnvEntry], redactor: Optional[Redactor] = None) -> str:
    """Emit a JSON object mapping keys to values."""
    data = {
        e.key: _maybe_redact(e, redactor)
        for e in entries
        if e.key
    }
    return json.dumps(data, indent=2)


def export_yaml(entries: List[EnvEntry], redactor: Optional[Redactor] = None) -> str:
    """Emit a simple YAML mapping (no external dependency)."""
    lines = []
    for e in entries:
        if not e.key:
            continue
        value = _maybe_redact(e, redactor)
        # Wrap in quotes if value contains special YAML characters
        if any(c in value for c in (':', '#', '{', '}', '[', ']', ',', '&', '*', '?', '|', '-', '<', '>', '=', '!', '%', '@', '`', '"', "'")):
            escaped = value.replace('"', '\\"')
            lines.append(f'{e.key}: "{escaped}"')
        else:
            lines.append(f"{e.key}: {value}" if value else f"{e.key}: \"\"")
    return "\n".join(lines)


def export_docker(entries: List[EnvEntry], redactor: Optional[Redactor] = None) -> str:
    """Emit '--env KEY=VALUE' flags for use with docker run."""
    lines = []
    for e in entries:
        if not e.key:
            continue
        value = _maybe_redact(e, redactor)
        lines.append(f"--env {e.key}={value}")
    return " ".join(lines)


def export_entries(
    result: ParseResult,
    fmt: ExportFormat,
    redactor: Optional[Redactor] = None,
) -> str:
    """Dispatch to the correct exporter based on format."""
    entries = [e for e in result.entries if e.key]
    dispatch = {
        ExportFormat.SHELL: export_shell,
        ExportFormat.JSON: export_json,
        ExportFormat.YAML: export_yaml,
        ExportFormat.DOCKER: export_docker,
    }
    return dispatch[fmt](entries, redactor)
