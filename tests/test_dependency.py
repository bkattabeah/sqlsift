"""Tests for sqlsift.dependency."""

from __future__ import annotations

import pytest

from sqlsift.schema import Column, Schema, Table
from sqlsift.dependency import (
    DependencyOptions,
    build_dependency_graph,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "INTEGER", nullable: bool = False) -> Column:
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
# Tests
# ---------------------------------------------------------------------------

def test_no_edges_for_unrelated_tables():
    schema = _make_schema(
        _make_table("users", _make_col("id"), _make_col("name", "TEXT")),
        _make_table("products", _make_col("id"), _make_col("title", "TEXT")),
    )
    graph = build_dependency_graph(schema)
    assert graph.edges == []


def test_fk_column_creates_edge():
    schema = _make_schema(
        _make_table("users", _make_col("id"), _make_col("name", "TEXT")),
        _make_table("orders", _make_col("id"), _make_col("users_id")),
    )
    graph = build_dependency_graph(schema)
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.from_table == "orders"
    assert edge.from_column == "users_id"
    assert edge.to_table == "users"
    assert edge.to_column == "id"


def test_nullable_fk_has_lower_confidence():
    schema = _make_schema(
        _make_table("users", _make_col("id")),
        _make_table("orders", _make_col("id"), _make_col("users_id", nullable=True)),
    )
    graph = build_dependency_graph(schema)
    assert len(graph.edges) == 1
    assert graph.edges[0].confidence == pytest.approx(0.75)


def test_non_nullable_fk_has_full_confidence():
    schema = _make_schema(
        _make_table("users", _make_col("id")),
        _make_table("orders", _make_col("id"), _make_col("users_id", nullable=False)),
    )
    graph = build_dependency_graph(schema)
    assert graph.edges[0].confidence == pytest.approx(1.0)


def test_min_confidence_filters_low_confidence_edges():
    schema = _make_schema(
        _make_table("users", _make_col("id")),
        _make_table("orders", _make_col("id"), _make_col("users_id", nullable=True)),
    )
    opts = DependencyOptions(min_confidence=0.9)
    graph = build_dependency_graph(schema, options=opts)
    assert graph.edges == []


def test_edges_for_table_filters_correctly():
    schema = _make_schema(
        _make_table("users", _make_col("id")),
        _make_table("products", _make_col("id")),
        _make_table("orders",
                    _make_col("id"),
                    _make_col("users_id"),
                    _make_col("products_id")),
    )
    graph = build_dependency_graph(schema)
    assert len(graph.edges_for_table("orders")) == 2
    assert graph.edges_for_table("users") == []


def test_referenced_by_filters_correctly():
    schema = _make_schema(
        _make_table("users", _make_col("id")),
        _make_table("orders", _make_col("id"), _make_col("users_id")),
        _make_table("reviews", _make_col("id"), _make_col("users_id")),
    )
    graph = build_dependency_graph(schema)
    refs = graph.referenced_by("users")
    assert len(refs) == 2
    from_tables = {e.from_table for e in refs}
    assert from_tables == {"orders", "reviews"}


def test_missing_target_id_column_skips_edge():
    """If the target table has no 'id' column, no edge should be created."""
    schema = _make_schema(
        _make_table("users", _make_col("user_pk", "INTEGER")),  # no 'id'
        _make_table("orders", _make_col("id"), _make_col("users_id")),
    )
    graph = build_dependency_graph(schema)
    assert graph.edges == []
