"""Tests for sqlsift.exporter module."""

from __future__ import annotations

import csv
import io
import json

import pytest

from sqlsift.diff import SchemaDiff, _diff_table
from sqlsift.exporter import ExportOptions, export_diff
from sqlsift.schema import Column, Schema, Table


def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, columns: list[Column]) -> Table:
    t = Table(name=name)
    for col in columns:
        t.add_column(col)
    return t


def _make_schema(tables: list[Table]) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def _simple_diff() -> SchemaDiff:
    old = _make_schema([
        _make_table("users", [_make_col("id", "INT"), _make_col("email", "TEXT")]),
        _make_table("orders", [_make_col("id", "INT")]),
    ])
    new = _make_schema([
        _make_table("users", [_make_col("id", "INT"), _make_col("name", "TEXT")]),
        _make_table("products", [_make_col("id", "INT")]),
    ])
    from sqlsift.diff import compute_diff
    return compute_diff(old, new)


def test_export_json_structure():
    diff = _simple_diff()
    result = export_diff(diff, ExportOptions(format="json"))
    records = json.loads(result)
    assert isinstance(records, list)
    for record in records:
        assert "change" in record
        assert "table" in record
        assert "column" in record
        assert "detail" in record


def test_export_json_contains_expected_changes():
    diff = _simple_diff()
    result = export_diff(diff, ExportOptions(format="json"))
    records = json.loads(result)
    changes = {(r["change"], r["table"]) for r in records}
    assert ("added_table", "products") in changes
    assert ("removed_table", "orders") in changes


def test_export_markdown_headers():
    diff = _simple_diff()
    result = export_diff(diff, ExportOptions(format="markdown"))
    assert "| Change |" in result
    assert "| Table |" in result


def test_export_markdown_rows():
    diff = _simple_diff()
    result = export_diff(diff, ExportOptions(format="markdown"))
    assert "added_table" in result or "removed_table" in result


def test_export_csv_parseable():
    diff = _simple_diff()
    result = export_diff(diff, ExportOptions(format="csv"))
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) > 0
    assert "change" in rows[0]


def test_export_no_changes_json():
    schema = _make_schema([_make_table("users", [_make_col("id", "INT")])])
    from sqlsift.diff import compute_diff
    diff = compute_diff(schema, schema)
    result = export_diff(diff)
    assert json.loads(result) == []


def test_export_no_changes_markdown():
    schema = _make_schema([_make_table("users", [_make_col("id", "INT")])])
    from sqlsift.diff import compute_diff
    diff = compute_diff(schema, schema)
    result = export_diff(diff, ExportOptions(format="markdown"))
    assert "No changes detected" in result


def test_export_invalid_format():
    schema = _make_schema([])
    from sqlsift.diff import compute_diff
    diff = compute_diff(schema, schema)
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_diff(diff, ExportOptions(format="xml"))  # type: ignore[arg-type]
