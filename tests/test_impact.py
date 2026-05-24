"""Tests for sqlsift.impact — impact analysis from a SchemaDiff."""
from __future__ import annotations

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.impact import (
    ImpactOptions,
    ImpactReport,
    ImpactedObject,
    analyze_impact,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, cols: list) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


def _make_schema(*tables) -> "Schema":
    from sqlsift.schema import Schema
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_no_impact_when_no_changes():
    s = _make_schema(_make_table("users", [_make_col("id", "INT")]))
    diff = compute_diff(s, s)
    report = analyze_impact(diff)
    assert not report.has_impact
    assert report.items == []


def test_removed_table_creates_impact():
    old = _make_schema(_make_table("orders", [_make_col("id", "INT")]))
    new = _make_schema()
    diff = compute_diff(old, new)
    report = analyze_impact(diff)
    assert report.has_impact
    assert len(report.by_table("orders")) == 1
    item = report.by_table("orders")[0]
    assert item.kind == "application"
    assert "orders" in item.reason


def test_removed_table_suppressed_by_option():
    old = _make_schema(_make_table("orders", [_make_col("id", "INT")]))
    new = _make_schema()
    diff = compute_diff(old, new)
    opts = ImpactOptions(warn_removed_tables=False)
    report = analyze_impact(diff, opts)
    assert not report.has_impact


def test_removed_column_creates_impact():
    old = _make_schema(_make_table("users", [_make_col("id", "INT"), _make_col("email")]))
    new = _make_schema(_make_table("users", [_make_col("id", "INT")]))
    diff = compute_diff(old, new)
    report = analyze_impact(diff)
    assert report.has_impact
    items = report.by_table("users")
    assert any(i.column == "email" for i in items)


def test_removed_column_suppressed_by_option():
    old = _make_schema(_make_table("users", [_make_col("id", "INT"), _make_col("email")]))
    new = _make_schema(_make_table("users", [_make_col("id", "INT")]))
    diff = compute_diff(old, new)
    opts = ImpactOptions(warn_removed_columns=False)
    report = analyze_impact(diff, opts)
    assert not report.has_impact


def test_type_change_creates_impact():
    old = _make_schema(_make_table("users", [_make_col("age", "INT")]))
    new = _make_schema(_make_table("users", [_make_col("age", "TEXT")]))
    diff = compute_diff(old, new)
    report = analyze_impact(diff)
    assert report.has_impact
    item = report.items[0]
    assert item.column == "age"
    assert "type" in item.reason.lower()


def test_nullable_change_creates_impact():
    old = _make_schema(_make_table("users", [_make_col("name", "TEXT", nullable=True)]))
    new = _make_schema(_make_table("users", [_make_col("name", "TEXT", nullable=False)]))
    diff = compute_diff(old, new)
    report = analyze_impact(diff)
    assert report.has_impact
    item = report.items[0]
    assert item.column == "name"
    assert "nullab" in item.reason.lower()


def test_by_kind_filter():
    old = _make_schema(_make_table("orders", [_make_col("id", "INT")]))
    new = _make_schema()
    diff = compute_diff(old, new)
    opts = ImpactOptions(application_name="my_app")
    report = analyze_impact(diff, opts)
    assert report.by_kind("application")
    assert not report.by_kind("view")


def test_custom_application_name_appears_in_item():
    old = _make_schema(_make_table("logs", [_make_col("id", "INT")]))
    new = _make_schema()
    diff = compute_diff(old, new)
    opts = ImpactOptions(application_name="billing_service")
    report = analyze_impact(diff, opts)
    assert report.items[0].name == "billing_service"
