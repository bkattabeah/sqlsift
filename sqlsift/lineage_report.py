"""Render a lineage graph as text, JSON, or Markdown."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from sqlsift.lineage import LineageGraph


@dataclass
class LineageReportOptions:
    fmt: Literal["text", "json", "markdown"] = "text"
    include_reason: bool = True


def _fmt_text(graph: LineageGraph, opts: LineageReportOptions) -> str:
    if not graph.edges:
        return "No lineage edges found.\n"
    lines = ["Lineage Edges:", ""]
    for edge in graph.edges:
        src = f"{edge.source.snapshot_label}:{edge.source.table}.{edge.source.column}"
        tgt = f"{edge.target.snapshot_label}:{edge.target.table}.{edge.target.column}"
        reason_part = f" [{edge.reason}]" if opts.include_reason else ""
        lines.append(f"  {src} -> {tgt}{reason_part}")
    return "\n".join(lines) + "\n"


def _fmt_json(graph: LineageGraph, opts: LineageReportOptions) -> str:
    records = []
    for edge in graph.edges:
        rec = {
            "source": {
                "snapshot": edge.source.snapshot_label,
                "table": edge.source.table,
                "column": edge.source.column,
            },
            "target": {
                "snapshot": edge.target.snapshot_label,
                "table": edge.target.table,
                "column": edge.target.column,
            },
        }
        if opts.include_reason:
            rec["reason"] = edge.reason
        records.append(rec)
    return json.dumps({"edges": records}, indent=2)


def _fmt_markdown(graph: LineageGraph, opts: LineageReportOptions) -> str:
    if not graph.edges:
        return "_No lineage edges found._\n"
    header = "| Source | Target |"
    sep = "| --- | --- |"
    if opts.include_reason:
        header += " Reason |"
        sep += " --- |"
    lines = ["## Lineage Edges", "", header, sep]
    for edge in graph.edges:
        src = f"`{edge.source.snapshot_label}:{edge.source.table}.{edge.source.column}`"
        tgt = f"`{edge.target.snapshot_label}:{edge.target.table}.{edge.target.column}`"
        row = f"| {src} | {tgt} |"
        if opts.include_reason:
            row += f" {edge.reason} |"
        lines.append(row)
    return "\n".join(lines) + "\n"


def generate_lineage_report(
    graph: LineageGraph,
    opts: LineageReportOptions | None = None,
) -> str:
    if opts is None:
        opts = LineageReportOptions()
    if opts.fmt == "json":
        return _fmt_json(graph, opts)
    if opts.fmt == "markdown":
        return _fmt_markdown(graph, opts)
    return _fmt_text(graph, opts)
