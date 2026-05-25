"""Render a DriftScore as text, JSON, or Markdown."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Literal

from .scorer import DriftScore


@dataclass
class ScorerReportOptions:
    format: Literal["text", "json", "markdown"] = "text"
    include_breakdown: bool = True
    color: bool = False


_SEVERITY_COLOR = {
    "none": "\033[32m",
    "low": "\033[36m",
    "medium": "\033[33m",
    "high": "\033[31m",
    "critical": "\033[35m",
}
_RESET = "\033[0m"


def _colorize(text: str, severity: str, use_color: bool) -> str:
    if not use_color:
        return text
    code = _SEVERITY_COLOR.get(severity, "")
    return f"{code}{text}{_RESET}" if code else text


def _fmt_text(score: DriftScore, opts: ScorerReportOptions) -> str:
    sev = score.severity
    lines = [
        f"Drift Score : {_colorize(str(score.total), sev, opts.color)}",
        f"Severity    : {_colorize(sev.upper(), sev, opts.color)}",
    ]
    if opts.include_breakdown:
        lines.append("Breakdown:")
        lines.append(f"  added_tables    : {score.added_tables}")
        lines.append(f"  removed_tables  : {score.removed_tables}")
        lines.append(f"  added_columns   : {score.added_columns}")
        lines.append(f"  removed_columns : {score.removed_columns}")
        lines.append(f"  modified_columns: {score.modified_columns}")
    return "\n".join(lines)


def _fmt_json(score: DriftScore, opts: ScorerReportOptions) -> str:
    data: dict = {
        "total": score.total,
        "severity": score.severity,
    }
    if opts.include_breakdown:
        data["breakdown"] = {
            "added_tables": score.added_tables,
            "removed_tables": score.removed_tables,
            "added_columns": score.added_columns,
            "removed_columns": score.removed_columns,
            "modified_columns": score.modified_columns,
        }
    return json.dumps(data, indent=2)


def _fmt_markdown(score: DriftScore, opts: ScorerReportOptions) -> str:
    sev = score.severity
    lines = [
        "## Drift Score Report",
        "",
        f"| Metric | Value |",
        "|--------|-------|}",
        f"| **Total Score** | `{score.total}` |",
        f"| **Severity** | `{sev.upper()}` |",
    ]
    if opts.include_breakdown:
        lines += [
            "",
            "### Breakdown",
            "",
            "| Change Type | Count |",
            "|-------------|-------|}",
            f"| Added Tables | {score.added_tables} |",
            f"| Removed Tables | {score.removed_tables} |",
            f"| Added Columns | {score.added_columns} |",
            f"| Removed Columns | {score.removed_columns} |",
            f"| Modified Columns | {score.modified_columns} |",
        ]
    return "\n".join(lines)


def generate_scorer_report(score: DriftScore, opts: ScorerReportOptions | None = None) -> str:
    """Return a formatted report string for *score*."""
    if opts is None:
        opts = ScorerReportOptions()
    dispatch = {"text": _fmt_text, "json": _fmt_json, "markdown": _fmt_markdown}
    fmt = dispatch.get(opts.format)
    if fmt is None:
        raise ValueError(f"Unknown format: {opts.format!r}")
    return fmt(score, opts)
