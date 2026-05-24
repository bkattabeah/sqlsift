"""Tests for sqlsift.lineage."""
import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.lineage import (
    LineageNode,
    LineageEdge,
    build_lineage,
)


def _make_col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None, primary_key=False)


def _make_table(name: str, *col_names: str) -> Table:
    t = Table(name=name)
    for c in col_names:
        t.add_column(_make_col(c))
    return t


def _make_schema(*tables: Table) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def test_empty_snapshots_returns_empty_graph():
    graph = build_lineage([])
    assert graph.nodes == []
    assert graph.edges == []


def test_single_snapshot_has_nodes_no_edges():
    schema = _make_schema(_make_table("users", "id", "name"))
    graph = build_lineage([("v1", schema)])
    assert len(graph.nodes) == 2
    assert graph.edges == []


def test_persisted_column_creates_edge():
    s1 = _make_schema(_make_table("users", "id", "email"))
    s2 = _make_schema(_make_table("users", "id", "email"))
    graph = build_lineage([("v1", s1), ("v2", s2)])
    reasons = {e.reason for e in graph.edges}
    assert reasons == {"persisted"}
    assert len(graph.edges) == 2


def test_new_column_has_no_edge():
    s1 = _make_schema(_make_table("users", "id"))
    s2 = _make_schema(_make_table("users", "id", "email"))
    graph = build_lineage([("v1", s1), ("v2", s2)])
    targets = {e.target.column for e in graph.edges}
    assert "email" not in targets
    assert "id" in targets


def test_renamed_column_creates_renamed_edge():
    s1 = _make_schema(_make_table("orders", "amt"))
    s2 = _make_schema(_make_table("orders", "amount"))
    hints = {"orders": {"amt": "amount"}}
    graph = build_lineage([("v1", s1), ("v2", s2)], rename_hints=hints)
    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.reason == "renamed"
    assert edge.source.column == "amt"
    assert edge.target.column == "amount"


def test_predecessors_and_successors():
    s1 = _make_schema(_make_table("t", "col"))
    s2 = _make_schema(_make_table("t", "col"))
    graph = build_lineage([("v1", s1), ("v2", s2)])
    v2_node = LineageNode("t", "col", "v2")
    v1_node = LineageNode("t", "col", "v1")
    assert graph.predecessors(v2_node) == [v1_node]
    assert graph.successors(v1_node) == [v2_node]


def test_three_snapshot_chain():
    s1 = _make_schema(_make_table("t", "x"))
    s2 = _make_schema(_make_table("t", "x"))
    s3 = _make_schema(_make_table("t", "x"))
    graph = build_lineage([("v1", s1), ("v2", s2), ("v3", s3)])
    assert len(graph.edges) == 2
    labels = [(e.source.snapshot_label, e.target.snapshot_label) for e in graph.edges]
    assert ("v1", "v2") in labels
    assert ("v2", "v3") in labels
