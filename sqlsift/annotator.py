"""Annotate schema columns and tables with metadata tags."""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.schema import Schema, Table, Column


@dataclass
class AnnotationOptions:
    """Controls which annotations are applied."""
    tag_nullable: bool = True
    tag_primary_keys: bool = True
    tag_large_types: bool = True
    large_type_threshold: int = 255  # for VARCHAR-like types


@dataclass
class Annotation:
    """A single annotation attached to a column or table."""
    tag: str
    reason: str

    def __repr__(self) -> str:
        return f"Annotation(tag={self.tag!r}, reason={self.reason!r})"


AnnotationMap = Dict[str, List[Annotation]]  # key: "table.column" or "table"


def _large_type(col: Column, threshold: int) -> bool:
    """Return True if the column type looks like a large string/binary type."""
    t = (col.data_type or "").upper()
    for prefix in ("VARCHAR", "NVARCHAR", "CHAR", "BINARY", "VARBINARY"):
        if t.startswith(prefix):
            # Try to parse length, e.g. VARCHAR(512)
            try:
                length = int(t.split("(")[1].rstrip(")"))
                return length > threshold
            except (IndexError, ValueError):
                return False
    return t in ("TEXT", "BLOB", "CLOB", "LONGTEXT", "MEDIUMTEXT")


def annotate_schema(
    schema: Schema,
    options: Optional[AnnotationOptions] = None,
) -> AnnotationMap:
    """Return an AnnotationMap for all columns and tables in *schema*."""
    if options is None:
        options = AnnotationOptions()

    result: AnnotationMap = {}

    for table_name, table in schema.tables.items():
        for col in table.columns.values():
            key = f"{table_name}.{col.name}"
            annotations: List[Annotation] = []

            if options.tag_nullable and col.nullable:
                annotations.append(
                    Annotation(tag="nullable", reason="Column allows NULL values")
                )

            if options.tag_primary_keys and col.primary_key:
                annotations.append(
                    Annotation(tag="primary_key", reason="Column is a primary key")
                )

            if options.tag_large_types and _large_type(col, options.large_type_threshold):
                annotations.append(
                    Annotation(
                        tag="large_type",
                        reason=f"Column type '{col.data_type}' may store large data",
                    )
                )

            if annotations:
                result[key] = annotations

    return result
