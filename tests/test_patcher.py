"""Tests for sqlsift.patcher."""

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import SchemaDiff
from sqlsift.patcher import PatchOptions, generate_patch


def _make_col(name, data_type="TEXT", nullable=True, default=None):
    return Column(name=name, data_type=data_type, nullable=nullable, default=default)


def _make_table(name, cols):
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


def _make_schema(tables):
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def _simple_diff(**kwargs):
    base = dict(
        added_tables=[],
        removed_tables=[],
        modified_tables={},
    )
    base.update(kwargs)
    old = base.pop("old_schema", _make_schema([]))
    new = base.pop("new_schema", _make_schema([]))
    return SchemaDiff(old_schema=old, new_schema=new, **base)


def test_generate_patch_added_table():
    col = _make_col("id", "INTEGER", nullable=False)
    table = _make_table("users", [col])
    new_schema = _make_schema([table])
    diff = _simple_diff(added_tables=["users"], new_schema=new_schema)
    stmts = generate_patch(diff)
    assert len(stmts) == 1
    assert stmts[0].startswith('CREATE TABLE "users"')
    assert '"id" INTEGER NOT NULL' in stmts[0]


def test_generate_patch_removed_table():
    old_schema = _make_schema([_make_table("legacy", [_make_col("x")])])
    diff = _simple_diff(removed_tables=["legacy"], old_schema=old_schema)
    stmts = generate_patch(diff)
    assert any('DROP TABLE "legacy"' in s for s in stmts)


def test_generate_patch_removed_table_suppressed():
    old_schema = _make_schema([_make_table("legacy", [_make_col("x")])])
    diff = _simple_diff(removed_tables=["legacy"], old_schema=old_schema)
    opts = PatchOptions(include_drop_table=False)
    stmts = generate_patch(diff, opts)
    assert not any("DROP TABLE" in s for s in stmts)


def test_generate_patch_added_column():
    col = _make_col("email", "TEXT")
    table = _make_table("users", [col])
    new_schema = _make_schema([table])
    diff = _simple_diff(
        modified_tables={"users": {"added_columns": ["email"], "removed_columns": [], "modified_columns": {}}},
        new_schema=new_schema,
    )
    stmts = generate_patch(diff)
    assert any('ADD COLUMN "email" TEXT' in s for s in stmts)


def test_generate_patch_dropped_column():
    diff = _simple_diff(
        modified_tables={"users": {"added_columns": [], "removed_columns": ["old_col"], "modified_columns": {}}},
    )
    stmts = generate_patch(diff)
    assert any('DROP COLUMN "old_col"' in s for s in stmts)


def test_generate_patch_modified_column_type():
    col = _make_col("score", "FLOAT")
    table = _make_table("results", [col])
    new_schema = _make_schema([table])
    diff = _simple_diff(
        modified_tables={"results": {
            "added_columns": [],
            "removed_columns": [],
            "modified_columns": {"score": {"data_type": {"old": "INTEGER", "new": "FLOAT"}}},
        }},
        new_schema=new_schema,
    )
    stmts = generate_patch(diff)
    assert any('ALTER COLUMN "score" TYPE FLOAT' in s for s in stmts)


def test_empty_diff_returns_no_statements():
    diff = _simple_diff()
    assert generate_patch(diff) == []
