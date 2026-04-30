"""Tests for envoy_local.schema."""
from __future__ import annotations

import json

import pytest

from envoy_local.schema import (
    EnvSchema,
    FieldSchema,
    SchemaViolation,
    validate_schema,
)


def _schema(**fields_kwargs) -> EnvSchema:
    fields = {}
    for key, spec in fields_kwargs.items():
        fields[key] = FieldSchema(**spec)
    return EnvSchema(fields=fields)


def test_valid_entries_produce_no_violations():
    schema = _schema(PORT={"required": True, "pattern": r"\d+"})
    result = validate_schema({"PORT": "8080"}, schema)
    assert result.ok
    assert result.violations == []


def test_missing_required_key_is_violation():
    schema = _schema(DATABASE_URL={"required": True})
    result = validate_schema({}, schema)
    assert not result.ok
    assert any(v.key == "DATABASE_URL" for v in result.violations)


def test_pattern_mismatch_is_violation():
    schema = _schema(PORT={"pattern": r"\d+"})
    result = validate_schema({"PORT": "not-a-number"}, schema)
    assert not result.ok
    assert result.violations[0].key == "PORT"
    assert "pattern" in result.violations[0].message


def test_pattern_match_passes():
    schema = _schema(ENV={"pattern": r"(dev|staging|prod)"})
    result = validate_schema({"ENV": "prod"}, schema)
    assert result.ok


def test_allowed_values_violation():
    schema = _schema(LOG_LEVEL={"allowed_values": ["DEBUG", "INFO", "WARNING"]})
    result = validate_schema({"LOG_LEVEL": "VERBOSE"}, schema)
    assert not result.ok
    assert "not in allowed values" in result.violations[0].message


def test_allowed_values_passes():
    schema = _schema(LOG_LEVEL={"allowed_values": ["DEBUG", "INFO"]})
    result = validate_schema({"LOG_LEVEL": "INFO"}, schema)
    assert result.ok


def test_extra_key_allowed_by_default():
    schema = EnvSchema(fields={}, allow_extra=True)
    result = validate_schema({"EXTRA": "value"}, schema)
    assert result.ok


def test_extra_key_disallowed_when_flag_set():
    schema = EnvSchema(fields={}, allow_extra=False)
    result = validate_schema({"EXTRA": "value"}, schema)
    assert not result.ok
    assert result.violations[0].key == "EXTRA"
    assert "extra key" in result.violations[0].message


def test_optional_key_absent_is_fine():
    schema = _schema(OPTIONAL_KEY={"required": False, "pattern": r"\d+"})
    result = validate_schema({}, schema)
    assert result.ok


def test_from_dict_parses_correctly():
    data = {
        "allow_extra": False,
        "fields": {
            "PORT": {"required": True, "pattern": r"\d+", "description": "HTTP port"},
            "ENV": {"allowed_values": ["dev", "prod"]},
        },
    }
    schema = EnvSchema.from_dict(data)
    assert not schema.allow_extra
    assert schema.fields["PORT"].required is True
    assert schema.fields["PORT"].pattern == r"\d+"
    assert schema.fields["ENV"].allowed_values == ["dev", "prod"]


def test_schema_load_from_file(tmp_path):
    schema_file = tmp_path / "schema.json"
    schema_data = {
        "allow_extra": False,
        "fields": {
            "PORT": {"required": True, "pattern": r"\d+"},
            "LOG_LEVEL": {"allowed_values": ["DEBUG", "INFO", "WARNING"]},
        },
    }
    schema_file.write_text(json.dumps(schema_data))

    schema = EnvSchema.from_dict(json.loads(schema_file.read_text()))
    assert not schema.allow_extra
    assert schema.fields["PORT"].required is True
    assert schema.fields["LOG_LEVEL"].allowed_values == ["DEBUG", "INFO", "WARNING"]
