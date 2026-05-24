"""Tests for sqlsift.watcher."""

from __future__ import annotations

from unittest.mock import patch, MagicMock
from typing import List

import pytest

from sqlsift.schema import Schema, Table, Column
from sqlsift.watcher import WatchOptions, WatchEvent, watch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, cols: List[Column]) -> Table:
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

def test_watch_single_iteration_no_drift():
    """With max_iterations=1 only the loader is called once; no diff is emitted."""
    schema = _make_schema(_make_table("users", [_make_col("id", "INT")]))
    loader = MagicMock(return_value=schema)
    opts = WatchOptions(interval=0, max_iterations=1)

    with patch("time.sleep"):
        events = watch(loader, opts)

    assert events == []  # first call has no previous snapshot
    loader.assert_called_once()


def test_watch_detects_drift_on_second_call():
    schema_v1 = _make_schema(_make_table("users", [_make_col("id", "INT")]))
    schema_v2 = _make_schema(
        _make_table("users", [_make_col("id", "INT"), _make_col("email", "TEXT")])
    )
    loader = MagicMock(side_effect=[schema_v1, schema_v2])
    drift_cb = MagicMock()
    opts = WatchOptions(interval=0, max_iterations=2, on_drift=drift_cb)

    with patch("time.sleep"):
        events = watch(loader, opts)

    assert len(events) == 1
    assert events[0].had_drift is True
    drift_cb.assert_called_once()


def test_watch_no_drift_callback_called():
    schema = _make_schema(_make_table("orders", [_make_col("id", "INT")]))
    loader = MagicMock(return_value=schema)
    no_change_cb = MagicMock()
    opts = WatchOptions(interval=0, max_iterations=2, on_no_change=no_change_cb)

    with patch("time.sleep"):
        events = watch(loader, opts)

    assert len(events) == 1
    assert events[0].had_drift is False
    no_change_cb.assert_called_once()


def test_watch_multiple_iterations():
    s1 = _make_schema(_make_table("t", [_make_col("a")]))
    s2 = _make_schema(_make_table("t", [_make_col("a"), _make_col("b")]))
    s3 = _make_schema(_make_table("t", [_make_col("a"), _make_col("b")]))
    loader = MagicMock(side_effect=[s1, s2, s3])
    opts = WatchOptions(interval=0, max_iterations=3)

    with patch("time.sleep"):
        events = watch(loader, opts)

    assert len(events) == 2
    assert events[0].had_drift is True
    assert events[1].had_drift is False


def test_watch_event_repr_smoke():
    schema = _make_schema(_make_table("x", [_make_col("id")]))
    loader = MagicMock(side_effect=[schema, schema])
    opts = WatchOptions(interval=0, max_iterations=2)

    with patch("time.sleep"):
        events = watch(loader, opts)

    assert "WatchEvent" in repr(events[0])


def test_watch_sleep_called_between_iterations():
    schema = _make_schema(_make_table("t", [_make_col("id")]))
    loader = MagicMock(return_value=schema)
    opts = WatchOptions(interval=30.0, max_iterations=2)

    with patch("time.sleep") as mock_sleep:
        watch(loader, opts)

    mock_sleep.assert_called_once_with(30.0)
