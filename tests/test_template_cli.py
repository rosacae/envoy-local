"""Integration tests for envoy_local.template_cli."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envoy_local.template_cli import cmd_template_list, cmd_template_render


@pytest.fixture()
def env_file(tmp_path: Path) -> Path:
    p = tmp_path / ".env"
    p.write_text("HOST=db.local\nPORT=5432\nSECRET=s3cr3t\n")
    return p


@pytest.fixture()
def template_file(tmp_path: Path) -> Path:
    p = tmp_path / "config.tmpl"
    p.write_text("host={{HOST}}\nport={{PORT}}\n")
    return p


def _ns(**kwargs) -> argparse.Namespace:
    defaults = dict(
        template=None,
        env_file=None,
        output=None,
        allow_missing=False,
        vault=None,
        vault_key=None,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cmd_render_stdout(capsys, env_file, template_file):
    ns = _ns(template=str(template_file), env_file=str(env_file))
    rc = cmd_template_render(ns)
    assert rc == 0
    captured = capsys.readouterr()
    assert "host=db.local" in captured.out
    assert "port=5432" in captured.out


def test_cmd_render_to_output_file(tmp_path, env_file, template_file):
    out = tmp_path / "result.txt"
    ns = _ns(template=str(template_file), env_file=str(env_file), output=str(out))
    rc = cmd_template_render(ns)
    assert rc == 0
    assert out.exists()
    assert "host=db.local" in out.read_text()


def test_cmd_render_missing_placeholder_returns_1(capsys, tmp_path, env_file):
    tmpl = tmp_path / "t.tmpl"
    tmpl.write_text("x={{UNDEFINED_KEY}}")
    ns = _ns(template=str(tmpl), env_file=str(env_file))
    rc = cmd_template_render(ns)
    assert rc == 1


def test_cmd_render_allow_missing_returns_0(capsys, tmp_path, env_file):
    tmpl = tmp_path / "t.tmpl"
    tmpl.write_text("x={{UNDEFINED_KEY}}")
    ns = _ns(template=str(tmpl), env_file=str(env_file), allow_missing=True)
    rc = cmd_template_render(ns)
    assert rc == 0


def test_cmd_render_missing_template_returns_2(capsys, tmp_path, env_file):
    ns = _ns(template=str(tmp_path / "nope.tmpl"), env_file=str(env_file))
    rc = cmd_template_render(ns)
    assert rc == 2


def test_cmd_render_missing_env_file_returns_2(capsys, tmp_path, template_file):
    ns = _ns(template=str(template_file), env_file=str(tmp_path / "nope.env"))
    rc = cmd_template_render(ns)
    assert rc == 2


def test_cmd_list_placeholders(capsys, template_file):
    ns = _ns(template=str(template_file))
    rc = cmd_template_list(ns)
    assert rc == 0
    out = capsys.readouterr().out
    assert "HOST" in out
    assert "PORT" in out


def test_cmd_list_missing_template_returns_2(capsys, tmp_path):
    ns = _ns(template=str(tmp_path / "nope.tmpl"))
    rc = cmd_template_list(ns)
    assert rc == 2
