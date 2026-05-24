"""Tests for sqlsift.watcher_cli."""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from sqlsift.watcher_cli import _build_parser, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCHEMA_DICT = {
    "tables": [
        {
            "name": "users",
            "columns": [
                {"name": "id", "type": "INT", "nullable": False},
                {"name": "email", "type": "TEXT", "nullable": True},
            ],
        }
    ]
}


def _write_schema(path: str, d: dict) -> None:
    with open(path, "w") as fh:
        json.dump(d, fh)


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_parser_defaults():
    p = _build_parser()
    args = p.parse_args(["schema.json"])
    assert args.interval == 60.0
    assert args.iterations is None
    assert args.color is False


def test_parser_custom_interval():
    p = _build_parser()
    args = p.parse_args(["schema.json", "--interval", "5"])
    assert args.interval == 5.0


def test_parser_iterations():
    p = _build_parser()
    args = p.parse_args(["schema.json", "--iterations", "3"])
    assert args.iterations == 3


# ---------------------------------------------------------------------------
# main() integration tests
# ---------------------------------------------------------------------------

def test_main_exits_zero_after_limited_iterations():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "schema.json")
        _write_schema(path, _SCHEMA_DICT)

        with patch("time.sleep"):
            rc = main([path, "--iterations", "1"])

    assert rc == 0


def test_main_drift_printed_when_schema_changes(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "schema.json")
        _write_schema(path, _SCHEMA_DICT)

        schema_v2 = {
            "tables": [
                {
                    "name": "users",
                    "columns": [
                        {"name": "id", "type": "INT", "nullable": False},
                        {"name": "email", "type": "TEXT", "nullable": True},
                        {"name": "phone", "type": "TEXT", "nullable": True},
                    ],
                }
            ]
        }

        call_count = 0

        def _fake_load_from_json(text):
            from sqlsift.loader import load_from_json as real
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return real(json.dumps(schema_v2))
            return real(text)

        with patch("sqlsift.watcher_cli.load_from_json", side_effect=_fake_load_from_json):
            with patch("time.sleep"):
                main([path, "--iterations", "2"])

    captured = capsys.readouterr()
    assert "phone" in captured.out or "users" in captured.out
