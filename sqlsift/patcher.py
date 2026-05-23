"""Generate SQL patch statements from a SchemaDiff."""

from dataclasses import dataclass, field
from typing import List

from sqlsift.diff import SchemaDiff


@dataclass
class PatchOptions:
    dialect: str = "generic"  # future: mysql, postgres, sqlite
    include_drop_table: bool = True
    include_drop_column: bool = True


def _quote(name: str) -> str:
    return f'"{name}"'


def _col_def(col) -> str:
    parts = [_quote(col.name), col.data_type.upper()]
    if not col.nullable:
        parts.append("NOT NULL")
    if col.default is not None:
        parts.append(f"DEFAULT {col.default}")
    return " ".join(parts)


def generate_patch(diff: SchemaDiff, options: PatchOptions | None = None) -> List[str]:
    """Return a list of SQL DDL statements that migrate old schema to new."""
    if options is None:
        options = PatchOptions()

    statements: List[str] = []

    for table_name in diff.added_tables:
        table = diff.new_schema.tables[table_name]
        col_defs = ", ".join(_col_def(c) for c in table.columns.values())
        statements.append(
            f"CREATE TABLE {_quote(table_name)} ({col_defs});"
        )

    if options.include_drop_table:
        for table_name in diff.removed_tables:
            statements.append(f"DROP TABLE {_quote(table_name)};")

    for table_name, table_diff in diff.modified_tables.items():
        for col_name in table_diff.get("added_columns", []):
            col = diff.new_schema.tables[table_name].columns[col_name]
            statements.append(
                f"ALTER TABLE {_quote(table_name)} ADD COLUMN {_col_def(col)};"
            )

        if options.include_drop_column:
            for col_name in table_diff.get("removed_columns", []):
                statements.append(
                    f"ALTER TABLE {_quote(table_name)} DROP COLUMN {_quote(col_name)};"
                )

        for col_name, changes in table_diff.get("modified_columns", {}).items():
            if "data_type" in changes:
                new_type = changes["data_type"]["new"].upper()
                statements.append(
                    f"ALTER TABLE {_quote(table_name)} "
                    f"ALTER COLUMN {_quote(col_name)} TYPE {new_type};"
                )

    return statements
