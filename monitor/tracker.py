
"""
tracker.py
----------
Developer-built: Live data tracking engine.
Scrapes a URL every 60 seconds, compares with previous snapshot,
detects changes, and triggers alerts.
Zero AI involved — pure scraping + comparison logic.
"""
 
import time
import logging
import hashlib
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
 
logger = logging.getLogger(__name__)
 
 
def _fingerprint(records: list) -> str:
    """MD5 fingerprint of records for change detection."""
    content = json.dumps(records, sort_keys=True, default=str)
    return hashlib.md5(content.encode()).hexdigest()
 
 
def detect_changes(
    previous: List[Dict],
    current: List[Dict],
    key_field: Optional[str] = None,
    value_fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compare two snapshots and detect what changed.
 
    Developer-built: field-level diff logic.
 
    Args:
        previous: Previous snapshot records.
        current: Current snapshot records.
        key_field: Field to match records by (e.g. 'name', 'symbol').
        value_fields: Fields to watch for changes (e.g. 'price', 'revenue').
 
    Returns:
        Dict with added, removed, changed records and change summary.
    """
    changes = {
        "timestamp": datetime.now().isoformat(),
        "added": [],
        "removed": [],
        "changed": [],
        "unchanged_count": 0,
        "total_changes": 0,
        "has_changes": False,
    }
 
    if not previous and not current:
        return changes
 
    if not previous:
        changes["added"] = current
        changes["total_changes"] = len(current)
        changes["has_changes"] = True
        return changes
 
    if not current:
        changes["removed"] = previous
        changes["total_changes"] = len(previous)
        changes["has_changes"] = True
        return changes
 
    # Auto-detect key field if not specified
    if not key_field and previous:
        # Try common key fields
        for candidate in ["name", "symbol", "title", "company", "id", "rank"]:
            if candidate in previous[0]:
                key_field = candidate
                break
        if not key_field:
            key_field = list(previous[0].keys())[0]
 
    # Build lookup maps
    prev_map = {str(r.get(key_field, i)): r for i, r in enumerate(previous)}
    curr_map = {str(r.get(key_field, i)): r for i, r in enumerate(current)}
 
    prev_keys = set(prev_map.keys())
    curr_keys = set(curr_map.keys())
 
    # Added records
    for key in curr_keys - prev_keys:
        changes["added"].append(curr_map[key])
 
    # Removed records
    for key in prev_keys - curr_keys:
        changes["removed"].append(prev_map[key])
 
    # Changed records
    for key in prev_keys & curr_keys:
        prev_rec = prev_map[key]
        curr_rec = curr_map[key]
 
        field_changes = []
        watch_fields = value_fields or list(curr_rec.keys())
 
        for field in watch_fields:
            prev_val = prev_rec.get(field)
            curr_val = curr_rec.get(field)
 
            if str(prev_val) != str(curr_val):
                # Try to compute numeric change
                try:
                    prev_num = float(str(prev_val).replace(",", "").replace("$", "").replace("£", "").replace("₹", "").replace("%", ""))
                    curr_num = float(str(curr_val).replace(",", "").replace("$", "").replace("£", "").replace("₹", "").replace("%", ""))
                    diff = curr_num - prev_num
                    pct_change = (diff / prev_num * 100) if prev_num != 0 else 0
                    direction = "up" if diff > 0 else "down"
                    field_changes.append({
                        "field": field,
                        "previous": prev_val,
                        "current": curr_val,
                        "diff": round(diff, 4),
                        "pct_change": round(pct_change, 2),
                        "direction": direction,
                    })
                except (ValueError, TypeError):
                    field_changes.append({
                        "field": field,
                        "previous": prev_val,
                        "current": curr_val,
                        "diff": None,
                        "pct_change": None,
                        "direction": "changed",
                    })
 
        if field_changes:
            changes["changed"].append({
                "record": curr_rec,
                "key": key,
                "field_changes": field_changes,
            })
        else:
            changes["unchanged_count"] += 1
 
    changes["total_changes"] = (
        len(changes["added"]) +
        len(changes["removed"]) +
        len(changes["changed"])
    )
    changes["has_changes"] = changes["total_changes"] > 0
 
    return changes
 
 
def check_alerts(
    changes: Dict[str, Any],
    alert_rules: List[Dict],
) -> List[Dict]:
    """
    Check if any changes trigger alert rules.
 
    Alert rule format:
    {
        "field": "price",
        "condition": "above" | "below" | "change_pct",
        "threshold": 5.0,
        "label": "Price spike alert"
    }
 
    Developer-built: rule-based alert engine.
 
    Args:
        changes: Output from detect_changes().
        alert_rules: List of alert rule dicts.
 
    Returns:
        List of triggered alerts.
    """
    triggered = []
 
    for change_record in changes.get("changed", []):
        for field_change in change_record.get("field_changes", []):
            for rule in alert_rules:
                if rule.get("field") != field_change.get("field"):
                    continue
 
                condition = rule.get("condition")
                threshold = float(rule.get("threshold", 0))
                curr_val = field_change.get("current")
                pct_change = field_change.get("pct_change")
 
                triggered_flag = False
 
                try:
                    curr_num = float(str(curr_val).replace(",", "").replace("$", "").replace("£", "").replace("₹", "").replace("%", ""))
 
                    if condition == "above" and curr_num > threshold:
                        triggered_flag = True
                    elif condition == "below" and curr_num < threshold:
                        triggered_flag = True
                    elif condition == "change_pct" and pct_change is not None and abs(pct_change) >= threshold:
                        triggered_flag = True
                except (ValueError, TypeError):
                    pass
 
                if triggered_flag:
                    triggered.append({
                        "alert": rule.get("label", f"{field_change['field']} alert"),
                        "field": field_change["field"],
                        "record_key": change_record["key"],
                        "previous": field_change["previous"],
                        "current": field_change["current"],
                        "pct_change": pct_change,
                        "direction": field_change.get("direction"),
                        "triggered_at": datetime.now().isoformat(),
                    })
 
    return triggered
 
 
class MonitorSession:
    """
    Tracks the history of snapshots for a single monitored URL.
    Stores up to 60 snapshots (60 minutes of 1-min intervals).
    Developer-built: in-memory session state manager.
    """
 
    MAX_HISTORY = 60
 
    def __init__(self, url: str, key_field: Optional[str] = None,
                 value_fields: Optional[List[str]] = None):
        self.url = url
        self.key_field = key_field
        self.value_fields = value_fields
        self.snapshots: List[Dict] = []  # List of {timestamp, records, changes}
        self.all_changes: List[Dict] = []
        self.alert_history: List[Dict] = []
        self.created_at = datetime.now().isoformat()
 
    def add_snapshot(self, records: list, alert_rules: Optional[List] = None) -> Dict:
        """
        Add a new snapshot and compute changes vs previous.
 
        Args:
            records: Newly scraped records.
            alert_rules: Optional alert rules to check.
 
        Returns:
            Change summary dict.
        """
        timestamp = datetime.now().isoformat()
 
        # Get previous records
        previous_records = self.snapshots[-1]["records"] if self.snapshots else []
 
        # Detect changes
        changes = detect_changes(
            previous_records,
            records,
            key_field=self.key_field,
            value_fields=self.value_fields,
        )
        changes["snapshot_number"] = len(self.snapshots) + 1
 
        # Check alerts
        alerts = []
        if alert_rules and changes["has_changes"]:
            alerts = check_alerts(changes, alert_rules)
            self.alert_history.extend(alerts)
 
        # Store snapshot
        snapshot = {
            "timestamp": timestamp,
            "records": records,
            "changes": changes,
            "alerts": alerts,
            "record_count": len(records),
        }
 
        self.snapshots.append(snapshot)
 
        # Keep only last MAX_HISTORY snapshots
        if len(self.snapshots) > self.MAX_HISTORY:
            self.snapshots = self.snapshots[-self.MAX_HISTORY:]
 
        if changes["has_changes"]:
            self.all_changes.append(changes)
 
        return changes
 
    def get_latest(self) -> Optional[Dict]:
        """Get the most recent snapshot."""
        return self.snapshots[-1] if self.snapshots else None
 
    def get_previous(self) -> Optional[Dict]:
        """Get the second most recent snapshot."""
        return self.snapshots[-2] if len(self.snapshots) >= 2 else None
 
    def get_price_history(self, field: str) -> List[Dict]:
        """
        Get time-series history for a specific field across all records.
        Used for sparkline/trend charts.
 
        Args:
            field: Field name to track over time.
 
        Returns:
            List of {timestamp, values} dicts.
        """
        history = []
        for snap in self.snapshots:
            values = {}
            for record in snap["records"]:
                key = str(record.get(self.key_field or list(record.keys())[0], ""))
                val = record.get(field)
                if val is not None:
                    try:
                        val = float(str(val).replace(",", "").replace("$", "").replace("£", "").replace("₹", "").replace("%", ""))
                        values[key] = val
                    except (ValueError, TypeError):
                        values[key] = val
            history.append({
                "timestamp": snap["timestamp"],
                "values": values,
            })
        return history
 
    def summary(self) -> Dict:
        """Get session summary statistics."""
        total_changes = sum(
            s["changes"]["total_changes"] for s in self.snapshots
        )
        return {
            "url": self.url,
            "snapshots_taken": len(self.snapshots),
            "total_changes_detected": total_changes,
            "total_alerts_triggered": len(self.alert_history),
            "created_at": self.created_at,
            "latest_snapshot": self.snapshots[-1]["timestamp"] if self.snapshots else None,
        }
 