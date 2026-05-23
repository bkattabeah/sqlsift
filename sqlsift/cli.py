"""Minimal CLI entry-point for sqlsift."""
import argparse
import sys
from sqlsift.loader import load_from_json
from sqlsift.diff import compute_diff
from sqlsift.validator import validate_schema
from sqlsift.writer import write_diff
from sqlsift.reporter import generate_report, ReportOptions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlsift",
        description="Detect schema drift between two SQL database snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    diff_p = sub.add_parser("diff", help="Compute diff between two schema snapshots.")
    diff_p.add_argument("old", help="Path to old schema JSON file.")
    diff_p.add_argument("new", help="Path to new schema JSON file.")
    diff_p.add_argument("-o", "--output", help="Write diff to file (format inferred from extension).")
    diff_p.add_argument("--no-color", action="store_true", help="Disable colored output.")

    val_p = sub.add_parser("validate", help="Validate a schema snapshot.")
    val_p.add_argument("schema", help="Path to schema JSON file.")

    return parser


def _cmd_diff(args) -> int:
    old_schema = load_from_json(args.old)
    new_schema = load_from_json(args.new)
    diff = compute_diff(old_schema, new_schema)
    opts = ReportOptions(use_color=not args.no_color)
    if args.output:
        write_diff(diff, args.output)
        print(f"Diff written to {args.output}")
    else:
        print(generate_report(diff, opts))
    return 0


def _cmd_validate(args) -> int:
    schema = load_from_json(args.schema)
    result = validate_schema(schema)
    for issue in result.issues:
        print(repr(issue))
    if result.is_valid:
        print("Schema is valid.")
        return 0
    print(f"{len(result.errors)} error(s) found.", file=sys.stderr)
    return 1


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "diff":
        return _cmd_diff(args)
    if args.command == "validate":
        return _cmd_validate(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
