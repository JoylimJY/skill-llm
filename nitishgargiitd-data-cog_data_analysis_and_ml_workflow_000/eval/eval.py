import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1])
CALLS_LOG = Path("/tmp/cellcog_calls.jsonl")

checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── Load API call log ──────────────────────────────────────────────────────
calls = []
try:
    if CALLS_LOG.exists():
        with open(CALLS_LOG) as f:
            for line in f:
                line = line.strip()
                if line:
                    calls.append(json.loads(line))
except Exception as e:
    checks.append(make_check("api_call_log_readable", False, f"Could not read call log: {e}"))

# Check: at least one API call was made
at_least_one_call = len(calls) > 0
checks.append(make_check(
    "api_call_made",
    at_least_one_call,
    f"Found {len(calls)} API call(s) to the CellCog mock server." if at_least_one_call else "No API calls detected. Agent never called create_chat."
))

if not calls:
    # No calls at all - fail fast
    result = {
        "passed": False,
        "score": 0.0,
        "checks": checks
    }
    print(json.dumps(result))
    sys.exit(0)

# Use the most relevant call (last one, or one with SHOW_FILE)
primary_call = None
for c in reversed(calls):
    if "SHOW_FILE" in c.get("prompt", ""):
        primary_call = c
        break
if primary_call is None:
    primary_call = calls[-1]

prompt_text = primary_call.get("prompt", "")
chat_mode = primary_call.get("chat_mode", "")
notify_key = primary_call.get("notify_session_key", "")
task_label = primary_call.get("task_label", "")

# ── CHECK 1: SHOW_FILE tag used correctly ──────────────────────────────────
# Must contain <SHOW_FILE>/absolute/path/to/customer_loyalty_study.csv</SHOW_FILE>
show_file_pattern = re.compile(r'<SHOW_FILE>([^<]+)</SHOW_FILE>', re.IGNORECASE)
show_file_matches = show_file_pattern.findall(prompt_text)

show_file_used = len(show_file_matches) > 0
checks.append(make_check(
    "show_file_tag_present",
    show_file_used,
    f"SHOW_FILE tags found with paths: {show_file_matches}" if show_file_used else "No <SHOW_FILE>...</SHOW_FILE> tag found in prompt. Agent must use proprietary file embedding syntax."
))

# ── CHECK 2: SHOW_FILE references the correct dataset ─────────────────────
correct_file_ref = False
correct_file_detail = "No SHOW_FILE path references the required dataset."
if show_file_matches:
    for path_str in show_file_matches:
        if "customer_loyalty_study.csv" in path_str or "data/raw" in path_str:
            correct_file_ref = True
            correct_file_detail = f"Correct dataset referenced: {path_str}"
            break
    if not correct_file_ref:
        correct_file_detail = f"SHOW_FILE found but points to wrong file(s): {show_file_matches}"
checks.append(make_check("show_file_correct_dataset", correct_file_ref, correct_file_detail))

# ── CHECK 3: chat_mode is "agent team" ────────────────────────────────────
# The task requires ML model comparison + A/B statistical analysis + comprehensive report
# → must use "agent team", NOT plain "agent"
chat_mode_normalized = chat_mode.strip().lower()
correct_chat_mode = chat_mode_normalized == "agent team"
checks.append(make_check(
    "chat_mode_agent_team",
    correct_chat_mode,
    f"chat_mode='{chat_mode}' — correct ('agent team' required for complex ML + statistical multi-technique analysis)." if correct_chat_mode
    else f"chat_mode='{chat_mode}' — WRONG. Complex multi-technique ML + statistical analysis requires 'agent team', not '{chat_mode}'."
))

# ── CHECK 4: notify_session_key is set and matches proprietary format ──────
# Required format per SKILL.md: "agent:main:main"
notify_key_present = bool(notify_key)
notify_key_correct = notify_key == "agent:main:main"
checks.append(make_check(
    "notify_session_key_present",
    notify_key_present,
    f"notify_session_key='{notify_key}'" if notify_key_present else "notify_session_key missing — required for fire-and-forget daemon notification."
))
checks.append(make_check(
    "notify_session_key_correct_format",
    notify_key_correct,
    f"notify_session_key='{notify_key}' matches required 'agent:main:main'." if notify_key_correct
    else f"notify_session_key='{notify_key}' — WRONG. Must be exactly 'agent:main:main' per SDK spec."
))

