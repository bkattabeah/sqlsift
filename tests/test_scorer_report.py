"""Tests for sqlsift.scorer_report."""
import json
import pytest

from sqlsift.scorer import DriftScore
from sqlsift.scorer_report import (
    ScorerReportOptions,
    generate_scorer_report,
)


def _make_score(**kwargs) -> DriftScore:
    defaults = dict(
        total=0,
        added_tables=0,
        removed_tables=0,
        added_columns=0,
        removed_columns=0,
        modified_columns=0,
    )
    defaults.update(kwargs)
    return DriftScore(**defaults)


def test_text_format_contains_score():
    score = _make_score(total=42, added_tables=2)
    report = generate_scorer_report(score)
    assert "42" in report


def test_text_format_contains_severity():
    score = _make_score(total=5, added_columns=1)
    report = generate_scorer_report(score)
    assert "Severity" in report


def test_text_format_breakdown_shown_by_default():
    score = _make_score(total=10, removed_columns=2)
    report = generate_scorer_report(score)
    assert "removed_columns" in report
    assert "2" in report


def test_text_format_breakdown_hidden_when_disabled():
    score = _make_score(total=10, removed_columns=2)
    opts = ScorerReportOptions(include_breakdown=False)
    report = generate_scorer_report(score, opts)
    assert "removed_columns" not in report


def test_json_format_is_valid_json():
    score = _make_score(total=7, modified_columns=3)
    opts = ScorerReportOptions(format="json")
    report = generate_scorer_report(score, opts)
    data = json.loads(report)
    assert data["total"] == 7


def test_json_format_breakdown_included():
    score = _make_score(total=7, modified_columns=3)
    opts = ScorerReportOptions(format="json")
    data = json.loads(generate_scorer_report(score, opts))
    assert "breakdown" in data
    assert data["breakdown"]["modified_columns"] == 3


def test_json_format_breakdown_omitted_when_disabled():
    score = _make_score(total=7, modified_columns=3)
    opts = ScorerReportOptions(format="json", include_breakdown=False)
    data = json.loads(generate_scorer_report(score, opts))
    assert "breakdown" not in data


def test_markdown_format_contains_header():
    score = _make_score(total=0)
    opts = ScorerReportOptions(format="markdown")
    report = generate_scorer_report(score, opts)
    assert "## Drift Score Report" in report


def test_markdown_format_contains_score():
    score = _make_score(total=15, added_tables=3)
    opts = ScorerReportOptions(format="markdown")
    report = generate_scorer_report(score, opts)
    assert "15" in report


def test_markdown_breakdown_section_present():
    score = _make_score(total=15, added_tables=3)
    opts = ScorerReportOptions(format="markdown")
    report = generate_scorer_report(score, opts)
    assert "Breakdown" in report


def test_unknown_format_raises():
    score = _make_score(total=0)
    opts = ScorerReportOptions(format="xml")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Unknown format"):
        generate_scorer_report(score, opts)


def test_default_opts_used_when_none_passed():
    score = _make_score(total=3, added_columns=1)
    report = generate_scorer_report(score, None)
    assert "Drift Score" in report
