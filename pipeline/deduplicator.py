"""
deduplicator.py
---------------
Developer-built: Record cleaning, deduplication, and None value handling.
All processing done locally — zero AI needed.
"""

import hashlib
import json
import logging
import re
from typing import List, Dict, Any, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def _record_fingerprint(record: dict, key_fields: Optional[List[str]] = None) -> str:
    if key_fields:
        subset = {k: record.get(k) for k in key_fields if k in record}
        content = json.dumps(subset, sort_keys=True, ensure_ascii=False)
    else:
        content = json.dumps(record, sort_keys=True, ensure_ascii=False)
    return hashlib.md5(content.encode("utf-8")).hexdigest()


def deduplicate(
    records: List[Dict[str, Any]],
    key_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Remove duplicate records."""
    if not records:
        return []
    seen = set()
    unique = []
    dupes = 0
    for record in records:
        if not isinstance(record, dict):
            unique.append(record)
            continue
        fp = _record_fingerprint(record, key_fields)
        if fp not in seen:
            seen.add(fp)
            unique.append(record)
        else:
            dupes += 1
    if dupes:
        logger.info(f"[Deduplicator] Removed {dupes} duplicates")
    return unique


def clean_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Developer-built: Clean extracted records locally without any AI.

    Steps:
    1. Remove records that are ALL None values
    2. Drop columns where 80%+ values are None
    3. Fill remaining None with 'N/A'
    4. Flatten nested lists/dicts to strings
    5. Strip extra whitespace
    """
    if not records:
        return []

    # Step 1 — Remove fully empty records
    cleaned = []
    for record in records:
        if not isinstance(record, dict):
            continue
        # Keep record if at least 2 fields have real values
        real_values = sum(
            1 for v in record.values()
            if v is not None and v != "" and v != [] and v != {}
        )
        if real_values >= 2:
            cleaned.append(record)

    if not cleaned:
        return records  # Return original if all got filtered

    # Step 2 — Find columns with too many Nones (>80%)
    all_keys = set()
    for r in cleaned:
        all_keys.update(r.keys())

    columns_to_drop = set()
    for key in all_keys:
        none_count = sum(
            1 for r in cleaned
            if r.get(key) is None or r.get(key) == ""
        )
        none_pct = none_count / len(cleaned)
        if none_pct > 0.8:
            columns_to_drop.add(key)

    # Step 3 — Clean each record
    result = []
    for record in cleaned:
        clean_record = {}
        for key, value in record.items():
            # Skip mostly-empty columns
            if key in columns_to_drop:
                continue

            # Flatten nested structures
            if isinstance(value, list):
                if len(value) == 0:
                    value = "N/A"
                elif all(isinstance(v, str) for v in value):
                    value = ", ".join(value)
                elif all(isinstance(v, dict) for v in value):
                    value = "; ".join(
                        ", ".join(f"{k}:{v}" for k, v in item.items())
                        for item in value[:3]
                    )
                else:
                    value = str(value)
            elif isinstance(value, dict):
                value = ", ".join(f"{k}: {v}" for k, v in value.items())
            elif value is None or value == "":
                value = "N/A"
            elif isinstance(value, bool):
                value = "Yes" if value else "No"
            elif isinstance(value, str):
                value = value.strip()

            clean_record[key] = value

        if clean_record:
            result.append(clean_record)

    logger.info(f"[Cleaner] Cleaned {len(records)} → {len(result)} records, dropped {len(columns_to_drop)} empty columns")
    return result


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Developer-built: Clean a DataFrame locally.
    - Drop columns with 80%+ None/NaN
    - Fill remaining NaN with 'N/A'
    - Strip string whitespace
    """
    if df.empty:
        return df

    # Drop columns that are mostly empty
    threshold = 0.8
    min_non_null = len(df) * (1 - threshold)
    df = df.dropna(axis=1, thresh=max(1, int(min_non_null)))

    # Fill remaining NaN
    df = df.fillna("N/A")

    # Strip string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].astype(str).str.strip()

    return df


def merge_and_deduplicate(
    *record_lists: List[Dict[str, Any]],
    key_fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Merge multiple record lists and deduplicate."""
    combined = []
    for record_list in record_lists:
        if isinstance(record_list, list):
            combined.extend(record_list)
    return deduplicate(combined, key_fields=key_fields)
