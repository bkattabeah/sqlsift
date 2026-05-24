"""Tag tables and columns in a schema with arbitrary labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from sqlsift.schema import Schema, Table


@dataclass
class TagOptions:
    """Options controlling how tags are applied."""
    table_tags: Dict[str, List[str]] = field(default_factory=dict)
    # column_tags: {"table_name.column_name": ["tag", ...]}
    column_tags: Dict[str, List[str]] = field(default_factory=dict)
    overwrite: bool = False


@dataclass
class TaggedColumn:
    name: str
    data_type: str
    nullable: bool
    default: Optional[str]
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TaggedColumn({self.name!r}, tags={self.tags})"


@dataclass
class TaggedTable:
    name: str
    columns: List[TaggedColumn] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TaggedTable({self.name!r}, tags={self.tags})"


@dataclass
class TaggedSchema:
    tables: List[TaggedTable] = field(default_factory=list)

    def get_table(self, name: str) -> Optional[TaggedTable]:
        for t in self.tables:
            if t.name == name:
                return t
        return None


def _resolve_tags(
    existing: List[str], new_tags: List[str], overwrite: bool
) -> List[str]:
    if overwrite:
        return list(new_tags)
    merged = list(existing)
    for tag in new_tags:
        if tag not in merged:
            merged.append(tag)
    return merged


def tag_schema(schema: Schema, options: TagOptions) -> TaggedSchema:
    """Apply tags from *options* to every table/column in *schema*."""
    tagged_tables: List[TaggedTable] = []

    for table in schema.tables:
        table_tag_list = options.table_tags.get(table.name, [])
        tagged_cols: List[TaggedColumn] = []

        for col in table.columns:
            key = f"{table.name}.{col.name}"
            col_tag_list = options.column_tags.get(key, [])
            tagged_cols.append(
                TaggedColumn(
                    name=col.name,
                    data_type=col.data_type,
                    nullable=col.nullable,
                    default=col.default,
                    tags=_resolve_tags([], col_tag_list, options.overwrite),
                )
            )

        tagged_tables.append(
            TaggedTable(
                name=table.name,
                columns=tagged_cols,
                tags=_resolve_tags([], table_tag_list, options.overwrite),
            )
        )

    return TaggedSchema(tables=tagged_tables)
