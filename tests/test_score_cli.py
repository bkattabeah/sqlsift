"""Tests for sqlsift.score_cli."""
import json
import pytest
from pathlib import Path

from sqlsift.score_cli import _build_parser, _parse_weights, main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_SCHEMA_A = {
    "tables": {
        "users": {
            "columns": {
                "id": {"type": "int", "nullable": False, "primary_key": True}
            }
        }
    }
}

_SCHEMA_B = {
    "tables": {
        "users": {
            "columns": {
                "id": {"type": "int", "nullable": False, "primary_key": True},
                "email": {"type": "varchar", "nullable": True, "primary_key": False},
            }
        },
        "orders": {
            "columns": {
                "id": {"type": "int", "nullable": False, "primary_key": True}
            }
        },
    }
}


def _write(tmp_path: Path, name: str, data: dict) -> Path:
    p = tmp_path / name
    p.write_text(json.dumps(data))
    return p


# ---------------------------------------------------------------------------
# Parser tests
# ---------------------------------------------------------------------------

def test_parser_defaults():
    p = _build_parser()
    args = p.parse_args(["old.json", "new.json"])
    assert args.format == "text"
    assert args.no_breakdown is False
    assert args.color is False
    assert args.exit_code is False


def test_parser_format_option():
    p = _build_parser()
    args = p.parse_args(["a.json", "b.json", "--format", "json"])
    assert args.format == "json"


def test_parse_weights_basic():
    result = _parse_weights(["added_table=5", "removed_table=10"])
    assert result["added_table"] == 5
    assert result["removed_table"] == 10


def test_parse_weights_empty():
    assert _parse_weights([]) == {}


# ---------------------------------------------------------------------------
# Integration-style tests using tmp files
# ---------------------------------------------------------------------------

def test_main_no_drift_exits_zero(tmp_path):
    old = _write(tmp_path, "old.json", _SCHEMA_A)
    new = _write(tmp_path, "new.json", _SCHEMA_A)
    main([str(old), str(new)])  # should not raise


def test_main_with_drift_text_output(tmp_path, capsys):
    old = _write(tmp_path, "old.json", _SCHEMA_A)
    new = _write(tmp_path, "new.json", _SCHEMA_B)
    main([str(old), str(new)])
    captured = capsys.readouterr()
    assert "Drift Score" in captured.out


def test_main_json_format_is_parseable(tmp_path, capsys):
    old = _write(tmp_path, "old.json", _SCHEMA_A)
    new = _write(tmp_path, "new.json", _SCHEMA_B)
    main([str(old), str(new), "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "total" in data
    assert data["total"] > 0


def test_main_exit_code_raises_on_drift(tmp_path):
    old = _write(tmp_path, "old.json", _SCHEMA_A)
    new = _write(tmp_path, "new.json", _SCHEMA_B)
    with pytest.raises(SystemExit) as exc_info:
        main([str(old), str(new), "--exit-code"])
    assert exc_info.value.code == 1


def test_main_exit_code_no_raise_when_no_drift(tmp_path):
    old = _write(tmp_path, "old.json", _SCHEMA_A)
    new = _write(tmp_path, "new.json", _SCHEMA_A)
    main([str(old), str(new), "--exit-code"])  # should not raise


def test_main_markdown_contains_header(tmp_path, capsys):
    old = _write(tmp_path, "old.json", _SCHEMA_A)
    new = _write(tmp_path, "new.json", _SCHEMA_B)
    main([str(old), str(new), "--format", "markdown"])
    captured = capsys.readouterr()
    assert "## Drift Score Report" in captured.out
