"""Divergence detection: measure how far two schemas have drifted over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.schema import Schema


@dataclass
class DivergencePoint:
    """A single point in a divergence timeline."""

    label: str
    added_tables: int
    removed_tables: int
    modified_tables: int
    added_columns: int
    removed_columns: int
    modified_columns: int

    @property
    def total(self) -> int:
        return (
            self.added_tables
            + self.removed_tables
            + self.modified_tables
            + self.added_columns
            + self.removed_columns
            + self.modified_columns
        )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DivergencePoint(label={self.label!r}, total={self.total})"
        )


@dataclass
class DivergenceReport:
    """Aggregated divergence across a sequence of schema pairs."""

    points: List[DivergencePoint] = field(default_factory=list)

    @property
    def peak(self) -> DivergencePoint | None:
        return max(self.points, key=lambda p: p.total) if self.points else None

    @property
    def total_drift(self) -> int:
        return sum(p.total for p in self.points)


def _count_from_diff(diff: SchemaDiff) -> dict:
    added_cols = sum(len(td.added_columns) for td in diff.modified_tables.values())
    removed_cols = sum(len(td.removed_columns) for td in diff.modified_tables.values())
    modified_cols = sum(len(td.modified_columns) for td in diff.modified_tables.values())
    return {
        "added_tables": len(diff.added_tables),
        "removed_tables": len(diff.removed_tables),
        "modified_tables": len(diff.modified_tables),
        "added_columns": added_cols,
        "removed_columns": removed_cols,
        "modified_columns": modified_cols,
    }


def measure_divergence(
    snapshots: List[tuple[str, Schema]],
) -> DivergenceReport:
    """Compute divergence between consecutive (label, Schema) pairs.

    Args:
        snapshots: Ordered list of (label, Schema) tuples.  At least two
                   entries are required to produce any points.

    Returns:
        A :class:`DivergenceReport` with one point per consecutive pair.
    """
    report = DivergenceReport()
    for i in range(1, len(snapshots)):
        label_a, schema_a = snapshots[i - 1]
        label_b, schema_b = snapshots[i]
        diff: SchemaDiff = compute_diff(schema_a, schema_b)
        counts = _count_from_diff(diff)
        label = f"{label_a} -> {label_b}"
        report.points.append(DivergencePoint(label=label, **counts))
    return report
