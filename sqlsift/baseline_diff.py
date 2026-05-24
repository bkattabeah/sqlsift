"""Compare the current schema against a saved baseline."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from sqlsift.baseline import Baseline, load_baseline
from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.schema import Schema
from sqlsift.loader import load_from_json


@dataclass
class BaselineDiffResult:
    baseline_name: str
    baseline_created_at: str
    diff: SchemaDiff

    @property
    def has_drift(self) -> bool:
        return self.diff.has_changes()


def diff_against_baseline(
    current: Schema,
    baseline_path: str,
) -> BaselineDiffResult:
    """Load *baseline_path* and diff *current* schema against it."""
    baseline: Baseline = load_baseline(baseline_path)
    diff = compute_diff(baseline.schema, current)
    return BaselineDiffResult(
        baseline_name=baseline.metadata.name,
        baseline_created_at=baseline.metadata.created_at,
        diff=diff,
    )


def diff_two_baselines(
    old_path: str,
    new_path: str,
) -> BaselineDiffResult:
    """Compare two baseline files directly."""
    old_baseline = load_baseline(old_path)
    new_baseline = load_baseline(new_path)
    diff = compute_diff(old_baseline.schema, new_baseline.schema)
    return BaselineDiffResult(
        baseline_name=f"{old_baseline.metadata.name} -> {new_baseline.metadata.name}",
        baseline_created_at=new_baseline.metadata.created_at,
        diff=diff,
    )
