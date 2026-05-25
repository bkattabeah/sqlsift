"""Tests for sqlsift.divergence and sqlsift.divergence_report."""
import json

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.divergence import measure_divergence, DivergenceReport
from sqlsift.divergence_report import (
    DivergenceReportOptions,
    generate_divergence_report,
)


def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, cols: list) -> Table:
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
# measure_divergence
# ---------------------------------------------------------------------------

def test_empty_snapshots_returns_empty_report():
    report = measure_divergence([])
    assert report.points == []
    assert report.total_drift == 0
    assert report.peak is None


def test_single_snapshot_returns_empty_report():
    s = _make_schema(_make_table("users", [_make_col("id")]))
    report = measure_divergence([("v1", s)])
    assert report.points == []


def test_identical_snapshots_produce_zero_point():
    s = _make_schema(_make_table("users", [_make_col("id")]))
    report = measure_divergence([("v1", s), ("v2", s)])
    assert len(report.points) == 1
    assert report.points[0].total == 0
    assert report.total_drift == 0


def test_added_table_counted():
    s1 = _make_schema(_make_table("users", [_make_col("id")]))
    s2 = _make_schema(
        _make_table("users", [_make_col("id")]),
        _make_table("orders", [_make_col("id")]),
    )
    report = measure_divergence([("v1", s1), ("v2", s2)])
    assert report.points[0].added_tables == 1
    assert report.points[0].total == 1


def test_removed_column_counted():
    s1 = _make_schema(_make_table("users", [_make_col("id"), _make_col("email")]))
    s2 = _make_schema(_make_table("users", [_make_col("id")]))
    report = measure_divergence([("v1", s1), ("v2", s2)])
    assert report.points[0].removed_columns == 1


def test_multiple_transitions_summed():
    s1 = _make_schema(_make_table("a", [_make_col("id")]))
    s2 = _make_schema(
        _make_table("a", [_make_col("id")]),
        _make_table("b", [_make_col("id")]),
    )
    s3 = _make_schema(
        _make_table("a", [_make_col("id")]),
        _make_table("b", [_make_col("id")]),
        _make_table("c", [_make_col("id")]),
    )
    report = measure_divergence([("v1", s1), ("v2", s2), ("v3", s3)])
    assert len(report.points) == 2
    assert report.total_drift == 2


def test_peak_is_highest_point():
    s1 = _make_schema()
    s2 = _make_schema(
        _make_table("a", [_make_col("id")]),
        _make_table("b", [_make_col("id")]),
    )
    s3 = _make_schema(
        _make_table("a", [_make_col("id")]),
        _make_table("b", [_make_col("id")]),
        _make_table("c", [_make_col("id")]),
    )
    report = measure_divergence([("v1", s1), ("v2", s2), ("v3", s3)])
    assert report.peak.label == "v1 -> v2"


# ---------------------------------------------------------------------------
# generate_divergence_report
# ---------------------------------------------------------------------------

def _two_point_report() -> DivergenceReport:
    s1 = _make_schema()
    s2 = _make_schema(_make_table("users", [_make_col("id")]))
    s3 = _make_schema(
        _make_table("users", [_make_col("id"), _make_col("email")]),
    )
    return measure_divergence([("v1", s1), ("v2", s2), ("v3", s3)])


def test_text_report_contains_header():
    report = _two_point_report()
    out = generate_divergence_report(report)
    assert "Schema Divergence Report" in out


def test_text_report_contains_transition_label():
    report = _two_point_report()
    out = generate_divergence_report(report)
    assert "v1 -> v2" in out


def test_json_report_is_valid_json():
    report = _two_point_report()
    opts = DivergenceReportOptions(format="json")
    out = generate_divergence_report(report, opts)
    data = json.loads(out)
    assert "points" in data
    assert "total_drift" in data


def test_json_report_point_count():
    report = _two_point_report()
    opts = DivergenceReportOptions(format="json")
    data = json.loads(generate_divergence_report(report, opts))
    assert len(data["points"]) == 2


def test_markdown_report_contains_table_header():
    report = _two_point_report()
    opts = DivergenceReportOptions(format="markdown")
    out = generate_divergence_report(report, opts)
    assert "| Transition |" in out


def test_hide_zero_points_option():
    s = _make_schema(_make_table("users", [_make_col("id")]))
    report = measure_divergence([("v1", s), ("v2", s)])
    opts = DivergenceReportOptions(show_zero_points=False)
    out = generate_divergence_report(report, opts)
    assert "No divergence detected" in out


def test_no_changes_text_report():
    report = measure_divergence([])
    out = generate_divergence_report(report)
    assert "No divergence detected" in out
