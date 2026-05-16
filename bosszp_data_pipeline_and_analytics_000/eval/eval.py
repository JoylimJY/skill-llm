import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

checks = []
total_score = 0.0
max_score = 0.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    global total_score, max_score
    max_score += weight
    if passed:
        total_score += weight

# -------------------------------------------------------
# CHECK 1: Find analysis_report.json
# -------------------------------------------------------
report_files = list(Path(workspace).rglob("analysis_report.json"))
if not report_files:
    add_check("analysis_report.json exists", False, "File 'analysis_report.json' not found anywhere in workspace.", weight=2.0)
    # Cannot proceed with further checks
    result = {
        "passed": False,
        "score": 0.0,
        "checks": checks + [
            {"name": "salary_distribution", "passed": False, "detail": "Skipped: report file missing"},
            {"name": "finance_stage_distribution", "passed": False, "detail": "Skipped: report file missing"},
            {"name": "top10_companies", "passed": False, "detail": "Skipped: report file missing"},
            {"name": "correct_field_names_used", "passed": False, "detail": "Skipped: report file missing"},
            {"name": "database_table_exists", "passed": False, "detail": "Skipped: report file missing"},
            {"name": "database_correct_columns", "passed": False, "detail": "Skipped: report file missing"},
        ]
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)

report_path = report_files[0]
add_check("analysis_report.json exists", True, f"Found at {report_path}", weight=2.0)

# -------------------------------------------------------
# Load the report
# -------------------------------------------------------
try:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
except Exception as e:
    add_check("analysis_report.json is valid JSON", False, f"Parse error: {e}", weight=1.0)
    report = None
else:
    add_check("analysis_report.json is valid JSON", True, "Parsed successfully", weight=1.0)

if report is None:
    for name in ["salary_distribution", "finance_stage_distribution", "top10_companies", "correct_field_names_used"]:
        checks.append({"name": name, "passed": False, "detail": "Skipped: JSON parse failed"})
        max_score += 1.0