# ── CHECK 5: task_label is set ─────────────────────────────────────────────
task_label_present = bool(task_label and task_label.strip())
checks.append(make_check(
    "task_label_present",
    task_label_present,
    f"task_label='{task_label}' — present." if task_label_present else "task_label missing — should be set (e.g., 'data-analysis')."
))

# ── CHECK 6: Prompt requests churn prediction (ML) ────────────────────────
churn_keywords = ["churn", "predict", "model", "classif", "ml", "machine learning", "random forest", "gradient", "logistic"]
prompt_lower = prompt_text.lower()
churn_requested = any(kw in prompt_lower for kw in churn_keywords)
checks.append(make_check(
    "prompt_requests_churn_ml",
    churn_requested,
    "Prompt includes churn prediction / ML modeling request." if churn_requested
    else "Prompt does not mention churn prediction or ML modeling — core business requirement missing."
))

# ── CHECK 7: Prompt requests A/B test / statistical analysis ──────────────
ab_keywords = ["a/b", "ab test", "a/b test", "variant", "statistical", "significance", "p-value", "p value",
               "conversion rate", "hypothesis", "confidence interval"]
ab_requested = any(kw in prompt_lower for kw in ab_keywords)
checks.append(make_check(
    "prompt_requests_ab_analysis",
    ab_requested,
    "Prompt includes A/B test / statistical analysis request." if ab_requested
    else "Prompt does not request A/B test or statistical analysis — a core requirement."
))

# ── CHECK 8: Prompt requests a report output format ───────────────────────
report_keywords = ["html", "dashboard", "pdf", "report", "markdown", "chart", "visual"]
report_requested = any(kw in prompt_lower for kw in report_keywords)
checks.append(make_check(
    "prompt_requests_output_format",
    report_requested,
    "Prompt specifies a visual/report output format." if report_requested
    else "Prompt does not specify a desired output format (HTML/PDF/dashboard)."
))

# ── CHECK 9: Fire-and-forget — no explicit polling call present ────────────
# Verify agent did NOT try to poll (multiple calls with poll/status patterns)
polling_detected = False
poll_keywords = ["poll", "status", "check_status", "get_result", "wait_for"]
all_prompts = [c.get("prompt", "") for c in calls]
# Check if there are suspicious repeated identical calls (polling pattern)
if len(calls) > 3:
    polling_detected = True

# Also check if any agent script file contains polling logic
agent_scripts = list(workspace.rglob("*.py"))
for script_path in agent_scripts:
    try:
        content = script_path.read_text(errors="ignore").lower()
        if any(kw in content for kw in ["while true", "time.sleep", "poll", "get_status", "check_result"]):
            # Check if it's a meaningful polling loop (not just setup)
            if "create_chat" in content and ("while" in content or "for _ in range" in content):
                polling_detected = True
    except Exception:
        pass

checks.append(make_check(
    "fire_and_forget_no_polling",
    not polling_detected,
    "Fire-and-forget pattern used correctly — no polling loop detected." if not polling_detected
    else "Agent appears to be polling for results — SKILL.md explicitly states 'do NOT poll'."
))

# ── Final scoring ──────────────────────────────────────────────────────────
# Weighted: critical checks carry more weight
weights = {
    "api_call_made": 2,
    "show_file_tag_present": 3,
    "show_file_correct_dataset": 2,
    "chat_mode_agent_team": 4,       # Highest weight - this is the proprietary trap
    "notify_session_key_present": 2,
    "notify_session_key_correct_format": 3,
    "task_label_present": 1,
    "prompt_requests_churn_ml": 2,
    "prompt_requests_ab_analysis": 2,
    "prompt_requests_output_format": 1,
    "fire_and_forget_no_polling": 2,
}

total_weight = sum(weights.values())
earned_weight = sum(weights.get(c["name"], 1) for c in checks if c["passed"])
score = round(earned_weight / total_weight, 4)

# Must pass the critical proprietary checks to fully pass
critical_checks = ["show_file_tag_present", "chat_mode_agent_team", "notify_session_key_correct_format", "api_call_made"]
critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
overall_passed = critical_passed and score >= 0.70

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))