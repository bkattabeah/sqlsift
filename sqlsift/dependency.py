"""Detect column and table dependencies within a schema based on naming conventions and foreign key hints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.schema import Schema, Table


@dataclass
class DependencyEdge:
    """Represents a dependency from one table/column to another."""

    from_table: str
    from_column: str
    to_table: str
    to_column: str
    confidence: float  # 0.0 – 1.0

    def __repr__(self) -> str:
        return (
            f"DependencyEdge({self.from_table}.{self.from_column} "
            f"-> {self.to_table}.{self.to_column}, "
            f"confidence={self.confidence:.2f})"
        )


@dataclass
class DependencyGraph:
    """Collection of dependency edges for a schema."""

    edges: List[DependencyEdge] = field(default_factory=list)

    def edges_for_table(self, table_name: str) -> List[DependencyEdge]:
        """Return all edges where *from_table* matches."""
        return [e for e in self.edges if e.from_table == table_name]

    def referenced_by(self, table_name: str) -> List[DependencyEdge]:
        """Return all edges where *to_table* matches."""
        return [e for e in self.edges if e.to_table == table_name]


@dataclass
class DependencyOptions:
    """Options controlling dependency detection."""

    min_confidence: float = 0.5
    id_column: str = "id"


def _candidate_target(col_name: str, table_names: List[str]) -> Optional[str]:
    """Return the table name that *col_name* looks like a FK for, or None."""
    if not col_name.endswith("_id"):
        return None
    prefix = col_name[:-3]  # strip trailing '_id'
    for tname in table_names:
        if tname.lower() == prefix.lower():
            return tname
    return None


def build_dependency_graph(
    schema: Schema,
    options: Optional[DependencyOptions] = None,
) -> DependencyGraph:
    """Analyse *schema* and return a :class:`DependencyGraph`.

    Detection strategy: a column named ``<table>_id`` in one table is treated
    as a foreign-key reference to the primary-key column (``id`` by default)
    of ``<table>`` when that table exists in the schema.
    """
    if options is None:
        options = DependencyOptions()

    table_names = list(schema.tables.keys())
    edges: List[DependencyEdge] = []

    for tname, table in schema.tables.items():
        for col in table.columns.values():
            target = _candidate_target(col.name, table_names)
            if target is None or target == tname:
                continue
            target_table: Table = schema.tables[target]
            if options.id_column not in target_table.columns:
                continue
            confidence = 1.0 if not col.nullable else 0.75
            if confidence >= options.min_confidence:
                edges.append(
                    DependencyEdge(
                        from_table=tname,
                        from_column=col.name,
                        to_table=target,
                        to_column=options.id_column,
                        confidence=confidence,
                    )
                )

    return DependencyGraph(edges=edges)
