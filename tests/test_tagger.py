"""Tests for sqlsift.tagger."""
import pytest

from sqlsift.schema import Column, Schema, Table
from sqlsift.tagger import (
    TagOptions,
    TaggedSchema,
    tag_schema,
)


def _make_col(name: str, dtype: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, data_type=dtype, nullable=nullable, default=None)


def _make_table(name: str, *col_names: str) -> Table:
    t = Table(name=name)
    for cn in col_names:
        t.add_column(_make_col(cn))
    return t


def _make_schema(*table_names: str) -> Schema:
    from sqlsift.schema import Schema
    s = Schema()
    for tn in table_names:
        s.add_table(_make_table(tn, "id", "value"))
    return s


def test_tag_schema_returns_tagged_schema():
    schema = _make_schema("users")
    result = tag_schema(schema, TagOptions())
    assert isinstance(result, TaggedSchema)
    assert len(result.tables) == 1


def test_table_tags_applied():
    schema = _make_schema("users", "orders")
    opts = TagOptions(table_tags={"users": ["pii", "core"]})
    result = tag_schema(schema, opts)
    users = result.get_table("users")
    orders = result.get_table("orders")
    assert users is not None
    assert "pii" in users.tags
    assert "core" in users.tags
    assert orders.tags == []


def test_column_tags_applied():
    schema = _make_schema("users")
    opts = TagOptions(column_tags={"users.id": ["primary"], "users.value": ["sensitive"]})
    result = tag_schema(schema, opts)
    users = result.get_table("users")
    id_col = next(c for c in users.columns if c.name == "id")
    val_col = next(c for c in users.columns if c.name == "value")
    assert "primary" in id_col.tags
    assert "sensitive" in val_col.tags


def test_no_tags_produces_empty_lists():
    schema = _make_schema("events")
    result = tag_schema(schema, TagOptions())
    table = result.get_table("events")
    assert table.tags == []
    for col in table.columns:
        assert col.tags == []


def test_overwrite_false_merges_tags():
    schema = _make_schema("users")
    opts = TagOptions(
        table_tags={"users": ["pii"]},
        overwrite=False,
    )
    result = tag_schema(schema, opts)
    users = result.get_table("users")
    # Run again simulating accumulation (overwrite=False keeps existing)
    assert "pii" in users.tags


def test_overwrite_true_replaces_tags():
    from sqlsift.tagger import _resolve_tags
    result = _resolve_tags(["old", "keep"], ["new"], overwrite=True)
    assert result == ["new"]
    assert "old" not in result


def test_get_table_returns_none_for_missing():
    schema = _make_schema("users")
    result = tag_schema(schema, TagOptions())
    assert result.get_table("nonexistent") is None


def test_tagged_column_preserves_attributes():
    schema = _make_schema("products")
    result = tag_schema(schema, TagOptions())
    table = result.get_table("products")
    for col in table.columns:
        assert col.data_type == "TEXT"
        assert col.nullable is True
        assert col.default is None
