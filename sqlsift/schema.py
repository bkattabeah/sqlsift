"""Core data structures for representing SQL database schemas."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Column:
    """Represents a single column in a database table."""

    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Column):
            return NotImplemented
        return (
            self.name == other.name
            and self.data_type == other.data_type
            and self.nullable == other.nullable
            and self.default == other.default
            and self.primary_key == other.primary_key
        )


@dataclass
class Table:
    """Represents a single table in a database schema."""

    name: str
    columns: Dict[str, Column] = field(default_factory=dict)

    def add_column(self, column: Column) -> None:
        self.columns[column.name] = column

    def column_names(self) -> List[str]:
        return list(self.columns.keys())


@dataclass
class Schema:
    """Represents a full database schema snapshot."""

    name: str
    tables: Dict[str, Table] = field(default_factory=dict)

    def add_table(self, table: Table) -> None:
        self.tables[table.name] = table

    def table_names(self) -> List[str]:
        return list(self.tables.keys())
