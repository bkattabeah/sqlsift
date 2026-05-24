"""sqlsift — SQL schema drift detection toolkit."""

from sqlsift.schema import Column, Table, Schema
from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.reporter import ReportOptions, generate_report
from sqlsift.loader import load_from_dict, load_from_json, dump_to_dict, dump_to_json
from sqlsift.exporter import ExportOptions, export_diff
from sqlsift.writer import write_diff
from sqlsift.filter import FilterOptions, filter_diff
from sqlsift.validator import ValidationResult, validate_schema
from sqlsift.summary import DiffSummary, summarize_diff
from sqlsift.patcher import PatchOptions, generate_patch
from sqlsift.scorer import ScorerOptions, DriftScore, score_diff
from sqlsift.comparator import ColumnSimilarity, TableSimilarity, compare_tables
from sqlsift.merger import MergeOptions, merge_schemas
from sqlsift.baseline import Baseline, save_baseline, load_baseline, list_baselines
from sqlsift.baseline_diff import BaselineDiffResult, diff_against_baseline
from sqlsift.watcher import WatchOptions, WatchEvent, watch
from sqlsift.watcher_store import WatchStore
from sqlsift.annotator import AnnotationOptions, Annotation, annotate_schema

__all__ = [
    # schema
    "Column", "Table", "Schema",
    # diff
    "SchemaDiff", "compute_diff",
    # reporter
    "ReportOptions", "generate_report",
    # loader
    "load_from_dict", "load_from_json", "dump_to_dict", "dump_to_json",
    # exporter / writer
    "ExportOptions", "export_diff", "write_diff",
    # filter
    "FilterOptions", "filter_diff",
    # validator
    "ValidationResult", "validate_schema",
    # summary
    "DiffSummary", "summarize_diff",
    # patcher
    "PatchOptions", "generate_patch",
    # scorer
    "ScorerOptions", "DriftScore", "score_diff",
    # comparator
    "ColumnSimilarity", "TableSimilarity", "compare_tables",
    # merger
    "MergeOptions", "merge_schemas",
    # baseline
    "Baseline", "save_baseline", "load_baseline", "list_baselines",
    "BaselineDiffResult", "diff_against_baseline",
    # watcher
    "WatchOptions", "WatchEvent", "watch", "WatchStore",
    # annotator
    "AnnotationOptions", "Annotation", "annotate_schema",
]
