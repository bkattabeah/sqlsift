"""Drift heatmap: ranks tables by change frequency across multiple diffs."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Sequence

from sqlsift.diff import SchemaDiff


@dataclass
class TableHeat:
    table: str
    change_count: int
    diff_appearances: int  # how many diffs contained this table

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"TableHeat(table={self.table!r}, changes={self.change_count}, "
            f"appearances={self.diff_appearances})"
        )


@dataclass
class DriftHeatmap:
    entries: List[TableHeat] = field(default_factory=list)

    def hottest(self, n: int = 5) -> List[TableHeat]:
        """Return up to *n* tables sorted by change_count descending."""
        return sorted(self.entries, key=lambda e: e.change_count, reverse=True)[:n]

    def __len__(self) -> int:
        return len(self.entries)


def _count_table_changes(diff: SchemaDiff) -> Dict[str, int]:
    """Return a mapping of table_name -> number of changes in *diff*."""
    counts: Dict[str, int] = {}

    for tname in diff.added_tables:
        counts[tname] = counts.get(tname, 0) + 1

    for tname in diff.removed_tables:
        counts[tname] = counts.get(tname, 0) + 1

    for tname, tdiff in diff.modified_tables.items():
        n = (
            len(tdiff.added_columns)
            + len(tdiff.removed_columns)
            + len(tdiff.modified_columns)
        )
        if n:
            counts[tname] = counts.get(tname, 0) + n

    return counts


def build_heatmap(diffs: Sequence[SchemaDiff]) -> DriftHeatmap:
    """Aggregate multiple diffs into a :class:`DriftHeatmap`."""
    total_changes: Dict[str, int] = {}
    appearances: Dict[str, int] = {}

    for diff in diffs:
        table_counts = _count_table_changes(diff)
        for tname, cnt in table_counts.items():
            total_changes[tname] = total_changes.get(tname, 0) + cnt
            appearances[tname] = appearances.get(tname, 0) + 1

    entries = [
        TableHeat(
            table=tname,
            change_count=total_changes[tname],
            diff_appearances=appearances[tname],
        )
        for tname in total_changes
    ]
    return DriftHeatmap(entries=entries)
