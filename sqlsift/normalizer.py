"""Schema normalizer: standardize column types and names across a schema snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from sqlsift.schema import Column, Schema, Table


@dataclass
class NormalizeOptions:
    """Options controlling normalization behaviour."""

    # Map raw type strings (lower-cased) to canonical forms.
    type_aliases: Dict[str, str] = field(default_factory=lambda: {
        "integer": "INT",
        "int4": "INT",
        "int8": "BIGINT",
        "bool": "BOOLEAN",
        "varchar": "VARCHAR",
        "character varying": "VARCHAR",
        "text": "TEXT",
        "float4": "FLOAT",
        "float8": "DOUBLE",
        "numeric": "DECIMAL",
    })
    # When True, column names are lower-cased.
    lowercase_names: bool = True
    # When True, table names are lower-cased.
    lowercase_tables: bool = True


def _normalize_type(raw: str, aliases: Dict[str, str]) -> str:
    """Return the canonical type for *raw*, or *raw* upper-cased if unknown."""
    key = raw.strip().lower()
    return aliases.get(key, raw.strip().upper())


def _normalize_column(col: Column, opts: NormalizeOptions) -> Column:
    name = col.name.lower() if opts.lowercase_names else col.name
    col_type = _normalize_type(col.col_type, opts.type_aliases)
    return Column(
        name=name,
        col_type=col_type,
        nullable=col.nullable,
        default=col.default,
        primary_key=col.primary_key,
    )


def _normalize_table(table: Table, opts: NormalizeOptions) -> Table:
    name = table.name.lower() if opts.lowercase_tables else table.name
    new_table = Table(name=name)
    for col in table.columns.values():
        norm_col = _normalize_column(col, opts)
        new_table.add_column(norm_col)
    return new_table


def normalize_schema(
    schema: Schema,
    options: Optional[NormalizeOptions] = None,
) -> Schema:
    """Return a new :class:`Schema` with types and names normalized."""
    opts = options or NormalizeOptions()
    normalized = Schema()
    for table in schema.tables.values():
        norm_table = _normalize_table(table, opts)
        normalized.add_table(norm_table)
    return normalized
