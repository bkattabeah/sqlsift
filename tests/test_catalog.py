"""Tests for sqlsift.catalog and sqlsift.catalog_report."""
import json

import pytest

from sqlsift.catalog import Catalog, CatalogEntry, build_catalog
from sqlsift.catalog_report import CatalogReportOptions, generate_catalog_report
from sqlsift.schema import Column, Schema, Table


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_col(name: str, col_type: str = "TEXT") -> Column:
    return Column(name=name, col_type=col_type, nullable=True, default=None)


def _make_table(name: str, *col_names: str) -> Table:
    t = Table(name=name)
    for c in col_names:
        t.add_column(_make_col(c))
    return t


def _make_schema(*table_names: str) -> Schema:
    s = Schema()
    for name in table_names:
        s.add_table(_make_table(name, "id"))
    return s


# ---------------------------------------------------------------------------
# Catalog tests
# ---------------------------------------------------------------------------

def test_register_adds_entry():
    cat = Catalog()
    schema = _make_schema("users")
    entry = cat.register("prod", schema)
    assert isinstance(entry, CatalogEntry)
    assert cat.get("prod") is entry


def test_len_reflects_entries():
    cat = build_catalog({"a": _make_schema("t1"), "b": _make_schema("t2")})
    assert len(cat) == 2


def test_names_are_sorted():
    cat = build_catalog({"z": _make_schema(), "a": _make_schema()})
    assert cat.names() == ["a", "z"]


def test_remove_drops_entry():
    cat = Catalog()
    cat.register("x", _make_schema())
    cat.remove("x")
    assert cat.get("x") is None


def test_remove_unknown_is_silent():
    cat = Catalog()
    cat.remove("nonexistent")  # should not raise


def test_find_by_tag_returns_matching():
    cat = Catalog()
    cat.register("prod", _make_schema("orders"), tags=["production", "billing"])
    cat.register("staging", _make_schema("orders"), tags=["staging"])
    results = cat.find_by_tag("production")
    assert len(results) == 1
    assert results[0].name == "prod"


def test_find_by_tag_empty_when_no_match():
    cat = Catalog()
    cat.register("prod", _make_schema(), tags=["production"])
    assert cat.find_by_tag("staging") == []


def test_iter_yields_all_entries():
    cat = build_catalog({"a": _make_schema(), "b": _make_schema()})
    names = {e.name for e in cat}
    assert names == {"a", "b"}


# ---------------------------------------------------------------------------
# Report tests
# ---------------------------------------------------------------------------

def test_text_report_contains_name():
    cat = Catalog()
    cat.register("prod", _make_schema("users", "orders"))
    report = generate_catalog_report(cat)
    assert "prod" in report
    assert "2 tables" in report


def test_text_report_empty_catalog():
    report = generate_catalog_report(Catalog())
    assert "empty" in report


def test_json_report_is_valid_json():
    cat = Catalog()
    cat.register("prod", _make_schema("t1"), tags=["live"], description="Live DB")
    opts = CatalogReportOptions(format="json")
    data = json.loads(generate_catalog_report(cat, opts))
    assert isinstance(data, list)
    assert data[0]["name"] == "prod"
    assert data[0]["table_count"] == 1
    assert "live" in data[0]["tags"]


def test_markdown_report_contains_table_header():
    cat = build_catalog({"dev": _make_schema("logs")})
    opts = CatalogReportOptions(format="markdown")
    report = generate_catalog_report(cat, opts)
    assert "# Schema Catalog" in report
    assert "| dev |" in report


def test_text_report_shows_description():
    cat = Catalog()
    cat.register("prod", _make_schema(), description="Production database")
    opts = CatalogReportOptions(format="text", show_description=True)
    report = generate_catalog_report(cat, opts)
    assert "Production database" in report


def test_text_report_hides_tags_when_disabled():
    cat = Catalog()
    cat.register("prod", _make_schema(), tags=["live"])
    opts = CatalogReportOptions(format="text", show_tags=False)
    report = generate_catalog_report(cat, opts)
    assert "live" not in report
