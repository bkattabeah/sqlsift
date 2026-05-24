"""CLI entry-point for the sqlsift schema watcher."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from sqlsift.loader import load_from_json
from sqlsift.watcher import WatchOptions, watch
from sqlsift.reporter import ReportOptions, generate_report
from sqlsift.diff import SchemaDiff


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="sqlsift-watch",
        description="Watch a schema JSON file for drift.",
    )
    p.add_argument("schema", help="Path to schema JSON file to monitor.")
    p.add_argument(
        "--interval",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Poll interval in seconds (default: 60).",
    )
    p.add_argument(
        "--iterations",
        type=int,
        default=None,
        metavar="N",
        help="Stop after N iterations (useful for testing).",
    )
    p.add_argument(
        "--color",
        action="store_true",
        default=False,
        help="Colorize drift reports.",
    )
    return p


def _make_drift_handler(color: bool):
    def _on_drift(diff: SchemaDiff) -> None:
        report_opts = ReportOptions(use_color=color)
        print(generate_report(diff, report_opts))
    return _on_drift


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    schema_path: str = args.schema

    def loader():
        with open(schema_path) as fh:
            return load_from_json(fh.read())

    opts = WatchOptions(
        interval=args.interval,
        max_iterations=args.iterations,
        on_drift=_make_drift_handler(args.color),
    )

    try:
        watch(loader, opts)
    except KeyboardInterrupt:
        print("\n[sqlsift watcher] Stopped.", file=sys.stderr)

    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
