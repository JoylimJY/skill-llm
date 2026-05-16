import sys
import json
import re
from pathlib import Path

def load_json_safe(path):
    try:
        with open(path) as f:
            return json.load(f), None
    except Exception as e:
        return None, str(e)

def load_text_safe(path):
    try:
        with open(path) as f:
            return f.read(), None
    except Exception as e:
        return None, str(e)

def find_file(workspace, name):
    matches = list(Path(workspace).rglob(name))
    return matches[0] if matches else None

workspace = sys.argv[1]
checks = []

# =====================================================================
# FILE 1: workflow_governance.md
# =====================================================================
gov_path = find_file(workspace, "workflow_governance.md")

if gov_path is None:
    checks.append({"name": "workflow_governance.md exists", "passed": False,
                    "detail": "File not found anywhere in workspace"})
    gov_text = ""
else:
    checks.append({"name": "workflow_governance.md exists", "passed": True,
                    "detail": str(gov_path)})
    gov_text, err = load_text_safe(gov_path)
    if err:
        gov_text = ""
        checks.append({"name": "workflow_governance.md readable", "passed": False, "detail": err})
    else:
        checks.append({"name": "workflow_governance.md readable", "passed": True, "detail": f"{len(gov_text)} chars"})

gov_lower = gov_text.lower() if gov_text else ""

# Check: Three delivery states are documented
states_present = []
for state_kw in ["final result", "partial progress", "blocked"]:
    if state_kw in gov_lower:
        states_present.append(state_kw)
all_states = len(states_present) == 3
checks.append({
    "name": "gov: All 3 delivery states documented",
    "passed": all_states,
    "detail": f"Found states: {states_present}"
})

# Check: Two-phase pattern (acknowledgment + completion delivery) is present
has_phase1 = any(kw in gov_lower for kw in ["phase 1", "start acknowledgment", "acknowledgement", "ack", "one short"])
has_phase2 = any(kw in gov_lower for kw in ["phase 2", "completion delivery", "proactively", "follow-up", "follow up"])
two_phase = has_phase1 and has_phase2
checks.append({
    "name": "gov: Two-phase pattern documented (ack + delivery)",
    "passed": two_phase,
    "detail": f"Phase1 signals found: {has_phase1}, Phase2 signals found: {has_phase2}"
})

# Check: NO_REPLY conditions — all 3 must be present
# Condition 1: materially identical / duplicate content already received
cond1 = any(kw in gov_lower for kw in [
    "materially identical", "identical to what", "already received", "already got"
])
# Condition 2: user has already received an equivalent final answer
cond2 = any(kw in gov_lower for kw in [
    "equivalent final answer", "final answer", "equivalent answer", "already received"
])
# Condition 3: suppressing a duplicate internal event and will immediately send proper delivery
cond3 = any(kw in gov_lower for kw in [
    "suppressing", "duplicate internal", "will immediately send", "proper delivery", "suppress"
])
no_reply_conditions = sum([cond1, cond2, cond3])
checks.append({
    "name": "gov: NO_REPLY conditions documented (need ≥2 of 3 specific conditions)",
    "passed": no_reply_conditions >= 2,
    "detail": f"Conditions found: cond1={cond1}, cond2={cond2}, cond3={cond3} ({no_reply_conditions}/3)"
})

# Check: Minimal handoff template language is present
handoff_signals = [
    "own the final delivery",
    "one short acknowledgment",
    "proactively send",
    "do not wait for the user"
]
handoff_found = sum(1 for s in handoff_signals if s in gov_lower)
checks.append({
    "name": "gov: Minimal handoff template language present (≥2 of 4 key phrases)",
    "passed": handoff_found >= 2,
    "detail": f"Found {handoff_found}/4 handoff phrases: {[s for s in handoff_signals if s in gov_lower]}"
})

# Check: Output patterns for each state are described
pattern_final = any(kw in gov_lower for kw in ["concise conclusion", "essential evidence", "next step"])
pattern_partial = any(kw in gov_lower for kw in ["what is done", "what remains", "eta", "expected next"])
pattern_blocked = any(kw in gov_lower for kw in ["what is blocked", "what the user needs", "provide or approve"])
checks.append({
    "name": "gov: Output patterns for delivery states described",
    "passed": pattern_final or pattern_partial or pattern_blocked,
    "detail": f"final={pattern_final}, partial={pattern_partial}, blocked={pattern_blocked}"
})

# =====================================================================
# FILE 2: event_classifications.json
# =====================================================================
ec_path = find_file(workspace, "event_classifications.json")

if ec_path is None:
    checks.append({"name": "event_classifications.json exists", "passed": False,
                    "detail": "File not found anywhere in workspace"})
    ec_data = None
else:
    checks.append({"name": "event_classifications.json exists", "passed": True,
                    "detail": str(ec_path)})
    ec_data, err = load_json_safe(ec_path)
    if err:
        ec_data = None
        checks.append({"name": "event_classifications.json valid JSON", "passed": False, "detail": err})
    else:
        checks.append({"name": "event_classifications.json valid JSON", "passed": True,
                        "detail": f"Type: {type(ec_data).__name__}, len: {len(ec_data) if isinstance(ec_data, list) else 'N/A'}"})

# Ground truth classifications
GROUND_TRUTH = {
    "REC-20240315-001":      "final_result",
    "SYNC-20240315-007":     "partial_progress",
    "WRBK-20240315-003":     "blocked",
    "REC-20240315-002":      "no_reply",
    "PAY-20240315-019":      "blocked",
    "ANOM-20240315-005":     "final_result",
    "BATCH-20240315-011":    "partial_progress",
    "ANOM-20240315-005-RESEND": "no_reply",
}

