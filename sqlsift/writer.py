"""Write exported diff content to files or stdout."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import IO, Optional

from sqlsift.diff import SchemaDiff
from sqlsift.exporter import ExportFormat, ExportOptions, export_diff

_EXTENSION_MAP: dict[str, ExportFormat] = {
    ".json": "json",
    ".md": "markdown",
    ".csv": "csv",
}


def _infer_format(path: Path) -> ExportFormat:
    """Infer export format from file extension."""
    ext = path.suffix.lower()
    if ext not in _EXTENSION_MAP:
        raise ValueError(
            f"Cannot infer format from extension {ext!r}. "
            f"Supported: {list(_EXTENSION_MAP.keys())}"
        )
    return _EXTENSION_MAP[ext]


def write_diff(
    diff: SchemaDiff,
    output: str | Path | None = None,
    options: ExportOptions | None = None,
) -> None:
    """
    Write a schema diff to a file or stdout.

    Args:
        diff: The SchemaDiff to export.
        output: File path to write to. If None, writes to stdout.
        options: Export options. If None, defaults are used. When output is a
                 file path and options.format is not set explicitly, the format
                 is inferred from the file extension.
    """
    if options is None:
        options = ExportOptions()

    if output is not None:
        output = Path(output)
        # Auto-detect format from extension when caller hasn't customised it
        if options.format == "json" and output.suffix.lower() in _EXTENSION_MAP:
            inferred = _infer_format(output)
            if inferred != options.format:
                options = ExportOptions(
                    format=inferred,
                    indent=options.indent,
                    include_unchanged=options.include_unchanged,
                )

    content = export_diff(diff, options)

    if output is None:
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
