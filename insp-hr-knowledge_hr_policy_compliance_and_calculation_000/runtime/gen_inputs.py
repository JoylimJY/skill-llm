import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# --- Directory structure with distractor files ---
dirs = [
    "hr_cases/li_wei",
    "hr_cases/zhang_san",
    "hr_cases/archive",
    "finance/invoices/2026_02",
    "finance/invoices/2026_03",
    "finance/reports",
    "attendance/raw_logs",
    "attendance/processed",
    "policies/old_versions",
    "policies/current",
    "onboarding/templates",
    "offboarding/templates",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# --- Distractor files ---
distractors = {
    "hr_cases/zhang_san/attendance_march.txt": "Zhang San attendance: all normal, no issues.",
    "hr_cases/archive/Q4_2025_summary.txt": "Q4 2025 HR summary archived.",
    "finance/reports/monthly_summary_feb.txt": "February 2026 finance summary report.",
    "attendance/processed/batch_jan.json": json.dumps({"month": "2026-01", "processed": True}),
    "policies/old_versions/attendance_2024.txt": "Old policy: Late fee 30 yuan per instance (DEPRECATED).",
    "policies/current/welfare.txt": "Staff welfare policy: annual health check, team building budget.",
    "onboarding/templates/checklist.txt": "Onboarding checklist template - sign handbook, get badge, open accounts.",
    "offboarding/templates/handover_table1_template.txt": "Table 1: Project Handover - Project ID, Status, Assignee.",
    "offboarding/templates/handover_table2_template.txt": "Table 2: Loans outstanding - Amount, Date, Purpose.",
    "offboarding/templates/handover_table3_template.txt": "Table 3: Rebate details - Project ID, Rebate Amount, Received Date.",
    "finance/invoices/2026_02/inv_001.txt": "Invoice #INV2026020001: Client entertainment 3 persons, total 480 RMB. Date: 2026-02-15",
    "attendance/raw_logs/template.txt": "Format: date, type(in/out/waijin), timestamp",
}
for path, content in distractors.items():
    with open(os.path.join(WORKSPACE, path), "w", encoding="utf-8") as f:
        f.write(content)

# --- Employee profile for Li Wei ---
# Li Wei: confirmed employee (转正), has an outstanding loan (借款), and has rebates (返点)
employee_profile = {
    "name": "李威 (Li Wei)",
    "employee_id": "EMP20240312",
    "status": "confirmed",  # 转正员工
    "department": "Sales & BD",
    "position": "Manager",  # 经理级
    "resignation_email_sent_date": "2026-03-10",  # Monday
    "desired_last_day": "2026-03-20",  # 10 days notice
    "has_outstanding_loan": True,
    "loan_amount_rmb": 3500,
    "has_rebates_to_collect": True,
    "notes": "Employee is a media buyer (媒介). Has outstanding project loans and pending rebates."
}
with open(os.path.join(WORKSPACE, "hr_cases/li_wei/employee_profile.json"), "w", encoding="utf-8") as f:
    json.dump(employee_profile, f, ensure_ascii=False, indent=2)

# --- Attendance log for Li Wei (March 2026) ---
# Official hours: Start 09:30-10:00, End 18:30-19:00
# For our purposes, we'll treat standard end as 18:30
# Weekday OT: starts 30 min after 18:30 = 19:00, minimum 1 hour, 1:1 ratio
# Weekend OT: minimum 2 continuous hours, 1:0.7 ratio

# March 2026 calendar context:
# Mar 2 (Mon), Mar 3(Tue), Mar 4(Wed), Mar 5(Thu), Mar 6(Fri) - weekdays
# Mar 7(Sat), Mar 8(Sun) - weekend
# Mar 9(Mon), Mar 10(Tue), Mar 11(Wed), Mar 12(Thu), Mar 13(Fri)
# Mar 14(Sat), Mar 15(Sun) - weekend
# Mar 16(Mon), Mar 17(Tue), Mar 18(Wed), Mar 19(Thu), Mar 20(Fri)

attendance_log = {
    "employee_id": "EMP20240312",
    "month": "2026-03",
    "records": [
        # Week 1
        {"date": "2026-03-02", "day_type": "weekday", "check_in": "09:45", "check_out": "21:30", "note": "Project deadline"},
        # Late 15min, OT: from 19:00 to 21:30 = 2.5h -> rounds to 2h (1h minimum, per-hour counting)
        # Actually OT starts at 19:00. 21:30-19:00 = 2.5h, minimum 1h, so 2h of OT (floor to whole hours)
        {"date": "2026-03-03", "day_type": "weekday", "check_in": "09:25", "check_out": "19:45", "note": ""},
        # OT: 19:45 - 19:00 = 45 min < 1 hour -> NO OT counted
        {"date": "2026-03-04", "day_type": "weekday", "check_in": "10:05", "check_out": "22:15", "note": "Late night push"},
        # Late 5min (within 15min bracket -> 50 RMB deduction), OT from 19:00 to 22:15 = 3.25h -> 3h OT, also after 22:00 can claim transport/meal benefit
        {"date": "2026-03-05", "day_type": "weekday", "check_in": "09:30", "check_out": "18:30", "note": "Normal day"},
        # No OT
        {"date": "2026-03-06", "day_type": "weekday", "check_in": "09:30", "check_out": "18:30", "note": "Normal day"},
        # Weekend work
        {"date": "2026-03-07", "day_type": "weekend", "check_in": "10:00", "check_out": "11:30", "waijin_punched": True, "note": "Short work"},
        # 1.5h < 2h threshold -> NO OT counted for weekend
        {"date": "2026-03-08", "day_type": "weekend", "check_in": "09:00", "check_out": "13:30", "waijin_punched": True, "note": "Campaign launch"},
        # 4.5h >= 2h -> OT: 4.5h * 0.7 = 3.15h -> floor to 3h compensatory (using floor on final result)
        # Week 2
        {"date": "2026-03-09", "day_type": "weekday", "check_in": "10:20", "check_out": "19:00", "note": ""},
        # Late: 10:20, that's 20min late (15 < T <= 30) -> 100 RMB deduction
        # OT: 19:00 - 19:00 = 0 min -> NO OT (must be AFTER 19:00)
        {"date": "2026-03-10", "day_type": "weekday", "check_in": "09:30", "check_out": "20:30", "note": "Resignation email sent today"},
        # OT: 20:30 - 19:00 = 1.5h -> 1h OT (floor)
        {"date": "2026-03-11", "day_type": "weekday", "check_in": None, "check_out": "18:30", "note": "Forgot to punch in - missed punch"},
        # Missed punch (补卡 opportunity used)
        {"date": "2026-03-12", "day_type": "weekday", "check_in": "09:30", "check_out": "18:30", "note": ""},
        {"date": "2026-03-13", "day_type": "weekday", "check_in": "09:30", "check_out": "18:30", "note": ""},
        # Weekend
        {"date": "2026-03-14", "day_type": "weekend", "check_in": "14:00", "check_out": "17:00", "waijin_punched": False, "note": "Worked from home, forgot waijin"},
        # 3h >= 2h BUT no waijin punch -> OT CANNOT be counted (backend can't track)
        {"date": "2026-03-15", "day_type": "weekend", "check_in": None, "check_out": None, "note": "Rest"},
        # Week 3
        {"date": "2026-03-16", "day_type": "weekday", "check_in": "09:30", "check_out": "23:00", "note": "Major event"},
        # OT: 23:00 - 19:00 = 4h OT, also after 22:00 benefit applies
        {"date": "2026-03-17", "day_type": "weekday", "check_in": "09:30", "check_out": "18:30", "note": ""},
        {"date": "2026-03-18", "day_type": "weekday", "check_in": "09:30", "check_out": "18:30", "note": ""},
        {"date": "2026-03-19", "day_type": "weekday", "check_in": "09:30", "check_out": "18:30", "note": ""},
        {"date": "2026-03-20", "day_type": "weekday", "check_in": "09:30", "check_out": "18:30", "note": "Last day (desired)"},
    ]
}
with open(os.path.join(WORKSPACE, "hr_cases/li_wei/attendance_march_2026.json"), "w", encoding="utf-8") as f:
    json.dump(attendance_log, f, ensure_ascii=False, indent=2)

# --- Expense claims for Li Wei in March 2026 ---
expense_claims = {
    "employee_id": "EMP20240312",
    "month": "2026-03",
    "submission_date": "2026-03-26",  # AFTER the 24th deadline -> delayed to next cycle
    "claims": [
        {
            "id": "EXP001",
            "type": "招待费",
            "description": "Client dinner with 3 guests + Li Wei = 4 people total",
            "total_amount_rmb": 920,
            "persons": 4,
            "date": "2026-03-05",
            "invoice_provided": True
        },
        {
            "id": "EXP002",
            "type": "团建费",
            "description": "Team building for 8 people",
            "total_amount_rmb": 800,
            "persons": 8,
            "date": "2026-03-12",
            "invoice_provided": True
        },
        {
            "id": "EXP003",
            "type": "团建费",
            "description": "Second team building this month, 5 people",
            "total_amount_rmb": 400,
            "persons": 5,
            "date": "2026-03-19",
            "invoice_provided": True,
            "note": "After resignation email sent on 2026-03-10"
        },
        {
            "id": "EXP004",
            "type": "误餐费",
            "description": "Meal allowance for overtime on 2026-03-04",
            "total_amount_rmb": 50,
            "persons": 1,
            "date": "2026-03-04",
            "invoice_provided": True
        },
        {
            "id": "EXP005",
            "type": "NBC",
            "description": "New client prospecting expenses",
            "total_amount_rmb": 300,
            "persons": 1,
            "date": "2026-03-08",
            "invoice_provided": False  # No invoice!
        }
    ]
}
with open(os.path.join(WORKSPACE, "hr_cases/li_wei/expense_claims_march_2026.json"), "w", encoding="utf-8") as f:
    json.dump(expense_claims, f, ensure_ascii=False, indent=2)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(WORKSPACE):
    for fname in files:
        print(f"  {os.path.join(root, fname)}")