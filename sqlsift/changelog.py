"""changelog.py – generate a human-readable changelog from a sequence of SchemaDiff objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.diff import SchemaDiff


@dataclass
class ChangelogEntry:
    version: str
    description: str
    added_tables: List[str] = field(default_factory=list)
    removed_tables: List[str] = field(default_factory=list)
    modified_tables: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"ChangelogEntry(version={self.version!r}, "
            f"added={self.added_tables}, removed={self.removed_tables}, "
            f"modified={self.modified_tables})"
        )


@dataclass
class Changelog:
    entries: List[ChangelogEntry] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.entries)


@dataclass
class ChangelogOptions:
    include_unchanged: bool = False
    version_prefix: str = "v"


def _entry_from_diff(
    diff: SchemaDiff,
    version: str,
    description: str,
) -> ChangelogEntry:
    added = list(diff.added_tables.keys())
    removed = list(diff.removed_tables.keys())
    modified = list(diff.modified_tables.keys())
    return ChangelogEntry(
        version=version,
        description=description,
        added_tables=sorted(added),
        removed_tables=sorted(removed),
        modified_tables=sorted(modified),
    )


def build_changelog(
    diffs: List[SchemaDiff],
    descriptions: Optional[List[str]] = None,
    options: Optional[ChangelogOptions] = None,
) -> Changelog:
    """Build a Changelog from an ordered list of SchemaDiff objects."""
    opts = options or ChangelogOptions()
    descs = descriptions or []
    entries: List[ChangelogEntry] = []

    for idx, diff in enumerate(diffs):
        version = f"{opts.version_prefix}{idx + 1}"
        description = descs[idx] if idx < len(descs) else ""
        if not opts.include_unchanged and not diff.has_changes():
            continue
        entries.append(_entry_from_diff(diff, version, description))

    return Changelog(entries=entries)


def format_changelog(changelog: Changelog) -> str:
    """Render a Changelog as plain text."""
    if not changelog.entries:
        return "No changes recorded."

    lines: List[str] = []
    for entry in changelog.entries:
        lines.append(f"## {entry.version}")
        if entry.description:
            lines.append(entry.description)
        if entry.added_tables:
            lines.append("  Added tables: " + ", ".join(entry.added_tables))
        if entry.removed_tables:
            lines.append("  Removed tables: " + ", ".join(entry.removed_tables))
        if entry.modified_tables:
            lines.append("  Modified tables: " + ", ".join(entry.modified_tables))
        lines.append("")
    return "\n".join(lines).rstrip()
