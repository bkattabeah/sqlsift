"""sqlsift.rename_report — human-readable reports for rename hints."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import List, Optional

from sqlsift.renamer import RenameHint


@dataclass
class RenameReportOptions:
    """Options controlling rename report output."""
    fmt: str = "text"          # 'text', 'json', or 'markdown'
    min_score: float = 0.0     # filter hints below this score
    show_score: bool = True


def _fmt_text(hints: List[RenameHint], show_score: bool) -> str:
    if not hints:
        return "No rename hints detected.\n"
    lines = ["Rename Hints", "============"]
    for h in hints:
        score_part = f"  (score: {h.score:.2f})" if show_score else ""
        if h.kind == "table":
            lines.append(f"[TABLE]  {h.old_name!r} -> {h.new_name!r}{score_part}")
        else:
            lines.append(
                f"[COLUMN] {h.table_name}.{h.old_name!r} -> {h.new_name!r}{score_part}"
            )
    return "\n".join(lines) + "\n"


def _fmt_json(hints: List[RenameHint], show_score: bool) -> str:
    records = []
    for h in hints:
        rec = {
            "kind": h.kind,
            "table": h.table_name,
            "old_name": h.old_name,
            "new_name": h.new_name,
        }
        if show_score:
            rec["score"] = round(h.score, 4)
        records.append(rec)
    return json.dumps(records, indent=2)


def _fmt_markdown(hints: List[RenameHint], show_score: bool) -> str:
    if not hints:
        return "_No rename hints detected._\n"
    header = "| Kind | Table | Old Name | New Name |"
    if show_score:
        header += " Score |"
    sep = "|------|-------|----------|----------|"
    if show_score:
        sep += "-------|"
    rows = [header, sep]
    for h in hints:
        row = f"| {h.kind} | {h.table_name} | `{h.old_name}` | `{h.new_name}` |"
        if show_score:
            row += f" {h.score:.2f} |"
        rows.append(row)
    return "\n".join(rows) + "\n"


_FORMATTERS = {
    "text": _fmt_text,
    "json": _fmt_json,
    "markdown": _fmt_markdown,
}


def generate_rename_report(
    hints: List[RenameHint],
    options: Optional[RenameReportOptions] = None,
) -> str:
    """Render *hints* as a formatted string according to *options*."""
    if options is None:
        options = RenameReportOptions()

    fmt = options.fmt.lower()
    if fmt not in _FORMATTERS:
        raise ValueError(f"Unknown format {fmt!r}. Choose from: {list(_FORMATTERS)}.")

    filtered = [h for h in hints if h.score >= options.min_score]
    return _FORMATTERS[fmt](filtered, options.show_score)