# Accepted label variants
LABEL_MAP = {
    "final_result": ["final_result", "final result", "final"],
    "partial_progress": ["partial_progress", "partial progress", "partial", "in_progress", "progress"],
    "blocked": ["blocked", "blocker"],
    "no_reply": ["no_reply", "no reply", "silence", "silent", "duplicate", "suppress", "noreply"],
}

def normalize_label(raw):
    if raw is None:
        return None
    raw_l = str(raw).lower().strip().replace("-", "_").replace(" ", "_")
    for canonical, variants in LABEL_MAP.items():
        for v in variants:
            if v.replace(" ", "_") in raw_l or raw_l == v.replace(" ", "_"):
                return canonical
    return raw_l

if ec_data is not None and isinstance(ec_data, list):
    correct = 0
    total = len(GROUND_TRUTH)
    per_event_results = []

    for item in ec_data:
        if not isinstance(item, dict):
            continue
        # Try multiple key names for job_id
        job_id = item.get("job_id") or item.get("id") or item.get("event_id")
        raw_classification = item.get("classification") or item.get("state") or item.get("delivery_state") or item.get("status")
        message = item.get("message") or item.get("user_message") or item.get("delivery_message") or item.get("output") or ""

        if job_id not in GROUND_TRUTH:
            continue

        expected = GROUND_TRUTH[job_id]
        got = normalize_label(raw_classification)
        is_correct = (got == expected)
        if is_correct:
            correct += 1

        # Check message quality for non-no_reply events
        msg_ok = True
        msg_detail = ""
        if expected == "no_reply":
            # For no_reply, message should be empty or explicitly note silence
            msg_ok = (not message or len(str(message).strip()) < 50 or
                      any(kw in str(message).lower() for kw in ["no reply", "silence", "duplicate", "already sent", "suppress"]))
            msg_detail = f"no_reply message check: {'ok' if msg_ok else 'message too substantive for a silent event'}"
        elif expected == "final_result":
            # Should contain a conclusion and something from the result payload
            msg_ok = len(str(message).strip()) > 20
            msg_detail = f"final_result message length: {len(str(message))}"
        elif expected == "partial_progress":
            # Should mention what's done and what remains
            msg_lower = str(message).lower()
            msg_ok = len(str(message).strip()) > 20
            msg_detail = f"partial_progress message length: {len(str(message))}"
        elif expected == "blocked":
            # Should explain the blocker
            msg_lower = str(message).lower()
            msg_ok = len(str(message).strip()) > 20
            msg_detail = f"blocked message length: {len(str(message))}"

        per_event_results.append({
            "job_id": job_id,
            "expected": expected,
            "got": got,
            "correct": is_correct,
            "msg_ok": msg_ok,
            "msg_detail": msg_detail
        })

    # Report per-classification
    correct_classifications = sum(1 for r in per_event_results if r["correct"])
    total_classified = len(per_event_results)

    checks.append({
        "name": "ec: All 8 events present in classifications",
        "passed": total_classified == 8,
        "detail": f"Found {total_classified}/8 known job_ids in output"
    })

    checks.append({
        "name": "ec: Classification accuracy ≥6/8",
        "passed": correct_classifications >= 6,
        "detail": f"Correct: {correct_classifications}/{total_classified}. Details: " +
                  "; ".join(f"{r['job_id']}: expected={r['expected']}, got={r['got']}" for r in per_event_results)
    })

    # Check NO_REPLY events are correctly identified (critical proprietary rule)
    no_reply_events = [r for r in per_event_results if r["expected"] == "no_reply"]
    no_reply_correct = sum(1 for r in no_reply_events if r["correct"])
    checks.append({
        "name": "ec: NO_REPLY events correctly silenced (both must be correct)",
        "passed": no_reply_correct == 2,
        "detail": f"NO_REPLY correct: {no_reply_correct}/2. " +
                  "; ".join(f"{r['job_id']}={r['got']}" for r in no_reply_events)
    })

    # Check BLOCKED events
    blocked_events = [r for r in per_event_results if r["expected"] == "blocked"]
    blocked_correct = sum(1 for r in blocked_events if r["correct"])
    checks.append({
        "name": "ec: BLOCKED events correctly classified (both must be correct)",
        "passed": blocked_correct == 2,
        "detail": f"BLOCKED correct: {blocked_correct}/2. " +
                  "; ".join(f"{r['job_id']}={r['got']}" for r in blocked_events)
    })

    # Check message quality for delivered events (non-no_reply)
    delivery_events = [r for r in per_event_results if r["expected"] != "no_reply"]
    msg_ok_count = sum(1 for r in delivery_events if r["msg_ok"])
    checks.append({
        "name": "ec: Delivery messages are substantive (≥4 of 6 delivered events)",
        "passed": msg_ok_count >= 4,
        "detail": f"Substantive messages: {msg_ok_count}/{len(delivery_events)}. " +
                  "; ".join(f"{r['job_id']}: {r['msg_detail']}" for r in delivery_events)
    })

elif ec_data is not None:
    checks.append({
        "name": "ec: Classifications is a list",
        "passed": False,
        "detail": f"Expected list, got {type(ec_data).__name__}"
    })

# =====================================================================
# SCORING
# =====================================================================
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 3) if total > 0 else 0.0
passed = score >= 0.70

result = {
    "passed": passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))