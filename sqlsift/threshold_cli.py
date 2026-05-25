"""CLI entry point for threshold evaluation."""
from __future__ import annotations

import argparse
import sys

from sqlsift.loader import load_from_json
from sqlsift.diff import compute_diff
from sqlsift.scorer import ScorerOptions, score_diff
from sqlsift.threshold import ThresholdOptions, evaluate_threshold
from sqlsift.threshold_report import ThresholdReportOptions, generate_threshold_report


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlsift-threshold",
        description="Evaluate drift score against warn/critical thresholds.",
    )
    p.add_argument("old", help="Path to old schema JSON")
    p.add_argument("new", help="Path to new schema JSON")
    p.add_argument("--warn", type=float, default=0.3, metavar="W",
                   help="Warn threshold (default: 0.3)")
    p.add_argument("--critical", type=float, default=0.7, metavar="C",
                   help="Critical threshold (default: 0.7)")
    p.add_argument("--format", choices=["text", "json", "markdown"], default="text")
    p.add_argument("--color", action="store_true", default=False)
    return p


def main(argv=None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    with open(args.old) as fh:
        old_schema = load_from_json(fh.read())
    with open(args.new) as fh:
        new_schema = load_from_json(fh.read())

    diff = compute_diff(old_schema, new_schema)
    drift = score_diff(diff, ScorerOptions())
    threshold_opts = ThresholdOptions(warn_above=args.warn, critical_above=args.critical)
    alert = evaluate_threshold(drift, threshold_opts)

    report_opts = ThresholdReportOptions(format=args.format, color=args.color)
    print(generate_threshold_report(alert, report_opts))

    if alert.level == "critical":
        sys.exit(2)
    if alert.level == "warn":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":  # pragma: no cover
    main()
