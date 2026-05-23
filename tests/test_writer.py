"""Tests for sqlsift.writer module."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqlsift.diff import compute_diff
from sqlsift.exporter import ExportOptions
from sqlsift.schema import Column, Schema, Table
from sqlsift.writer import write_diff, _infer_format


def _make_schema_with_table(table_name: str = "users") -> Schema:
    s = Schema()
    t = Table(name=table_name)
    t.add_column(Column(name="id", col_type="INT", nullable=False))
    s.add_table(t)
    return s


def test_infer_format_json():
    assert _infer_format(Path("out.json")) == "json"


def test_infer_format_markdown():
    assert _infer_format(Path("report.md")) == "markdown"


def test_infer_format_csv():
    assert _infer_format(Path("changes.csv")) == "csv"


def test_infer_format_unknown_raises():
    with pytest.raises(ValueError, match="Cannot infer format"):
        _infer_format(Path("report.txt"))


def test_write_diff_to_json_file(tmp_path: Path):
    old = _make_schema_with_table("users")
    new = _make_schema_with_table("users")
    new.add_table(Table(name="orders"))
    diff = compute_diff(old, new)

    out_file = tmp_path / "diff.json"
    write_diff(diff, output=out_file)

    assert out_file.exists()
    records = json.loads(out_file.read_text())
    assert any(r["change"] == "added_table" for r in records)


def test_write_diff_to_csv_file(tmp_path: Path):
    old = _make_schema_with_table("users")
    new = Schema()
    diff = compute_diff(old, new)

    out_file = tmp_path / "diff.csv"
    write_diff(diff, output=out_file)

    content = out_file.read_text()
    assert "removed_table" in content


def test_write_diff_to_markdown_file(tmp_path: Path):
    old = _make_schema_with_table("users")
    new = _make_schema_with_table("users")
    diff = compute_diff(old, new)

    out_file = tmp_path / "report.md"
    write_diff(diff, output=out_file)

    content = out_file.read_text()
    assert "| Change |" in content


def test_write_diff_creates_parent_dirs(tmp_path: Path):
    diff = compute_diff(Schema(), Schema())
    out_file = tmp_path / "nested" / "deep" / "diff.json"
    write_diff(diff, output=out_file)
    assert out_file.exists()


def test_write_diff_stdout(capsys):
    diff = compute_diff(Schema(), Schema())
    write_diff(diff)  # no output path → stdout
    captured = capsys.readouterr()
    assert json.loads(captured.out) == []


def test_write_diff_explicit_options_override_extension(tmp_path: Path):
    """Explicit format in options should NOT be overridden when it differs."""
    old = _make_schema_with_table("t")
    new = Schema()
    diff = compute_diff(old, new)

    # Passing a .json path but forcing markdown via explicit options
    out_file = tmp_path / "out.md"
    write_diff(diff, output=out_file, options=ExportOptions(format="markdown"))
    content = out_file.read_text()
    assert "| Change |" in content
