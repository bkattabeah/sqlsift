"""Produce a concise summary of a SchemaDiff."""
from dataclasses import dataclass
from sqlsift.diff import SchemaDiff


@dataclass
class DiffSummary:
    added_tables: int
    removed_tables: int
    modified_tables: int
    added_columns: int
    removed_columns: int
    modified_columns: int

    @property
    def total_changes(self) -> int:
        return (
            self.added_tables
            + self.removed_tables
            + self.modified_tables
            + self.added_columns
            + self.removed_columns
            + self.modified_columns
        )

    def __str__(self) -> str:
        lines = [
            "Schema Diff Summary",
            "-------------------",
            f"  Tables added:      {self.added_tables}",
            f"  Tables removed:    {self.removed_tables}",
            f"  Tables modified:   {self.modified_tables}",
            f"  Columns added:     {self.added_columns}",
            f"  Columns removed:   {self.removed_columns}",
            f"  Columns modified:  {self.modified_columns}",
            f"  Total changes:     {self.total_changes}",
        ]
        return "\n".join(lines)


def summarize_diff(diff: SchemaDiff) -> DiffSummary:
    """Compute a DiffSummary from a SchemaDiff."""
    added_cols = removed_cols = modified_cols = 0
    for td in diff.modified_tables.values():
        added_cols += len(td.added_columns)
        removed_cols += len(td.removed_columns)
        modified_cols += len(td.modified_columns)
    return DiffSummary(
        added_tables=len(diff.added_tables),
        removed_tables=len(diff.removed_tables),
        modified_tables=len(diff.modified_tables),
        added_columns=added_cols,
        removed_columns=removed_cols,
        modified_columns=modified_cols,
    )
