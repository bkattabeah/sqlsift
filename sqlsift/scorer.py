"""Drift severity scoring for schema diffs."""

from dataclasses import dataclass, field
from typing import Dict

from sqlsift.diff import SchemaDiff

# Default weights for each change type
DEFAULT_WEIGHTS: Dict[str, float] = {
    "added_table": 1.0,
    "removed_table": 3.0,  # removals are more severe
    "added_column": 0.5,
    "removed_column": 2.0,
    "modified_column": 1.5,
}


@dataclass
class ScorerOptions:
    """Weights used to compute the drift score."""

    weights: Dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))


@dataclass
class DriftScore:
    """Numeric result of scoring a diff."""

    total: float
    breakdown: Dict[str, float]

    def __repr__(self) -> str:  # pragma: no cover
        return f"DriftScore(total={self.total:.2f}, breakdown={self.breakdown})"

    @property
    def severity(self) -> str:
        """Human-readable severity label based on total score."""
        if self.total == 0.0:
            return "none"
        if self.total < 3.0:
            return "low"
        if self.total < 10.0:
            return "medium"
        return "high"


def score_diff(diff: SchemaDiff, options: ScorerOptions | None = None) -> DriftScore:
    """Compute a weighted drift score from a *SchemaDiff*.

    Args:
        diff: The schema diff to score.
        options: Optional scoring weights; defaults to :data:`DEFAULT_WEIGHTS`.

    Returns:
        A :class:`DriftScore` with the total and per-category breakdown.
    """
    if options is None:
        options = ScorerOptions()

    w = options.weights

    counts: Dict[str, int] = {
        "added_table": len(diff.added_tables),
        "removed_table": len(diff.removed_tables),
        "added_column": sum(len(cols) for cols in diff.added_columns.values()),
        "removed_column": sum(len(cols) for cols in diff.removed_columns.values()),
        "modified_column": sum(len(cols) for cols in diff.modified_columns.values()),
    }

    breakdown: Dict[str, float] = {
        key: counts[key] * w.get(key, 0.0) for key in counts
    }
    total = sum(breakdown.values())

    return DriftScore(total=round(total, 4), breakdown=breakdown)
