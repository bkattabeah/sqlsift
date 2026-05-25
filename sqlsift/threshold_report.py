"""Reporting for threshold alerts."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Optional

from sqlsift.threshold import ThresholdAlert


@dataclass
class ThresholdReportOptions:
    format: str = "text"  # "text", "json", "markdown"
    color: bool = False


_LEVEL_COLORS = {"ok": "\033[32m", "warn": "\033[33m", "critical": "\033[31m"}
_RESET = "\033[0m"


def _colorize(text: str, level: str, color: bool) -> str:
    if not color:
        return text
    return f"{_LEVEL_COLORS.get(level, '')}{text}{_RESET}"


def _fmt_text(alert: ThresholdAlert, opts: ThresholdReportOptions) -> str:
    level_str = _colorize(alert.level.upper(), alert.level, opts.color)
    return f"[{level_str}] {alert.message}"


def _fmt_json(alert: ThresholdAlert) -> str:
    return json.dumps(
        {"level": alert.level, "score": round(alert.score, 6), "message": alert.message},
        indent=2,
    )


def _fmt_markdown(alert: ThresholdAlert) -> str:
    emoji = {"ok": "✅", "warn": "⚠️", "critical": "🚨"}.get(alert.level, "")
    return f"## Threshold Alert\n\n{emoji} **{alert.level.upper()}** — {alert.message}\n"


def generate_threshold_report(
    alert: ThresholdAlert,
    options: Optional[ThresholdReportOptions] = None,
) -> str:
    """Render a threshold alert as a formatted report string."""
    opts = options or ThresholdReportOptions()
    if opts.format == "json":
        return _fmt_json(alert)
    if opts.format == "markdown":
        return _fmt_markdown(alert)
    return _fmt_text(alert, opts)
