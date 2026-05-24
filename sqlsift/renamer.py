"""sqlsift.renamer — utilities for detecting and applying column/table renames."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from sqlsift.schema import Schema, Table
from sqlsift.comparator import compare_columns, ColumnSimilarity


@dataclass
class RenameOptions:
    """Configuration for rename detection."""
    column_similarity_threshold: float = 0.75
    table_similarity_threshold: float = 0.60


@dataclass
class RenameHint:
    """A single rename suggestion."""
    kind: str          # 'table' or 'column'
    table_name: str    # always the *new* table name (or old for table renames)
    old_name: str
    new_name: str
    score: float

    def __repr__(self) -> str:
        return (
            f"RenameHint(kind={self.kind!r}, table={self.table_name!r}, "
            f"{self.old_name!r} -> {self.new_name!r}, score={self.score:.2f})"
        )


def _best_match(
    candidate: str,
    pool: List[str],
    scored: Dict[Tuple[str, str], float],
) -> Optional[Tuple[str, float]]:
    """Return the highest-scoring (name, score) from pool for candidate."""
    best: Optional[Tuple[str, float]] = None
    for name in pool:
        s = scored.get((candidate, name), scored.get((name, candidate), 0.0))
        if best is None or s > best[1]:
            best = (name, s)
    return best


def detect_renames(
    old_schema: Schema,
    new_schema: Schema,
    options: Optional[RenameOptions] = None,
) -> List[RenameHint]:
    """Compare two schemas and return likely rename hints.

    Only tables/columns that were *removed* in old and *added* in new are
    considered — matching is done by structural similarity.
    """
    if options is None:
        options = RenameOptions()

    hints: List[RenameHint] = []

    old_names = set(old_schema.tables)
    new_names = set(new_schema.tables)
    removed_tables = old_names - new_names
    added_tables = new_names - old_names
    common_tables = old_names & new_names

    # --- table-level rename detection ---
    for old_t in removed_tables:
        old_table = old_schema.tables[old_t]
        best_score = 0.0
        best_name: Optional[str] = None
        for new_t in added_tables:
            new_table = new_schema.tables[new_t]
            sim = compare_columns(list(old_table.columns.values()),
                                  list(new_table.columns.values()))
            if sim.score > best_score:
                best_score = sim.score
                best_name = new_t
        if best_name and best_score >= options.table_similarity_threshold:
            hints.append(RenameHint(
                kind="table",
                table_name=old_t,
                old_name=old_t,
                new_name=best_name,
                score=best_score,
            ))

    # --- column-level rename detection within common tables ---
    for tname in common_tables:
        old_table: Table = old_schema.tables[tname]
        new_table: Table = new_schema.tables[tname]
        removed_cols = set(old_table.columns) - set(new_table.columns)
        added_cols = set(new_table.columns) - set(old_table.columns)
        for old_c in removed_cols:
            best_score = 0.0
            best_new: Optional[str] = None
            for new_c in added_cols:
                sim: ColumnSimilarity = compare_columns(
                    [old_table.columns[old_c]],
                    [new_table.columns[new_c]],
                )
                if sim.score > best_score:
                    best_score = sim.score
                    best_new = new_c
            if best_new and best_score >= options.column_similarity_threshold:
                hints.append(RenameHint(
                    kind="column",
                    table_name=tname,
                    old_name=old_c,
                    new_name=best_new,
                    score=best_score,
                ))

    return hints
