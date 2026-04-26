"""Schema validation for .env files against a JSON Schema-like definition."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
import re


@dataclass
class FieldSchema:
    required: bool = False
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None
    description: str = ""


@dataclass
class EnvSchema:
    fields: Dict[str, FieldSchema] = field(default_factory=dict)
    allow_extra: bool = True

    @staticmethod
    def from_dict(data: dict) -> "EnvSchema":
        fields = {}
        for key, spec in data.get("fields", {}).items():
            fields[key] = FieldSchema(
                required=spec.get("required", False),
                pattern=spec.get("pattern"),
                allowed_values=spec.get("allowed_values"),
                description=spec.get("description", ""),
            )
        return EnvSchema(
            fields=fields,
            allow_extra=data.get("allow_extra", True),
        )

    @staticmethod
    def load(path: str) -> "EnvSchema":
        with open(path, "r", encoding="utf-8") as fh:
            return EnvSchema.from_dict(json.load(fh))


@dataclass
class SchemaViolation:
    key: str
    message: str

    def to_dict(self) -> dict:
        return {"key": self.key, "message": self.message}


@dataclass
class SchemaValidationResult:
    violations: List[SchemaViolation] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.violations) == 0


def validate_schema(
    entries: Dict[str, str],
    schema: EnvSchema,
) -> SchemaValidationResult:
    """Validate a dict of env entries against an EnvSchema."""
    violations: List[SchemaViolation] = []

    for key, fschema in schema.fields.items():
        if fschema.required and key not in entries:
            violations.append(SchemaViolation(key=key, message="required key is missing"))
            continue
        if key not in entries:
            continue
        value = entries[key]
        if fschema.pattern and not re.fullmatch(fschema.pattern, value):
            violations.append(
                SchemaViolation(key=key, message=f"value does not match pattern '{fschema.pattern}'")
            )
        if fschema.allowed_values is not None and value not in fschema.allowed_values:
            allowed = ", ".join(fschema.allowed_values)
            violations.append(
                SchemaViolation(key=key, message=f"value '{value}' not in allowed values: {allowed}")
            )

    if not schema.allow_extra:
        for key in entries:
            if key not in schema.fields:
                violations.append(SchemaViolation(key=key, message="extra key not allowed by schema"))

    return SchemaValidationResult(violations=violations)
