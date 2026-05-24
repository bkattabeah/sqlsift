"""Tests for sqlsift.comparator."""

import pytest

from sqlsift.schema import Column, Table
from sqlsift.comparator import (
    ColumnSimilarity,
    TableSimilarity,
    _column_score,
    compare_columns,
    compare_tables,
)


def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, cols: list) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


# --- _column_score ---

def test_identical_columns_score_one():
    col = _make_col("id", "INT", False)
    result = _column_score(col, col)
    assert result.score == 1.0
    assert result.matched_type is True
    assert result.matched_nullable is True


def test_different_type_lowers_score():
    a = _make_col("id", "INT", True)
    b = _make_col("id", "TEXT", True)
    result = _column_score(a, b)
    assert result.matched_type is False
    assert result.score < 1.0


def test_different_nullable_lowers_score():
    a = _make_col("id", "INT", True)
    b = _make_col("id", "INT", False)
    result = _column_score(a, b)
    assert result.matched_nullable is False
    assert result.score < 1.0


def test_column_score_type_case_insensitive():
    a = _make_col("x", "varchar", True)
    b = _make_col("x", "VARCHAR", True)
    result = _column_score(a, b)
    assert result.matched_type is True


# --- compare_columns ---

def test_compare_columns_returns_only_common():
    cols_a = {"id": _make_col("id"), "name": _make_col("name")}
    cols_b = {"id": _make_col("id"), "email": _make_col("email")}
    results = compare_columns(cols_a, cols_b)
    assert len(results) == 1
    assert results[0].name_a == "id"


def test_compare_columns_empty_intersection():
    cols_a = {"a": _make_col("a")}
    cols_b = {"b": _make_col("b")}
    assert compare_columns(cols_a, cols_b) == []


# --- compare_tables ---

def test_identical_tables_score_one():
    cols = [_make_col("id", "INT", False), _make_col("val", "TEXT", True)]
    a = _make_table("users", cols)
    b = _make_table("users", cols)
    result = compare_tables(a, b)
    assert result.overall_score == 1.0
    assert len(result.column_pairs) == 2


def test_empty_tables_score_one():
    a = _make_table("empty", [])
    b = _make_table("empty", [])
    result = compare_tables(a, b)
    assert result.overall_score == 1.0


def test_no_common_columns_score_zero():
    a = _make_table("t", [_make_col("x")])
    b = _make_table("t", [_make_col("y")])
    result = compare_tables(a, b)
    assert result.overall_score == 0.0


def test_partial_overlap_score_between_zero_and_one():
    a = _make_table("t", [_make_col("id"), _make_col("name")])
    b = _make_table("t", [_make_col("id"), _make_col("email")])
    result = compare_tables(a, b)
    assert 0.0 < result.overall_score < 1.0
