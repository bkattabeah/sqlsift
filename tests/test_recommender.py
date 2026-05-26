"""Tests for sqlsift.recommender."""

from __future__ import annotations

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import SchemaDiff, _diff_table
from sqlsift.recommender import recommend, Recommendation, RecommendationReport


def _make_col(name: str, dtype: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, data_type=dtype, nullable=nullable)


def _make_table(name: str, cols: list) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


def _make_schema(tables: list) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def _empty_diff() -> SchemaDiff:
    return SchemaDiff()


def _diff_with_added_table() -> SchemaDiff:
    d = SchemaDiff()
    d.added_tables.append("orders")
    return d


def _diff_with_removed_table() -> SchemaDiff:
    d = SchemaDiff()
    d.removed_tables.append("legacy")
    return d


def _diff_with_column_changes() -> SchemaDiff:
    from sqlsift.diff import TableDiff

    d = SchemaDiff()
    td = TableDiff(table_name="users")
    td.added_columns.append(_make_col("email"))
    td.removed_columns.append(_make_col("phone"))
    old_col = _make_col("age", dtype="TEXT", nullable=True)
    new_col = _make_col("age", dtype="INTEGER", nullable=True)
    td.modified_columns.append((old_col, new_col))
    d.modified_tables["users"] = td
    return d


def _diff_with_nullability_change() -> SchemaDiff:
    from sqlsift.diff import TableDiff

    d = SchemaDiff()
    td = TableDiff(table_name="products")
    old_col = _make_col("sku", dtype="TEXT", nullable=True)
    new_col = _make_col("sku", dtype="TEXT", nullable=False)
    td.modified_columns.append((old_col, new_col))
    d.modified_tables["products"] = td
    return d


def test_empty_diff_returns_empty_report():
    report = recommend(_empty_diff())
    assert isinstance(report, RecommendationReport)
    assert len(report) == 0


def test_added_table_creates_recommendation():
    report = recommend(_diff_with_added_table())
    assert len(report) == 1
    rec = report.recommendations[0]
    assert rec.table == "orders"
    assert rec.category == "add_table"
    assert rec.priority == 2


def test_removed_table_is_high_priority():
    report = recommend(_diff_with_removed_table())
    assert len(report) == 1
    rec = report.recommendations[0]
    assert rec.category == "drop_table"
    assert rec.priority == 1
    assert len(report.high) == 1


def test_column_changes_produce_multiple_recommendations():
    report = recommend(_diff_with_column_changes())
    categories = {r.category for r in report.recommendations}
    assert "add_column" in categories
    assert "drop_column" in categories
    assert "type_change" in categories


def test_drop_column_is_high_priority():
    report = recommend(_diff_with_column_changes())
    drop_recs = [r for r in report.recommendations if r.category == "drop_column"]
    assert drop_recs
    assert all(r.priority == 1 for r in drop_recs)


def test_add_column_is_low_priority():
    report = recommend(_diff_with_column_changes())
    add_recs = [r for r in report.recommendations if r.category == "add_column"]
    assert add_recs
    assert all(r.priority == 3 for r in add_recs)


def test_nullability_change_is_medium_priority():
    report = recommend(_diff_with_nullability_change())
    null_recs = [r for r in report.recommendations if r.category == "nullability"]
    assert null_recs
    assert all(r.priority == 2 for r in null_recs)


def test_recommendations_sorted_by_priority():
    report = recommend(_diff_with_column_changes())
    priorities = [r.priority for r in report.recommendations]
    assert priorities == sorted(priorities)


def test_report_high_medium_low_partitions():
    report = recommend(_diff_with_column_changes())
    all_recs = report.high + report.medium + report.low
    assert len(all_recs) == len(report)
