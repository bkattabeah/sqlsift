"""Tests for sqlsift.changelog."""

from __future__ import annotations

import pytest

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.changelog import (
    ChangelogOptions,
    build_changelog,
    format_changelog,
)


def _make_col(name: str, col_type: str = "TEXT", nullable: bool = True) -> Column:
    return Column(name=name, col_type=col_type, nullable=nullable)


def _make_table(name: str, cols: list | None = None) -> Table:
    t = Table(name=name)
    for c in cols or []:
        t.add_column(c)
    return t


def _make_schema(*tables: Table) -> Schema:
    s = Schema()
    for t in tables:
        s.add_table(t)
    return s


def _empty_diff() -> SchemaDiff:
    s = _make_schema(_make_table("users", [_make_col("id", "INT")]))
    return compute_diff(s, s)


def _diff_with_added() -> SchemaDiff:
    old = _make_schema(_make_table("users", [_make_col("id", "INT")]))
    new = _make_schema(
        _make_table("users", [_make_col("id", "INT")]),
        _make_table("orders", [_make_col("id", "INT")]),
    )
    return compute_diff(old, new)


def _diff_with_removed() -> SchemaDiff:
    old = _make_schema(
        _make_table("users", [_make_col("id", "INT")]),
        _make_table("logs", [_make_col("id", "INT")]),
    )
    new = _make_schema(_make_table("users", [_make_col("id", "INT")]))
    return compute_diff(old, new)


# --- tests ---

def test_build_changelog_skips_empty_diffs_by_default():
    changelog = build_changelog([_empty_diff()])
    assert len(changelog) == 0


def test_build_changelog_include_unchanged():
    opts = ChangelogOptions(include_unchanged=True)
    changelog = build_changelog([_empty_diff()], options=opts)
    assert len(changelog) == 1


def test_build_changelog_added_table_recorded():
    changelog = build_changelog([_diff_with_added()])
    assert len(changelog) == 1
    entry = changelog.entries[0]
    assert "orders" in entry.added_tables


def test_build_changelog_removed_table_recorded():
    changelog = build_changelog([_diff_with_removed()])
    entry = changelog.entries[0]
    assert "logs" in entry.removed_tables


def test_build_changelog_version_uses_prefix():
    opts = ChangelogOptions(version_prefix="rel-")
    changelog = build_changelog([_diff_with_added()], options=opts)
    assert changelog.entries[0].version == "rel-1"


def test_build_changelog_descriptions_applied():
    changelog = build_changelog(
        [_diff_with_added()],
        descriptions=["Initial release"],
    )
    assert changelog.entries[0].description == "Initial release"


def test_build_changelog_missing_description_is_empty_string():
    changelog = build_changelog([_diff_with_added()])
    assert changelog.entries[0].description == ""


def test_format_changelog_no_entries():
    from sqlsift.changelog import Changelog
    result = format_changelog(Changelog())
    assert result == "No changes recorded."


def test_format_changelog_contains_version():
    changelog = build_changelog([_diff_with_added()])
    text = format_changelog(changelog)
    assert "## v1" in text


def test_format_changelog_contains_added_table_name():
    changelog = build_changelog([_diff_with_added()])
    text = format_changelog(changelog)
    assert "orders" in text


def test_format_changelog_multiple_entries_ordered():
    diffs = [_diff_with_added(), _diff_with_removed()]
    changelog = build_changelog(diffs)
    text = format_changelog(changelog)
    assert text.index("## v1") < text.index("## v2")
