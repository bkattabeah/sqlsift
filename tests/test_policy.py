"""Tests for sqlsift.policy."""

from __future__ import annotations

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.policy import (
    PolicyOptions,
    PolicyViolation,
    PolicyResult,
    enforce_policy,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "VARCHAR(255)", primary_key: bool = False) -> Column:
    return Column(name=name, col_type=col_type, nullable=True, primary_key=primary_key, default=None)


def _make_table(name: str, cols: list[Column]) -> Table:
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
# tests
# ---------------------------------------------------------------------------

def test_clean_schema_passes():
    table = _make_table("users", [
        _make_col("id", "INT", primary_key=True),
        _make_col("email"),
    ])
    result = enforce_policy(_make_schema(table))
    assert result.passed
    assert result.violations == []


def test_missing_primary_key_raises_p001():
    table = _make_table("orders", [_make_col("amount", "DECIMAL")])
    result = enforce_policy(_make_schema(table))
    assert not result.passed
    rules = [v.rule for v in result.violations]
    assert "P001" in rules


def test_primary_key_check_disabled():
    table = _make_table("orders", [_make_col("amount", "DECIMAL")])
    opts = PolicyOptions(require_primary_key=False)
    result = enforce_policy(_make_schema(table), opts)
    assert result.passed


def test_long_column_name_raises_p002():
    long_name = "a" * 64
    table = _make_table("things", [
        _make_col("id", primary_key=True),
        _make_col(long_name),
    ])
    result = enforce_policy(_make_schema(table))
    rules = [v.rule for v in result.violations]
    assert "P002" in rules


def test_unconstrained_text_raises_p003():
    table = _make_table("docs", [
        _make_col("id", "INT", primary_key=True),
        _make_col("body", "TEXT"),
    ])
    opts = PolicyOptions(disallow_unconstrained_text=True)
    result = enforce_policy(_make_schema(table), opts)
    rules = [v.rule for v in result.violations]
    assert "P003" in rules


def test_unconstrained_text_allowed_by_default():
    table = _make_table("docs", [
        _make_col("id", "INT", primary_key=True),
        _make_col("body", "TEXT"),
    ])
    result = enforce_policy(_make_schema(table))
    rules = [v.rule for v in result.violations]
    assert "P003" not in rules


def test_forbidden_prefix_raises_p004():
    table = _make_table("metrics", [
        _make_col("id", "INT", primary_key=True),
        _make_col("tmp_value"),
    ])
    opts = PolicyOptions(forbidden_prefixes=["tmp_"])
    result = enforce_policy(_make_schema(table), opts)
    rules = [v.rule for v in result.violations]
    assert "P004" in rules


def test_multiple_tables_aggregate_violations():
    t1 = _make_table("a", [_make_col("x")])
    t2 = _make_table("b", [_make_col("y")])
    result = enforce_policy(_make_schema(t1, t2))
    tables_with_p001 = {v.table for v in result.violations if v.rule == "P001"}
    assert tables_with_p001 == {"a", "b"}


def test_violation_repr():
    v = PolicyViolation(rule="P001", table="users", column=None, message="no pk")
    assert "P001" in repr(v)
    assert "users" in repr(v)


def test_violation_repr_with_column():
    v = PolicyViolation(rule="P002", table="users", column="long_col", message="too long")
    assert "long_col" in repr(v)
