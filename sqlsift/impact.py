"""Impact analysis: given a SchemaDiff, estimate which downstream
objects (views, stored procedures, applications) may be affected."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.diff import SchemaDiff


@dataclass
class ImpactedObject:
    """Represents a downstream object potentially affected by a change."""

    kind: str          # e.g. 'view', 'index', 'application', 'report'
    name: str
    reason: str        # human-readable explanation
    table: str
    column: Optional[str] = None

    def __repr__(self) -> str:  # pragma: no cover
        col_part = f".{self.column}" if self.column else ""
        return f"ImpactedObject({self.kind}:{self.name} <- {self.table}{col_part})"


@dataclass
class ImpactReport:
    """Collection of all impacted objects derived from a diff."""

    items: List[ImpactedObject] = field(default_factory=list)

    @property
    def has_impact(self) -> bool:
        return bool(self.items)

    def by_table(self, table: str) -> List[ImpactedObject]:
        return [i for i in self.items if i.table == table]

    def by_kind(self, kind: str) -> List[ImpactedObject]:
        return [i for i in self.items if i.kind == kind]


@dataclass
class ImpactOptions:
    """Controls which synthetic impact rules are applied."""

    warn_removed_tables: bool = True
    warn_removed_columns: bool = True
    warn_type_changes: bool = True
    warn_nullable_changes: bool = True
    application_name: str = "downstream_app"


def _removed_table_impacts(
    table: str, opts: ImpactOptions
) -> List[ImpactedObject]:
    impacts: List[ImpactedObject] = []
    if opts.warn_removed_tables:
        impacts.append(
            ImpactedObject(
                kind="application",
                name=opts.application_name,
                reason=f"Table '{table}' was removed; any query referencing it will break.",
                table=table,
            )
        )
    return impacts


def _column_impacts(
    table: str, col_name: str, change_kind: str, opts: ImpactOptions
) -> List[ImpactedObject]:
    impacts: List[ImpactedObject] = []
    if change_kind == "removed" and opts.warn_removed_columns:
        impacts.append(
            ImpactedObject(
                kind="application",
                name=opts.application_name,
                reason=f"Column '{col_name}' removed from '{table}'; SELECT * and explicit references break.",
                table=table,
                column=col_name,
            )
        )
    elif change_kind == "type_changed" and opts.warn_type_changes:
        impacts.append(
            ImpactedObject(
                kind="application",
                name=opts.application_name,
                reason=f"Column '{col_name}' in '{table}' changed type; implicit casts may fail.",
                table=table,
                column=col_name,
            )
        )
    elif change_kind == "nullable_changed" and opts.warn_nullable_changes:
        impacts.append(
            ImpactedObject(
                kind="application",
                name=opts.application_name,
                reason=f"Column '{col_name}' in '{table}' changed nullability; NOT NULL constraints may break inserts.",
                table=table,
                column=col_name,
            )
        )
    return impacts


def analyze_impact(
    diff: SchemaDiff,
    opts: Optional[ImpactOptions] = None,
) -> ImpactReport:
    """Walk *diff* and produce an :class:`ImpactReport`."""
    if opts is None:
        opts = ImpactOptions()

    items: List[ImpactedObject] = []

    for table in diff.removed_tables:
        items.extend(_removed_table_impacts(table, opts))

    for table, td in diff.modified_tables.items():
        for col in td.removed_columns:
            items.extend(_column_impacts(table, col, "removed", opts))
        for col in td.modified_columns:
            old = td.old_columns[col]
            new = td.new_columns[col]
            if old.col_type != new.col_type:
                items.extend(_column_impacts(table, col, "type_changed", opts))
            if old.nullable != new.nullable:
                items.extend(_column_impacts(table, col, "nullable_changed", opts))

    return ImpactReport(items=items)
