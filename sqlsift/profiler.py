"""Schema profiler: compute statistics and metadata about a schema."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sqlsift.schema import Schema, Table


@dataclass
class ColumnProfile:
    name: str
    data_type: str
    nullable: bool
    has_default: bool

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ColumnProfile(name={self.name!r}, type={self.data_type!r}, "
            f"nullable={self.nullable}, has_default={self.has_default})"
        )


@dataclass
class TableProfile:
    name: str
    column_count: int
    nullable_count: int
    non_nullable_count: int
    columns_with_defaults: int
    column_profiles: List[ColumnProfile] = field(default_factory=list)

    @property
    def nullable_ratio(self) -> float:
        if self.column_count == 0:
            return 0.0
        return self.nullable_count / self.column_count


@dataclass
class SchemaProfile:
    table_count: int
    total_columns: int
    table_profiles: Dict[str, TableProfile] = field(default_factory=dict)

    @property
    def average_columns_per_table(self) -> float:
        if self.table_count == 0:
            return 0.0
        return self.total_columns / self.table_count


def _profile_table(table: Table) -> TableProfile:
    col_profiles: List[ColumnProfile] = []
    nullable_count = 0
    columns_with_defaults = 0

    for col in table.columns.values():
        has_default = col.default is not None
        col_profiles.append(
            ColumnProfile(
                name=col.name,
                data_type=col.data_type,
                nullable=col.nullable,
                has_default=has_default,
            )
        )
        if col.nullable:
            nullable_count += 1
        if has_default:
            columns_with_defaults += 1

    column_count = len(table.columns)
    return TableProfile(
        name=table.name,
        column_count=column_count,
        nullable_count=nullable_count,
        non_nullable_count=column_count - nullable_count,
        columns_with_defaults=columns_with_defaults,
        column_profiles=col_profiles,
    )


def profile_schema(schema: Schema) -> SchemaProfile:
    """Return a :class:`SchemaProfile` summarising *schema*."""
    table_profiles: Dict[str, TableProfile] = {}
    total_columns = 0

    for table in schema.tables.values():
        tp = _profile_table(table)
        table_profiles[table.name] = tp
        total_columns += tp.column_count

    return SchemaProfile(
        table_count=len(schema.tables),
        total_columns=total_columns,
        table_profiles=table_profiles,
    )
