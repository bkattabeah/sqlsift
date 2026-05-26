"""Tests for sqlsift.heatmap and sqlsift.heatmap_report."""
import json

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.heatmap import build_heatmap, DriftHeatmap
from sqlsift.heatmap_report import HeatmapReportOptions, generate_heatmap_report


def _make_col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None, primary_key=False)


def _make_table(name: str, cols=()) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


def _make_schema(*tables) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


# --- build_heatmap ---

def test_empty_diffs_returns_empty_heatmap():
    hm = build_heatmap([])
    assert len(hm) == 0
    assert hm.hottest() == []


def test_added_table_counted():
    old = _make_schema()
    new = _make_schema(_make_table("orders", [_make_col("id")]))
    diff = compute_diff(old, new)
    hm = build_heatmap([diff])
    assert len(hm) == 1
    assert hm.entries[0].table == "orders"
    assert hm.entries[0].change_count == 1


def test_removed_table_counted():
    old = _make_schema(_make_table("orders", [_make_col("id")]))
    new = _make_schema()
    diff = compute_diff(old, new)
    hm = build_heatmap([diff])
    assert hm.entries[0].change_count == 1


def test_column_changes_counted():
    old = _make_schema(_make_table("users", [_make_col("id")]))
    new = _make_schema(_make_table("users", [_make_col("id"), _make_col("email")]))
    diff = compute_diff(old, new)
    hm = build_heatmap([diff])
    assert hm.entries[0].change_count == 1  # one added column


def test_multiple_diffs_accumulate():
    base = _make_schema(_make_table("users", [_make_col("id")]))
    v2 = _make_schema(_make_table("users", [_make_col("id"), _make_col("name")]))
    v3 = _make_schema(_make_table("users", [_make_col("id"), _make_col("name"), _make_col("email")]))
    d1 = compute_diff(base, v2)
    d2 = compute_diff(v2, v3)
    hm = build_heatmap([d1, d2])
    assert hm.entries[0].change_count == 2
    assert hm.entries[0].diff_appearances == 2


def test_hottest_limits_results():
    diffs = []
    for i in range(8):
        old = _make_schema()
        new = _make_schema(_make_table(f"tbl_{i}", [_make_col("id")]))
        diffs.append(compute_diff(old, new))
    hm = build_heatmap(diffs)
    assert len(hm.hottest(3)) == 3


# --- generate_heatmap_report ---

def test_text_report_contains_table_name():
    old = _make_schema()
    new = _make_schema(_make_table("events", [_make_col("id")]))
    hm = build_heatmap([compute_diff(old, new)])
    report = generate_heatmap_report(hm)
    assert "events" in report


def test_text_report_empty_heatmap():
    hm = DriftHeatmap()
    report = generate_heatmap_report(hm)
    assert "no changes" in report


def test_json_report_is_valid_json():
    old = _make_schema()
    new = _make_schema(_make_table("logs", [_make_col("id")]))
    hm = build_heatmap([compute_diff(old, new)])
    opts = HeatmapReportOptions(format="json")
    data = json.loads(generate_heatmap_report(hm, opts))
    assert "heatmap" in data
    assert data["heatmap"][0]["table"] == "logs"


def test_markdown_report_has_header():
    hm = DriftHeatmap()
    opts = HeatmapReportOptions(format="markdown")
    report = generate_heatmap_report(hm, opts)
    assert "## Drift Heatmap" in report


def test_markdown_report_with_entries():
    old = _make_schema()
    new = _make_schema(_make_table("products", [_make_col("id")]))
    hm = build_heatmap([compute_diff(old, new)])
    opts = HeatmapReportOptions(format="markdown")
    report = generate_heatmap_report(hm, opts)
    assert "products" in report
    assert "|" in report
