"""Tests for sqlsift.reporter module."""

import pytest
from sqlsift.schema import Column, Table
from sqlsift.diff import compute_diff
from sqlsift.reporter import generate_report, ReportOptions


def _make_table(name: str, columns: list) -> Table:
    t = Table(name=name)
    for col_name, col_type in columns:
        t.add_column(Column(name=col_name, data_type=col_type))
    return t


def _make_schema(*tables: Table) -> dict:
    return {t.name: t for t in tables}


def test_report_no_changes():
    schema = _make_schema(_make_table("users", [("id", "INTEGER")]))
    diff = compute_diff(schema, schema)
    report = generate_report(diff, ReportOptions(use_color=False))
    assert "No schema changes detected" in report


def test_report_added_table():
    old = _make_schema()
    new = _make_schema(_make_table("orders", [("id", "INTEGER")]))
    diff = compute_diff(old, new)
    report = generate_report(diff, ReportOptions(use_color=False))
    assert "Added tables" in report
    assert "+ orders" in report


def test_report_removed_table():
    old = _make_schema(_make_table("orders", [("id", "INTEGER")]))
    new = _make_schema()
    diff = compute_diff(old, new)
    report = generate_report(diff, ReportOptions(use_color=False))
    assert "Removed tables" in report
    assert "- orders" in report


def test_report_modified_table_added_column():
    old = _make_schema(_make_table("users", [("id", "INTEGER")]))
    new = _make_schema(_make_table("users", [("id", "INTEGER"), ("email", "TEXT")]))
    diff = compute_diff(old, new)
    report = generate_report(diff, ReportOptions(use_color=False))
    assert "Modified tables" in report
    assert "users" in report
    assert "+ column: email" in report


def test_report_modified_table_removed_column():
    old = _make_schema(_make_table("users", [("id", "INTEGER"), ("email", "TEXT")]))
    new = _make_schema(_make_table("users", [("id", "INTEGER")]))
    diff = compute_diff(old, new)
    report = generate_report(diff, ReportOptions(use_color=False))
    assert "- column: email" in report


def test_report_modified_column_type():
    old = _make_schema(_make_table("users", [("id", "INTEGER")]))
    new = _make_schema(_make_table("users", [("id", "BIGINT")]))
    diff = compute_diff(old, new)
    report = generate_report(diff, ReportOptions(use_color=False))
    assert "~ column: id" in report
    assert "INTEGER -> BIGINT" in report


def test_report_uses_color_by_default():
    old = _make_schema()
    new = _make_schema(_make_table("logs", [("id", "INTEGER")]))
    diff = compute_diff(old, new)
    report = generate_report(diff)
    assert "\033[" in report
