"""Render a :class:`DriftHeatmap` as text, JSON, or Markdown."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from sqlsift.heatmap import DriftHeatmap


@dataclass
class HeatmapReportOptions:
    format: Literal["text", "json", "markdown"] = "text"
    top_n: int = 10
    show_appearances: bool = True


def _fmt_text(heatmap: DriftHeatmap, opts: HeatmapReportOptions) -> str:
    lines = ["Drift Heatmap", "=" * 40]
    entries = heatmap.hottest(opts.top_n)
    if not entries:
        lines.append("  (no changes recorded)")
        return "\n".join(lines)
    for rank, entry in enumerate(entries, 1):
        line = f"  {rank:>3}. {entry.table:<30} changes={entry.change_count}"
        if opts.show_appearances:
            line += f"  diffs={entry.diff_appearances}"
        lines.append(line)
    return "\n".join(lines)


def _fmt_json(heatmap: DriftHeatmap, opts: HeatmapReportOptions) -> str:
    entries = heatmap.hottest(opts.top_n)
    data = [
        {
            "table": e.table,
            "change_count": e.change_count,
            "diff_appearances": e.diff_appearances,
        }
        for e in entries
    ]
    return json.dumps({"heatmap": data}, indent=2)


def _fmt_markdown(heatmap: DriftHeatmap, opts: HeatmapReportOptions) -> str:
    lines = ["## Drift Heatmap", ""]
    entries = heatmap.hottest(opts.top_n)
    if not entries:
        lines.append("_No changes recorded._")
        return "\n".join(lines)
    header = "| Rank | Table | Changes |"
    sep = "|------|-------|--------|"
    if opts.show_appearances:
        header += " Diffs |"
        sep += "-------|"
    lines += [header, sep]
    for rank, entry in enumerate(entries, 1):
        row = f"| {rank} | {entry.table} | {entry.change_count} |"
        if opts.show_appearances:
            row += f" {entry.diff_appearances} |"
        lines.append(row)
    return "\n".join(lines)


def generate_heatmap_report(
    heatmap: DriftHeatmap,
    opts: HeatmapReportOptions | None = None,
) -> str:
    """Return a formatted report string for *heatmap*."""
    if opts is None:
        opts = HeatmapReportOptions()
    if opts.format == "json":
        return _fmt_json(heatmap, opts)
    if opts.format == "markdown":
        return _fmt_markdown(heatmap, opts)
    return _fmt_text(heatmap, opts)
