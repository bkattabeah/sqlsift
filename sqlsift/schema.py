"""Core schema data model for sqlsift."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Column:
    """Represents a single column in a database table."""

    name: str
    col_type: str
    nullable: bool = True
    primary_key: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Column):
            return NotImplemented
        return (
            self.name == other.name
            and self.col_type == other.col_type
            and self.nullable == other.nullable
            and self.primary_key == other.primary_key
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Column(name={self.name!r}, col_type={self.col_type!r}, "
            f"nullable={self.nullable}, primary_key={self.primary_key})"
        )


@dataclass
class Table:
    """Represents a database table with an ordered collection of columns."""

    name: str
    columns: Dict[str, Column] = field(default_factory=dict)

    def add_column(self, column: Column) -> None:
        """Add a column to this table."""
        self.columns[column.name] = column

    def column_names(self) -> List[str]:
        """Return column names in insertion order."""
        return list(self.columns.keys())

    def get_column(self, name: str) -> Optional[Column]:
        """Return a column by name, or None if not found."""
        return self.columns.get(name)


@dataclass
class Schema:
    """Represents a full database schema (collection of tables)."""

    tables: Dict[str, Table] = field(default_factory=dict)

    def add_table(self, table: Table) -> None:
        """Add a table to this schema."""
        self.tables[table.name] = table

    def table_names(self) -> List[str]:
        """Return table names in insertion order."""
        return list(self.tables.keys())

    def get_table(self, name: str) -> Optional[Table]:
        """Return a table by name, or None if not found."""
        return self.tables.get(name)
