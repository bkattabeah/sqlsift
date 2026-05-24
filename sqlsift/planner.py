"""Migration planner: orders patch statements by dependency and groups them
into logical migration phases."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.diff import SchemaDiff
from sqlsift.patcher import PatchOptions, generate_patch


@dataclass
class MigrationPhase:
    name: str
    statements: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"MigrationPhase(name={self.name!r}, statements={len(self.statements)})"


@dataclass
class MigrationPlan:
    phases: List[MigrationPhase] = field(default_factory=list)

    @property
    def all_statements(self) -> List[str]:
        """Flat list of all SQL statements in phase order."""
        result: List[str] = []
        for phase in self.phases:
            result.extend(phase.statements)
        return result

    def __repr__(self) -> str:  # pragma: no cover
        total = sum(len(p.statements) for p in self.phases)
        return f"MigrationPlan(phases={len(self.phases)}, statements={total})"


@dataclass
class PlannerOptions:
    patch_options: Optional[PatchOptions] = None
    include_drops: bool = True


def _classify(statement: str) -> str:
    """Return a phase name based on the SQL verb."""
    upper = statement.strip().upper()
    if upper.startswith("CREATE TABLE"):
        return "create_tables"
    if upper.startswith("DROP TABLE"):
        return "drop_tables"
    if upper.startswith("ALTER TABLE") and "ADD COLUMN" in upper:
        return "add_columns"
    if upper.startswith("ALTER TABLE") and "DROP COLUMN" in upper:
        return "drop_columns"
    if upper.startswith("ALTER TABLE"):
        return "alter_columns"
    return "other"


_PHASE_ORDER = [
    "create_tables",
    "add_columns",
    "alter_columns",
    "drop_columns",
    "drop_tables",
    "other",
]


def build_migration_plan(
    diff: SchemaDiff,
    options: Optional[PlannerOptions] = None,
) -> MigrationPlan:
    """Generate an ordered MigrationPlan from a SchemaDiff."""
    options = options or PlannerOptions()
    patch_opts = options.patch_options or PatchOptions()

    raw_sql = generate_patch(diff, patch_opts)
    statements = [
        s.strip() for s in raw_sql.split(";") if s.strip()
    ]

    buckets: dict[str, List[str]] = {name: [] for name in _PHASE_ORDER}
    for stmt in statements:
        phase_name = _classify(stmt)
        buckets[phase_name].append(stmt + ";")

    if not options.include_drops:
        buckets["drop_tables"] = []
        buckets["drop_columns"] = []

    phases = [
        MigrationPhase(name=name, statements=stmts)
        for name in _PHASE_ORDER
        if (stmts := buckets[name])
    ]
    return MigrationPlan(phases=phases)
