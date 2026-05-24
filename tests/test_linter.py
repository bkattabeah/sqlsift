"""Tests for sqlsift.linter."""
import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.linter import LintOptions, LintIssue, lint_schema


def _make_col(name: str, col_type: str = "INTEGER", nullable: bool = False,
              primary_key: bool = False) -> Column:
    col = Column(name=name, col_type=col_type, nullable=nullable)
    col.primary_key = primary_key
    return col


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


def test_no_issues_for_clean_schema():
    schema = _make_schema(
        _make_table("users", [
            _make_col("id", primary_key=True),
            _make_col("name", "VARCHAR", nullable=True),
        ])
    )
    issues = lint_schema(schema)
    assert issues == []


def test_missing_primary_key_raises_e003():
    schema = _make_schema(
        _make_table("orders", [_make_col("amount", "DECIMAL")])
    )
    issues = lint_schema(schema)
    codes = [i.code for i in issues]
    assert "E003" in codes


def test_no_primary_key_check_when_disabled():
    schema = _make_schema(
        _make_table("orders", [_make_col("amount", "DECIMAL")])
    )
    opts = LintOptions(require_primary_key=False)
    issues = lint_schema(schema, opts)
    codes = [i.code for i in issues]
    assert "E003" not in codes


def test_table_name_pattern_violation():
    schema = _make_schema(
        _make_table("MyTable", [_make_col("id", primary_key=True)])
    )
    opts = LintOptions(table_name_pattern=r'^[a-z_][a-z0-9_]*$')
    issues = lint_schema(schema, opts)
    codes = [i.code for i in issues]
    assert "E001" in codes


def test_column_name_pattern_violation():
    schema = _make_schema(
        _make_table("users", [
            _make_col("UserID", primary_key=True),
        ])
    )
    opts = LintOptions(column_name_pattern=r'^[a-z_][a-z0-9_]*$')
    issues = lint_schema(schema, opts)
    codes = [i.code for i in issues]
    assert "E004" in codes


def test_nullable_primary_key_raises_e005():
    schema = _make_schema(
        _make_table("users", [
            _make_col("id", primary_key=True, nullable=True),
        ])
    )
    issues = lint_schema(schema)
    codes = [i.code for i in issues]
    assert "E005" in codes


def test_too_many_columns_raises_e002():
    cols = [_make_col(f"col_{i}") for i in range(5)]
    cols[0].primary_key = True
    schema = _make_schema(_make_table("wide", cols))
    opts = LintOptions(max_columns_per_table=3)
    issues = lint_schema(schema, opts)
    codes = [i.code for i in issues]
    assert "E002" in codes


def test_empty_schema_returns_no_issues():
    schema = Schema()
    issues = lint_schema(schema)
    assert issues == []
