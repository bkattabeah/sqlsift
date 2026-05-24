"""Baseline management: save and load reference schema snapshots."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlsift.schema import Schema
from sqlsift.loader import dump_to_dict, load_from_dict


@dataclass
class BaselineMetadata:
    name: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    description: str = ""


@dataclass
class Baseline:
    metadata: BaselineMetadata
    schema: Schema


def save_baseline(
    schema: Schema,
    path: str,
    name: str,
    description: str = "",
) -> None:
    """Persist a schema snapshot as a baseline JSON file."""
    meta = BaselineMetadata(name=name, description=description)
    payload = {
        "metadata": {
            "name": meta.name,
            "created_at": meta.created_at,
            "description": meta.description,
        },
        "schema": dump_to_dict(schema),
    }
    os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def load_baseline(path: str) -> Baseline:
    """Load a previously saved baseline from disk."""
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    raw_meta = payload["metadata"]
    meta = BaselineMetadata(
        name=raw_meta["name"],
        created_at=raw_meta["created_at"],
        description=raw_meta.get("description", ""),
    )
    schema = load_from_dict(payload["schema"])
    return Baseline(metadata=meta, schema=schema)


def list_baselines(directory: str) -> list[str]:
    """Return paths to all baseline files in *directory*."""
    if not os.path.isdir(directory):
        return []
    return sorted(
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".json")
    )
