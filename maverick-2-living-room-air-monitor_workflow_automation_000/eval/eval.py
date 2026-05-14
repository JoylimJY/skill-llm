#!/usr/bin/env python3
"""
Evaluation script for the living-room-air-monitor task.

The agent must produce a file named 'march_2025_air_audit.json' containing:
  {
    "month": "2025-03",
    "averages": {
      "temperature": <float>,
      "humidity":    <float>,
      "pm25":        <float>,
      "co2":         <float>
    },
    "assessments": {
      "pm25": "Good" | "Moderate" | "Unhealthy",
      "co2":  "Good" | "Moderate" | "Poor"
    },
    "weekly_report_chars": <int>,   // length of the week-ending-2025-03-16 text report
    "weekly_report_file":  <str>    // path to saved weekly text report
  }

AND must save the weekly text report (week ending 2025-03-16) to a file named
'week_ending_20250316_report.txt' somewhere on disk.

Grading:
  1. march_2025_air_audit.json exists                          (required)
  2. averages match computed ground truth (±0.5 tolerance)     (proprietary DB path)
  3. pm25 assessment uses exact proprietary labels             (Unhealthy, not Poor)
  4. co2 assessment uses exact proprietary labels              (Poor, not Unhealthy)
  5. weekly report file exists and has substantial content     (uses generate_text_report)
  6. weekly_report_chars in JSON matches actual file length    (±50 chars)
"""

import sys
import json
import sqlite3
import math
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/root/workspace"
workspace = Path(workspace)

checks = []
score  = 0.0

# ── Ground Truth Computation ────────────────────────────────────────────────
db_path = workspace / "skills" / "living-room-air-monitor" / "data" / "air_quality.db"

def compute_ground_truth_monthly_avgs(db, year_month):
    """Compute true monthly averages directly from DB."""
    try:
        conn = sqlite3.connect(str(db))
        cur  = conn.cursor()
        cur.execute(
            "SELECT AVG(temperature), AVG(humidity), AVG(pm25), AVG(co2) "
            "FROM air_quality WHERE datetime >= ? AND datetime <= ?",
            (f"{year_month}-01 00:00:00", f"{year_month}-31 23:59:59")
        )
        row = cur.fetchone()
        conn.close()
        if row and row[0] is not None:
            return {
                "temperature": round(row[0], 2),
                "humidity":    round(row[1], 2),
                "pm25":        round(row[2], 2),
                "co2":         round(row[3], 2),
            }
    except Exception as e:
        return None
    return None

def compute_ground_truth_pm25_assessment(avg_pm25):
    if avg_pm25 is None: return "Unknown"
    if avg_pm25 <= 12:   return "Good"
    if avg_pm25 <= 35:   return "Moderate"
    return "Unhealthy"   # NOT "Poor" — proprietary label

def compute_ground_truth_co2_assessment(avg_co2):
    if avg_co2 is None:   return "Unknown"
    if avg_co2 <= 1000:   return "Good"
    if avg_co2 <= 2000:   return "Moderate"
    return "Poor"         # NOT "Unhealthy" — proprietary label

def compute_ground_truth_weekly_report(db, end_date="2025-03-16"):
    """Compute text report for week ending 2025-03-16 (2025-03-10 to 2025-03-16)."""
    try:
        conn = sqlite3.connect(str(db))
        cur  = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM air_quality WHERE datetime >= ? AND datetime <= ?",
            ("2025-03-10 00:00:00", "2025-03-16 23:59:59")
        )
        row = cur.fetchone()
        conn.close()
        return row[0] if row else 0
    except:
        return 0

gt_avgs = compute_ground_truth_monthly_avgs(db_path, "2025-03")
gt_pm25_label = compute_ground_truth_pm25_assessment(gt_avgs["pm25"] if gt_avgs else None)
gt_co2_label  = compute_ground_truth_co2_assessment(gt_avgs["co2"]  if gt_avgs else None)
gt_weekly_row_count = compute_ground_truth_weekly_report(db_path)


