"""Tests for sqlsift.validator."""
import pytest
from sqlsift.schema import Schema, Table, Column
from sqlsift.validator import (
    validate_schema,
    ValidationResult,
    ValidationIssue,
)


def _make_col(name: str, dtype: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, data_type=dtype, nullable=nullable, default=None)


def _make_table(name: str, cols=None) -> Table:
    t = Table(name=name)
    for c in (cols or []):
        t.add_column(c)
    return t


def _make_schema(tables=None) -> Schema:
    s = Schema()
    for t in (tables or []):
        s.add_table(t)
    return s


def test_valid_schema_returns_no_issues():
    schema = _make_schema([
        _make_table("users", [_make_col("id", "INT"), _make_col("email", "TEXT")])
    ])
    result = validate_schema(schema)
    assert result.is_valid
    assert result.issues == []


def test_empty_schema_warns():
    result = validate_schema(_make_schema([]))
    assert len(result.warnings) == 1
    assert "no tables" in result.warnings[0].message


def test_table_with_no_columns_warns():
    schema = _make_schema([_make_table("empty_table", [])])
    result = validate_schema(schema)
    warnings = [i for i in result.warnings if i.table == "empty_table"]
    assert any("no columns" in w.message for w in warnings)


def test_column_missing_data_type_warns():
    col = Column(name="mystery", data_type="", nullable=True, default=None)
    schema = _make_schema([_make_table("t", [col])])
    result = validate_schema(schema)
    assert any("no data type" in i.message for i in result.warnings)


def test_column_empty_name_errors():
    col = Column(name="", data_type="INT", nullable=False, default=None)
    schema = _make_schema([_make_table("t", [col])])
    result = validate_schema(schema)
    assert not result.is_valid
    assert any("empty name" in e.message for e in result.errors)


def test_is_valid_false_when_errors_present():
    col = Column(name="", data_type="INT", nullable=False, default=None)
    schema = _make_schema([_make_table("t", [col])])
    result = validate_schema(schema)
    assert result.is_valid is False


def test_validation_issue_repr():
    issue = ValidationIssue(table="users", column="id", message="bad", severity="error")
    assert "[ERROR]" in repr(issue)
    assert "users.id" in repr(issue)


def test_validation_issue_repr_no_column():
    issue = ValidationIssue(table="users", column=None, message="bad", severity="warning")
    assert "[WARNING]" in repr(issue)
    assert "users" in repr(issue)
    assert "." not in repr(issue).split("]")[1].split(":")[0]
