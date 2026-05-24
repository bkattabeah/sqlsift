"""Column-level lineage tracking across schema snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.schema import Schema


@dataclass
class LineageNode:
    table: str
    column: str
    snapshot_label: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"LineageNode({self.snapshot_label!r}: {self.table}.{self.column})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, LineageNode):
            return NotImplemented
        return (
            self.table == other.table
            and self.column == other.column
            and self.snapshot_label == other.snapshot_label
        )

    def __hash__(self) -> int:
        return hash((self.table, self.column, self.snapshot_label))


@dataclass
class LineageEdge:
    source: LineageNode
    target: LineageNode
    reason: str = "persisted"  # persisted | renamed | type_changed

    def __repr__(self) -> str:  # pragma: no cover
        return f"LineageEdge({self.source!r} -> {self.target!r}, {self.reason!r})"


@dataclass
class LineageGraph:
    nodes: List[LineageNode] = field(default_factory=list)
    edges: List[LineageEdge] = field(default_factory=list)

    def predecessors(self, node: LineageNode) -> List[LineageNode]:
        return [e.source for e in self.edges if e.target == node]

    def successors(self, node: LineageNode) -> List[LineageNode]:
        return [e.target for e in self.edges if e.source == node]


def build_lineage(
    snapshots: List[tuple[str, Schema]],
    rename_hints: Optional[Dict[str, Dict[str, str]]] = None,
) -> LineageGraph:
    """Build a lineage graph from an ordered list of (label, schema) pairs.

    *rename_hints* maps ``{table: {old_col: new_col}}`` for known renames.
    """
    graph = LineageGraph()
    if not snapshots:
        return graph

    renames: Dict[str, Dict[str, str]] = rename_hints or {}

    prev_label, prev_schema = snapshots[0]
    for table_name, table in prev_schema.tables.items():
        for col_name in table.columns:
            graph.nodes.append(LineageNode(table_name, col_name, prev_label))

    for curr_label, curr_schema in snapshots[1:]:
        for table_name, table in curr_schema.tables.items():
            table_renames = renames.get(table_name, {})
            reverse_renames = {v: k for k, v in table_renames.items()}

            for col_name in table.columns:
                node = LineageNode(table_name, col_name, curr_label)
                graph.nodes.append(node)

                prev_col = reverse_renames.get(col_name, col_name)
                prev_table = prev_schema.tables.get(table_name)
                if prev_table and prev_col in prev_table.columns:
                    prev_node = LineageNode(table_name, prev_col, prev_label)
                    reason = "renamed" if prev_col != col_name else "persisted"
                    graph.edges.append(LineageEdge(prev_node, node, reason))

        prev_label, prev_schema = curr_label, curr_schema

    return graph
