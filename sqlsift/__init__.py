"""sqlsift — SQL schema drift detection library."""

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.loader import load_from_dict, load_from_json, dump_to_dict, dump_to_json
from sqlsift.reporter import ReportOptions, generate_report
from sqlsift.exporter import ExportOptions, export_diff
from sqlsift.writer import write_diff
from sqlsift.filter import FilterOptions, filter_diff
from sqlsift.validator import ValidationResult, validate_schema
from sqlsift.summary import DiffSummary, summarize_diff
from sqlsift.patcher import PatchOptions, generate_patch
from sqlsift.scorer import ScorerOptions, DriftScore, score_diff
from sqlsift.comparator import (
    ColumnSimilarity,
    TableSimilarity,
    compare_columns,
    compare_tables,
)

__all__ = [
    "Column", "Table", "Schema",
    "SchemaDiff", "compute_diff",
    "load_from_dict", "load_from_json", "dump_to_dict", "dump_to_json",
    "ReportOptions", "generate_report",
    "ExportOptions", "export_diff",
    "write_diff",
    "FilterOptions", "filter_diff",
    "ValidationResult", "validate_schema",
    "DiffSummary", "summarize_diff",
    "PatchOptions", "generate_patch",
    "ScorerOptions", "DriftScore", "score_diff",
    "ColumnSimilarity", "TableSimilarity", "compare_columns", "compare_tables",
]

__version__ = "0.1.0"
