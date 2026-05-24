"""Schema linting: enforce naming conventions and structural best practices."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.schema import Schema


@dataclass
class LintOptions:
    require_primary_key: bool = True
    column_name_pattern: Optional[str] = None  # regex, e.g. r'^[a-z_][a-z0-9_]*$'
    table_name_pattern: Optional[str] = None
    max_columns_per_table: int = 100
    disallow_nullable_primary_key: bool = True


@dataclass
class LintIssue:
    table: str
    column: Optional[str]
    code: str
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        loc = f"{self.table}.{self.column}" if self.column else self.table
        return f"LintIssue({self.code}, {loc!r}: {self.message})"


def _check_table(table, opts: LintOptions) -> List[LintIssue]:
    import re

    issues: List[LintIssue] = []

    if opts.table_name_pattern and not re.match(opts.table_name_pattern, table.name):
        issues.append(LintIssue(
            table=table.name, column=None,
            code="E001",
            message=f"Table name '{table.name}' does not match pattern '{opts.table_name_pattern}'",
        ))

    if len(table.columns) > opts.max_columns_per_table:
        issues.append(LintIssue(
            table=table.name, column=None,
            code="E002",
            message=f"Table has {len(table.columns)} columns, exceeds max {opts.max_columns_per_table}",
        ))

    pk_cols = [c for c in table.columns.values() if getattr(c, 'primary_key', False)]

    if opts.require_primary_key and not pk_cols:
        issues.append(LintIssue(
            table=table.name, column=None,
            code="E003",
            message="Table has no primary key column",
        ))

    for col in table.columns.values():
        if opts.column_name_pattern and not re.match(opts.column_name_pattern, col.name):
            issues.append(LintIssue(
                table=table.name, column=col.name,
                code="E004",
                message=f"Column name '{col.name}' does not match pattern '{opts.column_name_pattern}'",
            ))

        if opts.disallow_nullable_primary_key and getattr(col, 'primary_key', False) and col.nullable:
            issues.append(LintIssue(
                table=table.name, column=col.name,
                code="E005",
                message=f"Primary key column '{col.name}' is nullable",
            ))

    return issues


def lint_schema(schema: Schema, opts: Optional[LintOptions] = None) -> List[LintIssue]:
    """Return a list of LintIssues found in *schema*."""
    if opts is None:
        opts = LintOptions()
    issues: List[LintIssue] = []
    for table in schema.tables.values():
        issues.extend(_check_table(table, opts))
    return issues
