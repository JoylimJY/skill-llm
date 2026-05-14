import json
import sys
import os
from pathlib import Path
from collections import defaultdict

workspace = Path(sys.argv[1])
home_dir = Path.home()
datafile = home_dir / ".clawdbot" / "session-costs.json"
report_file = workspace / "by_task_stats_report.txt"

checks = []
passed_all = True

# ─── Expected session data (ground truth) ─────────────────────────────────────
# Internal label -> SKILL.md category mapping:
# SHIPPED    -> creation
# FIXED      -> high
# CLEANUP    -> refactor
# MONITOR    -> maintenance
# EXPLORE    -> low
# FASTSHIP   -> debt
# WASTED     -> zero
# USEFUL     -> medium

EXPECTED_SESSIONS = [
    {"id": "S001", "task_kw": "refactored auth module",         "value": "refactor",     "tokens": 9200,  "log_format": "full"},
    {"id": "S002", "task_kw": "onboarding email sequence",      "value": "creation",     "tokens": 15400, "log_format": "full"},
    {"id": "S003", "task_kw": "memory leak",                    "value": "high",         "tokens": 7800,  "log_format": "full"},
    {"id": "S004", "task_kw": "infra health check",             "value": "maintenance",  "tokens": 3100,  "log_format": "quick"},
    {"id": "S005", "task_kw": "vector DB",                      "value": "low",          "tokens": 11200, "log_format": "quick"},
    {"id": "S006", "task_kw": "v2 API",                         "value": "debt",         "tokens": 18900, "log_format": "quick"},
    {"id": "S007", "task_kw": "competitor price",               "value": "zero",         "tokens": 6600,  "log_format": "quick"},
    {"id": "S008", "task_kw": "investor update memo",           "value": "creation",     "tokens": 13300, "log_format": "quick"},
    {"id": "S009", "task_kw": "support tickets",                "value": "medium",       "tokens": 5500,  "log_format": "quick"},
    {"id": "S010", "task_kw": "last month sessions",            "value": "maintenance",  "tokens": 2800,  "log_format": "quick"},
]

# ─── Check 1: session-costs.json exists and is valid JSON ─────────────────────
try:
    with open(datafile, "r") as f:
        sessions = json.load(f)
    checks.append({"name": "session_data_file_exists_and_valid",
                   "passed": True,
                   "detail": f"Found {len(sessions)} sessions in {datafile}"})
except FileNotFoundError:
    checks.append({"name": "session_data_file_exists_and_valid",
                   "passed": False,
                   "detail": f"File not found: {datafile}"})
    passed_all = False
    sessions = []
except json.JSONDecodeError as e:
    checks.append({"name": "session_data_file_exists_and_valid",
                   "passed": False,
                   "detail": f"Invalid JSON: {e}"})
    passed_all = False
    sessions = []

# ─── Check 2: All 10 sessions are logged ──────────────────────────────────────
try:
    n = len(sessions)
    ok = n >= 10
    checks.append({"name": "all_10_sessions_logged",
                   "passed": ok,
                   "detail": f"Found {n} sessions, expected >= 10"})
    if not ok:
        passed_all = False
except Exception as e:
    checks.append({"name": "all_10_sessions_logged", "passed": False, "detail": str(e)})
    passed_all = False

# ─── Check 3: Correct value category mapping (all 8 unique categories) ────────
def find_session(sessions, task_kw):
    task_kw_lower = task_kw.lower()
    for s in sessions:
        if task_kw_lower in s.get("task", "").lower():
            return s
    return None

value_mapping_passed = True
value_detail_parts = []

for exp in EXPECTED_SESSIONS:
    s = find_session(sessions, exp["task_kw"])
    if s is None:
        value_mapping_passed = False
        value_detail_parts.append(f"{exp['id']}: NOT FOUND (kw='{exp['task_kw']}')")
    elif s.get("value") != exp["value"]:
        value_mapping_passed = False
        value_detail_parts.append(
            f"{exp['id']}: WRONG value '{s.get('value')}' (expected '{exp['value']}')"
        )
    else:
        value_detail_parts.append(f"{exp['id']}: OK ({exp['value']})")

checks.append({
    "name": "correct_value_category_mapping",
    "passed": value_mapping_passed,
    "detail": "; ".join(value_detail_parts)
})
if not value_mapping_passed:
    passed_all = False

# ─── Check 4: Extended categories actually used (not substituted with basics) ──
try:
    used_values = {s.get("value") for s in sessions}
    extended = {"creation", "maintenance", "debt", "refactor"}
    missing_extended = extended - used_values
    ok = len(missing_extended) == 0
    checks.append({
        "name": "extended_value_categories_used",
        "passed": ok,
        "detail": (f"All extended categories found: {sorted(extended)}"
                   if ok else
                   f"Missing extended categories: {sorted(missing_extended)}. "
                   f"Used values: {sorted(used_values)}")
    })
    if not ok:
        passed_all = False
except Exception as e:
    checks.append({"name": "extended_value_categories_used", "passed": False, "detail": str(e)})
    passed_all = False

