"""Threshold-based alerting for drift scores."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.scorer import DriftScore


@dataclass
class ThresholdOptions:
    warn_above: float = 0.3
    critical_above: float = 0.7
    ignore_tables: List[str] = field(default_factory=list)


@dataclass
class ThresholdAlert:
    level: str  # "ok", "warn", "critical"
    score: float
    message: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"ThresholdAlert(level={self.level!r}, score={self.score:.3f})"


def _level(score: float, opts: ThresholdOptions) -> str:
    if score >= opts.critical_above:
        return "critical"
    if score >= opts.warn_above:
        return "warn"
    return "ok"


def evaluate_threshold(
    drift_score: DriftScore,
    options: Optional[ThresholdOptions] = None,
) -> ThresholdAlert:
    """Return a ThresholdAlert describing whether the drift score breaches limits."""
    opts = options or ThresholdOptions()
    value = drift_score.score
    lvl = _level(value, opts)
    messages = {
        "ok": f"Drift score {value:.3f} is within acceptable limits.",
        "warn": f"Drift score {value:.3f} exceeds warn threshold ({opts.warn_above}).",
        "critical": f"Drift score {value:.3f} exceeds critical threshold ({opts.critical_above}).",
    }
    return ThresholdAlert(level=lvl, score=value, message=messages[lvl])
