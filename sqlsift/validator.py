"""Schema validation utilities for sqlsift."""
from dataclasses import dataclass, field
from typing import List, Optional
from sqlsift.schema import Schema, Table, Column


@dataclass
class ValidationIssue:
    table: str
    column: Optional[str]
    message: str
    severity: str  # 'error' | 'warning'

    def __repr__(self) -> str:
        loc = f"{self.table}.{self.column}" if self.column else self.table
        return f"[{self.severity.upper()}] {loc}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not any(i.severity == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def _validate_column(table_name: str, col: Column) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not col.name or not col.name.strip():
        issues.append(ValidationIssue(table_name, None, "Column has empty name", "error"))
    if not col.data_type or not col.data_type.strip():
        issues.append(ValidationIssue(table_name, col.name, "Column has no data type", "warning"))
    return issues


def _validate_table(table: Table) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    if not table.name or not table.name.strip():
        issues.append(ValidationIssue(table.name or "<unknown>", None, "Table has empty name", "error"))
    if not table.columns:
        issues.append(ValidationIssue(table.name, None, "Table has no columns", "warning"))
    seen: set = set()
    for col in table.columns.values():
        if col.name in seen:
            issues.append(ValidationIssue(table.name, col.name, "Duplicate column name", "error"))
        seen.add(col.name)
        issues.extend(_validate_column(table.name, col))
    return issues


def validate_schema(schema: Schema) -> ValidationResult:
    """Validate a Schema object and return a ValidationResult."""
    result = ValidationResult()
    if not schema.tables:
        result.issues.append(ValidationIssue("<schema>", None, "Schema contains no tables", "warning"))
        return result
    for table in schema.tables.values():
        result.issues.extend(_validate_table(table))
    return result
