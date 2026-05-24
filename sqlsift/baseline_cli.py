"""CLI helpers for baseline sub-commands (save / compare)."""

from __future__ import annotations

import argparse
import sys

from sqlsift.loader import load_from_json
from sqlsift.baseline import save_baseline, list_baselines
from sqlsift.baseline_diff import diff_against_baseline, diff_two_baselines
from sqlsift.reporter import generate_report, ReportOptions


def _build_baseline_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlsift baseline",
        description="Manage schema baselines.",
    )
    sub = parser.add_subparsers(dest="subcommand", required=True)

    save_p = sub.add_parser("save", help="Save current schema as a baseline.")
    save_p.add_argument("schema", help="Path to schema JSON file.")
    save_p.add_argument("output", help="Destination baseline JSON file.")
    save_p.add_argument("--name", default="baseline", help="Baseline name.")
    save_p.add_argument("--description", default="", help="Optional description.")

    cmp_p = sub.add_parser("compare", help="Diff current schema against a baseline.")
    cmp_p.add_argument("schema", help="Path to current schema JSON file.")
    cmp_p.add_argument("baseline", help="Path to saved baseline JSON file.")
    cmp_p.add_argument("--color", action="store_true", help="Colorize output.")

    cmp2_p = sub.add_parser("compare-two", help="Diff two baseline files.")
    cmp2_p.add_argument("old", help="Older baseline JSON file.")
    cmp2_p.add_argument("new", help="Newer baseline JSON file.")
    cmp2_p.add_argument("--color", action="store_true", help="Colorize output.")

    list_p = sub.add_parser("list", help="List baselines in a directory.")
    list_p.add_argument("directory", help="Directory containing baseline files.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_baseline_parser()
    args = parser.parse_args(argv)

    if args.subcommand == "save":
        schema = load_from_json(args.schema)
        save_baseline(schema, args.output, name=args.name, description=args.description)
        print(f"Baseline saved to {args.output}")
        return 0

    if args.subcommand == "compare":
        current = load_from_json(args.schema)
        result = diff_against_baseline(current, args.baseline)
        opts = ReportOptions(use_color=args.color)
        print(generate_report(result.diff, opts))
        return 1 if result.has_drift else 0

    if args.subcommand == "compare-two":
        result = diff_two_baselines(args.old, args.new)
        opts = ReportOptions(use_color=args.color)
        print(generate_report(result.diff, opts))
        return 1 if result.has_drift else 0

    if args.subcommand == "list":
        paths = list_baselines(args.directory)
        if not paths:
            print("No baselines found.")
        for p in paths:
            print(p)
        return 0

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
