"""Schema diff engine for detecting drift between two Schema snapshots."""

from dataclasses import dataclass, field
from typing import Dict, List

from sqlsift.schema import Column, Schema, Table


@dataclass
class SchemaDiff:
    """Holds the results of comparing two schema snapshots."""

    added_tables: List[str] = field(default_factory=list)
    removed_tables: List[str] = field(default_factory=list)
    # table_name -> {added, removed, modified columns}
    modified_tables: Dict[str, Dict] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return bool(
            self.added_tables or self.removed_tables or self.modified_tables
        )


def _diff_table(old: Table, new: Table) -> Dict:
    """Return column-level changes between two versions of the same table."""
    old_cols = set(old.columns.keys())
    new_cols = set(new.columns.keys())

    added = list(new_cols - old_cols)
    removed = list(old_cols - new_cols)
    modified: List[Dict] = []

    for col_name in old_cols & new_cols:
        old_col: Column = old.columns[col_name]
        new_col: Column = new.columns[col_name]
        if old_col != new_col:
            modified.append(
                {
                    "column": col_name,
                    "before": old_col,
                    "after": new_col,
                }
            )

    return {"added_columns": added, "removed_columns": removed, "modified_columns": modified}


def compute_diff(old: Schema, new: Schema) -> SchemaDiff:
    """Compute the drift between an old and a new schema snapshot."""
    diff = SchemaDiff()

    old_tables = set(old.tables.keys())
    new_tables = set(new.tables.keys())

    diff.added_tables = sorted(new_tables - old_tables)
    diff.removed_tables = sorted(old_tables - new_tables)

    for table_name in old_tables & new_tables:
        changes = _diff_table(old.tables[table_name], new.tables[table_name])
        if any(changes[k] for k in changes):
            diff.modified_tables[table_name] = changes

    return diff
