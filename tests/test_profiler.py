"""Tests for sqlsift.profiler."""

from __future__ import annotations

import pytest

from sqlsift.schema import Column, Schema, Table
from sqlsift.profiler import (
    profile_schema,
    SchemaProfile,
    TableProfile,
    ColumnProfile,
)


def _make_col(
    name: str,
    data_type: str = "TEXT",
    nullable: bool = True,
    default=None,
) -> Column:
    col = Column(name=name, data_type=data_type, nullable=nullable)
    col.default = default
    return col


def _make_table(name: str, columns: list) -> Table:
    t = Table(name=name)
    for col in columns:
        t.add_column(col)
    return t


def _make_schema(*tables) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def test_empty_schema_returns_zero_counts():
    result = profile_schema(_make_schema())
    assert isinstance(result, SchemaProfile)
    assert result.table_count == 0
    assert result.total_columns == 0
    assert result.average_columns_per_table == 0.0


def test_table_count_matches_schema():
    schema = _make_schema(
        _make_table("users", [_make_col("id")]),
        _make_table("orders", [_make_col("id")]),
    )
    result = profile_schema(schema)
    assert result.table_count == 2


def test_total_columns_summed_across_tables():
    schema = _make_schema(
        _make_table("users", [_make_col("id"), _make_col("name")]),
        _make_table("orders", [_make_col("order_id")]),
    )
    result = profile_schema(schema)
    assert result.total_columns == 3


def test_average_columns_per_table():
    schema = _make_schema(
        _make_table("a", [_make_col("x"), _make_col("y")]),
        _make_table("b", [_make_col("z")]),
    )
    result = profile_schema(schema)
    assert result.average_columns_per_table == pytest.approx(1.5)


def test_nullable_count():
    schema = _make_schema(
        _make_table(
            "users",
            [
                _make_col("id", nullable=False),
                _make_col("email", nullable=True),
                _make_col("phone", nullable=True),
            ],
        )
    )
    tp: TableProfile = profile_schema(schema).table_profiles["users"]
    assert tp.nullable_count == 2
    assert tp.non_nullable_count == 1
    assert tp.nullable_ratio == pytest.approx(2 / 3)


def test_columns_with_defaults():
    schema = _make_schema(
        _make_table(
            "items",
            [
                _make_col("id", nullable=False, default=None),
                _make_col("status", nullable=True, default="active"),
            ],
        )
    )
    tp: TableProfile = profile_schema(schema).table_profiles["items"]
    assert tp.columns_with_defaults == 1


def test_column_profile_fields():
    schema = _make_schema(
        _make_table("t", [_make_col("col1", data_type="INT", nullable=False, default=0)])
    )
    tp = profile_schema(schema).table_profiles["t"]
    cp: ColumnProfile = tp.column_profiles[0]
    assert cp.name == "col1"
    assert cp.data_type == "INT"
    assert cp.nullable is False
    assert cp.has_default is True


def test_table_profile_stored_by_name():
    schema = _make_schema(
        _make_table("alpha", [_make_col("a")]),
        _make_table("beta", [_make_col("b")]),
    )
    result = profile_schema(schema)
    assert "alpha" in result.table_profiles
    assert "beta" in result.table_profiles
