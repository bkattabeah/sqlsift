"""Filtering utilities for schema diffs — allows narrowing results by table name or change type."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from sqlsift.diff import SchemaDiff


@dataclass
class FilterOptions:
    """Options controlling which parts of a SchemaDiff are retained."""

    include_tables: Optional[List[str]] = None  # whitelist; None means all
    exclude_tables: Optional[List[str]] = None  # blacklist
    change_types: Optional[List[str]] = None    # e.g. ['added_tables', 'removed_columns']

    def _include_set(self) -> Optional[Set[str]]:
        return set(self.include_tables) if self.include_tables is not None else None

    def _exclude_set(self) -> Set[str]:
        return set(self.exclude_tables) if self.exclude_tables is not None else set()

    def _change_type_set(self) -> Optional[Set[str]]:
        return set(self.change_types) if self.change_types is not None else None


_ALL_CHANGE_TYPES = {
    "added_tables",
    "removed_tables",
    "added_columns",
    "removed_columns",
    "modified_columns",
}


def _table_allowed(table_name: str, opts: FilterOptions) -> bool:
    include = opts._include_set()
    exclude = opts._exclude_set()
    if include is not None and table_name not in include:
        return False
    if table_name in exclude:
        return False
    return True


def filter_diff(diff: SchemaDiff, opts: FilterOptions) -> SchemaDiff:
    """Return a new SchemaDiff containing only the entries that satisfy *opts*."""
    change_types = opts._change_type_set() or _ALL_CHANGE_TYPES

    def keep_table(name: str) -> bool:
        return _table_allowed(name, opts)

    added_tables = (
        {n: t for n, t in diff.added_tables.items() if keep_table(n)}
        if "added_tables" in change_types
        else {}
    )
    removed_tables = (
        {n: t for n, t in diff.removed_tables.items() if keep_table(n)}
        if "removed_tables" in change_types
        else {}
    )

    added_columns = (
        {n: cols for n, cols in diff.added_columns.items() if keep_table(n)}
        if "added_columns" in change_types
        else {}
    )
    removed_columns = (
        {n: cols for n, cols in diff.removed_columns.items() if keep_table(n)}
        if "removed_columns" in change_types
        else {}
    )
    modified_columns = (
        {n: cols for n, cols in diff.modified_columns.items() if keep_table(n)}
        if "modified_columns" in change_types
        else {}
    )

    return SchemaDiff(
        added_tables=added_tables,
        removed_tables=removed_tables,
        added_columns=added_columns,
        removed_columns=removed_columns,
        modified_columns=modified_columns,
    )
