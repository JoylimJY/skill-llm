#!/usr/bin/env python3
"""
Generate the sandbox workspace for the Chinese Workdays evaluation task.
The agent must fix a broken 2027.yaml, then produce a JSON report of workday counts.
"""
import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ── 1. Install the skill package into the workspace ──────────────────────────
skill_src = Path("/opt/skill")
# Create symlinks so the skill is importable from /workspace
(WORKSPACE / "chinese_workdays.py").unlink(missing_ok=True)
(WORKSPACE / "workdays_cmd.py").unlink(missing_ok=True)

import shutil

# Copy skill files into workspace
for fname in ["chinese_workdays.py", "workdays_cmd.py", "__init__.py"]:
    src = skill_src / fname
    dst = WORKSPACE / fname
    if src.exists():
        shutil.copy2(src, dst)

# Copy data directory
data_src = skill_src / "data"
data_dst = WORKSPACE / "data"
data_dst.mkdir(exist_ok=True)
if data_src.exists():
    for f in data_src.iterdir():
        shutil.copy2(f, data_dst / f.name)

# ── 2. Create a BROKEN 2027.yaml ──────────────────────────────────────────────
# The file uses WRONG field names and is missing critical makeup workdays.
# According to China's 2027 holiday schedule (typical pattern):
# The agent must produce a correct one. We intentionally corrupt it.

broken_2027 = """\
year: 2027
country: "China"
# WARNING: This file was auto-generated and contains errors. DO NOT USE AS-IS.
holidays:
  - name: "元旦"
    begin: "2027-01-01"       # WRONG field name, should be 'start'
    finish: "2027-01-03"      # WRONG field name, should be 'end'
    off_days: ["2027-01-01"]  # WRONG field name, should be 'days_off'
    # makeup_workdays is missing entirely

  - name: "春节"
    start: "2027-02-06"
    end: "2027-02-12"
    days_off: ["2027-02-06", "2027-02-07", "2027-02-08", "2027-02-09", "2027-02-10"]
    # makeup_workdays missing - crucial for correct calculation
    note: "春节假期"

  - name: "清明节"
    start: "2027-04-05"
    end: "2027-04-05"
    days_off: ["2027-04-05"]
    note: "清明节放假"

  - name: "劳动节"
    start: "2027-05-01"
    end: "2027-05-05"
    days_off: ["2027-05-01", "2027-05-02", "2027-05-03", "2027-05-04", "2027-05-05"]
    note: "劳动节假期"

  - name: "端午节"
    start: "2027-05-30"
    end: "2027-06-01"
    off_days: ["2027-05-30", "2027-05-31", "2027-06-01"]  # WRONG field name

  - name: "中秋节"
    start: "2027-09-15"
    end: "2027-09-17"
    days_off: ["2027-09-15", "2027-09-16", "2027-09-17"]
    note: "中秋节假期"

  - name: "国庆节"
    start: "2027-10-01"
    end: "2027-10-07"
    days_off: ["2027-10-01", "2027-10-02", "2027-10-03", "2027-10-04", "2027-10-05", "2027-10-06", "2027-10-07"]
    makeup_workday: ["2027-09-26", "2027-10-09"]  # WRONG field name (singular), should be 'makeup_workdays'
    note: "国庆节假期"
"""

(data_dst / "2027.yaml").write_text(broken_2027, encoding="utf-8")

# ── 3. Create distractor files ────────────────────────────────────────────────

# HR project directory structure
dirs = [
    "hr_project/reports/2026",
    "hr_project/reports/2027",
    "hr_project/planning/q1",
    "hr_project/planning/q2",
    "hr_project/raw_data",
    "hr_project/templates",
    "hr_project/archive/2025",
    "legacy_tools",
    "config",
    "notes",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractors = {
    "hr_project/reports/2026/annual_summary.txt": "2026年年度工作日报告\n总工作日: 248天（待核实）\n请勿直接使用此文件",
    "hr_project/reports/2026/q3_headcount.csv": "department,headcount,avg_workdays\nEngineering,45,62\nHR,12,61\nFinance,8,63",
    "hr_project/planning/q1/staffing_plan.md": "# Q1 2027 Staffing Plan\n\n- Need accurate workday counts\n- Contact HR operations for calendar data\n- Review local holiday regulations",
    "hr_project/planning/q2/project_milestones.txt": "Project Alpha: 120 workdays\nProject Beta: 85 workdays\n(Note: workday counts are estimates, not verified against official calendar)",
    "hr_project/raw_data/employee_list.csv": "id,name,dept,contract_start\n1001,Zhang Wei,Eng,2027-01-15\n1002,Li Na,HR,2027-03-01\n1003,Wang Fang,Finance,2027-07-01",
    "hr_project/templates/leave_request.txt": "Leave Request Form\nEmployee: ___\nDates: ___ to ___\nWorking days requested: ___",
    "hr_project/archive/2025/workday_notes.txt": "2025年调休安排备注\n元旦: 1天假\n春节: 7天假，2个调休\n注意：调休工作日必须计入工作日统计",
    "legacy_tools/old_calculator.py": "# DEPRECATED - Do not use\n# This script uses hardcoded weekends only\ndef count_workdays(start, end):\n    # WARNING: does not account for Chinese holidays\n    pass",
    "config/settings.json": json.dumps({"timezone": "Asia/Shanghai", "fiscal_year_start": "01-01", "locale": "zh_CN"}, indent=2),
    "notes/hr_manager_email.txt": "From: hr-manager@company.com\nSubject: 2027 Working Day Counts Needed\n\nPlease provide accurate working day figures for 2027.\nWe need:\n- Full year total\n- Q2 total (Apr-Jun)\n- Each month of Q2 separately (April, May, June)\n- The period from 2027-05-10 to 2027-06-30\n\nThe data file I found seems broken. Please fix it and then produce a report.\nSave results to workday_report_2027.json",
    "notes/calendar_issues.txt": "Known issues with 2027.yaml:\n- Field names appear non-standard\n- Makeup workdays missing for some holidays\n- Do not trust raw totals from this file",
}

for rel_path, content in distractors.items():
    fp = WORKSPACE / rel_path
    fp.write_text(content, encoding="utf-8")

# ── 4. Intentionally do NOT create workday_report_2027.json (agent must create it) ──
print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")