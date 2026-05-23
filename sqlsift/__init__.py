"""sqlsift — detect schema drift between SQL database snapshots."""

from sqlsift.diff import SchemaDiff, compute_diff
from sqlsift.exporter import ExportOptions, export_diff
from sqlsift.loader import dump_to_dict, dump_to_json, load_from_dict, load_from_json
from sqlsift.reporter import ReportOptions, generate_report
from sqlsift.schema import Column, Schema, Table
from sqlsift.writer import write_diff

__all__ = [
    # schema
    "Column",
    "Table",
    "Schema",
    # diff
    "SchemaDiff",
    "compute_diff",
    # loader
    "load_from_dict",
    "load_from_json",
    "dump_to_dict",
    "dump_to_json",
    # reporter
    "ReportOptions",
    "generate_report",
    # exporter
    "ExportOptions",
    "export_diff",
    # writer
    "write_diff",
]

__version__ = "0.2.0"
