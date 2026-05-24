"""CLI entry-point for the sqlsift audit sub-command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlsift.auditor import load_audit_log, record_audit
from sqlsift.diff import compute_diff
from sqlsift.loader import load_from_json


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sqlsift-audit",
        description="Record and review schema-diff audit logs.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # record sub-command
    rec = sub.add_parser("record", help="Diff two schemas and append an audit entry.")
    rec.add_argument("before", help="Path to the 'before' schema JSON file.")
    rec.add_argument("after", help="Path to the 'after' schema JSON file.")
    rec.add_argument("--log", default="audit.jsonl", help="Audit log file (JSONL).")
    rec.add_argument("--actor", default="unknown", help="Name of the actor performing the diff.")
    rec.add_argument("--label", default=None, help="Optional baseline label.")

    # list sub-command
    lst = sub.add_parser("list", help="Print all entries in an audit log.")
    lst.add_argument("log", help="Path to the audit log JSONL file.")
    lst.add_argument("--only-changes", action="store_true", help="Show only entries with changes.")

    return parser


def _cmd_record(args: argparse.Namespace) -> int:
    before = load_from_json(args.before)
    after = load_from_json(args.after)
    diff = compute_diff(before, after)
    entry = record_audit(
        diff,
        path=Path(args.log),
        actor=args.actor,
        baseline_label=args.label,
    )
    status = "CHANGED" if entry.has_changes else "NO CHANGE"
    print(f"[{status}] entry {entry.entry_id} recorded by {entry.actor} at {entry.timestamp}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    entries = load_audit_log(Path(args.log))
    if not entries:
        print("No audit entries found.")
        return 0
    for e in entries:
        if args.only_changes and not e.has_changes:
            continue
        label = f" [{e.baseline_label}]" if e.baseline_label else ""
        print(f"{e.timestamp}  {e.actor}{label}  {'CHANGED' if e.has_changes else 'ok'}  ({e.entry_id})")
    return 0


def main(argv: list[str] | None = None) -> None:  # pragma: no cover
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command == "record":
        sys.exit(_cmd_record(args))
    elif args.command == "list":
        sys.exit(_cmd_list(args))