else:
    # -------------------------------------------------------
    # CHECK 2: salary_distribution section exists and has ≤10 entries
    # -------------------------------------------------------
    try:
        salary_dist = report.get("salary_distribution") or report.get("薪资分布") or None
        if salary_dist is None:
            add_check("salary_distribution present", False, f"Key 'salary_distribution' (or '薪资分布') not found in report. Keys: {list(report.keys())}", weight=1.5)
        else:
            if isinstance(salary_dist, (dict, list)):
                n = len(salary_dist)
                if n <= 10:
                    add_check("salary_distribution present", True, f"Found salary_distribution with {n} entries (≤10 as per Top10 requirement)", weight=1.5)
                else:
                    add_check("salary_distribution present", False, f"salary_distribution has {n} entries, expected ≤10 (Top10 only)", weight=1.5)
            else:
                add_check("salary_distribution present", False, f"salary_distribution is not a list or dict: {type(salary_dist)}", weight=1.5)
    except Exception as e:
        add_check("salary_distribution present", False, f"Exception: {e}", weight=1.5)

    # -------------------------------------------------------
    # CHECK 3: finance_stage_distribution exists with expected categories
    # -------------------------------------------------------
    try:
        fin_dist = report.get("finance_stage_distribution") or report.get("融资阶段分布") or None
        expected_stages = {"已上市", "D轮及以上", "C轮", "B轮", "A轮", "天使轮", "不需要融资"}
        if fin_dist is None:
            add_check("finance_stage_distribution present", False, f"Key 'finance_stage_distribution' (or '融资阶段分布') not found. Keys: {list(report.keys())}", weight=1.5)
        else:
            if isinstance(fin_dist, dict):
                keys_found = set(fin_dist.keys())
            elif isinstance(fin_dist, list):
                # list of {stage: X, count: Y} dicts
                keys_found = set()
                for item in fin_dist:
                    if isinstance(item, dict):
                        for k in ["stage", "finance_stage", "融资阶段", "name", "label"]:
                            if k in item:
                                keys_found.add(item[k])
                                break
            else:
                keys_found = set()

            overlap = keys_found & expected_stages
            if len(overlap) >= 3:
                add_check("finance_stage_distribution present", True,
                          f"Found finance_stage_distribution with stages: {keys_found}", weight=1.5)
            else:
                add_check("finance_stage_distribution present", False,
                          f"finance_stage_distribution found but stages don't match expected. Got: {keys_found}", weight=1.5)
    except Exception as e:
        add_check("finance_stage_distribution present", False, f"Exception: {e}", weight=1.5)

    # -------------------------------------------------------
    # CHECK 4: top10_companies exists and has ≤10 entries with counts
    # -------------------------------------------------------
    try:
        top10 = report.get("top10_companies") or report.get("公司排名") or report.get("company_ranking") or None
        if top10 is None:
            add_check("top10_companies present", False, f"Key 'top10_companies' (or variants) not found. Keys: {list(report.keys())}", weight=1.5)
        else:
            if isinstance(top10, (dict, list)):
                n = len(top10)
                if n <= 10:
                    # Check that counts/values are numeric
                    has_numeric = False
                    if isinstance(top10, dict):
                        has_numeric = any(isinstance(v, (int, float)) for v in top10.values())
                    elif isinstance(top10, list):
                        for item in top10:
                            if isinstance(item, dict):
                                vals = list(item.values())
                                if any(isinstance(v, (int, float)) for v in vals):
                                    has_numeric = True
                                    break
                            elif isinstance(item, (int, float)):
                                has_numeric = True
                                break
                    if has_numeric or isinstance(top10, dict):
                        add_check("top10_companies present", True, f"Found top10_companies with {n} entries", weight=1.5)
                    else:
                        add_check("top10_companies present", False, f"top10_companies found but values don't appear numeric: {top10[:3] if isinstance(top10, list) else top10}", weight=1.5)
                else:
                    add_check("top10_companies present", False, f"top10_companies has {n} entries, expected ≤10", weight=1.5)
            else:
                add_check("top10_companies present", False, f"top10_companies is not list/dict: {type(top10)}", weight=1.5)
    except Exception as e:
        add_check("top10_companies present", False, f"Exception: {e}", weight=1.5)

    # -------------------------------------------------------
    # CHECK 5: Verify the report uses SKILL.md field names (proprietary trap)
    # -------------------------------------------------------
    try:
        report_str = json.dumps(report, ensure_ascii=False)
        # Check for canonical field names from SKILL.md
        canonical_fields = ["finance_stage", "com_name", "job_salary", "job_name"]
        found_fields = [f for f in canonical_fields if f in report_str]
        if len(found_fields) >= 2:
            add_check("correct_field_names_used", True,
                      f"Report references canonical SKILL.md field names: {found_fields}", weight=1.0)
        else:
            # Also accept Chinese equivalents with warning
            chinese_fields = ["融资阶段", "公司名称", "薪资", "岗位名称"]
            found_cn = [f for f in chinese_fields if f in report_str]
            if len(found_cn) >= 2:
                add_check("correct_field_names_used", True,
                          f"Report uses Chinese field equivalents: {found_cn} (acceptable)", weight=1.0)
            else:
                add_check("correct_field_names_used", False,
                          f"Report does not reference canonical SKILL.md field names. Found: {found_fields}. Report keys: {list(report.keys())}", weight=1.0)
    except Exception as e:
        add_check("correct_field_names_used", False, f"Exception: {e}", weight=1.0)

# -------------------------------------------------------
# CHECK 6: Database table exists with correct schema
# (Try SQLite first as fallback, then MySQL)
# -------------------------------------------------------
db_table_exists = False
db_correct_cols = False

# Look for SQLite databases
sqlite_files = list(Path(workspace).rglob("*.db")) + list(Path(workspace).rglob("*.sqlite")) + list(Path(workspace).rglob("*.sqlite3"))

