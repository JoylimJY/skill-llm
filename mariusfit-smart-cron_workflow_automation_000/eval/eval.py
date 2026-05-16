#!/usr/bin/env python3
"""
Evaluation script for the smart-cron scheduling task.
Checks:
1. All 5 jobs are scheduled (by verifying job DB or the report file)
2. Jobs C and D are paused; Jobs A, B, E are active
3. Schedule expressions produce correct cron strings
4. Timezone is correctly applied to Jobs A and C (Europe/Bucharest)
5. config.json has correct values: alert_channel=telegram, alert_on_failure=true, log_retention_days=60, default_timezone=Europe/Bucharest
6. scheduled_jobs_report.json exists and is valid
"""

import sys
import json
import sqlite3
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
home = Path.home()
data_dir = home / ".openclaw" / "workspace" / "smart-cron-data"
db_path = data_dir / "jobs.db"
config_path = data_dir / "config.json"

checks = []
total_score = 0.0

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed


def read_jobs():
    if not db_path.exists():
        return None, "Database not found at ~/.openclaw/workspace/smart-cron-data/jobs.db"
    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM jobs").fetchall()
        conn.close()
        return [dict(r) for r in rows], None
    except Exception as e:
        return None, str(e)


# ======== CHECK 1: Database exists and has jobs ========
jobs, err = read_jobs()
if add_check(
    "Database exists with jobs",
    jobs is not None and len(jobs) >= 5,
    f"Found {len(jobs) if jobs else 0} jobs. Error: {err}" if err or not jobs else f"Found {len(jobs)} jobs."
):
    total_score += 0.10


# ======== CHECK 2: All 5 expected tasks are present ========
EXPECTED_TASKS = {
    "A": "check all apis and alert if any is down",
    "B": "generate monthly financial reconciliation report",
    "C": "scan and quarantine suspicious transactions",
    "D": "archive old payment logs and compress audit trail",
    "E": "sync fraud model weights from model registry",
}

def task_matches(db_task, expected_fragment):
    """Check if a DB task name loosely matches an expected task."""
    db_lower = db_task.lower().strip()
    # Accept partial keyword matches
    key_words = {
        "A": ["api", "alert", "down"],
        "B": ["monthly", "reconcil", "report"],
        "C": ["suspicious", "transact", "quarantin"],
        "D": ["archive", "payment", "log"],
        "E": ["fraud", "model", "sync", "weight"],
    }
    return expected_fragment

found_jobs = {}
if jobs:
    keyword_map = {
        "A": ["api", "alert", "down"],
        "B": ["monthly", "reconcil", "report"],
        "C": ["suspicious", "transact", "quarantin", "scan"],
        "D": ["archive", "payment", "log", "compress"],
        "E": ["fraud", "model", "sync", "weight"],
    }
    for job in jobs:
        task_lower = job["task"].lower()
        for label, keywords in keyword_map.items():
            if label not in found_jobs and sum(1 for k in keywords if k in task_lower) >= 2:
                found_jobs[label] = job

all_tasks_found = len(found_jobs) == 5
add_check(
    "All 5 required jobs are scheduled",
    all_tasks_found,
    f"Found job labels: {list(found_jobs.keys())}. Missing: {[k for k in 'ABCDE' if k not in found_jobs]}"
)
if all_tasks_found:
    total_score += 0.15


# ======== CHECK 3: Jobs C and D are paused ========
jobs_c_paused = found_jobs.get("C", {}).get("status") == "paused"
jobs_d_paused = found_jobs.get("D", {}).get("status") == "paused"
add_check(
    "Job C (suspicious transactions) is paused",
    jobs_c_paused,
    f"Job C status: {found_jobs.get('C', {}).get('status', 'NOT FOUND')}"
)
add_check(
    "Job D (archive logs) is paused",
    jobs_d_paused,
    f"Job D status: {found_jobs.get('D', {}).get('status', 'NOT FOUND')}"
)
if jobs_c_paused:
    total_score += 0.075
if jobs_d_paused:
    total_score += 0.075


# ======== CHECK 4: Jobs A, B, E are active ========
jobs_a_active = found_jobs.get("A", {}).get("status") == "active"
jobs_b_active = found_jobs.get("B", {}).get("status") == "active"
jobs_e_active = found_jobs.get("E", {}).get("status") == "active"
add_check(
    "Jobs A, B, E are active",
    jobs_a_active and jobs_b_active and jobs_e_active,
    f"A:{found_jobs.get('A', {}).get('status','?')} B:{found_jobs.get('B', {}).get('status','?')} E:{found_jobs.get('E', {}).get('status','?')}"
)
if jobs_a_active and jobs_b_active and jobs_e_active:
    total_score += 0.10


# ======== CHECK 5: Cron expressions are correct ========
def check_cron(job, expected_pattern, label):
    if not job:
        return False, f"Job {label} not found"
    cron = job.get("cron_expr", "")
    if re.fullmatch(expected_pattern, cron):
        return True, f"Cron '{cron}' matches expected pattern '{expected_pattern}'"
    return False, f"Job {label} cron '{cron}' does not match expected '{expected_pattern}'"

# Job A: every 5 minutes → */5 * * * *
passed_a_cron, detail_a_cron = check_cron(found_jobs.get("A"), r"\*/5 \* \* \* \*", "A")
add_check("Job A cron expression (*/5 * * * *)", passed_a_cron, detail_a_cron)
if passed_a_cron: total_score += 0.05

# Job B: 1st of month at 9am → 0 9 1 * *
passed_b_cron, detail_b_cron = check_cron(found_jobs.get("B"), r"0 9 1 \* \*", "B")
add_check("Job B cron expression (0 9 1 * *)", passed_b_cron, detail_b_cron)
if passed_b_cron: total_score += 0.05

