"""Tests for sqlsift.renamer."""
from __future__ import annotations

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.renamer import RenameOptions, RenameHint, detect_renames


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, cols: list[Column]) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


def _make_schema(tables: list[Table]) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


# ---------------------------------------------------------------------------
# column rename tests
# ---------------------------------------------------------------------------

def test_no_hints_when_schemas_identical():
    col = _make_col("id", "INT", False)
    t = _make_table("users", [col])
    schema = _make_schema([t])
    hints = detect_renames(schema, schema)
    assert hints == []


def test_column_rename_detected():
    old_col = _make_col("username", "VARCHAR", False)
    new_col = _make_col("user_name", "VARCHAR", False)  # same type/nullable
    old_schema = _make_schema([_make_table("users", [old_col])])
    new_schema = _make_schema([_make_table("users", [new_col])])

    hints = detect_renames(old_schema, new_schema)
    col_hints = [h for h in hints if h.kind == "column"]
    assert len(col_hints) == 1
    h = col_hints[0]
    assert h.old_name == "username"
    assert h.new_name == "user_name"
    assert h.table_name == "users"
    assert 0.0 < h.score <= 1.0


def test_column_rename_below_threshold_not_returned():
    # Completely different type and nullability → low score
    old_col = _make_col("age", "INT", False)
    new_col = _make_col("bio", "TEXT", True)
    old_schema = _make_schema([_make_table("users", [old_col])])
    new_schema = _make_schema([_make_table("users", [new_col])])

    opts = RenameOptions(column_similarity_threshold=0.99)
    hints = detect_renames(old_schema, new_schema, options=opts)
    col_hints = [h for h in hints if h.kind == "column"]
    assert col_hints == []


# ---------------------------------------------------------------------------
# table rename tests
# ---------------------------------------------------------------------------

def test_table_rename_detected():
    cols = [_make_col("id", "INT", False), _make_col("email", "TEXT", True)]
    old_schema = _make_schema([_make_table("customers", cols)])
    new_schema = _make_schema([_make_table("clients", cols)])

    hints = detect_renames(old_schema, new_schema)
    table_hints = [h for h in hints if h.kind == "table"]
    assert len(table_hints) == 1
    h = table_hints[0]
    assert h.old_name == "customers"
    assert h.new_name == "clients"


def test_no_table_rename_when_columns_differ_too_much():
    old_cols = [_make_col("id", "INT"), _make_col("x", "INT")]
    new_cols = [_make_col("ref", "TEXT"), _make_col("y", "TEXT")]
    old_schema = _make_schema([_make_table("alpha", old_cols)])
    new_schema = _make_schema([_make_table("beta", new_cols)])

    opts = RenameOptions(table_similarity_threshold=0.99)
    hints = detect_renames(old_schema, new_schema, options=opts)
    table_hints = [h for h in hints if h.kind == "table"]
    assert table_hints == []


def test_rename_hint_repr():
    h = RenameHint(kind="column", table_name="users",
                   old_name="nm", new_name="name", score=0.9)
    r = repr(h)
    assert "column" in r
    assert "nm" in r
    assert "name" in r


def test_detect_renames_default_options():
    """detect_renames works when options=None (uses defaults)."""
    old_col = _make_col("val", "INT", False)
    new_col = _make_col("value", "INT", False)
    old_schema = _make_schema([_make_table("metrics", [old_col])])
    new_schema = _make_schema([_make_table("metrics", [new_col])])
    # Should not raise
    hints = detect_renames(old_schema, new_schema)
    assert isinstance(hints, list)
