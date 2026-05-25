"""Schema catalog: store and query multiple named schemas."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterator, List, Optional

from sqlsift.schema import Schema


@dataclass
class CatalogEntry:
    name: str
    schema: Schema
    tags: List[str] = field(default_factory=list)
    description: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return f"CatalogEntry(name={self.name!r}, tables={len(self.schema.tables)})"


@dataclass
class Catalog:
    _entries: Dict[str, CatalogEntry] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Mutation
    # ------------------------------------------------------------------

    def register(
        self,
        name: str,
        schema: Schema,
        *,
        tags: Optional[List[str]] = None,
        description: str = "",
    ) -> CatalogEntry:
        """Add or replace a named schema in the catalog."""
        entry = CatalogEntry(
            name=name,
            schema=schema,
            tags=list(tags or []),
            description=description,
        )
        self._entries[name] = entry
        return entry

    def remove(self, name: str) -> None:
        """Remove a schema by name; silently ignore unknown names."""
        self._entries.pop(name, None)

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get(self, name: str) -> Optional[CatalogEntry]:
        return self._entries.get(name)

    def names(self) -> List[str]:
        return sorted(self._entries.keys())

    def find_by_tag(self, tag: str) -> List[CatalogEntry]:
        return [e for e in self._entries.values() if tag in e.tags]

    def __iter__(self) -> Iterator[CatalogEntry]:
        return iter(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)


def build_catalog(entries: Dict[str, Schema]) -> Catalog:
    """Convenience: build a Catalog from a plain name→Schema mapping."""
    catalog = Catalog()
    for name, schema in entries.items():
        catalog.register(name, schema)
    return catalog
