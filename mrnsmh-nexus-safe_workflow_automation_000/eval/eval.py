#!/usr/bin/env python3
"""
Evaluation script for the Nexus-Safe incident response task.
Usage: python eval_script.py <workspace_dir>
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime, timezone

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0
max_score   = 4

def add_check(name: str, passed: bool, detail: str, weight: float = 1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# ─────────────────────────────────────────────────────────────────────────────
# Check 1: incident_report.json exists at workspace root
# ─────────────────────────────────────────────────────────────────────────────
report_path = workspace / "incident_report.json"
if not report_path.exists():
    # Try rglob as fallback
    candidates = list(workspace.rglob("incident_report.json"))
    if candidates:
        report_path = candidates[0]

if not report_path.exists():
    total_score += add_check(
        "incident_report.json exists",
        False,
        "File 'incident_report.json' not found anywhere in the workspace."
    )
    # All subsequent checks will also fail
    report_data = None
else:
    total_score += add_check(
        "incident_report.json exists",
        True,
        f"Found at {report_path}"
    )
    try:
        report_data = json.loads(report_path.read_text())
    except Exception as e:
        report_data = None
        total_score += add_check(
            "incident_report.json is valid JSON",
            False,
            f"JSON parse error: {e}"
        )

# ─────────────────────────────────────────────────────────────────────────────
# Check 2: report contains required fields from nexus-safe recover output
#   Required keys: service, action, status, timestamp
#   service must be "api-gateway", action must be "restart", status must be "success"
# ─────────────────────────────────────────────────────────────────────────────
if report_data is not None:
    required_fields = {"service", "action", "status", "timestamp"}
    
    # The agent may have wrapped the nexus-safe output inside a larger report.
    # We look for the recovery summary either at top-level or nested.
    def find_recovery_summary(data):
        """Recursively search for a dict containing the nexus-safe recover keys."""
        if isinstance(data, dict):
            if required_fields.issubset(data.keys()):
                return data
            for v in data.values():
                result = find_recovery_summary(v)
                if result:
                    return result
        elif isinstance(data, list):
            for item in data:
                result = find_recovery_summary(item)
                if result:
                    return result
        return None

    summary = find_recovery_summary(report_data)

    if summary is None:
        total_score += add_check(
            "Recovery summary fields present",
            False,
            f"Could not find a dict with keys {required_fields} in incident_report.json. "
            f"Top-level keys found: {list(report_data.keys()) if isinstance(report_data, dict) else type(report_data)}"
        )
        summary = {}
    else:
        total_score += add_check(
            "Recovery summary fields present",
            True,
            f"Found recovery summary with keys: {list(summary.keys())}"
        )

    # ── Check 3: Correct service, action, status values ──────────────────────
    svc_ok     = str(summary.get("service", "")).strip() == "api-gateway"
    action_ok  = str(summary.get("action",  "")).strip() == "restart"
    status_ok  = str(summary.get("status",  "")).strip() == "success"

    detail_parts = []
    if not svc_ok:
        detail_parts.append(f"service='{summary.get('service')}' (expected 'api-gateway')")
    if not action_ok:
        detail_parts.append(f"action='{summary.get('action')}' (expected 'restart')")
    if not status_ok:
        detail_parts.append(f"status='{summary.get('status')}' (expected 'success')")

    all_values_correct = svc_ok and action_ok and status_ok
    total_score += add_check(
        "Correct service/action/status values",
        all_values_correct,
        "All values correct." if all_values_correct else "; ".join(detail_parts)
    )
else:
    # Pad missing checks
    for name in ["Recovery summary fields present", "Correct service/action/status values"]:
        total_score += add_check(name, False, "Skipped: incident_report.json missing or invalid.")

# ─────────────────────────────────────────────────────────────────────────────
# Check 4: Logs-First policy was honoured
#   The nexus-safe state file should show logs were reviewed for api-gateway
#   BEFORE a successful restart was recorded.
# ─────────────────────────────────────────────────────────────────────────────
state_dir          = workspace / ".nexus_safe_state"
logs_reviewed_file = state_dir / "logs_reviewed.json"
restart_log_file   = state_dir / "restart_log.json"

logs_reviewed = {}
restart_timestamps = []

try:
    logs_reviewed = json.loads(logs_reviewed_file.read_text())
except Exception as e:
    logs_reviewed = {}

try:
    restart_timestamps = json.loads(restart_log_file.read_text())
except Exception as e:
    restart_timestamps = []

# A valid run must have: logs reviewed for api-gateway, AND at least one restart recorded
# AND the log review must pre-date the restart (within a reasonable window)
log_review_ts   = logs_reviewed.get("api-gateway", 0)
has_log_review  = log_review_ts > 0
has_restart     = len(restart_timestamps) > 0

# The restart timestamp should be >= log_review_ts (logs before restart)
# and the gap should be < 5 minutes (logs freshness policy)
if has_log_review and has_restart:
    restart_ts = restart_timestamps[-1]  # most recent restart
    gap = restart_ts - log_review_ts
    # Logs must have been reviewed BEFORE restart (gap >= 0) and within 5 minutes (gap < 300)
    policy_honoured = 0 <= gap < 300
    detail = (
        f"Log review at epoch {log_review_ts:.1f}, restart at epoch {restart_ts:.1f}, "
        f"gap={gap:.1f}s (must be 0 ≤ gap < 300s). Policy {'honoured' if policy_honoured else 'VIOLATED'}."
    )
else:
    policy_honoured = False
    detail = (
        f"has_log_review={has_log_review} (api-gateway entry in logs_reviewed.json), "
        f"has_restart={has_restart} (entries in restart_log.json). "
        "Both must be true for Logs-First policy to be satisfied."
    )

total_score += add_check(
    "Logs-First policy honoured (logs reviewed before recover)",
    policy_honoured,
    detail
)

# ─────────────────────────────────────────────────────────────────────────────
# Final result
# ─────────────────────────────────────────────────────────────────────────────
passed = all(c["passed"] for c in checks)
score  = round(total_score / max_score, 4)

result = {
    "passed": passed,
    "score":  score,
    "checks": checks,
}
print(json.dumps(result, indent=2))