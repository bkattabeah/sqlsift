"""Recommender: suggest remediation actions based on a SchemaDiff."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sqlsift.diff import SchemaDiff


@dataclass
class Recommendation:
    table: str
    column: str | None
    category: str  # e.g. 'add_column', 'drop_column', 'type_change', 'nullability'
    message: str
    priority: int  # 1=high, 2=medium, 3=low

    def __repr__(self) -> str:  # pragma: no cover
        col_part = f".{self.column}" if self.column else ""
        return f"<Recommendation [{self.priority}] {self.table}{col_part}: {self.category}>"


@dataclass
class RecommendationReport:
    recommendations: List[Recommendation] = field(default_factory=list)

    @property
    def high(self) -> List[Recommendation]:
        return [r for r in self.recommendations if r.priority == 1]

    @property
    def medium(self) -> List[Recommendation]:
        return [r for r in self.recommendations if r.priority == 2]

    @property
    def low(self) -> List[Recommendation]:
        return [r for r in self.recommendations if r.priority == 3]

    def __len__(self) -> int:
        return len(self.recommendations)


def _priority_for_category(category: str) -> int:
    return {"drop_column": 1, "type_change": 1, "nullability": 2, "add_column": 3}.get(
        category, 2
    )


def recommend(diff: SchemaDiff) -> RecommendationReport:
    """Inspect *diff* and return actionable recommendations."""
    recs: List[Recommendation] = []

    for table_name in diff.added_tables:
        recs.append(
            Recommendation(
                table=table_name,
                column=None,
                category="add_table",
                message=f"New table '{table_name}' detected; ensure downstream consumers are updated.",
                priority=2,
            )
        )

    for table_name in diff.removed_tables:
        recs.append(
            Recommendation(
                table=table_name,
                column=None,
                category="drop_table",
                message=f"Table '{table_name}' was removed; verify no active dependencies remain.",
                priority=1,
            )
        )

    for table_name, td in diff.modified_tables.items():
        for col in td.added_columns:
            cat = "add_column"
            recs.append(
                Recommendation(
                    table=table_name,
                    column=col.name,
                    category=cat,
                    message=f"Column '{col.name}' added to '{table_name}'; check NOT NULL constraints.",
                    priority=_priority_for_category(cat),
                )
            )
        for col in td.removed_columns:
            cat = "drop_column"
            recs.append(
                Recommendation(
                    table=table_name,
                    column=col.name,
                    category=cat,
                    message=f"Column '{col.name}' removed from '{table_name}'; high-risk change.",
                    priority=_priority_for_category(cat),
                )
            )
        for old_col, new_col in td.modified_columns:
            if old_col.data_type != new_col.data_type:
                cat = "type_change"
                recs.append(
                    Recommendation(
                        table=table_name,
                        column=old_col.name,
                        category=cat,
                        message=(
                            f"Column '{old_col.name}' in '{table_name}' changed type "
                            f"from '{old_col.data_type}' to '{new_col.data_type}'."
                        ),
                        priority=_priority_for_category(cat),
                    )
                )
            if old_col.nullable != new_col.nullable:
                cat = "nullability"
                direction = "nullable → NOT NULL" if not new_col.nullable else "NOT NULL → nullable"
                recs.append(
                    Recommendation(
                        table=table_name,
                        column=old_col.name,
                        category=cat,
                        message=(
                            f"Column '{old_col.name}' in '{table_name}' nullability changed "
                            f"({direction})."
                        ),
                        priority=_priority_for_category(cat),
                    )
                )

    recs.sort(key=lambda r: r.priority)
    return RecommendationReport(recommendations=recs)
