"""Human-readable and JSON reports for a Schema Catalog."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from sqlsift.catalog import Catalog


@dataclass
class CatalogReportOptions:
    format: Literal["text", "json", "markdown"] = "text"
    show_tags: bool = True
    show_description: bool = True


def _fmt_text(catalog: Catalog, opts: CatalogReportOptions) -> str:
    lines: list[str] = ["Schema Catalog", "=" * 40]
    if not len(catalog):
        lines.append("(empty)")
        return "\n".join(lines)
    for entry in catalog:
        lines.append(f"  {entry.name}  ({len(entry.schema.tables)} tables)")
        if opts.show_description and entry.description:
            lines.append(f"    Description : {entry.description}")
        if opts.show_tags and entry.tags:
            lines.append(f"    Tags        : {', '.join(sorted(entry.tags))}")
    return "\n".join(lines)


def _fmt_json(catalog: Catalog, opts: CatalogReportOptions) -> str:
    data = []
    for entry in catalog:
        record: dict = {
            "name": entry.name,
            "table_count": len(entry.schema.tables),
        }
        if opts.show_description:
            record["description"] = entry.description
        if opts.show_tags:
            record["tags"] = sorted(entry.tags)
        data.append(record)
    return json.dumps(data, indent=2)


def _fmt_markdown(catalog: Catalog, opts: CatalogReportOptions) -> str:
    lines: list[str] = ["# Schema Catalog", ""]
    if not len(catalog):
        lines.append("_(empty)_")
        return "\n".join(lines)
    header = "| Name | Tables |"
    sep = "| --- | --- |"
    if opts.show_description:
        header += " Description |"
        sep += " --- |"
    if opts.show_tags:
        header += " Tags |"
        sep += " --- |"
    lines += [header, sep]
    for entry in catalog:
        row = f"| {entry.name} | {len(entry.schema.tables)} |"
        if opts.show_description:
            row += f" {entry.description} |"
        if opts.show_tags:
            row += f" {', '.join(sorted(entry.tags))} |"
        lines.append(row)
    return "\n".join(lines)


def generate_catalog_report(
    catalog: Catalog,
    opts: CatalogReportOptions | None = None,
) -> str:
    """Return a formatted string report for *catalog*."""
    if opts is None:
        opts = CatalogReportOptions()
    if opts.format == "json":
        return _fmt_json(catalog, opts)
    if opts.format == "markdown":
        return _fmt_markdown(catalog, opts)
    return _fmt_text(catalog, opts)
