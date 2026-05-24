"""Tests for sqlsift.baseline (save / load / list)."""

import json
import os
import tempfile

import pytest

from sqlsift.schema import Schema, Table, Column
from sqlsift.baseline import save_baseline, load_baseline, list_baselines


def _make_col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _make_schema() -> Schema:
    schema = Schema()
    table = Table(name="users")
    table.add_column(_make_col("id", "INTEGER"))
    table.add_column(_make_col("email", "TEXT"))
    schema.add_table(table)
    return schema


def test_save_creates_file():
    schema = _make_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "baseline.json")
        save_baseline(schema, path, name="v1")
        assert os.path.isfile(path)


def test_save_file_contains_metadata():
    schema = _make_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "baseline.json")
        save_baseline(schema, path, name="v1", description="initial snapshot")
        with open(path) as fh:
            payload = json.load(fh)
        assert payload["metadata"]["name"] == "v1"
        assert payload["metadata"]["description"] == "initial snapshot"
        assert "created_at" in payload["metadata"]


def test_load_roundtrip_schema():
    schema = _make_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "baseline.json")
        save_baseline(schema, path, name="v1")
        baseline = load_baseline(path)
        assert "users" in baseline.schema.tables
        cols = {c.name for c in baseline.schema.tables["users"].columns}
        assert cols == {"id", "email"}


def test_load_baseline_metadata():
    schema = _make_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "baseline.json")
        save_baseline(schema, path, name="release-1", description="prod snapshot")
        baseline = load_baseline(path)
        assert baseline.metadata.name == "release-1"
        assert baseline.metadata.description == "prod snapshot"


def test_list_baselines_empty_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = list_baselines(tmpdir)
        assert result == []


def test_list_baselines_returns_json_files():
    schema = _make_schema()
    with tempfile.TemporaryDirectory() as tmpdir:
        for name in ("a", "b", "c"):
            save_baseline(schema, os.path.join(tmpdir, f"{name}.json"), name=name)
        result = list_baselines(tmpdir)
        assert len(result) == 3
        assert all(r.endswith(".json") for r in result)


def test_list_baselines_missing_dir():
    result = list_baselines("/nonexistent/path/xyz")
    assert result == []
