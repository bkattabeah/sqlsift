"""Tests for sqlsift.lineage_report."""
import json

from sqlsift.schema import Column, Table, Schema
from sqlsift.lineage import build_lineage
from sqlsift.lineage_report import (
    LineageReportOptions,
    generate_lineage_report,
)


def _make_col(name: str) -> Column:
    return Column(name=name, col_type="INT", nullable=False, default=None, primary_key=False)


def _make_table(name: str, *cols: str) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(_make_col(c))
    return t


def _make_schema(*tables: Table) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def _two_snapshot_graph():
    s1 = _make_schema(_make_table("users", "id", "name"))
    s2 = _make_schema(_make_table("users", "id", "name"))
    return build_lineage([("v1", s1), ("v2", s2)])


def test_text_report_contains_arrow():
    graph = _two_snapshot_graph()
    report = generate_lineage_report(graph)
    assert "->" in report


def test_text_report_no_edges_message():
    s1 = _make_schema(_make_table("t", "x"))
    graph = build_lineage([("v1", s1)])
    report = generate_lineage_report(graph)
    assert "No lineage edges" in report


def test_text_report_includes_reason_by_default():
    graph = _two_snapshot_graph()
    report = generate_lineage_report(graph)
    assert "persisted" in report


def test_text_report_hides_reason_when_disabled():
    graph = _two_snapshot_graph()
    opts = LineageReportOptions(include_reason=False)
    report = generate_lineage_report(graph, opts)
    assert "persisted" not in report


def test_json_report_parses():
    graph = _two_snapshot_graph()
    opts = LineageReportOptions(fmt="json")
    data = json.loads(generate_lineage_report(graph, opts))
    assert "edges" in data
    assert len(data["edges"]) == 2
    assert "reason" in data["edges"][0]


def test_json_report_omits_reason_when_disabled():
    graph = _two_snapshot_graph()
    opts = LineageReportOptions(fmt="json", include_reason=False)
    data = json.loads(generate_lineage_report(graph, opts))
    assert "reason" not in data["edges"][0]


def test_markdown_report_has_table_header():
    graph = _two_snapshot_graph()
    opts = LineageReportOptions(fmt="markdown")
    report = generate_lineage_report(graph, opts)
    assert "| Source | Target |" in report


def test_markdown_no_edges_message():
    s1 = _make_schema(_make_table("t", "x"))
    graph = build_lineage([("v1", s1)])
    opts = LineageReportOptions(fmt="markdown")
    report = generate_lineage_report(graph, opts)
    assert "No lineage edges" in report


def test_default_options_used_when_none_passed():
    graph = _two_snapshot_graph()
    report = generate_lineage_report(graph, None)
    assert "->" in report
