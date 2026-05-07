"""Tests for envoy_local.split."""
from pathlib import Path

import pytest

from envoy_local.split import split_env_file


@pytest.fixture()
def base_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(p: Path, text: str) -> Path:
    p.write_text(text, encoding="utf-8")
    return p


def test_split_missing_source_returns_error(base_dir: Path) -> None:
    result = split_env_file(
        base_dir / "missing.env",
        base_dir / "out",
        prefixes=["APP_"],
    )
    assert not result.ok
    assert "not found" in result.error


def test_split_creates_output_files(base_dir: Path) -> None:
    src = _write(
        base_dir / ".env",
        "APP_HOST=localhost\nDB_HOST=db\nAPP_PORT=8080\n",
    )
    result = split_env_file(src, base_dir / "out", prefixes=["APP_", "DB_"])
    assert result.ok
    assert len(result.files_written) == 2


def test_split_correct_keys_in_each_file(base_dir: Path) -> None:
    src = _write(
        base_dir / ".env",
        "APP_HOST=localhost\nDB_HOST=db\nAPP_PORT=8080\n",
    )
    out = base_dir / "out"
    split_env_file(src, out, prefixes=["APP_", "DB_"])
    app_text = (out / "app.env").read_text()
    assert "APP_HOST" in app_text
    assert "APP_PORT" in app_text
    assert "DB_HOST" not in app_text


def test_split_ungrouped_counted(base_dir: Path) -> None:
    src = _write(
        base_dir / ".env",
        "APP_HOST=localhost\nUNKNOWN=value\n",
    )
    result = split_env_file(src, base_dir / "out", prefixes=["APP_"])
    assert result.ok
    assert result.ungrouped_count == 1


def test_split_strip_prefix_removes_prefix(base_dir: Path) -> None:
    src = _write(base_dir / ".env", "APP_HOST=localhost\nAPP_PORT=8080\n")
    out = base_dir / "out"
    split_env_file(src, out, prefixes=["APP_"], strip_prefix=True)
    text = (out / "app.env").read_text()
    assert "HOST" in text
    assert "PORT" in text
    assert "APP_" not in text


def test_split_no_overwrite_returns_error_on_existing(base_dir: Path) -> None:
    src = _write(base_dir / ".env", "APP_KEY=val\n")
    out = base_dir / "out"
    out.mkdir()
    (out / "app.env").write_text("existing", encoding="utf-8")
    result = split_env_file(src, out, prefixes=["APP_"], overwrite=False)
    assert not result.ok
    assert "overwrite" in result.error


def test_split_overwrite_replaces_existing(base_dir: Path) -> None:
    src = _write(base_dir / ".env", "APP_KEY=newval\n")
    out = base_dir / "out"
    out.mkdir()
    (out / "app.env").write_text("APP_KEY=old\n", encoding="utf-8")
    result = split_env_file(src, out, prefixes=["APP_"], overwrite=True)
    assert result.ok
    assert "newval" in (out / "app.env").read_text()


def test_split_empty_prefix_group_not_written(base_dir: Path) -> None:
    src = _write(base_dir / ".env", "APP_KEY=val\n")
    out = base_dir / "out"
    result = split_env_file(src, out, prefixes=["APP_", "DB_"])
    assert result.ok
    assert len(result.files_written) == 1
    assert not (out / "db.env").exists()


def test_split_summary_contains_file_count(base_dir: Path) -> None:
    src = _write(base_dir / ".env", "APP_KEY=val\n")
    result = split_env_file(src, base_dir / "out", prefixes=["APP_"])
    assert "1 file" in result.summary()
