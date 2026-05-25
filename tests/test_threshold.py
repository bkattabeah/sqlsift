"""Tests for sqlsift.threshold."""
import pytest

from sqlsift.scorer import DriftScore
from sqlsift.threshold import ThresholdOptions, ThresholdAlert, evaluate_threshold


def _score(value: float) -> DriftScore:
    return DriftScore(
        score=value,
        added_tables=0,
        removed_tables=0,
        modified_tables=0,
        added_columns=0,
        removed_columns=0,
        modified_columns=0,
    )


def test_ok_when_below_warn():
    alert = evaluate_threshold(_score(0.1))
    assert alert.level == "ok"


def test_warn_when_between_thresholds():
    alert = evaluate_threshold(_score(0.5))
    assert alert.level == "warn"


def test_critical_when_above_critical():
    alert = evaluate_threshold(_score(0.9))
    assert alert.level == "critical"


def test_score_stored_on_alert():
    alert = evaluate_threshold(_score(0.55))
    assert abs(alert.score - 0.55) < 1e-9


def test_message_contains_score():
    alert = evaluate_threshold(_score(0.5))
    assert "0.500" in alert.message


def test_custom_thresholds_respected():
    opts = ThresholdOptions(warn_above=0.1, critical_above=0.2)
    assert evaluate_threshold(_score(0.05), opts).level == "ok"
    assert evaluate_threshold(_score(0.15), opts).level == "warn"
    assert evaluate_threshold(_score(0.25), opts).level == "critical"


def test_exact_warn_boundary():
    opts = ThresholdOptions(warn_above=0.3, critical_above=0.7)
    assert evaluate_threshold(_score(0.3), opts).level == "warn"


def test_exact_critical_boundary():
    opts = ThresholdOptions(warn_above=0.3, critical_above=0.7)
    assert evaluate_threshold(_score(0.7), opts).level == "critical"
