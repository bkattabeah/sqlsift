"""Tests for sqlsift.annotator."""
import pytest
from sqlsift.schema import Schema, Table, Column
from sqlsift.annotator import (
    AnnotationOptions,
    Annotation,
    annotate_schema,
    _large_type,
)


def _make_col(
    name: str,
    data_type: str = "INTEGER",
    nullable: bool = False,
    primary_key: bool = False,
) -> Column:
    return Column(name=name, data_type=data_type, nullable=nullable, primary_key=primary_key)


def _make_schema(*tables: Table) -> Schema:
    return Schema(tables={t.name: t for t in tables})


def _make_table(name: str, *cols: Column) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


# ---------------------------------------------------------------------------
# _large_type helper
# ---------------------------------------------------------------------------

def test_large_type_text_is_large():
    col = _make_col("body", data_type="TEXT")
    assert _large_type(col, threshold=255) is True


def test_large_type_varchar_below_threshold():
    col = _make_col("name", data_type="VARCHAR(100)")
    assert _large_type(col, threshold=255) is False


def test_large_type_varchar_above_threshold():
    col = _make_col("bio", data_type="VARCHAR(1000)")
    assert _large_type(col, threshold=255) is True


def test_large_type_integer_is_not_large():
    col = _make_col("id", data_type="INTEGER")
    assert _large_type(col, threshold=255) is False


# ---------------------------------------------------------------------------
# annotate_schema
# ---------------------------------------------------------------------------

def test_no_annotations_for_plain_column():
    schema = _make_schema(_make_table("users", _make_col("id", "INTEGER")))
    result = annotate_schema(schema)
    assert "users.id" not in result


def test_nullable_column_gets_tag():
    schema = _make_schema(
        _make_table("users", _make_col("email", "VARCHAR(200)", nullable=True))
    )
    result = annotate_schema(schema)
    tags = [a.tag for a in result.get("users.email", [])]
    assert "nullable" in tags


def test_primary_key_column_gets_tag():
    schema = _make_schema(
        _make_table("users", _make_col("id", "INTEGER", primary_key=True))
    )
    result = annotate_schema(schema)
    tags = [a.tag for a in result.get("users.id", [])]
    assert "primary_key" in tags


def test_large_type_column_gets_tag():
    schema = _make_schema(
        _make_table("posts", _make_col("body", "TEXT"))
    )
    result = annotate_schema(schema)
    tags = [a.tag for a in result.get("posts.body", [])]
    assert "large_type" in tags


def test_multiple_tags_on_same_column():
    schema = _make_schema(
        _make_table("docs", _make_col("content", "TEXT", nullable=True))
    )
    result = annotate_schema(schema)
    tags = [a.tag for a in result.get("docs.content", [])]
    assert "nullable" in tags
    assert "large_type" in tags


def test_disable_nullable_tagging():
    opts = AnnotationOptions(tag_nullable=False)
    schema = _make_schema(
        _make_table("users", _make_col("email", "VARCHAR(50)", nullable=True))
    )
    result = annotate_schema(schema, options=opts)
    tags = [a.tag for a in result.get("users.email", [])]
    assert "nullable" not in tags


def test_annotation_repr():
    a = Annotation(tag="nullable", reason="allows null")
    assert "nullable" in repr(a)
    assert "allows null" in repr(a)


def test_empty_schema_returns_empty_map():
    schema = Schema(tables={})
    result = annotate_schema(schema)
    assert result == {}
