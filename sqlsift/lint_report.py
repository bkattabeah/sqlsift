"""Format LintIssue lists into human-readable or machine-readable output."""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Literal

from sqlsift.linter import LintIssue


@dataclass
class LintReportOptions:
    fmt: Literal["text", "json", "markdown"] = "text"
    color: bool = False


_SEVERITY: dict = {
    "E001": "warning",
    "E002": "warning",
    "E003": "error",
    "E004": "warning",
    "E005": "error",
}

_ANSI = {"error": "\033[31m", "warning": "\033[33m", "reset": "\033[0m"}


def _severity(code: str) -> str:
    return _SEVERITY.get(code, "info")


def _fmt_text(issues: List[LintIssue], color: bool) -> str:
    if not issues:
        return "No lint issues found.\n"
    lines = []
    for issue in issues:
        loc = f"{issue.table}.{issue.column}" if issue.column else issue.table
        sev = _severity(issue.code)
        line = f"[{issue.code}] {sev.upper()} {loc}: {issue.message}"
        if color:
            c = _ANSI.get(sev, "")
            line = f"{c}{line}{_ANSI['reset']}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def _fmt_json(issues: List[LintIssue]) -> str:
    import json
    records = [
        {
            "code": i.code,
            "severity": _severity(i.code),
            "table": i.table,
            "column": i.column,
            "message": i.message,
        }
        for i in issues
    ]
    return json.dumps(records, indent=2)


def _fmt_markdown(issues: List[LintIssue]) -> str:
    if not issues:
        return "_No lint issues found._\n"
    lines = ["| Code | Severity | Location | Message |",
             "|------|----------|----------|---------|"]  
    for issue in issues:
        loc = f"{issue.table}.{issue.column}" if issue.column else issue.table
        sev = _severity(issue.code)
        lines.append(f"| {issue.code} | {sev} | {loc} | {issue.message} |")
    return "\n".join(lines) + "\n"


def format_lint_report(issues: List[LintIssue],
                       opts: LintReportOptions | None = None) -> str:
    """Return a formatted string representation of *issues*."""
    if opts is None:
        opts = LintReportOptions()
    if opts.fmt == "json":
        return _fmt_json(issues)
    if opts.fmt == "markdown":
        return _fmt_markdown(issues)
    return _fmt_text(issues, color=opts.color)