if sqlite_files:
    try:
        import sqlite3
        db_path = sqlite_files[0]
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cur.fetchall()]
        
        # Look for a jobs/boss table
        job_table = None
        for t in tables:
            if any(kw in t.lower() for kw in ["job", "boss", "position", "recruit", "岗位", "职位"]):
                job_table = t
                break
        if not job_table and tables:
            job_table = tables[0]
        
        if job_table:
            db_table_exists = True
            add_check("database_table_exists", True, f"Found SQLite DB at {db_path}, table: {job_table}", weight=2.0)
            
            cur.execute(f"PRAGMA table_info({job_table});")
            cols = [row[1] for row in cur.fetchall()]
            required_cols = ["job_name", "job_area", "job_salary", "com_name", "com_type",
                             "com_size", "finance_stage", "work_year", "education", "job_benefits"]
            found_cols = [c for c in required_cols if c in cols]
            if len(found_cols) >= 8:
                db_correct_cols = True
                add_check("database_correct_columns", True,
                          f"Table '{job_table}' has {len(found_cols)}/10 required SKILL.md columns: {found_cols}", weight=2.0)
            else:
                add_check("database_correct_columns", False,
                          f"Table '{job_table}' missing columns. Found: {cols}, Required: {required_cols}, Matched: {found_cols}", weight=2.0)
        else:
            add_check("database_table_exists", False, f"SQLite DB found at {db_path} but no suitable table. Tables: {tables}", weight=2.0)
            add_check("database_correct_columns", False, "Skipped: no job table found", weight=2.0)
        conn.close()
    except Exception as e:
        add_check("database_table_exists", False, f"SQLite check failed: {e}", weight=2.0)
        add_check("database_correct_columns", False, f"Skipped: SQLite check failed", weight=2.0)
else:
    # Try MySQL
    try:
        import pymysql
        conn = pymysql.connect(
            host='127.0.0.1', port=3306,
            user='bosszp', password='bosszp123',
            database='bosszp',
            charset='utf8mb4'
        )
        cur = conn.cursor()
        cur.execute("SHOW TABLES;")
        tables = [row[0] for row in cur.fetchall()]
        
        job_table = None
        for t in tables:
            if any(kw in t.lower() for kw in ["job", "boss", "position", "recruit"]):
                job_table = t
                break
        if not job_table and tables:
            job_table = tables[0]
        
        if job_table:
            db_table_exists = True
            add_check("database_table_exists", True, f"Found MySQL table: {job_table}", weight=2.0)
            cur.execute(f"DESCRIBE {job_table};")
            cols = [row[0] for row in cur.fetchall()]
            required_cols = ["job_name", "job_area", "job_salary", "com_name", "com_type",
                             "com_size", "finance_stage", "work_year", "education", "job_benefits"]
            found_cols = [c for c in required_cols if c in cols]
            if len(found_cols) >= 8:
                db_correct_cols = True
                add_check("database_correct_columns", True,
                          f"MySQL table '{job_table}' has {len(found_cols)}/10 required columns", weight=2.0)
            else:
                add_check("database_correct_columns", False,
                          f"MySQL table missing columns. Found: {cols}, Matched: {found_cols}", weight=2.0)
        else:
            add_check("database_table_exists", False, f"MySQL connected but no tables in 'bosszp'. Tables: {tables}", weight=2.0)
            add_check("database_correct_columns", False, "Skipped: no table found", weight=2.0)
        conn.close()
    except Exception as e:
        add_check("database_table_exists", False, f"No SQLite DB found and MySQL connection failed: {e}", weight=2.0)
        add_check("database_correct_columns", False, "Skipped: no DB accessible", weight=2.0)

# -------------------------------------------------------
# Final scoring
# -------------------------------------------------------
final_score = round(total_score / max_score, 3) if max_score > 0 else 0.0
passed = final_score >= 0.65 and any(c["name"] == "analysis_report.json exists" and c["passed"] for c in checks)

result = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))