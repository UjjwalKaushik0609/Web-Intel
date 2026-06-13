"""
exporter.py
-----------
Developer-built: Export scraped and AI-extracted data to CSV and JSON files.
Handles nested data flattening for CSV compatibility.
No AI involved — data formatting and file I/O only.
"""
 
import csv
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
 
import pandas as pd
 
logger = logging.getLogger(__name__)
 
# Default export directory
DEFAULT_EXPORT_DIR = "exports"
 
 
def _ensure_export_dir(export_dir: str) -> Path:
    """Create export directory if it doesn't exist."""
    path = Path(export_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path
 
 
def _flatten_record(record: dict, prefix: str = "", sep: str = "_") -> dict:
    """
    Recursively flatten a nested dict for CSV export.
 
    Example: {"a": {"b": 1}} → {"a_b": 1}
 
    Args:
        record: Potentially nested dictionary.
        prefix: Key prefix for nested fields.
        sep: Separator between nested key levels.
 
    Returns:
        Flat dictionary with no nested dicts/lists.
    """
    flat = {}
    for key, value in record.items():
        full_key = f"{prefix}{sep}{key}" if prefix else key
 
        if isinstance(value, dict):
            flat.update(_flatten_record(value, full_key, sep))
        elif isinstance(value, list):
            # Convert lists to pipe-separated strings for CSV
            flat[full_key] = " | ".join(str(v) for v in value)
        else:
            flat[full_key] = value
 
    return flat
 
 
def _timestamp_filename(base_name: str, extension: str) -> str:
    """Generate a timestamped filename."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{ts}.{extension}"
 
 
def export_to_json(
    data: Union[List, Dict],
    filename: Optional[str] = None,
    export_dir: str = DEFAULT_EXPORT_DIR,
    indent: int = 2,
) -> str:
    """
    Export data to a JSON file.
 
    Args:
        data: Data to export (list of records or single dict).
        filename: Output filename (auto-generated if None).
        export_dir: Directory for output file.
        indent: JSON indentation level.
 
    Returns:
        Full path to the exported file.
    """
    export_path = _ensure_export_dir(export_dir)
 
    if filename is None:
        filename = _timestamp_filename("scraped_data", "json")
 
    full_path = export_path / filename
 
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=indent, default=str)
 
        file_size = full_path.stat().st_size
        record_count = len(data) if isinstance(data, list) else 1
        logger.info(f"[Exporter] JSON exported: {full_path} ({record_count} records, {file_size} bytes)")
        return str(full_path)
 
    except (IOError, TypeError) as e:
        logger.error(f"[Exporter] JSON export failed: {e}")
        raise
 
 
def export_to_csv(
    data: Union[List[Dict], Dict],
    filename: Optional[str] = None,
    export_dir: str = DEFAULT_EXPORT_DIR,
    flatten: bool = True,
) -> str:
    """
    Export data to a CSV file using pandas for robust formatting.
 
    Args:
        data: List of record dicts, or single dict to wrap in list.
        filename: Output filename (auto-generated if None).
        export_dir: Directory for output file.
        flatten: Whether to flatten nested dicts for CSV compatibility.
 
    Returns:
        Full path to the exported file.
    """
    export_path = _ensure_export_dir(export_dir)
 
    if filename is None:
        filename = _timestamp_filename("scraped_data", "csv")
 
    full_path = export_path / filename
 
    # Normalize input to list of dicts
    if isinstance(data, dict):
        data = [data]
 
    if not data:
        logger.warning("[Exporter] No data to export to CSV")
        # Create empty CSV with header row
        pd.DataFrame().to_csv(full_path, index=False)
        return str(full_path)
 
    try:
        # Flatten nested structures if requested
        if flatten:
            records = [_flatten_record(r) if isinstance(r, dict) else {"value": r} for r in data]
        else:
            records = data
 
        df = pd.DataFrame(records)
 
        # Write CSV with UTF-8 BOM for Excel compatibility
        df.to_csv(full_path, index=False, encoding="utf-8-sig")
 
        logger.info(f"[Exporter] CSV exported: {full_path} ({len(df)} rows × {len(df.columns)} cols)")
        return str(full_path)
 
    except Exception as e:
        logger.error(f"[Exporter] CSV export failed: {e}")
        raise
 
 
def export_to_dataframe(data: Union[List[Dict], Dict], flatten: bool = True) -> pd.DataFrame:
    """
    Convert scraped data to a pandas DataFrame for in-memory analysis.
 
    Args:
        data: List of record dicts or single dict.
        flatten: Whether to flatten nested structures.
 
    Returns:
        pandas DataFrame.
    """
    if isinstance(data, dict):
        data = [data]
 
    if not data:
        return pd.DataFrame()
 
    if flatten:
        records = [_flatten_record(r) if isinstance(r, dict) else {"value": r} for r in data]
    else:
        records = data
 
    return pd.DataFrame(records)
 
 
def export_summary_report(
    url: str,
    summary: str,
    metadata: dict,
    export_dir: str = DEFAULT_EXPORT_DIR,
) -> str:
    """
    Export a text summary report with metadata.
 
    Args:
        url: Source URL.
        summary: AI-generated summary text.
        metadata: Page metadata dict.
        export_dir: Output directory.
 
    Returns:
        Full path to the report file.
    """
    export_path = _ensure_export_dir(export_dir)
    filename = _timestamp_filename("summary_report", "txt")
    full_path = export_path / filename
 
    report_lines = [
        "=" * 60,
        "WEB SCRAPING AI BOT — SUMMARY REPORT",
        "=" * 60,
        f"Generated: {datetime.now().isoformat()}",
        f"Source URL: {url}",
        "-" * 60,
        "PAGE METADATA:",
        *[f"  {k}: {v}" for k, v in metadata.items() if v],
        "-" * 60,
        "AI SUMMARY:",
        "",
        summary,
        "=" * 60,
    ]
 
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
 
        logger.info(f"[Exporter] Summary report saved: {full_path}")
        return str(full_path)
 
    except IOError as e:
        logger.error(f"[Exporter] Report export failed: {e}")
        raise
 