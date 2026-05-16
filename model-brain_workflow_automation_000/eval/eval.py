import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0

def find_report(workspace):
    for p in Path(workspace).rglob("routing_audit_report.json"):
        return p
    return None

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ── 1. File exists ────────────────────────────────────────────────────────────
report_path = find_report(workspace)
if report_path is None:
    checks.append(make_check("file_exists", False, "routing_audit_report.json not found anywhere in workspace"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

checks.append(make_check("file_exists", True, f"Found at {report_path}"))

# ── 2. Valid JSON ─────────────────────────────────────────────────────────────
try:
    with open(report_path) as f:
        report = json.load(f)
    checks.append(make_check("valid_json", True, "File parses as valid JSON"))
except Exception as e:
    checks.append(make_check("valid_json", False, f"JSON parse error: {e}"))
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── Helper: find a message entry by id ───────────────────────────────────────
def find_entry(report, msg_id):
    """Accept list at top level, or a key like 'results'/'routes'/'messages'."""
    if isinstance(report, list):
        candidates = report
    elif isinstance(report, dict):
        # try common keys
        for key in ("results", "routes", "messages", "routing", "data", "entries"):
            if key in report and isinstance(report[key], list):
                candidates = report[key]
                break
        else:
            # flatten all list values
            candidates = []
            for v in report.values():
                if isinstance(v, list):
                    candidates.extend(v)
    else:
        return None
    
    for item in candidates:
        if isinstance(item, dict):
            # match by id field
            for id_key in ("id", "msg_id", "message_id"):
                if item.get(id_key) == msg_id:
                    return item
            # match by nested message id
            msg = item.get("message", {})
            if isinstance(msg, dict) and msg.get("id") == msg_id:
                return item
    return None

def get_field(entry, *keys):
    """Try multiple possible field names."""
    for k in keys:
        if k in entry:
            return entry[k]
    return None

# ── 3. Correct routes for all 8 messages ──────────────────────────────────────

EXPECTED = {
    "msg-001": {
        "primary": "zero-llm",
        "fallback": "bankr/minimax-m2.5",
        "task_type": "deterministic",
    },
    "msg-002": {
        "primary": "bankr/minimax-m2.5",
        "fallback": "bankr/claude-sonnet-4.5",
        "task_type": "chat",
    },
    "msg-003": {
        "primary": "bankr/claude-sonnet-4.5",
        "fallback": "bankr/claude-opus-4.6",
        "task_type": "wallet/routine",
    },
    "msg-004": {
        "primary": "bankr/claude-opus-4.6",
        "fallback": "human-review",
        "task_type": "wallet/high",
    },
    "msg-005": {
        "primary": "bankr/gpt-5.2-codex",
        "fallback": "bankr/claude-sonnet-4.5",
        "task_type": "code",
    },
    "msg-006": {
        "primary": "bankr/gemini-3-pro",
        "fallback": "bankr/claude-sonnet-4.5",
        "task_type": "long-context",
    },
    "msg-007": {
        "primary": "bankr/claude-sonnet-4.5",
        # fallback can be claude-opus or any acceptable general fallback
        "task_type": "general",
    },
    "msg-008": {
        "primary": "bankr/claude-opus-4.6",
        "fallback": "human-review",
        "task_type": "wallet/high",
    },
}

routing_checks_passed = 0
for msg_id, exp in EXPECTED.items():
    entry = find_entry(report, msg_id)
    if entry is None:
        checks.append(make_check(
            f"route_{msg_id}",
            False,
            f"No entry found for {msg_id} in report"
        ))
        continue

    primary = get_field(entry, "primary", "primary_model", "model", "route", "primary_route")
    fallback = get_field(entry, "fallback", "fallback_model", "fallback_route")

    primary_ok = (primary == exp["primary"])
    fallback_ok = True  # default pass if not required strictly
    if "fallback" in exp:
        fallback_ok = (fallback == exp["fallback"])

    ok = primary_ok and fallback_ok
    if ok:
        routing_checks_passed += 1
    
    detail_parts = []
    if not primary_ok:
        detail_parts.append(f"primary: got '{primary}', expected '{exp['primary']}'")
    if not fallback_ok:
        detail_parts.append(f"fallback: got '{fallback}', expected '{exp['fallback']}'")
    if ok:
        detail_parts.append(f"primary='{primary}', fallback='{fallback}' ✓")

    checks.append(make_check(
        f"route_{msg_id}",
        ok,
        "; ".join(detail_parts)
    ))

# ── 4. shell/env output for the coding message ────────────────────────────────
# The agent must run select_model.sh with --mode env for msg-005 and include
# the shell-env output OR evidence thereof in the report or a side-file.

env_check_passed = False
env_detail = "No env-mode output found for msg-005 coding task"

# Check if report contains an env_output / shell_output field for msg-005
entry_005 = find_entry(report, "msg-005")
if entry_005:
    env_raw = get_field(entry_005, "env_output", "shell_output", "env", "shell_env", "env_lines")
    if env_raw and isinstance(env_raw, str):
        if "MODEL_PRIMARY=bankr/gpt-5.2-codex" in env_raw and "MODEL_FALLBACK=bankr/claude-sonnet-4.5" in env_raw:
            env_check_passed = True
            env_detail = "env-mode output correctly present with proper MODEL_PRIMARY and MODEL_FALLBACK"
        elif "gpt-5.2-codex" in env_raw:
            env_check_passed = True
            env_detail = f"env-mode output present and contains correct model name: {env_raw[:200]}"
    elif env_raw and isinstance(env_raw, dict):
        mp = env_raw.get("MODEL_PRIMARY", "")
        mf = env_raw.get("MODEL_FALLBACK", "")
        if "gpt-5.2-codex" in mp:
            env_check_passed = True
            env_detail = f"env-mode output as dict, MODEL_PRIMARY={mp}, MODEL_FALLBACK={mf}"

# Also search any side file
if not env_check_passed:
    for p in Path(workspace).rglob("*.txt"):
        try:
            content = p.read_text()
            if "MODEL_PRIMARY=bankr/gpt-5.2-codex" in content:
                env_check_passed = True
                env_detail = f"env-mode output found in side file {p}"
                break
        except Exception:
            pass
    for p in Path(workspace).rglob("*.env"):
        try:
            content = p.read_text()
            if "MODEL_PRIMARY=bankr/gpt-5.2-codex" in content:
                env_check_passed = True
                env_detail = f"env-mode output found in side file {p}"
                break
        except Exception:
            pass

checks.append(make_check("env_mode_output_msg005", env_check_passed, env_detail))

# ── 5. No hallucinated model names ────────────────────────────────────────────
VALID_MODELS = {
    "zero-llm",
    "bankr/minimax-m2.5",
    "bankr/claude-sonnet-4.5",
    "bankr/gpt-5.2-codex",
    "bankr/gemini-3-pro",
    "bankr/gemini-3-flash",
    "bankr/claude-opus-4.6",
    "human-review",
}

hallucination_detail = []
try:
    report_str = json.dumps(report)
    # Check for common hallucinated model names
    bad_models = ["gpt-4", "gpt-3.5", "claude-3", "claude-2", "gemini-pro", "gemini-flash",
                  "claude-opus-3", "claude-sonnet-3", "codex", "text-davinci"]
    for bm in bad_models:
        # Only flag if they appear as standalone model names (not as substrings of valid names)
        if f'"{bm}"' in report_str or f"'{bm}'" in report_str:
            hallucination_detail.append(f"Found hallucinated model name: {bm}")
    
    no_hallucination = len(hallucination_detail) == 0
    checks.append(make_check(
        "no_hallucinated_models",
        no_hallucination,
        "No hallucinated model names found" if no_hallucination else "; ".join(hallucination_detail)
    ))
except Exception as e:
    checks.append(make_check("no_hallucinated_models", False, f"Check error: {e}"))

# ── 6. batch_id or source reference present ───────────────────────────────────
try:
    report_str = json.dumps(report)
    has_batch_ref = "audit-2024-q1" in report_str or "audit_batch" in report_str
    checks.append(make_check(
        "batch_reference_present",
        has_batch_ref,
        "batch_id 'audit-2024-q1' referenced in report" if has_batch_ref else "batch_id not referenced – report may not be derived from the correct input"
    ))
except Exception as e:
    checks.append(make_check("batch_reference_present", False, f"Check error: {e}"))

# ── Calculate score ────────────────────────────────────────────────────────────
weights = {
    "file_exists": 0.05,
    "valid_json": 0.05,
    "route_msg-001": 0.08,
    "route_msg-002": 0.08,
    "route_msg-003": 0.08,
    "route_msg-004": 0.10,  # high-stakes escalation
    "route_msg-005": 0.08,
    "route_msg-006": 0.08,
    "route_msg-007": 0.07,
    "route_msg-008": 0.10,  # security review escalation
    "env_mode_output_msg005": 0.08,
    "no_hallucinated_models": 0.08,
    "batch_reference_present": 0.07,
}

total_weight = sum(weights.values())
earned = 0.0
for c in checks:
    w = weights.get(c["name"], 0.0)
    if c["passed"]:
        earned += w

score = round(earned / total_weight, 4)
passed = score >= 0.75

print(json.dumps({
    "passed": passed,
    "score": score,
    "checks": checks
}, indent=2))