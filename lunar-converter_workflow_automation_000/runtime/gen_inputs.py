import os
import json
import random

random.seed(42)

workspace = "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "hr/records/2024",
    "hr/records/2025",
    "hr/records/2026",
    "hr/policies",
    "hr/templates",
    "finance/reports",
    "finance/payroll",
    "it/configs",
    "it/logs",
    "marketing/campaigns",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── The real lunar.py script (skill entrypoint) ───────────────────────────────
lunar_script = '''\
import sys
import json
from lunardate import LunarDate

def lunar2solar(year, month, day):
    ld = LunarDate(year, month, day)
    sd = ld.toSolarDate()
    return {"result": sd.strftime("%Y-%m-%d")}

def solar2lunar(year, month, day):
    from datetime import date
    sd = date(year, month, day)
    ld = LunarDate.fromSolarDate(year, month, day)
    lunar_month_names = ["", "正", "二", "三", "四", "五", "六",
                         "七", "八", "九", "十", "冬", "腊"]
    lunar_day_names = ["", "初一", "初二", "初三", "初四", "初五",
                       "初六", "初七", "初八", "初九", "初十",
                       "十一", "十二", "十三", "十四", "十五",
                       "十六", "十七", "十八", "十九", "二十",
                       "廿一", "廿二", "廿三", "廿四", "廿五",
                       "廿六", "廿七", "廿八", "廿九", "三十"]
    result = f"{ld.year}年{lunar_month_names[ld.month]}月{lunar_day_names[ld.day]}"
    return {"result": result}

if __name__ == "__main__":
    cmd = sys.argv[1]
    y, m, d = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
    if cmd == "lunar2solar":
        print(json.dumps(lunar2solar(y, m, d), ensure_ascii=False))
    elif cmd == "solar2lunar":
        print(json.dumps(solar2lunar(y, m, d), ensure_ascii=False))
    else:
        print(json.dumps({"error": "unknown command"}))
        sys.exit(1)
'''
with open(os.path.join(workspace, "scripts/lunar.py"), "w", encoding="utf-8") as f:
    f.write(lunar_script)

# ── The core problem input: mixed-calendar employee birthday list ─────────────
# Some employees have solar birthdays, some have lunar birthdays.
# The agent must convert all to BOTH calendars for year 2026 and save a report.
employee_data = {
    "year": 2026,
    "description": "Annual birthday schedule reconciliation for 2026. Each employee has a birthday stored in either the solar (Gregorian) or lunar calendar. Convert all entries so that every employee has BOTH their solar_date and lunar_date for 2026 listed.",
    "employees": [
        {"id": "EMP001", "name": "Zhang Wei",   "calendar": "lunar", "month": 1,  "day": 15},
        {"id": "EMP002", "name": "Li Fang",     "calendar": "solar", "month": 3,  "day": 8},
        {"id": "EMP003", "name": "Wang Jing",   "calendar": "lunar", "month": 5,  "day": 5},
        {"id": "EMP004", "name": "Chen Bo",     "calendar": "solar", "month": 7,  "day": 1},
        {"id": "EMP005", "name": "Zhao Min",    "calendar": "lunar", "month": 8,  "day": 15},
        {"id": "EMP006", "name": "Liu Yang",    "calendar": "solar", "month": 10, "day": 3},
        {"id": "EMP007", "name": "Sun Lei",     "calendar": "lunar", "month": 11, "day": 20},
        {"id": "EMP008", "name": "Zhou Xin",   "calendar": "solar", "month": 1,  "day": 25},
        {"id": "EMP009", "name": "Xu Mei",      "calendar": "lunar", "month": 3,  "day": 3},
        {"id": "EMP010", "name": "Gao Peng",    "calendar": "solar", "month": 6,  "day": 18},
    ]
}

with open(os.path.join(workspace, "hr/records/2026/birthday_raw.json"), "w", encoding="utf-8") as f:
    json.dump(employee_data, f, ensure_ascii=False, indent=2)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "hr/policies/leave_policy.txt":
        "Annual leave: 15 days. Sick leave: 10 days. Public holidays as per national calendar.",
    "hr/policies/remote_work.md":
        "# Remote Work Policy\nEmployees may work remotely up to 3 days per week.",
    "hr/templates/offer_letter_template.txt":
        "Dear [NAME], We are pleased to offer you the position of [ROLE]...",
    "hr/records/2024/headcount.csv":
        "id,name,department\nEMP001,Zhang Wei,Engineering\nEMP002,Li Fang,Marketing",
    "hr/records/2025/performance_review.json":
        json.dumps({"year": 2025, "average_score": 4.2, "top_performer": "EMP005"}),
    "finance/reports/q1_2026.txt":
        "Q1 2026 Revenue: CNY 12,500,000. Expenses: CNY 9,800,000.",
    "finance/payroll/march_2026.csv":
        "id,name,gross,net\nEMP001,Zhang Wei,25000,19500",
    "it/configs/server.yaml":
        "host: 10.0.0.1\nport: 8080\nmax_connections: 200",
    "it/logs/app_2026-01-15.log":
        "[INFO] Service started\n[WARN] High memory usage detected\n[INFO] Service running normally",
    "marketing/campaigns/spring_festival_2026.txt":
        "Campaign: Spring Festival Red Packet\nBudget: CNY 50,000\nTarget: All employees",
    "hr/records/2026/org_chart_draft.txt":
        "CEO -> CTO -> Engineering Team\nCEO -> CFO -> Finance Team",
}

for relpath, content in distractors.items():
    fpath = os.path.join(workspace, relpath)
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace generated successfully.")