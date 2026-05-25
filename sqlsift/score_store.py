"""Persist drift scores to a JSONL file for trend analysis."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from .scorer import DriftScore


@dataclass
class ScoreRecord:
    """A single persisted drift score with metadata."""
    timestamp: str
    total: int
    severity: str
    added_tables: int
    removed_tables: int
    added_columns: int
    removed_columns: int
    modified_columns: int
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "total": self.total,
            "severity": self.severity,
            "added_tables": self.added_tables,
            "removed_tables": self.removed_tables,
            "added_columns": self.added_columns,
            "removed_columns": self.removed_columns,
            "modified_columns": self.modified_columns,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ScoreRecord":
        return cls(
            timestamp=data["timestamp"],
            total=data["total"],
            severity=data["severity"],
            added_tables=data.get("added_tables", 0),
            removed_tables=data.get("removed_tables", 0),
            added_columns=data.get("added_columns", 0),
            removed_columns=data.get("removed_columns", 0),
            modified_columns=data.get("modified_columns", 0),
            label=data.get("label", ""),
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def record_score(
    path: str | Path,
    score: DriftScore,
    label: str = "",
    timestamp: str | None = None,
) -> ScoreRecord:
    """Append *score* to the JSONL store at *path* and return the record."""
    rec = ScoreRecord(
        timestamp=timestamp or _now_iso(),
        total=score.total,
        severity=score.severity,
        added_tables=score.added_tables,
        removed_tables=score.removed_tables,
        added_columns=score.added_columns,
        removed_columns=score.removed_columns,
        modified_columns=score.modified_columns,
        label=label,
    )
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec.to_dict()) + "\n")
    return rec


def load_scores(path: str | Path) -> list[ScoreRecord]:
    """Load all score records from a JSONL store file."""
    p = Path(path)
    if not p.exists():
        return []
    records: list[ScoreRecord] = []
    with p.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                records.append(ScoreRecord.from_dict(json.loads(line)))
    return records


def latest_score(path: str | Path) -> ScoreRecord | None:
    """Return the most recently recorded score, or None if the store is empty."""
    records = load_scores(path)
    return records[-1] if records else None
