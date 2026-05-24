"""Audit trail for schema changes — records who diffed what and when."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from sqlsift.diff import SchemaDiff


@dataclass
class AuditEntry:
    entry_id: str
    timestamp: str
    actor: str
    baseline_label: Optional[str]
    added_tables: List[str]
    removed_tables: List[str]
    modified_tables: List[str]
    has_changes: bool

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"AuditEntry(id={self.entry_id!r}, actor={self.actor!r}, "
            f"ts={self.timestamp!r}, changes={self.has_changes})"
        )


def _entry_from_diff(
    diff: SchemaDiff,
    actor: str,
    baseline_label: Optional[str] = None,
) -> AuditEntry:
    return AuditEntry(
        entry_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        actor=actor,
        baseline_label=baseline_label,
        added_tables=list(diff.added_tables.keys()),
        removed_tables=list(diff.removed_tables.keys()),
        modified_tables=list(diff.modified_tables.keys()),
        has_changes=diff.has_changes,
    )


def _entry_to_dict(entry: AuditEntry) -> dict:
    return {
        "entry_id": entry.entry_id,
        "timestamp": entry.timestamp,
        "actor": entry.actor,
        "baseline_label": entry.baseline_label,
        "added_tables": entry.added_tables,
        "removed_tables": entry.removed_tables,
        "modified_tables": entry.modified_tables,
        "has_changes": entry.has_changes,
    }


def _entry_from_dict(d: dict) -> AuditEntry:
    return AuditEntry(
        entry_id=d["entry_id"],
        timestamp=d["timestamp"],
        actor=d["actor"],
        baseline_label=d.get("baseline_label"),
        added_tables=d.get("added_tables", []),
        removed_tables=d.get("removed_tables", []),
        modified_tables=d.get("modified_tables", []),
        has_changes=d["has_changes"],
    )


def record_audit(
    diff: SchemaDiff,
    path: Path,
    actor: str = "unknown",
    baseline_label: Optional[str] = None,
) -> AuditEntry:
    """Append an audit entry for *diff* to the JSONL file at *path*."""
    entry = _entry_from_diff(diff, actor=actor, baseline_label=baseline_label)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(_entry_to_dict(entry)) + "\n")
    return entry


def load_audit_log(path: Path) -> List[AuditEntry]:
    """Read all audit entries from a JSONL file."""
    path = Path(path)
    if not path.exists():
        return []
    entries: List[AuditEntry] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                entries.append(_entry_from_dict(json.loads(line)))
    return entries
