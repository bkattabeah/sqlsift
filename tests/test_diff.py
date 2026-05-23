"""Tests for the schema diff engine."""

import pytest

from sqlsift.diff import compute_diff
from sqlsift.schema import Column, Schema, Table


def _make_schema(name: str, tables) -> Schema:
    schema = Schema(name=name)
    for table in tables:
        schema.add_table(table)
    return schema


def _make_table(name: str, columns) -> Table:
    table = Table(name=name)
    for col in columns:
        table.add_column(col)
    return table


def test_no_changes():
    col = Column(name="id", data_type="INTEGER", primary_key=True)
    old = _make_schema("db", [_make_table("users", [col])])
    new = _make_schema("db", [_make_table("users", [col])])
    diff = compute_diff(old, new)
    assert not diff.has_changes()


def test_added_table():
    old = _make_schema("db", [])
    new = _make_schema("db", [_make_table("orders", [])])
    diff = compute_diff(old, new)
    assert "orders" in diff.added_tables
    assert not diff.removed_tables


def test_removed_table():
    old = _make_schema("db", [_make_table("orders", [])])
    new = _make_schema("db", [])
    diff = compute_diff(old, new)
    assert "orders" in diff.removed_tables
    assert not diff.added_tables


def test_added_column():
    old_table = _make_table("users", [Column("id", "INTEGER")])
    new_table = _make_table("users", [Column("id", "INTEGER"), Column("email", "TEXT")])
    diff = compute_diff(
        _make_schema("db", [old_table]),
        _make_schema("db", [new_table]),
    )
    assert "users" in diff.modified_tables
    assert "email" in diff.modified_tables["users"]["added_columns"]


def test_removed_column():
    old_table = _make_table("users", [Column("id", "INTEGER"), Column("email", "TEXT")])
    new_table = _make_table("users", [Column("id", "INTEGER")])
    diff = compute_diff(
        _make_schema("db", [old_table]),
        _make_schema("db", [new_table]),
    )
    assert "email" in diff.modified_tables["users"]["removed_columns"]


def test_modified_column_type():
    old_table = _make_table("users", [Column("age", "INTEGER")])
    new_table = _make_table("users", [Column("age", "BIGINT")])
    diff = compute_diff(
        _make_schema("db", [old_table]),
        _make_schema("db", [new_table]),
    )
    modified = diff.modified_tables["users"]["modified_columns"]
    assert len(modified) == 1
    assert modified[0]["column"] == "age"
    assert modified[0]["before"].data_type == "INTEGER"
    assert modified[0]["after"].data_type == "BIGINT"
