"""Tests for sqlsift.planner and sqlsift.plan_report."""

from __future__ import annotations

import json

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import compute_diff
from sqlsift.planner import PlannerOptions, build_migration_plan
from sqlsift.plan_report import PlanReportOptions, generate_plan_report


def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, columns: list[Column]) -> Table:
    t = Table(name=name)
    for col in columns:
        t.add_column(col)
    return t


def _make_schema(tables: list[Table]) -> "Schema":
    from sqlsift.schema import Schema
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def _simple_diff():
    old = _make_schema([_make_table("users", [_make_col("id", "INT")])])
    new = _make_schema([
        _make_table("users", [_make_col("id", "INT"), _make_col("email", "TEXT")]),
        _make_table("orders", [_make_col("id", "INT")]),
    ])
    return compute_diff(old, new)


# --- planner tests ---

def test_plan_has_phases_for_added_table():
    diff = _simple_diff()
    plan = build_migration_plan(diff)
    phase_names = [p.name for p in plan.phases]
    assert "create_tables" in phase_names


def test_plan_has_phase_for_added_column():
    diff = _simple_diff()
    plan = build_migration_plan(diff)
    phase_names = [p.name for p in plan.phases]
    assert "add_columns" in phase_names


def test_all_statements_is_flat_list():
    diff = _simple_diff()
    plan = build_migration_plan(diff)
    stmts = plan.all_statements
    assert isinstance(stmts, list)
    assert all(isinstance(s, str) for s in stmts)


def test_create_tables_before_add_columns():
    diff = _simple_diff()
    plan = build_migration_plan(diff)
    phase_names = [p.name for p in plan.phases]
    assert phase_names.index("create_tables") < phase_names.index("add_columns")


def test_no_drops_when_disabled():
    old = _make_schema([_make_table("users", [_make_col("id", "INT"), _make_col("old", "TEXT")])])
    new = _make_schema([_make_table("users", [_make_col("id", "INT")])])
    diff = compute_diff(old, new)
    plan = build_migration_plan(diff, PlannerOptions(include_drops=False))
    phase_names = [p.name for p in plan.phases]
    assert "drop_columns" not in phase_names
    assert "drop_tables" not in phase_names


def test_empty_diff_produces_empty_plan():
    schema = _make_schema([_make_table("users", [_make_col("id", "INT")])])
    diff = compute_diff(schema, schema)
    plan = build_migration_plan(diff)
    assert plan.phases == []
    assert plan.all_statements == []


# --- plan_report tests ---

def test_text_report_contains_phase_header():
    diff = _simple_diff()
    plan = build_migration_plan(diff)
    report = generate_plan_report(plan)
    assert "-- Phase:" in report


def test_text_report_no_changes_message():
    schema = _make_schema([_make_table("users", [_make_col("id", "INT")])])
    diff = compute_diff(schema, schema)
    plan = build_migration_plan(diff)
    report = generate_plan_report(plan)
    assert "No migration steps required" in report


def test_json_report_is_valid_json():
    diff = _simple_diff()
    plan = build_migration_plan(diff)
    report = generate_plan_report(plan, PlanReportOptions(format="json"))
    data = json.loads(report)
    assert isinstance(data, list)
    assert all("phase" in item and "statements" in item for item in data)


def test_markdown_report_contains_sql_fence():
    diff = _simple_diff()
    plan = build_migration_plan(diff)
    report = generate_plan_report(plan, PlanReportOptions(format="markdown"))
    assert "```sql" in report


def test_markdown_no_changes_message():
    schema = _make_schema([_make_table("users", [_make_col("id", "INT")])])
    diff = compute_diff(schema, schema)
    plan = build_migration_plan(diff)
    report = generate_plan_report(plan, PlanReportOptions(format="markdown"))
    assert "No migration steps required" in report
