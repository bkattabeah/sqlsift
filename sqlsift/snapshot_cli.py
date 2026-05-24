"""sqlsift.snapshot_cli — CLI for managing schema snapshots.

Usage examples::

    python -m sqlsift.snapshot_cli add schema.json --label v1
    python -m sqlsift.snapshot_cli diff snapshot_v1.json snapshot_v2.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sqlsift.loader import load_from_json
from sqlsift.snapshotter import (
    Snapshot,
    SnapshotStore,
    diff_snapshots,
    snapshot_to_dict,
    snapshot_from_dict,
)
from sqlsift.reporter import generate_report, ReportOptions


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlsift-snapshot",
        description="Manage and compare schema snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- add ---
    p_add = sub.add_parser("add", help="Capture a snapshot from a schema JSON file.")
    p_add.add_argument("schema", help="Path to schema JSON file.")
    p_add.add_argument("--label", default=None, help="Human-readable snapshot label.")
    p_add.add_argument("--out", required=True, help="Output path for the snapshot JSON.")

    # --- diff ---
    p_diff = sub.add_parser("diff", help="Diff two snapshot files.")
    p_diff.add_argument("older", help="Path to the older snapshot JSON.")
    p_diff.add_argument("newer", help="Path to the newer snapshot JSON.")
    p_diff.add_argument("--no-color", action="store_true", help="Disable ANSI colour.")

    return parser


def _cmd_add(args: argparse.Namespace) -> int:
    schema = load_from_json(args.schema)
    store = SnapshotStore()
    snap = store.add(schema, label=args.label)
    data = snapshot_to_dict(snap)
    Path(args.out).write_text(json.dumps(data, indent=2))
    print(f"Snapshot '{snap.label}' saved to {args.out}")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    older_data = json.loads(Path(args.older).read_text())
    newer_data = json.loads(Path(args.newer).read_text())
    older = snapshot_from_dict(older_data)
    newer = snapshot_from_dict(newer_data)
    diff = diff_snapshots(older, newer)
    opts = ReportOptions(use_color=not args.no_color)
    report = generate_report(diff, opts)
    print(report)
    return 1 if diff.has_changes() else 0


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handlers = {"add": _cmd_add, "diff": _cmd_diff}
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":  # pragma: no cover
    main()
