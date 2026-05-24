"""Export a TaggedSchema to JSON or Markdown for inspection."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from sqlsift.tagger import TaggedSchema


@dataclass
class TagExportOptions:
    format: Literal["json", "markdown"] = "json"
    include_empty_tags: bool = True


def _to_dict(schema: TaggedSchema, include_empty: bool) -> dict:
    tables = []
    for table in schema.tables:
        if not include_empty and not table.tags:
            cols_with_tags = [c for c in table.columns if c.tags]
            if not cols_with_tags:
                continue
        cols = []
        for col in table.columns:
            if not include_empty and not col.tags:
                continue
            cols.append(
                {
                    "name": col.name,
                    "data_type": col.data_type,
                    "tags": col.tags,
                }
            )
        tables.append({"table": table.name, "tags": table.tags, "columns": cols})
    return {"tagged_schema": tables}


def _to_markdown(schema: TaggedSchema, include_empty: bool) -> str:
    lines = ["# Tagged Schema\n"]
    for table in schema.tables:
        if not include_empty and not table.tags:
            cols_with_tags = [c for c in table.columns if c.tags]
            if not cols_with_tags:
                continue
        tag_str = ", ".join(f"`{t}`" for t in table.tags) if table.tags else "_none_"
        lines.append(f"## {table.name}")
        lines.append(f"**Table tags:** {tag_str}\n")
        lines.append("| Column | Type | Tags |")
        lines.append("|--------|------|------|")
        for col in table.columns:
            if not include_empty and not col.tags:
                continue
            col_tags = ", ".join(col.tags) if col.tags else ""
            lines.append(f"| {col.name} | {col.data_type} | {col_tags} |")
        lines.append("")
    return "\n".join(lines)


def export_tags(schema: TaggedSchema, options: TagExportOptions | None = None) -> str:
    """Serialise *schema* tags to the format specified in *options*."""
    if options is None:
        options = TagExportOptions()
    if options.format == "json":
        data = _to_dict(schema, options.include_empty_tags)
        return json.dumps(data, indent=2)
    if options.format == "markdown":
        return _to_markdown(schema, options.include_empty_tags)
    raise ValueError(f"Unsupported format: {options.format!r}")
