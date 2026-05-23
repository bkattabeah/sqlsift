"""Tests for sqlsift.cli."""
import json
import pytest
from pathlib import Path
from sqlsift.cli import main


_SCHEMA_A = {
    "tables": {
        "users": {
            "columns": {
                "id": {"data_type": "INT", "nullable": False, "default": None},
                "email": {"data_type": "TEXT", "nullable": True, "default": None},
            }
        }
    }
}

_SCHEMA_B = {
    "tables": {
        "users": {
            "columns": {
                "id": {"data_type": "INT", "nullable": False, "default": None},
                "email": {"data_type": "TEXT", "nullable": True, "default": None},
                "created_at": {"data_type": "TIMESTAMP", "nullable": True, "default": None},
            }
        },
        "orders": {
            "columns": {
                "order_id": {"data_type": "INT", "nullable": False, "default": None},
            }
        },
    }
}


@pytest.fixture()
def schema_files(tmp_path):
    old = tmp_path / "old.json"
    new = tmp_path / "new.json"
    old.write_text(json.dumps(_SCHEMA_A))
    new.write_text(json.dumps(_SCHEMA_B))
    return old, new


def test_diff_command_exits_zero(schema_files, capsys):
    old, new = schema_files
    rc = main(["diff", str(old), str(new)])
    assert rc == 0


def test_diff_command_output_contains_added(schema_files, capsys):
    old, new = schema_files
    main(["diff", str(old), str(new), "--no-color"])
    captured = capsys.readouterr()
    assert "orders" in captured.out


def test_diff_command_writes_file(schema_files, tmp_path):
    old, new = schema_files
    out = tmp_path / "result.json"
    rc = main(["diff", str(old), str(new), "-o", str(out)])
    assert rc == 0
    assert out.exists()


def test_validate_valid_schema(schema_files, capsys):
    old, _ = schema_files
    rc = main(["validate", str(old)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "valid" in captured.out


def test_validate_invalid_schema(tmp_path, capsys):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"tables": {"t": {"columns": {"bad_col": {"data_type": "", "nullable": True, "default": None}}}}}))
    rc = main(["validate", str(bad)])
    # empty data_type is only a warning, so still valid
    assert rc == 0
