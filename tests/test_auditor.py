"""Tests for sqlsift.auditor."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqlsift.auditor import AuditEntry, load_audit_log, record_audit
from sqlsift.diff import SchemaDiff
from sqlsift.schema import Column, Table


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _make_table(name: str, cols: list[str] | None = None) -> Table:
    t = Table(name=name)
    for c in cols or ["id"]:
        t.add_column(_make_col(c))
    return t


def _empty_diff() -> SchemaDiff:
    return SchemaDiff(
        added_tables={},
        removed_tables={},
        modified_tables={},
    )


def _diff_with_added() -> SchemaDiff:
    return SchemaDiff(
        added_tables={"orders": _make_table("orders")},
        removed_tables={},
        modified_tables={},
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_record_audit_creates_file(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    record_audit(_empty_diff(), path=log, actor="ci")
    assert log.exists()


def test_record_audit_entry_has_actor(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    entry = record_audit(_empty_diff(), path=log, actor="alice")
    assert entry.actor == "alice"


def test_record_audit_no_changes_flag(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    entry = record_audit(_empty_diff(), path=log)
    assert entry.has_changes is False


def test_record_audit_has_changes_flag(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    entry = record_audit(_diff_with_added(), path=log)
    assert entry.has_changes is True


def test_record_audit_added_tables_listed(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    entry = record_audit(_diff_with_added(), path=log)
    assert "orders" in entry.added_tables


def test_record_audit_baseline_label(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    entry = record_audit(_empty_diff(), path=log, baseline_label="v1.0")
    assert entry.baseline_label == "v1.0"


def test_load_audit_log_roundtrip(tmp_path: Path) -> None:
    log = tmp_path / "audit.jsonl"
    record_audit(_empty_diff(), path=log, actor="bob")
    record_audit(_diff_with_added(), path=log, actor="carol")
    entries = load_audit_log(log)
    assert len(entries) == 2
    assert entries[0].actor == "bob"
    assert entries[1].actor == "carol"


def test_load_audit_log_missing_file(tmp_path: Path) -> None:
    entries = load_audit_log(tmp_path / "nonexistent.jsonl")
    assert entries == []


def test_record_audit_creates_parent_dirs(tmp_path: Path) -> None:
    log = tmp_path / "deep" / "nested" / "audit.jsonl"
    record_audit(_empty_diff(), path=log)
    assert log.exists()
