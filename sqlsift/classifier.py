"""Classify tables and columns in a schema by inferred role or category."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.schema import Schema, Table, Column

_AUDIT_SUFFIXES = ("_at", "_by", "_on", "_date", "_time")
_AUDIT_PREFIXES = ("created", "updated", "deleted", "modified")
_ID_SUFFIXES = ("_id", "_uuid", "_key")
_FLAG_TYPES = {"boolean", "bool", "tinyint"}
_LARGE_TYPES = {"text", "blob", "json", "jsonb", "clob"}


@dataclass
class ColumnClassification:
    column_name: str
    table_name: str
    role: str  # 'primary_key', 'foreign_key', 'audit', 'flag', 'large', 'generic'
    reason: str

    def __repr__(self) -> str:  # pragma: no cover
        return f"ColumnClassification({self.table_name}.{self.column_name!r} -> {self.role!r})"


@dataclass
class TableClassification:
    table_name: str
    category: str  # 'lookup', 'audit_log', 'entity', 'unknown'
    column_classifications: List[ColumnClassification] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TableClassification({self.table_name!r} -> {self.category!r})"


@dataclass
class ClassifierOptions:
    large_varchar_threshold: int = 1024


def _classify_column(col: Column, table_name: str, opts: ClassifierOptions) -> ColumnClassification:
    name_lower = col.name.lower()
    type_lower = (col.col_type or "").lower()

    if col.primary_key:
        return ColumnClassification(col.name, table_name, "primary_key", "marked primary_key")

    if any(name_lower.endswith(s) for s in _ID_SUFFIXES) and not col.primary_key:
        return ColumnClassification(col.name, table_name, "foreign_key", "name ends with id/uuid/key suffix")

    audit_name = any(name_lower.endswith(s) for s in _AUDIT_SUFFIXES) or any(
        name_lower.startswith(p) for p in _AUDIT_PREFIXES
    )
    if audit_name:
        return ColumnClassification(col.name, table_name, "audit", "name matches audit pattern")

    if type_lower in _FLAG_TYPES:
        return ColumnClassification(col.name, table_name, "flag", f"type is {type_lower}")

    if type_lower in _LARGE_TYPES:
        return ColumnClassification(col.name, table_name, "large", f"type is {type_lower}")

    if "varchar" in type_lower or "char" in type_lower:
        try:
            length = int(type_lower.split("(")[1].rstrip(")"))
            if length >= opts.large_varchar_threshold:
                return ColumnClassification(col.name, table_name, "large", f"varchar length {length} >= threshold")
        except (IndexError, ValueError):
            pass

    return ColumnClassification(col.name, table_name, "generic", "no specific role detected")


def _classify_table(table: Table, col_classes: List[ColumnClassification]) -> str:
    roles = {cc.role for cc in col_classes}
    name_lower = table.name.lower()
    if "log" in name_lower or "audit" in name_lower or "history" in name_lower:
        return "audit_log"
    if len(table.columns) <= 3 and "primary_key" in roles and "foreign_key" not in roles:
        return "lookup"
    if "foreign_key" in roles or "primary_key" in roles:
        return "entity"
    return "unknown"


def classify_schema(
    schema: Schema,
    opts: Optional[ClassifierOptions] = None,
) -> Dict[str, TableClassification]:
    """Return a mapping of table name to TableClassification for *schema*."""
    if opts is None:
        opts = ClassifierOptions()
    result: Dict[str, TableClassification] = {}
    for table in schema.tables.values():
        col_classes = [_classify_column(col, table.name, opts) for col in table.columns.values()]
        category = _classify_table(table, col_classes)
        result[table.name] = TableClassification(
            table_name=table.name,
            category=category,
            column_classifications=col_classes,
        )
    return result
