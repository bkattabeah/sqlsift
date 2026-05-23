"""Tests for sqlsift.loader — schema serialization / deserialization."""

from __future__ import annotations

import json
import pytest

from sqlsift.loader import dump_to_dict, dump_to_json, load_from_dict, load_from_json
from sqlsift.schema import Column, Schema, Table


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_DICT = {
    "tables": {
        "users": {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
                {"name": "email", "type": "TEXT", "nullable": False, "primary_key": False},
            ]
        },
        "posts": {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False, "primary_key": True},
                {"name": "body", "type": "TEXT", "nullable": True, "primary_key": False},
            ]
        },
    }
}


def _sample_schema() -> Schema:
    schema = Schema()
    users = Table(name="users")
    users.add_column(Column("id", "INTEGER", nullable=False, primary_key=True))
    users.add_column(Column("email", "TEXT", nullable=False, primary_key=False))
    schema.add_table(users)
    return schema


# ---------------------------------------------------------------------------
# load_from_dict
# ---------------------------------------------------------------------------

def test_load_from_dict_tables():
    schema = load_from_dict(SAMPLE_DICT)
    assert set(schema.tables.keys()) == {"users", "posts"}


def test_load_from_dict_columns():
    schema = load_from_dict(SAMPLE_DICT)
    users = schema.tables["users"]
    assert users.column_names() == ["id", "email"]


def test_load_from_dict_column_attributes():
    schema = load_from_dict(SAMPLE_DICT)
    id_col = schema.tables["users"].columns["id"]
    assert id_col.col_type == "INTEGER"
    assert id_col.primary_key is True
    assert id_col.nullable is False


def test_load_from_dict_empty():
    schema = load_from_dict({})
    assert schema.tables == {}


# ---------------------------------------------------------------------------
# load_from_json / dump_to_json round-trip
# ---------------------------------------------------------------------------

def test_load_from_json(tmp_path):
    json_file = tmp_path / "schema.json"
    json_file.write_text(json.dumps(SAMPLE_DICT), encoding="utf-8")
    schema = load_from_json(json_file)
    assert "users" in schema.tables


def test_load_from_json_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_from_json(tmp_path / "nonexistent.json")


def test_round_trip_json(tmp_path):
    schema = _sample_schema()
    out = tmp_path / "out.json"
    dump_to_json(schema, out)
    loaded = load_from_json(out)
    assert loaded.tables.keys() == schema.tables.keys()
    assert loaded.tables["users"].column_names() == schema.tables["users"].column_names()


# ---------------------------------------------------------------------------
# dump_to_dict
# ---------------------------------------------------------------------------

def test_dump_to_dict_structure():
    schema = _sample_schema()
    data = dump_to_dict(schema)
    assert "tables" in data
    assert "users" in data["tables"]
    cols = data["tables"]["users"]["columns"]
    assert any(c["name"] == "id" and c["primary_key"] is True for c in cols)
