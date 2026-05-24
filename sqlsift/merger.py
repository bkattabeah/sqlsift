"""Schema merger: apply a baseline schema on top of another to produce a merged result."""

from dataclasses import dataclass, field
from typing import Optional

from sqlsift.schema import Schema, Table, Column


@dataclass
class MergeOptions:
    """Controls how two schemas are merged."""
    prefer: str = "right"          # 'left' | 'right' — which side wins on column conflicts
    add_new_tables: bool = True    # include tables only present in the overlay schema
    add_new_columns: bool = True   # include columns only present in the overlay table


def _merge_columns(base_cols: dict, overlay_cols: dict, opts: MergeOptions) -> dict:
    """Return a merged ordered dict of Column objects."""
    merged: dict[str, Column] = {}

    for name, col in base_cols.items():
        if name in overlay_cols:
            merged[name] = overlay_cols[name] if opts.prefer == "right" else col
        else:
            merged[name] = col

    if opts.add_new_columns:
        for name, col in overlay_cols.items():
            if name not in merged:
                merged[name] = col

    return merged


def _merge_table(base: Table, overlay: Table, opts: MergeOptions) -> Table:
    """Merge two Table objects into one."""
    merged_cols = _merge_columns(base.columns, overlay.columns, opts)
    result = Table(name=base.name)
    for col in merged_cols.values():
        result.add_column(col)
    return result


def merge_schemas(
    base: Schema,
    overlay: Schema,
    opts: Optional[MergeOptions] = None,
) -> Schema:
    """Merge *overlay* into *base* and return a new Schema.

    Tables present in both schemas are merged column-by-column according to
    *opts*.  Tables only in *overlay* are included when ``add_new_tables`` is
    True.  Tables only in *base* are always kept.
    """
    if opts is None:
        opts = MergeOptions()

    result = Schema()

    for name, table in base.tables.items():
        if name in overlay.tables:
            result.add_table(_merge_table(table, overlay.tables[name], opts))
        else:
            result.add_table(table)

    if opts.add_new_tables:
        for name, table in overlay.tables.items():
            if name not in base.tables:
                result.add_table(table)

    return result
