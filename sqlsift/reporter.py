"""Human-readable report generation for schema diffs."""

from dataclasses import dataclass
from typing import Optional
from sqlsift.diff import SchemaDiff


@dataclass
class ReportOptions:
    include_unchanged: bool = False
    use_color: bool = True
    indent: str = "  "


ANSI_RED = "\033[91m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RESET = "\033[0m"


def _colorize(text: str, color: str, use_color: bool) -> str:
    if not use_color:
        return text
    return f"{color}{text}{ANSI_RESET}"


def _append_section(lines: list, title: str, items: list) -> None:
    """Append a titled section to lines only if items is non-empty."""
    if items:
        lines.append(title)
        lines.extend(items)


def generate_report(diff: SchemaDiff, options: Optional[ReportOptions] = None) -> str:
    """Generate a human-readable report from a SchemaDiff.

    Args:
        diff: The SchemaDiff object describing changes between two schemas.
        options: Optional ReportOptions controlling formatting and color output.

    Returns:
        A formatted string summarizing added, removed, and modified tables.
    """
    if options is None:
        options = ReportOptions()

    lines = []
    indent = options.indent

    if not diff.has_changes():
        lines.append("No schema changes detected.")
        return "\n".join(lines)

    added_lines = [
        f"{indent}" + _colorize(f"+ {table_name}", ANSI_GREEN, options.use_color)
        for table_name in sorted(diff.added_tables)
    ]
    _append_section(lines, "Added tables:", added_lines)

    removed_lines = [
        f"{indent}" + _colorize(f"- {table_name}", ANSI_RED, options.use_color)
        for table_name in sorted(diff.removed_tables)
    ]
    _append_section(lines, "Removed tables:", removed_lines)

    if diff.modified_tables:
        lines.append("Modified tables:")
        for table_name, table_diff in sorted(diff.modified_tables.items()):
            lines.append(f"{indent}~ {table_name}:")
            for col in sorted(table_diff.added_columns):
                lines.append(f"{indent}{indent}" + _colorize(f"+ column: {col}", ANSI_GREEN, options.use_color))
            for col in sorted(table_diff.removed_columns):
                lines.append(f"{indent}{indent}" + _colorize(f"- column: {col}", ANSI_RED, options.use_color))
            for col, change in sorted(table_diff.modified_columns.items()):
                msg = f"~ column: {col} ({change.old_type} -> {change.new_type})"
                lines.append(f"{indent}{indent}" + _colorize(msg, ANSI_YELLOW, options.use_color))

    return "\n".join(lines)
