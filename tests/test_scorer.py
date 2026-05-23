"""Tests for sqlsift.scorer."""

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import SchemaDiff
from sqlsift.scorer import (
    DEFAULT_WEIGHTS,
    DriftScore,
    ScorerOptions,
    score_diff,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, *cols: Column) -> Table:
    t = Table(name=name)
    for c in cols:
        t.add_column(c)
    return t


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(
        added_tables=[],
        removed_tables=[],
        added_columns={},
        removed_columns={},
        modified_columns={},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_score_no_changes_is_zero():
    result = score_diff(_empty_diff())
    assert result.total == 0.0
    assert result.severity == "none"


def test_score_added_table():
    diff = _empty_diff()
    diff.added_tables.append(_make_table("users"))
    result = score_diff(diff)
    assert result.total == DEFAULT_WEIGHTS["added_table"]
    assert result.breakdown["added_table"] == DEFAULT_WEIGHTS["added_table"]


def test_score_removed_table_is_heavier():
    diff_add = _empty_diff()
    diff_add.added_tables.append(_make_table("t"))

    diff_rem = _empty_diff()
    diff_rem.removed_tables.append(_make_table("t"))

    assert score_diff(diff_rem).total > score_diff(diff_add).total


def test_score_multiple_column_changes():
    col_a = _make_col("a")
    col_b = _make_col("b")
    diff = _empty_diff()
    diff.added_columns["orders"] = [col_a]
    diff.removed_columns["orders"] = [col_b]
    result = score_diff(diff)
    expected = DEFAULT_WEIGHTS["added_column"] + DEFAULT_WEIGHTS["removed_column"]
    assert result.total == pytest.approx(expected)


def test_severity_labels():
    diff = _empty_diff()
    # low: add 1 column => 0.5
    diff.added_columns["t"] = [_make_col("x")]
    assert score_diff(diff).severity == "low"

    # medium: remove 4 tables => 12 ... wait, let's use 2 removed tables => 6
    diff2 = _empty_diff()
    diff2.removed_tables = [_make_table("a"), _make_table("b")]
    assert score_diff(diff2).severity == "medium"

    # high: remove 4 tables => 12
    diff3 = _empty_diff()
    diff3.removed_tables = [_make_table(str(i)) for i in range(4)]
    assert score_diff(diff3).severity == "high"


def test_custom_weights():
    opts = ScorerOptions(weights={"added_table": 10.0})
    diff = _empty_diff()
    diff.added_tables.append(_make_table("big"))
    result = score_diff(diff, options=opts)
    assert result.total == pytest.approx(10.0)


def test_drift_score_breakdown_keys():
    result = score_diff(_empty_diff())
    expected_keys = {"added_table", "removed_table", "added_column", "removed_column", "modified_column"}
    assert set(result.breakdown.keys()) == expected_keys
