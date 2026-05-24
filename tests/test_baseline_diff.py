"""Tests for sqlsift.baseline_diff."""

import os
import tempfile

import pytest

from sqlsift.schema import Schema, Table, Column
from sqlsift.baseline import save_baseline
from sqlsift.baseline_diff import diff_against_baseline, diff_two_baselines


def _make_col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _base_schema() -> Schema:
    schema = Schema()
    t = Table(name="orders")
    t.add_column(_make_col("id", "INTEGER"))
    t.add_column(_make_col("total", "NUMERIC"))
    schema.add_table(t)
    return schema


def _evolved_schema() -> Schema:
    schema = Schema()
    t = Table(name="orders")
    t.add_column(_make_col("id", "INTEGER"))
    t.add_column(_make_col("total", "NUMERIC"))
    t.add_column(_make_col("status", "TEXT"))
    schema.add_table(t)
    new_t = Table(name="shipments")
    new_t.add_column(_make_col("id", "INTEGER"))
    schema.add_table(new_t)
    return schema


def test_no_drift_when_schemas_identical():
    schema = _base_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "bl.json")
        save_baseline(schema, path, name="v1")
        result = diff_against_baseline(schema, path)
        assert not result.has_drift


def test_drift_detected_when_column_added():
    old = _base_schema()
    new = _evolved_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "bl.json")
        save_baseline(old, path, name="v1")
        result = diff_against_baseline(new, path)
        assert result.has_drift


def test_baseline_name_in_result():
    schema = _base_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "bl.json")
        save_baseline(schema, path, name="my-baseline")
        result = diff_against_baseline(schema, path)
        assert result.baseline_name == "my-baseline"


def test_diff_two_baselines_detects_new_table():
    old = _base_schema()
    new = _evolved_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        old_path = os.path.join(tmpdir, "old.json")
        new_path = os.path.join(tmpdir, "new.json")
        save_baseline(old, old_path, name="v1")
        save_baseline(new, new_path, name="v2")
        result = diff_two_baselines(old_path, new_path)
        assert result.has_drift
        assert "shipments" in result.diff.added_tables


def test_diff_two_identical_baselines_no_drift():
    schema = _base_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        p1 = os.path.join(tmpdir, "a.json")
        p2 = os.path.join(tmpdir, "b.json")
        save_baseline(schema, p1, name="v1")
        save_baseline(schema, p2, name="v2")
        result = diff_two_baselines(p1, p2)
        assert not result.has_drift
