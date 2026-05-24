"""Renders a MigrationPlan as text, JSON, or Markdown."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal

from sqlsift.planner import MigrationPlan


@dataclass
class PlanReportOptions:
    format: Literal["text", "json", "markdown"] = "text"
    show_phase_headers: bool = True


def _fmt_text(plan: MigrationPlan, options: PlanReportOptions) -> str:
    if not plan.phases:
        return "No migration steps required.\n"
    lines: list[str] = []
    for phase in plan.phases:
        if options.show_phase_headers:
            lines.append(f"-- Phase: {phase.name}")
        for stmt in phase.statements:
            lines.append(stmt)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _fmt_json(plan: MigrationPlan, _options: PlanReportOptions) -> str:
    payload = [
        {"phase": phase.name, "statements": phase.statements}
        for phase in plan.phases
    ]
    return json.dumps(payload, indent=2) + "\n"


def _fmt_markdown(plan: MigrationPlan, options: PlanReportOptions) -> str:
    if not plan.phases:
        return "_No migration steps required._\n"
    lines: list[str] = ["# Migration Plan", ""]
    for phase in plan.phases:
        if options.show_phase_headers:
            lines.append(f"## {phase.name.replace('_', ' ').title()}")
            lines.append("")
        lines.append("```sql")
        for stmt in phase.statements:
            lines.append(stmt)
        lines.append("```")
        lines.append("")
    return "\n".join(lines)


def generate_plan_report(
    plan: MigrationPlan,
    options: PlanReportOptions | None = None,
) -> str:
    """Return a formatted string representation of the migration plan."""
    options = options or PlanReportOptions()
    if options.format == "json":
        return _fmt_json(plan, options)
    if options.format == "markdown":
        return _fmt_markdown(plan, options)
    return _fmt_text(plan, options)
