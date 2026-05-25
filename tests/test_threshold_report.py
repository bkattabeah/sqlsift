"""Tests for sqlsift.threshold_report."""
import json
import pytest

from sqlsift.threshold import ThresholdAlert
from sqlsift.threshold_report import (
    ThresholdReportOptions,
    generate_threshold_report,
)


def _alert(level: str, score: float = 0.5) -> ThresholdAlert:
    return ThresholdAlert(level=level, score=score, message=f"Score {score:.3f} — {level}")


def test_text_format_contains_level():
    report = generate_threshold_report(_alert("warn"))
    assert "WARN" in report


def test_text_format_contains_message():
    report = generate_threshold_report(_alert("ok", 0.1))
    assert "0.100" in report


def test_json_format_is_valid_json():
    opts = ThresholdReportOptions(format="json")
    report = generate_threshold_report(_alert("critical", 0.8), opts)
    data = json.loads(report)
    assert data["level"] == "critical"
    assert abs(data["score"] - 0.8) < 1e-6


def test_json_format_has_message_key():
    opts = ThresholdReportOptions(format="json")
    data = json.loads(generate_threshold_report(_alert("ok"), opts))
    assert "message" in data


def test_markdown_contains_heading():
    opts = ThresholdReportOptions(format="markdown")
    report = generate_threshold_report(_alert("warn"), opts)
    assert "## Threshold Alert" in report


def test_markdown_ok_has_checkmark():
    opts = ThresholdReportOptions(format="markdown")
    report = generate_threshold_report(_alert("ok"), opts)
    assert "✅" in report


def test_markdown_critical_has_siren():
    opts = ThresholdReportOptions(format="markdown")
    report = generate_threshold_report(_alert("critical"), opts)
    assert "🚨" in report


def test_color_flag_adds_escape_codes():
    opts = ThresholdReportOptions(format="text", color=True)
    report = generate_threshold_report(_alert("critical"), opts)
    assert "\033[" in report


def test_no_color_by_default():
    report = generate_threshold_report(_alert("warn"))
    assert "\033[" not in report
