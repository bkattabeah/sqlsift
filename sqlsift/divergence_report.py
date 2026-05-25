"""Render a DivergenceReport as text, JSON, or Markdown."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from sqlsift.divergence import DivergenceReport


@dataclass
class DivergenceReportOptions:
    format: Literal["text", "json", "markdown"] = "text"
    show_zero_points: bool = True


def _fmt_text(report: DivergenceReport, opts: DivergenceReportOptions) -> str:
    lines = ["Schema Divergence Report", "=" * 26]
    points = [
        p for p in report.points if opts.show_zero_points or p.total > 0
    ]
    if not points:
        lines.append("No divergence detected.")
        return "\n".join(lines)
    for p in points:
        lines.append(f"  {p.label}")
        lines.append(f"    tables  : +{p.added_tables} / -{p.removed_tables} / ~{p.modified_tables}")
        lines.append(f"    columns : +{p.added_columns} / -{p.removed_columns} / ~{p.modified_columns}")
        lines.append(f"    total   : {p.total}")
    lines.append("")
    lines.append(f"Total drift: {report.total_drift}")
    if report.peak:
        lines.append(f"Peak point: {report.peak.label} ({report.peak.total} changes)")
    return "\n".join(lines)


def _fmt_json(report: DivergenceReport, opts: DivergenceReportOptions) -> str:
    points = [
        p for p in report.points if opts.show_zero_points or p.total > 0
    ]
    data = {
        "total_drift": report.total_drift,
        "peak": report.peak.label if report.peak else None,
        "points": [
            {
                "label": p.label,
                "added_tables": p.added_tables,
                "removed_tables": p.removed_tables,
                "modified_tables": p.modified_tables,
                "added_columns": p.added_columns,
                "removed_columns": p.removed_columns,
                "modified_columns": p.modified_columns,
                "total": p.total,
            }
            for p in points
        ],
    }
    return json.dumps(data, indent=2)


def _fmt_markdown(report: DivergenceReport, opts: DivergenceReportOptions) -> str:
    lines = ["# Schema Divergence Report", ""]
    points = [
        p for p in report.points if opts.show_zero_points or p.total > 0
    ]
    if not points:
        lines.append("_No divergence detected._")
        return "\n".join(lines)
    lines.append("| Transition | +Tables | -Tables | ~Tables | +Cols | -Cols | ~Cols | Total |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for p in points:
        lines.append(
            f"| {p.label} | {p.added_tables} | {p.removed_tables} |"
            f" {p.modified_tables} | {p.added_columns} | {p.removed_columns} |"
            f" {p.modified_columns} | {p.total} |"
        )
    lines.append("")
    lines.append(f"**Total drift:** {report.total_drift}")
    return "\n".join(lines)


def generate_divergence_report(
    report: DivergenceReport,
    opts: DivergenceReportOptions | None = None,
) -> str:
    if opts is None:
        opts = DivergenceReportOptions()
    if opts.format == "json":
        return _fmt_json(report, opts)
    if opts.format == "markdown":
        return _fmt_markdown(report, opts)
    return _fmt_text(report, opts)
