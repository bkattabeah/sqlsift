"""Tests for sqlsift.filter module."""

import pytest

from sqlsift.schema import Column, Table
from sqlsift.diff import SchemaDiff
from sqlsift.filter import FilterOptions, filter_diff


def _make_col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _make_table(name: str, *col_names: str) -> Table:
    t = Table(name=name)
    for cn in col_names:
        t.add_column(_make_col(cn))
    return t


def _simple_diff() -> SchemaDiff:
    return SchemaDiff(
        added_tables={"orders": _make_table("orders", "id")},
        removed_tables={"legacy": _make_table("legacy", "id")},
        added_columns={"users": [_make_col("email")], "products": [_make_col("sku")]},
        removed_columns={"users": [_make_col("phone")]},
        modified_columns={"products": [("price", _make_col("price", "INTEGER"), _make_col("price", "NUMERIC"))]},
    )


def test_filter_no_options_returns_full_diff():
    diff = _simple_diff()
    result = filter_diff(diff, FilterOptions())
    assert result.added_tables == diff.added_tables
    assert result.removed_tables == diff.removed_tables
    assert result.added_columns == diff.added_columns
    assert result.removed_columns == diff.removed_columns
    assert result.modified_columns == diff.modified_columns


def test_filter_include_tables():
    diff = _simple_diff()
    result = filter_diff(diff, FilterOptions(include_tables=["users"]))
    assert "users" in result.added_columns
    assert "products" not in result.added_columns
    assert result.added_tables == {}
    assert result.removed_tables == {}


def test_filter_exclude_tables():
    diff = _simple_diff()
    result = filter_diff(diff, FilterOptions(exclude_tables=["users"]))
    assert "users" not in result.added_columns
    assert "users" not in result.removed_columns
    assert "products" in result.added_columns


def test_filter_change_types_added_tables_only():
    diff = _simple_diff()
    result = filter_diff(diff, FilterOptions(change_types=["added_tables"]))
    assert result.added_tables == diff.added_tables
    assert result.removed_tables == {}
    assert result.added_columns == {}
    assert result.removed_columns == {}
    assert result.modified_columns == {}


def test_filter_change_types_columns_only():
    diff = _simple_diff()
    result = filter_diff(diff, FilterOptions(change_types=["added_columns", "removed_columns"]))
    assert result.added_tables == {}
    assert result.removed_tables == {}
    assert result.added_columns == diff.added_columns
    assert result.removed_columns == diff.removed_columns
    assert result.modified_columns == {}


def test_filter_include_and_change_type_combined():
    diff = _simple_diff()
    result = filter_diff(
        diff,
        FilterOptions(include_tables=["products"], change_types=["added_columns", "modified_columns"]),
    )
    assert list(result.added_columns.keys()) == ["products"]
    assert list(result.modified_columns.keys()) == ["products"]
    assert result.removed_columns == {}


def test_filter_exclude_all_tables_gives_empty_diff():
    diff = _simple_diff()
    all_tables = ["orders", "legacy", "users", "products"]
    result = filter_diff(diff, FilterOptions(exclude_tables=all_tables))
    assert not result.added_tables
    assert not result.removed_tables
    assert not result.added_columns
    assert not result.removed_columns
    assert not result.modified_columns