# ── CHECK 1: Find march_2025_air_audit.json ─────────────────────────────────
audit_files = list(Path("/").rglob("march_2025_air_audit.json"))
# Also search workspace
audit_files += list(workspace.rglob("march_2025_air_audit.json"))
audit_files  = list({str(f): f for f in audit_files}.values())  # deduplicate

if not audit_files:
    checks.append({
        "name": "audit_json_exists",
        "passed": False,
        "detail": "march_2025_air_audit.json not found anywhere on the filesystem"
    })
    # Can't continue most checks
    audit_data = None
else:
    audit_path = audit_files[0]
    try:
        audit_data = json.loads(audit_path.read_text())
        checks.append({
            "name": "audit_json_exists",
            "passed": True,
            "detail": f"Found at {audit_path}"
        })
    except Exception as e:
        audit_data = None
        checks.append({
            "name": "audit_json_exists",
            "passed": False,
            "detail": f"Found but failed to parse JSON: {e}"
        })


# ── CHECK 2: month field ────────────────────────────────────────────────────
if audit_data is not None:
    month_ok = audit_data.get("month") == "2025-03"
    checks.append({
        "name": "month_field_correct",
        "passed": month_ok,
        "detail": f"month={audit_data.get('month')!r}, expected '2025-03'"
    })
else:
    checks.append({"name": "month_field_correct", "passed": False, "detail": "No audit data"})


# ── CHECK 3: averages correct (tolerance ±0.5) ──────────────────────────────
avg_checks_passed = False
if audit_data is not None and gt_avgs is not None:
    avgs = audit_data.get("averages", {})
    tol  = 0.5
    results = {}
    all_ok  = True
    for metric in ["temperature", "humidity", "pm25", "co2"]:
        agent_val = avgs.get(metric)
        gt_val    = gt_avgs[metric]
        if agent_val is None:
            results[metric] = f"MISSING (expected ~{gt_val})"
            all_ok = False
        elif abs(float(agent_val) - float(gt_val)) > tol:
            results[metric] = f"{agent_val} (expected ~{gt_val}, diff={abs(float(agent_val)-float(gt_val)):.3f})"
            all_ok = False
        else:
            results[metric] = f"OK ({agent_val} ≈ {gt_val})"
    avg_checks_passed = all_ok
    checks.append({
        "name": "monthly_averages_correct",
        "passed": all_ok,
        "detail": str(results)
    })
elif gt_avgs is None:
    checks.append({
        "name": "monthly_averages_correct",
        "passed": False,
        "detail": "Could not compute ground truth (DB issue)"
    })
else:
    checks.append({"name": "monthly_averages_correct", "passed": False, "detail": "No audit data"})


# ── CHECK 4: PM2.5 assessment label (proprietary: "Unhealthy" not "Poor") ──
pm25_label_ok = False
if audit_data is not None:
    assessments = audit_data.get("assessments", {})
    agent_pm25  = assessments.get("pm25", "")
    pm25_label_ok = (agent_pm25 == gt_pm25_label)
    checks.append({
        "name": "pm25_assessment_label_proprietary",
        "passed": pm25_label_ok,
        "detail": f"agent='{agent_pm25}', expected='{gt_pm25_label}'. "
                  f"Note: PM2.5 >35 = 'Unhealthy' (not 'Poor') per skill spec"
    })
else:
    checks.append({
        "name": "pm25_assessment_label_proprietary",
        "passed": False,
        "detail": "No audit data"
    })


# ── CHECK 5: CO2 assessment label (proprietary: "Poor" not "Unhealthy") ────
co2_label_ok = False
if audit_data is not None:
    assessments = audit_data.get("assessments", {})
    agent_co2   = assessments.get("co2", "")
    co2_label_ok = (agent_co2 == gt_co2_label)
    checks.append({
        "name": "co2_assessment_label_proprietary",
        "passed": co2_label_ok,
        "detail": f"agent='{agent_co2}', expected='{gt_co2_label}'. "
                  f"Note: CO2 >2000 = 'Poor' (not 'Unhealthy') per skill spec"
    })
else:
    checks.append({
        "name": "co2_assessment_label_proprietary",
        "passed": False,
        "detail": "No audit data"
    })


