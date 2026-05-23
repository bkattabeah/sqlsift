"""Export schema diffs to various output formats (JSON, Markdown, CSV)."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict, dataclass
from typing import Literal

from sqlsift.diff import SchemaDiff

ExportFormat = Literal["json", "markdown", "csv"]


@dataclass
class ExportOptions:
    format: ExportFormat = "json"
    indent: int = 2  # used for JSON
    include_unchanged: bool = False


def _diff_to_records(diff: SchemaDiff) -> list[dict]:
    """Flatten a SchemaDiff into a list of change records."""
    records: list[dict] = []

    for table_name in diff.added_tables:
        records.append({"change": "added_table", "table": table_name, "column": "", "detail": ""})

    for table_name in diff.removed_tables:
        records.append({"change": "removed_table", "table": table_name, "column": "", "detail": ""})

    for table_name, table_diff in diff.modified_tables.items():
        for col in table_diff.added_columns:
            records.append({"change": "added_column", "table": table_name, "column": col.name, "detail": col.col_type})
        for col in table_diff.removed_columns:
            records.append({"change": "removed_column", "table": table_name, "column": col.name, "detail": col.col_type})
        for col_name, (old_col, new_col) in table_diff.modified_columns.items():
            detail = f"{old_col.col_type} -> {new_col.col_type}"
            records.append({"change": "modified_column", "table": table_name, "column": col_name, "detail": detail})

    return records


def _export_json(diff: SchemaDiff, options: ExportOptions) -> str:
    records = _diff_to_records(diff)
    return json.dumps(records, indent=options.indent)


def _export_markdown(diff: SchemaDiff, options: ExportOptions) -> str:
    records = _diff_to_records(diff)
    lines = ["| Change | Table | Column | Detail |", "|--------|-------|--------|--------|"]
    for r in records:
        lines.append(f"| {r['change']} | {r['table']} | {r['column']} | {r['detail']} |")
    if not records:
        lines.append("| — | — | — | No changes detected |")
    return "\n".join(lines)


def _export_csv(diff: SchemaDiff, options: ExportOptions) -> str:
    records = _diff_to_records(diff)
    output = io.StringIO()
    fieldnames = ["change", "table", "column", "detail"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def export_diff(diff: SchemaDiff, options: ExportOptions | None = None) -> str:
    """Export a SchemaDiff to the specified format string."""
    if options is None:
        options = ExportOptions()

    if options.format == "json":
        return _export_json(diff, options)
    elif options.format == "markdown":
        return _export_markdown(diff, options)
    elif options.format == "csv":
        return _export_csv(diff, options)
    else:
        raise ValueError(f"Unsupported export format: {options.format!r}")