# Job C: every weekday at 6pm → 0 18 * * 1-5
passed_c_cron, detail_c_cron = check_cron(found_jobs.get("C"), r"0 18 \* \* 1-5", "C")
add_check("Job C cron expression (0 18 * * 1-5)", passed_c_cron, detail_c_cron)
if passed_c_cron: total_score += 0.05

# Job D: every weekend at noon → 0 12 * * 6,0
passed_d_cron, detail_d_cron = check_cron(found_jobs.get("D"), r"0 12 \* \* 6,0", "D")
add_check("Job D cron expression (0 12 * * 6,0)", passed_d_cron, detail_d_cron)
if passed_d_cron: total_score += 0.05

# Job E: every hour → 0 * * * *
passed_e_cron, detail_e_cron = check_cron(found_jobs.get("E"), r"0 \* \* \* \*", "E")
add_check("Job E cron expression (0 * * * *)", passed_e_cron, detail_e_cron)
if passed_e_cron: total_score += 0.05


# ======== CHECK 6: Timezone for Jobs A and C ========
tz_a = found_jobs.get("A", {}).get("timezone", "")
tz_c = found_jobs.get("C", {}).get("timezone", "")
tz_a_correct = "Europe/Bucharest" in tz_a
tz_c_correct = "Europe/Bucharest" in tz_c
add_check(
    "Job A timezone is Europe/Bucharest",
    tz_a_correct,
    f"Job A timezone: '{tz_a}'"
)
add_check(
    "Job C timezone is Europe/Bucharest",
    tz_c_correct,
    f"Job C timezone: '{tz_c}'"
)
if tz_a_correct: total_score += 0.05
if tz_c_correct: total_score += 0.05


# ======== CHECK 7: config.json is correctly configured ========
config_checks_passed = 0
config_detail = []
try:
    config = json.loads(config_path.read_text())
    
    if config.get("alert_channel") == "telegram":
        config_checks_passed += 1
        config_detail.append("alert_channel=telegram ✓")
    else:
        config_detail.append(f"alert_channel='{config.get('alert_channel')}' (expected 'telegram') ✗")
    
    if config.get("alert_on_failure") is True:
        config_checks_passed += 1
        config_detail.append("alert_on_failure=true ✓")
    else:
        config_detail.append(f"alert_on_failure={config.get('alert_on_failure')} (expected true) ✗")
    
    if config.get("log_retention_days") == 60:
        config_checks_passed += 1
        config_detail.append("log_retention_days=60 ✓")
    else:
        config_detail.append(f"log_retention_days={config.get('log_retention_days')} (expected 60) ✗")
    
    if config.get("default_timezone") == "Europe/Bucharest":
        config_checks_passed += 1
        config_detail.append("default_timezone=Europe/Bucharest ✓")
    else:
        config_detail.append(f"default_timezone='{config.get('default_timezone')}' (expected 'Europe/Bucharest') ✗")
    
except FileNotFoundError:
    config_detail.append(f"config.json not found at {config_path}")
except Exception as e:
    config_detail.append(f"Error reading config.json: {e}")

config_all_correct = config_checks_passed == 4
add_check(
    "config.json fully correct (alert_channel=telegram, alert_on_failure=true, log_retention_days=60, default_timezone=Europe/Bucharest)",
    config_all_correct,
    "; ".join(config_detail)
)
if config_all_correct:
    total_score += 0.15
elif config_checks_passed >= 2:
    total_score += 0.05


# ======== CHECK 8: scheduled_jobs_report.json exists and is valid ========
report_files = list(workspace.rglob("scheduled_jobs_report.json"))
report_ok = False
report_detail = "File not found"

if report_files:
    report_path = report_files[0]
    try:
        report = json.loads(report_path.read_text())
        # Must be a list or dict containing job info
        is_list = isinstance(report, list)
        is_dict_with_jobs = isinstance(report, dict) and any(
            k in report for k in ["jobs", "scheduled_jobs", "tasks"]
        )
        
        jobs_data = report if is_list else report.get("jobs", report.get("scheduled_jobs", report.get("tasks", [])))
        
        if isinstance(jobs_data, list) and len(jobs_data) >= 5:
            # Check that it has job IDs and statuses
            sample = jobs_data[0] if jobs_data else {}
            has_id = any(k in sample for k in ["id", "job_id", "jobId"])
            has_status = any(k in sample for k in ["status", "state"])
            has_alert = any(k in sample for k in ["alert_channel", "alert"]) or \
                        "alert_channel" in report or "alert" in str(report)
            
            if has_id and has_status:
                report_ok = True
                report_detail = f"Valid report with {len(jobs_data)} jobs at {report_path}. Has ID: {has_id}, Status: {has_status}, Alert info: {has_alert}"
            else:
                report_detail = f"Report found but missing required fields. Has ID: {has_id}, Has status: {has_status}"
        else:
            report_detail = f"Report found at {report_path} but doesn't have expected structure (got {type(jobs_data).__name__} with {len(jobs_data) if isinstance(jobs_data, list) else '?'} items)"
    except Exception as e:
        report_detail = f"Error parsing report: {e}"

add_check(
    "scheduled_jobs_report.json exists and contains valid job summary",
    report_ok,
    report_detail
)
if report_ok:
    total_score += 0.10


# ======== FINAL RESULT ========
overall_passed = (
    (jobs is not None and len(jobs) >= 5) and
    all_tasks_found and
    jobs_c_paused and jobs_d_paused and
    jobs_a_active and jobs_b_active and jobs_e_active and
    config_all_correct and
    report_ok
)

total_score = min(1.0, round(total_score, 4))

result = {
    "passed": overall_passed,
    "score": total_score,
    "checks": checks
}
print(json.dumps(result, indent=2))