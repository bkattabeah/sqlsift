"""Tests for sqlsift.audit_cli."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sqlsift.audit_cli import _build_parser, _cmd_list, _cmd_record
from sqlsift.loader import dump_to_json
from sqlsift.schema import Column, Table
from sqlsift.loader import load_from_dict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _schema_dict(table_name: str, col_names: list[str]) -> dict:
    return {
        "tables": {
            table_name: {
                "columns": [
                    {"name": c, "type": "TEXT", "nullable": True, "default": None}
                    for c in col_names
                ]
            }
        }
    }


def _write_schema(path: Path, d: dict) -> None:
    path.write_text(json.dumps(d), encoding="utf-8")


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_parser_record_subcommand() -> None:
    parser = _build_parser()
    args = parser.parse_args(["record", "before.json", "after.json"])
    assert args.command == "record"
    assert args.before == "before.json"
    assert args.after == "after.json"


def test_parser_record_defaults() -> None:
    parser = _build_parser()
    args = parser.parse_args(["record", "a.json", "b.json"])
    assert args.log == "audit.jsonl"
    assert args.actor == "unknown"
    assert args.label is None


def test_parser_list_subcommand() -> None:
    parser = _build_parser()
    args = parser.parse_args(["list", "audit.jsonl"])
    assert args.command == "list"
    assert args.log == "audit.jsonl"


# ---------------------------------------------------------------------------
# _cmd_record tests
# ---------------------------------------------------------------------------

def test_cmd_record_exits_zero(tmp_path: Path) -> None:
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    _write_schema(before, _schema_dict("users", ["id"]))
    _write_schema(after, _schema_dict("users", ["id"]))
    log = tmp_path / "audit.jsonl"
    parser = _build_parser()
    args = parser.parse_args(["record", str(before), str(after), "--log", str(log)])
    assert _cmd_record(args) == 0


def test_cmd_record_creates_log(tmp_path: Path) -> None:
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    _write_schema(before, _schema_dict("users", ["id"]))
    _write_schema(after, _schema_dict("users", ["id", "email"]))
    log = tmp_path / "audit.jsonl"
    parser = _build_parser()
    args = parser.parse_args(["record", str(before), str(after), "--log", str(log), "--actor", "tester"])
    _cmd_record(args)
    assert log.exists()
    lines = log.read_text().strip().splitlines()
    assert len(lines) == 1
    data = json.loads(lines[0])
    assert data["actor"] == "tester"


# ---------------------------------------------------------------------------
# _cmd_list tests
# ---------------------------------------------------------------------------

def test_cmd_list_empty_log(tmp_path: Path, capsys) -> None:
    log = tmp_path / "empty.jsonl"
    parser = _build_parser()
    args = parser.parse_args(["list", str(log)])
    _cmd_list(args)
    captured = capsys.readouterr()
    assert "No audit entries" in captured.out


def test_cmd_list_shows_entries(tmp_path: Path, capsys) -> None:
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    _write_schema(before, _schema_dict("users", ["id"]))
    _write_schema(after, _schema_dict("orders", ["id"]))
    log = tmp_path / "audit.jsonl"
    rec_parser = _build_parser()
    rec_args = rec_parser.parse_args(["record", str(before), str(after), "--log", str(log), "--actor", "qa"])
    _cmd_record(rec_args)
    list_parser = _build_parser()
    list_args = list_parser.parse_args(["list", str(log)])
    _cmd_list(list_args)
    captured = capsys.readouterr()
    assert "qa" in captured.out