# ─── Check 5: S001, S002, S003 logged with full format ─────────────────────────
try:
    full_format_sessions = [
        ("refactored auth module", "S001"),
        ("onboarding email sequence", "S002"),
        ("memory leak", "S003"),
    ]
    full_format_ok = True
    full_format_details = []
    for kw, sid in full_format_sessions:
        s = find_session(sessions, kw)
        if s is None:
            full_format_ok = False
            full_format_details.append(f"{sid}: session not found")
        elif s.get("log_format") != "full":
            full_format_ok = False
            full_format_details.append(
                f"{sid}: log_format='{s.get('log_format')}' (expected 'full')"
            )
        elif not s.get("outcome", "").strip():
            full_format_ok = False
            full_format_details.append(f"{sid}: log_format=full but outcome is empty")
        else:
            full_format_details.append(f"{sid}: OK (full, outcome non-empty)")

    checks.append({
        "name": "s001_s002_s003_use_full_log_format",
        "passed": full_format_ok,
        "detail": "; ".join(full_format_details)
    })
    if not full_format_ok:
        passed_all = False
except Exception as e:
    checks.append({"name": "s001_s002_s003_use_full_log_format", "passed": False, "detail": str(e)})
    passed_all = False

# ─── Check 6: S004-S010 use quick format ───────────────────────────────────────
try:
    quick_sessions = [
        ("infra health check", "S004"),
        ("vector DB", "S005"),
        ("v2 API", "S006"),
        ("competitor price", "S007"),
        ("investor update memo", "S008"),
        ("support tickets", "S009"),
        ("last month sessions", "S010"),
    ]
    quick_ok = True
    quick_details = []
    for kw, sid in quick_sessions:
        s = find_session(sessions, kw)
        if s is None:
            quick_ok = False
            quick_details.append(f"{sid}: session not found")
        elif s.get("log_format") != "quick":
            quick_ok = False
            quick_details.append(
                f"{sid}: log_format='{s.get('log_format')}' (expected 'quick')"
            )
        else:
            quick_details.append(f"{sid}: OK (quick)")

    checks.append({
        "name": "s004_to_s010_use_quick_log_format",
        "passed": quick_ok,
        "detail": "; ".join(quick_details)
    })
    if not quick_ok:
        passed_all = False
except Exception as e:
    checks.append({"name": "s004_to_s010_use_quick_log_format", "passed": False, "detail": str(e)})
    passed_all = False

# ─── Check 7: Correct token counts ────────────────────────────────────────────
try:
    token_ok = True
    token_details = []
    for exp in EXPECTED_SESSIONS:
        s = find_session(sessions, exp["task_kw"])
        if s is None:
            token_ok = False
            token_details.append(f"{exp['id']}: not found")
        elif s.get("tokens") != exp["tokens"]:
            token_ok = False
            token_details.append(
                f"{exp['id']}: tokens={s.get('tokens')} (expected {exp['tokens']})"
            )
        else:
            token_details.append(f"{exp['id']}: OK ({exp['tokens']})")

    checks.append({
        "name": "correct_token_counts",
        "passed": token_ok,
        "detail": "; ".join(token_details)
    })
    if not token_ok:
        passed_all = False
except Exception as e:
    checks.append({"name": "correct_token_counts", "passed": False, "detail": str(e)})
    passed_all = False

# ─── Check 8: by_task_stats_report.txt exists and contains grouped output ──────
try:
    if not report_file.exists():
        checks.append({
            "name": "by_task_stats_report_exists",
            "passed": False,
            "detail": f"File not found: {report_file}"
        })
        passed_all = False
    else:
        content = report_file.read_text()
        # Must contain grouped-by-task markers
        has_grouped = "Grouped by Task" in content or "by-task" in content.lower() or any(
            f"[{v.upper()}]" in content
            for v in ["creation", "maintenance", "debt", "refactor", "high", "zero", "medium", "low"]
        )
        has_sessions_info = any(
            kw.lower() in content.lower()
            for kw in ["sessions", "tokens", "Stats"]
        )
        ok = has_grouped and has_sessions_info
        checks.append({
            "name": "by_task_stats_report_exists",
            "passed": ok,
            "detail": (f"Report found ({len(content)} chars). Has grouping: {has_grouped}, "
                       f"Has session info: {has_sessions_info}")
        })
        if not ok:
            passed_all = False
except Exception as e:
    checks.append({"name": "by_task_stats_report_exists", "passed": False, "detail": str(e)})
    passed_all = False

# ─── Check 9: Report contains all expected value group headers ────────────────
try:
    if report_file.exists():
        content = report_file.read_text().lower()
        required_groups = ["creation", "refactor", "maintenance", "debt", "high", "zero", "medium", "low"]
        found = [g for g in required_groups if g in content]
        missing = [g for g in required_groups if g not in content]
        ok = len(missing) == 0
        checks.append({
            "name": "report_contains_all_value_groups",
            "passed": ok,
            "detail": (f"Found groups: {found}" + (f"; Missing: {missing}" if missing else ""))
        })
        if not ok:
            passed_all = False
    else:
        checks.append({
            "name": "report_contains_all_value_groups",
            "passed": False,
            "detail": "Report file missing, skipping group check"
        })
        passed_all = False
except Exception as e:
    checks.append({"name": "report_contains_all_value_groups", "passed": False, "detail": str(e)})
    passed_all = False

# ─── Scoring ──────────────────────────────────────────────────────────────────
n_passed = sum(1 for c in checks if c["passed"])
score = round(n_passed / len(checks), 3)

result = {
    "passed": passed_all,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))