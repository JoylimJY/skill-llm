#!/usr/bin/env python3
"""
Evaluation script for meshtastic detection skill task.
Checks that the agent produced detection_summary.json with correct values
derived from both sensor_cli.py stats --since 24h AND event_monitor.py.
"""

import json
import sys
from pathlib import Path

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

    checks = []
    total_score = 0.0
    max_score = 6.0

    # Load ground truth
    ground_truth_path = workspace / "data" / "_ground_truth.json"
    try:
        gt = json.loads(ground_truth_path.read_text())
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "ground_truth_load", "passed": False,
                        "detail": f"Could not load ground truth: {e}"}]
        }))
        return

    expected_total_24h = gt["total_detections_24h"]
    expected_unique_senders = gt["unique_senders_24h"]
    expected_new_alerts = gt["new_alert_count_from_monitor"]

    # ── Find detection_summary.json ──────────────────────────────────────────
    summary_files = list(workspace.rglob("detection_summary.json"))
    if not summary_files:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False,
                        "detail": "detection_summary.json not found anywhere in workspace"}]
        }))
        return

    summary_path = summary_files[0]
    checks.append({
        "name": "file_exists",
        "passed": True,
        "detail": f"Found detection_summary.json at {summary_path}"
    })
    total_score += 0.5

    # ── Parse the JSON ────────────────────────────────────────────────────────
    try:
        summary = json.loads(summary_path.read_text())
    except Exception as e:
        checks.append({"name": "file_parseable", "passed": False,
                        "detail": f"JSON parse error: {e}"})
        print(json.dumps({"passed": False, "score": total_score / max_score,
                          "checks": checks}))
        return

    checks.append({"name": "file_parseable", "passed": True,
                   "detail": "detection_summary.json is valid JSON"})
    total_score += 0.5

    # ── Check 1: total_detections_24h ────────────────────────────────────────
    field_candidates = ["total_detections_24h", "total_detections", "detections_24h",
                        "total_detection_count", "detection_count_24h"]
    found_total = None
    found_total_key = None
    for k in field_candidates:
        if k in summary:
            found_total = summary[k]
            found_total_key = k
            break
    # Also search nested
    if found_total is None:
        for v in summary.values():
            if isinstance(v, dict):
                for k in field_candidates:
                    if k in v:
                        found_total = v[k]
                        found_total_key = k
                        break

    if found_total is not None and int(found_total) == expected_total_24h:
        checks.append({
            "name": "total_detections_24h_correct",
            "passed": True,
            "detail": f"Field '{found_total_key}' = {found_total} (expected {expected_total_24h})"
        })
        total_score += 1.5
    else:
        actual_display = found_total if found_total is not None else "field not found"
        checks.append({
            "name": "total_detections_24h_correct",
            "passed": False,
            "detail": f"Expected total_detections_24h={expected_total_24h}, got {actual_display}"
        })

    # ── Check 2: unique_senders_24h ──────────────────────────────────────────
    sender_candidates = ["unique_senders", "unique_senders_24h", "unique_sender_count",
                         "distinct_senders", "sender_count"]
    found_senders = None
    found_senders_key = None
    for k in sender_candidates:
        if k in summary:
            found_senders = summary[k]
            found_senders_key = k
            break
    if found_senders is None:
        for v in summary.values():
            if isinstance(v, dict):
                for k in sender_candidates:
                    if k in v:
                        found_senders = v[k]
                        found_senders_key = k
                        break

    if found_senders is not None and int(found_senders) == expected_unique_senders:
        checks.append({
            "name": "unique_senders_24h_correct",
            "passed": True,
            "detail": f"Field '{found_senders_key}' = {found_senders} (expected {expected_unique_senders})"
        })
        total_score += 1.5
    else:
        actual_display = found_senders if found_senders is not None else "field not found"
        checks.append({
            "name": "unique_senders_24h_correct",
            "passed": False,
            "detail": f"Expected unique_senders={expected_unique_senders}, got {actual_display}"
        })

    # ── Check 3: new_alert_count from event_monitor (incremental) ───────────
    alert_candidates = ["new_alerts", "new_alert_count", "unreviewed_alerts",
                        "incremental_alert_count", "alerts_since_last_check",
                        "alert_count", "new_detection_alerts"]
    found_alerts = None
    found_alerts_key = None
    for k in alert_candidates:
        if k in summary:
            found_alerts = summary[k]
            found_alerts_key = k
            break
    if found_alerts is None:
        for v in summary.values():
            if isinstance(v, dict):
                for k in alert_candidates:
                    if k in v:
                        found_alerts = v[k]
                        found_alerts_key = k
                        break

    if found_alerts is not None and int(found_alerts) == expected_new_alerts:
        checks.append({
            "name": "new_alerts_from_monitor_correct",
            "passed": True,
            "detail": (f"Field '{found_alerts_key}' = {found_alerts} "
                       f"(expected {expected_new_alerts} — correctly uses incremental monitor offset)")
        })
        total_score += 1.5
    else:
        actual_display = found_alerts if found_alerts is not None else "field not found"
        checks.append({
            "name": "new_alerts_from_monitor_correct",
            "passed": False,
            "detail": (
                f"Expected new_alert_count={expected_new_alerts} (from event_monitor.py incremental read), "
                f"got {actual_display}. "
                f"Note: A naive count of all DETECTION records would be wrong "
                f"({gt['total_detection_records_all']} total). "
                f"The monitor offset was pre-set to skip the first 20 lines."
            )
        })

    # ── Final verdict ─────────────────────────────────────────────────────────
    score_normalized = round(total_score / max_score, 4)
    passed = total_score >= 4.5  # Must get file + parse + at least 2 of 3 numeric checks

    print(json.dumps({
        "passed": passed,
        "score": score_normalized,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()