# ── CHECK 6: Weekly report file exists ──────────────────────────────────────
weekly_files = list(Path("/").rglob("week_ending_20250316_report.txt"))
weekly_files += list(workspace.rglob("week_ending_20250316_report.txt"))
weekly_files  = list({str(f): f for f in weekly_files}.values())

weekly_content = None
weekly_file_ok = False
if weekly_files:
    try:
        weekly_content = weekly_files[0].read_text()
        weekly_file_ok = len(weekly_content) > 200  # Must have substantial content
        checks.append({
            "name": "weekly_report_file_exists",
            "passed": weekly_file_ok,
            "detail": f"Found at {weekly_files[0]}, length={len(weekly_content)} chars"
        })
    except Exception as e:
        checks.append({
            "name": "weekly_report_file_exists",
            "passed": False,
            "detail": f"Found but failed to read: {e}"
        })
else:
    checks.append({
        "name": "weekly_report_file_exists",
        "passed": False,
        "detail": "week_ending_20250316_report.txt not found anywhere on filesystem"
    })


# ── CHECK 7: Weekly report covers correct date range ──────────────────────
weekly_range_ok = False
if weekly_content is not None:
    # Must contain dates from 2025-03-10 and 2025-03-16
    has_start = "2025-03-10" in weekly_content
    has_end   = "2025-03-16" in weekly_content
    weekly_range_ok = has_start and has_end
    checks.append({
        "name": "weekly_report_correct_date_range",
        "passed": weekly_range_ok,
        "detail": f"Contains '2025-03-10'={has_start}, '2025-03-16'={has_end}"
    })
else:
    checks.append({
        "name": "weekly_report_correct_date_range",
        "passed": False,
        "detail": "No weekly report content to check"
    })


# ── CHECK 8: weekly_report_chars field consistency ─────────────────────────
chars_ok = False
if audit_data is not None and weekly_content is not None:
    reported_chars = audit_data.get("weekly_report_chars")
    actual_chars   = len(weekly_content)
    if reported_chars is not None:
        chars_ok = abs(int(reported_chars) - actual_chars) <= 50
        checks.append({
            "name": "weekly_report_chars_consistent",
            "passed": chars_ok,
            "detail": f"reported={reported_chars}, actual={actual_chars}, diff={abs(int(reported_chars)-actual_chars)}"
        })
    else:
        checks.append({
            "name": "weekly_report_chars_consistent",
            "passed": False,
            "detail": "weekly_report_chars field missing from JSON"
        })
elif audit_data is None:
    checks.append({"name": "weekly_report_chars_consistent", "passed": False, "detail": "No audit data"})
else:
    checks.append({"name": "weekly_report_chars_consistent", "passed": False, "detail": "No weekly report content"})


# ── CHECK 9: weekly_report contains air quality assessment section ──────────
assessment_ok = False
if weekly_content is not None:
    assessment_ok = "AIR QUALITY ASSESSMENT" in weekly_content or "assessment" in weekly_content.lower()
    checks.append({
        "name": "weekly_report_has_assessment",
        "passed": assessment_ok,
        "detail": "Weekly report must include air quality assessment section (from generate_text_report)"
    })
else:
    checks.append({
        "name": "weekly_report_has_assessment",
        "passed": False,
        "detail": "No weekly report content"
    })


# ── Scoring ──────────────────────────────────────────────────────────────────
# Weights (must sum to 1.0):
weights = {
    "audit_json_exists":                0.10,
    "month_field_correct":              0.05,
    "monthly_averages_correct":         0.25,
    "pm25_assessment_label_proprietary": 0.15,
    "co2_assessment_label_proprietary":  0.15,
    "weekly_report_file_exists":         0.10,
    "weekly_report_correct_date_range":  0.08,
    "weekly_report_chars_consistent":    0.07,
    "weekly_report_has_assessment":      0.05,
}

total_score = 0.0
for check in checks:
    w = weights.get(check["name"], 0.0)
    if check["passed"]:
        total_score += w

result = {
    "passed": total_score >= 0.70,
    "score":  round(total_score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2))