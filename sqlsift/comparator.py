"""Column-level and table-level similarity scoring for schema comparison."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from sqlsift.schema import Column, Table


@dataclass
class ColumnSimilarity:
    """Similarity result between two columns."""
    name_a: str
    name_b: str
    score: float  # 0.0 – 1.0
    matched_type: bool
    matched_nullable: bool

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ColumnSimilarity({self.name_a!r} <-> {self.name_b!r}, "
            f"score={self.score:.2f})"
        )


@dataclass
class TableSimilarity:
    """Aggregate similarity result between two tables."""
    table_name: str
    overall_score: float
    column_pairs: List[ColumnSimilarity] = field(default_factory=list)


def _column_score(a: Column, b: Column) -> ColumnSimilarity:
    """Compute a similarity score between two columns."""
    matched_type = a.col_type.lower() == b.col_type.lower()
    matched_nullable = a.nullable == b.nullable

    type_score = 1.0 if matched_type else 0.0
    nullable_score = 1.0 if matched_nullable else 0.0
    name_score = 1.0 if a.name.lower() == b.name.lower() else 0.0

    score = (name_score * 0.5) + (type_score * 0.35) + (nullable_score * 0.15)
    return ColumnSimilarity(
        name_a=a.name,
        name_b=b.name,
        score=round(score, 4),
        matched_type=matched_type,
        matched_nullable=matched_nullable,
    )


def compare_columns(
    cols_a: Dict[str, Column],
    cols_b: Dict[str, Column],
) -> List[ColumnSimilarity]:
    """Return similarity scores for all columns present in both tables."""
    results: List[ColumnSimilarity] = []
    common = set(cols_a) & set(cols_b)
    for name in sorted(common):
        results.append(_column_score(cols_a[name], cols_b[name]))
    return results


def compare_tables(a: Table, b: Table) -> TableSimilarity:
    """Compute overall similarity between two tables with the same name."""
    pairs = compare_columns(a.columns, b.columns)

    all_cols = set(a.columns) | set(b.columns)
    if not all_cols:
        return TableSimilarity(table_name=a.name, overall_score=1.0, column_pairs=[])

    matched_count = len(pairs)
    coverage = matched_count / len(all_cols)
    avg_pair_score = (
        sum(p.score for p in pairs) / matched_count if matched_count else 0.0
    )
    overall = round(coverage * avg_pair_score, 4)
    return TableSimilarity(
        table_name=a.name, overall_score=overall, column_pairs=pairs
    )
