"""CLI entry-point: sqlsift-score — compute and display a drift score."""
from __future__ import annotations

import argparse
import sys

from .loader import load_from_json
from .diff import compute_diff
from .scorer import ScorerOptions, score_diff
from .scorer_report import ScorerReportOptions, generate_scorer_report


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlsift-score",
        description="Compute a numeric drift score between two schema snapshots.",
    )
    p.add_argument("old", help="Path to the old schema JSON file.")
    p.add_argument("new", help="Path to the new schema JSON file.")
    p.add_argument(
        "--format",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    p.add_argument(
        "--no-breakdown",
        action="store_true",
        help="Omit per-change-type breakdown from the report.",
    )
    p.add_argument(
        "--color",
        action="store_true",
        help="Colorize text output by severity.",
    )
    p.add_argument(
        "--weights",
        metavar="KEY=VAL",
        nargs="*",
        default=[],
        help="Override scorer weights, e.g. added_table=5 removed_table=10.",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 if drift is detected (score > 0).",
    )
    return p


def _parse_weights(pairs: list[str]) -> dict[str, int]:
    out: dict[str, int] = {}
    for pair in pairs:
        key, _, val = pair.partition("=")
        out[key.strip()] = int(val.strip())
    return out


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    with open(args.old) as fh:
        old_schema = load_from_json(fh.read())
    with open(args.new) as fh:
        new_schema = load_from_json(fh.read())

    diff = compute_diff(old_schema, new_schema)

    weight_overrides = _parse_weights(args.weights or [])
    scorer_kwargs = {
        k: v
        for k, v in weight_overrides.items()
        if k in ScorerOptions.__dataclass_fields__  # type: ignore[attr-defined]
    }
    scorer_opts = ScorerOptions(**scorer_kwargs)
    score = score_diff(diff, scorer_opts)

    report_opts = ScorerReportOptions(
        format=args.format,
        include_breakdown=not args.no_breakdown,
        color=args.color,
    )
    print(generate_scorer_report(score, report_opts))

    if args.exit_code and score.total > 0:
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
