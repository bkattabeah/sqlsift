"""sqlsift.snapshotter — capture and compare timestamped schema snapshots."""
from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.schema import Schema
from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.loader import dump_to_dict, load_from_dict


@dataclass
class Snapshot:
    """A schema captured at a specific point in time."""
    label: str
    captured_at: str  # ISO-8601 string
    schema: Schema

    def __repr__(self) -> str:  # pragma: no cover
        return f"Snapshot(label={self.label!r}, captured_at={self.captured_at!r})"


@dataclass
class SnapshotStore:
    """In-memory ordered store of schema snapshots."""
    _snapshots: List[Snapshot] = field(default_factory=list)

    def add(self, schema: Schema, label: Optional[str] = None) -> Snapshot:
        """Capture *schema* and append to the store."""
        now = datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"
        lbl = label or f"snapshot-{len(self._snapshots) + 1}"
        snap = Snapshot(label=lbl, captured_at=now, schema=schema)
        self._snapshots.append(snap)
        return snap

    def latest(self) -> Optional[Snapshot]:
        """Return the most recently added snapshot, or *None*."""
        return self._snapshots[-1] if self._snapshots else None

    def all(self) -> List[Snapshot]:
        """Return all snapshots in insertion order."""
        return list(self._snapshots)

    def clear(self) -> None:
        """Remove all stored snapshots."""
        self._snapshots.clear()

    def __len__(self) -> int:
        return len(self._snapshots)


def diff_snapshots(older: Snapshot, newer: Snapshot) -> SchemaDiff:
    """Return a :class:`~sqlsift.diff.SchemaDiff` between two snapshots."""
    return compute_diff(older.schema, newer.schema)


def snapshot_to_dict(snap: Snapshot) -> Dict:
    """Serialise a snapshot to a plain dictionary."""
    return {
        "label": snap.label,
        "captured_at": snap.captured_at,
        "schema": dump_to_dict(snap.schema),
    }


def snapshot_from_dict(data: Dict) -> Snapshot:
    """Deserialise a snapshot from a plain dictionary."""
    return Snapshot(
        label=data["label"],
        captured_at=data["captured_at"],
        schema=load_from_dict(data["schema"]),
    )
