"""Tests for sqlsift.normalizer."""

import pytest

from sqlsift.schema import Column, Schema, Table
from sqlsift.normalizer import NormalizeOptions, normalize_schema


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str, nullable: bool = True, pk: bool = False) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable, primary_key=pk)


def _make_table(name: str, cols) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


def _make_schema(*tables) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


# ---------------------------------------------------------------------------
# Type alias normalisation
# ---------------------------------------------------------------------------

def test_integer_alias_becomes_int():
    schema = _make_schema(_make_table("users", [_make_col("id", "integer")]))
    result = normalize_schema(schema)
    assert result.tables["users"].columns["id"].col_type == "INT"


def test_bool_alias_becomes_boolean():
    schema = _make_schema(_make_table("flags", [_make_col("active", "bool")]))
    result = normalize_schema(schema)
    assert result.tables["flags"].columns["active"].col_type == "BOOLEAN"


def test_character_varying_becomes_varchar():
    schema = _make_schema(_make_table("t", [_make_col("name", "character varying")]))
    result = normalize_schema(schema)
    assert result.tables["t"].columns["name"].col_type == "VARCHAR"


def test_unknown_type_is_uppercased():
    schema = _make_schema(_make_table("t", [_make_col("data", "jsonb")]))
    result = normalize_schema(schema)
    assert result.tables["t"].columns["data"].col_type == "JSONB"


# ---------------------------------------------------------------------------
# Name normalisation
# ---------------------------------------------------------------------------

def test_column_names_lowercased_by_default():
    schema = _make_schema(_make_table("Orders", [_make_col("OrderID", "INT")]))
    result = normalize_schema(schema)
    assert "orders" in result.tables
    assert "orderid" in result.tables["orders"].columns


def test_table_names_lowercased_by_default():
    schema = _make_schema(_make_table("Products", [_make_col("id", "INT")]))
    result = normalize_schema(schema)
    assert "products" in result.tables
    assert "Products" not in result.tables


def test_lowercase_disabled_preserves_case():
    opts = NormalizeOptions(lowercase_names=False, lowercase_tables=False)
    schema = _make_schema(_make_table("Orders", [_make_col("OrderID", "integer")]))
    result = normalize_schema(schema, options=opts)
    assert "Orders" in result.tables
    assert "OrderID" in result.tables["Orders"].columns


# ---------------------------------------------------------------------------
# Custom aliases
# ---------------------------------------------------------------------------

def test_custom_type_alias():
    opts = NormalizeOptions(type_aliases={"mytype": "CUSTOM"})
    schema = _make_schema(_make_table("t", [_make_col("x", "mytype")]))
    result = normalize_schema(schema, options=opts)
    assert result.tables["t"].columns["x"].col_type == "CUSTOM"


# ---------------------------------------------------------------------------
# Attribute preservation
# ---------------------------------------------------------------------------

def test_nullable_preserved_after_normalization():
    schema = _make_schema(_make_table("t", [_make_col("x", "integer", nullable=False)]))
    result = normalize_schema(schema)
    assert result.tables["t"].columns["x"].nullable is False


def test_primary_key_preserved_after_normalization():
    schema = _make_schema(_make_table("t", [_make_col("id", "int4", pk=True)]))
    result = normalize_schema(schema)
    assert result.tables["t"].columns["id"].primary_key is True
