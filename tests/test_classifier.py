"""Tests for sqlsift.classifier."""

from __future__ import annotations

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.classifier import (
    ClassifierOptions,
    classify_schema,
    ColumnClassification,
    TableClassification,
)


def _make_col(
    name: str,
    col_type: str = "varchar(64)",
    nullable: bool = True,
    primary_key: bool = False,
) -> Column:
    col = Column(name=name, col_type=col_type, nullable=nullable, primary_key=primary_key)
    return col


def _make_table(name: str, *cols: Column) -> Table:
    t = Table(name=name)
    for col in cols:
        t.add_column(col)
    return t


def _make_schema(*tables: Table) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def test_classify_primary_key_column():
    schema = _make_schema(_make_table("users", _make_col("id", "int", False, True)))
    result = classify_schema(schema)
    cc = result["users"].column_classifications[0]
    assert cc.role == "primary_key"


def test_classify_foreign_key_column():
    schema = _make_schema(_make_table("orders", _make_col("user_id", "int")))
    result = classify_schema(schema)
    cc = result["orders"].column_classifications[0]
    assert cc.role == "foreign_key"


def test_classify_audit_column_suffix():
    schema = _make_schema(_make_table("events", _make_col("created_at", "timestamp")))
    result = classify_schema(schema)
    cc = result["events"].column_classifications[0]
    assert cc.role == "audit"


def test_classify_audit_column_prefix():
    schema = _make_schema(_make_table("events", _make_col("updated_by", "varchar(64)")))
    result = classify_schema(schema)
    cc = result["events"].column_classifications[0]
    assert cc.role == "audit"


def test_classify_flag_column():
    schema = _make_schema(_make_table("settings", _make_col("is_active", "boolean")))
    result = classify_schema(schema)
    cc = result["settings"].column_classifications[0]
    assert cc.role == "flag"


def test_classify_large_type_column():
    schema = _make_schema(_make_table("posts", _make_col("body", "text")))
    result = classify_schema(schema)
    cc = result["posts"].column_classifications[0]
    assert cc.role == "large"


def test_classify_large_varchar_above_threshold():
    schema = _make_schema(_make_table("docs", _make_col("content", "varchar(2048)")))
    opts = ClassifierOptions(large_varchar_threshold=1024)
    result = classify_schema(schema, opts)
    cc = result["docs"].column_classifications[0]
    assert cc.role == "large"


def test_classify_varchar_below_threshold_is_generic():
    schema = _make_schema(_make_table("items", _make_col("label", "varchar(64)")))
    opts = ClassifierOptions(large_varchar_threshold=1024)
    result = classify_schema(schema, opts)
    cc = result["items"].column_classifications[0]
    assert cc.role == "generic"


def test_table_category_audit_log():
    schema = _make_schema(_make_table("audit_log", _make_col("id", "int", False, True)))
    result = classify_schema(schema)
    assert result["audit_log"].category == "audit_log"


def test_table_category_entity_with_fk():
    schema = _make_schema(
        _make_table(
            "orders",
            _make_col("id", "int", False, True),
            _make_col("user_id", "int"),
            _make_col("total", "numeric"),
        )
    )
    result = classify_schema(schema)
    assert result["orders"].category == "entity"


def test_empty_schema_returns_empty_dict():
    schema = Schema()
    result = classify_schema(schema)
    assert result == {}


def test_returns_table_classification_instances():
    schema = _make_schema(_make_table("things", _make_col("name", "varchar(32)")))
    result = classify_schema(schema)
    assert isinstance(result["things"], TableClassification)
    assert isinstance(result["things"].column_classifications[0], ColumnClassification)
