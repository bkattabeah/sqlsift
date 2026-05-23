"""Load database schemas from various sources into Schema objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from sqlsift.schema import Column, Schema, Table


def load_from_dict(data: dict) -> Schema:
    """Load a Schema from a plain Python dictionary.

    Expected format::

        {
            "tables": {
                "users": {
                    "columns": [
                        {"name": "id", "type": "INTEGER", "nullable": false, "primary_key": true},
                        {"name": "email", "type": "TEXT", "nullable": false, "primary_key": false}
                    ]
                }
            }
        }
    """
    schema = Schema()
    for table_name, table_data in data.get("tables", {}).items():
        table = Table(name=table_name)
        for col_data in table_data.get("columns", []):
            column = Column(
                name=col_data["name"],
                col_type=col_data["type"],
                nullable=col_data.get("nullable", True),
                primary_key=col_data.get("primary_key", False),
            )
            table.add_column(column)
        schema.add_table(table)
    return schema


def load_from_json(path: Union[str, Path]) -> Schema:
    """Load a Schema from a JSON file on disk."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return load_from_dict(data)


def dump_to_dict(schema: Schema) -> dict:
    """Serialize a Schema to a plain Python dictionary."""
    tables = {}
    for table_name, table in schema.tables.items():
        tables[table_name] = {
            "columns": [
                {
                    "name": col.name,
                    "type": col.col_type,
                    "nullable": col.nullable,
                    "primary_key": col.primary_key,
                }
                for col in table.columns.values()
            ]
        }
    return {"tables": tables}


def dump_to_json(schema: Schema, path: Union[str, Path], indent: int = 2) -> None:
    """Serialize a Schema to a JSON file on disk."""
    path = Path(path)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(dump_to_dict(schema), fh, indent=indent)
