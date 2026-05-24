"""Policy engine for enforcing schema conventions and constraints."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from sqlsift.schema import Schema, Table, Column


@dataclass
class PolicyRule:
    """A single named policy rule with an optional description."""

    name: str
    description: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"PolicyRule(name={self.name!r})"


@dataclass
class PolicyViolation:
    """A violation of a policy rule found in a schema."""

    rule: str
    table: str
    column: Optional[str]
    message: str

    def __repr__(self) -> str:
        loc = f"{self.table}.{self.column}" if self.column else self.table
        return f"PolicyViolation(rule={self.rule!r}, location={loc!r})"


@dataclass
class PolicyOptions:
    require_primary_key: bool = True
    disallow_unconstrained_text: bool = False
    max_column_name_length: int = 63
    forbidden_prefixes: List[str] = field(default_factory=list)


@dataclass
class PolicyResult:
    violations: List[PolicyViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0


def _check_table(table: Table, opts: PolicyOptions) -> List[PolicyViolation]:
    issues: List[PolicyViolation] = []

    if opts.require_primary_key:
        has_pk = any(c.primary_key for c in table.columns.values())
        if not has_pk:
            issues.append(PolicyViolation(
                rule="P001",
                table=table.name,
                column=None,
                message=f"Table '{table.name}' has no primary key column.",
            ))

    for col in table.columns.values():
        if len(col.name) > opts.max_column_name_length:
            issues.append(PolicyViolation(
                rule="P002",
                table=table.name,
                column=col.name,
                message=(
                    f"Column '{col.name}' exceeds max name length "
                    f"({opts.max_column_name_length})."
                ),
            ))

        if opts.disallow_unconstrained_text and col.col_type.upper() == "TEXT":
            issues.append(PolicyViolation(
                rule="P003",
                table=table.name,
                column=col.name,
                message=f"Column '{col.name}' uses unconstrained TEXT type.",
            ))

        for prefix in opts.forbidden_prefixes:
            if col.name.startswith(prefix):
                issues.append(PolicyViolation(
                    rule="P004",
                    table=table.name,
                    column=col.name,
                    message=(
                        f"Column '{col.name}' starts with forbidden "
                        f"prefix '{prefix}'."
                    ),
                ))
                break

    return issues


def enforce_policy(schema: Schema, opts: Optional[PolicyOptions] = None) -> PolicyResult:
    """Run all policy checks against *schema* and return a PolicyResult."""
    if opts is None:
        opts = PolicyOptions()

    result = PolicyResult()
    for table in schema.tables.values():
        result.violations.extend(_check_table(table, opts))
    return result
