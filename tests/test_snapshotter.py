"""Tests for sqlsift.snapshotter."""
from __future__ import annotations

import pytest

from sqlsift.schema import Schema, Table, Column
from sqlsift.snapshotter import (
    Snapshot,
    SnapshotStore,
    diff_snapshots,
    snapshot_to_dict,
    snapshot_from_dict,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _make_table(name: str, *col_names: str) -> Table:
    t = Table(name=name)
    for cn in col_names:
        t.add_column(_make_col(cn))
    return t


def _make_schema(*table_names: str) -> Schema:
    s = Schema()
    for tn in table_names:
        s.add_table(_make_table(tn, "id", "value"))
    return s


# ---------------------------------------------------------------------------
# SnapshotStore
# ---------------------------------------------------------------------------

def test_store_starts_empty():
    store = SnapshotStore()
    assert len(store) == 0
    assert store.latest() is None


def test_add_returns_snapshot():
    store = SnapshotStore()
    schema = _make_schema("users")
    snap = store.add(schema, label="v1")
    assert isinstance(snap, Snapshot)
    assert snap.label == "v1"
    assert len(store) == 1


def test_add_auto_label():
    store = SnapshotStore()
    snap = store.add(_make_schema("orders"))
    assert snap.label == "snapshot-1"


def test_latest_returns_most_recent():
    store = SnapshotStore()
    store.add(_make_schema("a"), label="first")
    store.add(_make_schema("b"), label="second")
    assert store.latest().label == "second"


def test_all_preserves_order():
    store = SnapshotStore()
    store.add(_make_schema("a"), label="one")
    store.add(_make_schema("b"), label="two")
    store.add(_make_schema("c"), label="three")
    labels = [s.label for s in store.all()]
    assert labels == ["one", "two", "three"]


def test_clear_empties_store():
    store = SnapshotStore()
    store.add(_make_schema("x"))
    store.clear()
    assert len(store) == 0


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_diff_snapshots_no_changes():
    schema = _make_schema("users")
    store = SnapshotStore()
    s1 = store.add(schema, label="v1")
    s2 = store.add(schema, label="v2")
    diff = diff_snapshots(s1, s2)
    assert not diff.has_changes()


def test_diff_snapshots_detects_added_table():
    s1_schema = _make_schema("users")
    s2_schema = _make_schema("users", "orders")
    store = SnapshotStore()
    s1 = store.add(s1_schema, label="v1")
    s2 = store.add(s2_schema, label="v2")
    diff = diff_snapshots(s1, s2)
    assert diff.has_changes()
    assert "orders" in diff.added_tables


# ---------------------------------------------------------------------------
# serialisation round-trip
# ---------------------------------------------------------------------------

def test_snapshot_roundtrip():
    schema = _make_schema("products")
    store = SnapshotStore()
    original = store.add(schema, label="prod-v1")
    data = snapshot_to_dict(original)
    restored = snapshot_from_dict(data)
    assert restored.label == original.label
    assert restored.captured_at == original.captured_at
    assert list(restored.schema.tables.keys()) == list(original.schema.tables.keys())


def test_snapshot_to_dict_keys():
    snap = SnapshotStore().add(_make_schema("t"), label="lbl")
    d = snapshot_to_dict(snap)
    assert set(d.keys()) == {"label", "captured_at", "schema"}
