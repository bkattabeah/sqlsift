"""Tests for sqlsift.merger."""

import pytest

from sqlsift.schema import Schema, Table, Column
from sqlsift.merger import MergeOptions, merge_schemas


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, *cols: Column) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


def _make_schema(*tables: Table) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_merge_disjoint_tables():
    base = _make_schema(_make_table("users", _make_col("id", "INT")))
    overlay = _make_schema(_make_table("orders", _make_col("order_id", "INT")))
    result = merge_schemas(base, overlay)
    assert set(result.tables.keys()) == {"users", "orders"}


def test_merge_prefers_right_by_default():
    base_col = _make_col("email", "TEXT", nullable=True)
    overlay_col = _make_col("email", "VARCHAR(255)", nullable=False)
    base = _make_schema(_make_table("users", base_col))
    overlay = _make_schema(_make_table("users", overlay_col))
    result = merge_schemas(base, overlay)
    merged_col = result.tables["users"].columns["email"]
    assert merged_col.col_type == "VARCHAR(255)"
    assert merged_col.nullable is False


def test_merge_prefers_left():
    base_col = _make_col("email", "TEXT", nullable=True)
    overlay_col = _make_col("email", "VARCHAR(255)", nullable=False)
    base = _make_schema(_make_table("users", base_col))
    overlay = _make_schema(_make_table("users", overlay_col))
    opts = MergeOptions(prefer="left")
    result = merge_schemas(base, overlay, opts)
    merged_col = result.tables["users"].columns["email"]
    assert merged_col.col_type == "TEXT"


def test_merge_adds_new_columns():
    base = _make_schema(_make_table("users", _make_col("id", "INT")))
    overlay = _make_schema(_make_table("users", _make_col("id", "INT"), _make_col("name", "TEXT")))
    result = merge_schemas(base, overlay)
    assert "name" in result.tables["users"].columns


def test_merge_skips_new_columns_when_disabled():
    base = _make_schema(_make_table("users", _make_col("id", "INT")))
    overlay = _make_schema(_make_table("users", _make_col("id", "INT"), _make_col("name", "TEXT")))
    opts = MergeOptions(add_new_columns=False)
    result = merge_schemas(base, overlay, opts)
    assert "name" not in result.tables["users"].columns


def test_merge_skips_new_tables_when_disabled():
    base = _make_schema(_make_table("users", _make_col("id", "INT")))
    overlay = _make_schema(_make_table("orders", _make_col("order_id", "INT")))
    opts = MergeOptions(add_new_tables=False)
    result = merge_schemas(base, overlay, opts)
    assert "orders" not in result.tables
    assert "users" in result.tables


def test_merge_base_only_table_preserved():
    base = _make_schema(
        _make_table("users", _make_col("id", "INT")),
        _make_table("logs", _make_col("ts", "TIMESTAMP")),
    )
    overlay = _make_schema(_make_table("users", _make_col("id", "INT")))
    result = merge_schemas(base, overlay)
    assert "logs" in result.tables


def test_merge_empty_schemas():
    result = merge_schemas(Schema(), Schema())
    assert result.tables == {}
