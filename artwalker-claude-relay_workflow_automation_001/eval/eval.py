#!/usr/bin/env python3
"""
Evaluation script for the Claude Relay audit task.
Checks that the agent correctly:
1. Used the custom CLAUDE_RELAY_MAP (not the decoy) to resolve the 'fx-converter' alias
2. Determined the correct session name for 'FX Converter Service' using the proprietary sanitize() logic
3. Recorded exit code 6 when tailing a non-started session (via 'payments' alias)
4. Successfully started, sent, and stopped a session for the 'payments' alias
5. Wrote results to relay_audit.json with correct values
"""

import json
import sys
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
score = 0.0
MAX_SCORE = 5.0

def add_check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

# === Find relay_audit.json ===
audit_file = None
candidates = list(Path(workspace).rglob("relay_audit.json"))
if candidates:
    audit_file = candidates[0]

if not audit_file or not audit_file.exists():
    checks.append({
        "name": "relay_audit.json exists",
        "passed": False,
        "detail": f"File relay_audit.json not found anywhere in workspace. Searched: {workspace}"
    })
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

try:
    with open(audit_file, "r") as f:
        audit = json.load(f)
    score += add_check("relay_audit.json is valid JSON", True, f"Found at {audit_file}")
except Exception as e:
    checks.append({"name": "relay_audit.json is valid JSON", "passed": False, "detail": str(e)})
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

# === CHECK 1: fx-converter alias resolves to correct path ===
# The correct map is /workspace/config/relay/projects.map
# fx-converter=/workspace/fintech_projects/FX Converter Service
expected_fx_path = str(Path(workspace) / "fintech_projects" / "FX Converter Service")
try:
    fx_resolved = audit.get("fx_converter_resolved_path", "")
    passed = (str(fx_resolved).strip() == expected_fx_path)
    score += add_check(
        "fx-converter alias resolves to correct path",
        passed,
        f"Expected: '{expected_fx_path}', Got: '{fx_resolved}'"
    )
except Exception as e:
    score += add_check("fx-converter alias resolves to correct path", False, str(e))

# === CHECK 2: Session name for 'FX Converter Service' is correct ===
# sanitize("FX Converter Service"):
# 1. lowercase: "fx converter service"
# 2. replace non [a-z0-9_] with _: "fx_converter_service"
# 3. strip leading/trailing __: no change
# 4. truncate to 40: "fx_converter_service"
# session name: "cc_fx_converter_service"
expected_session_name = "cc_fx_converter_service"
try:
    reported_session = audit.get("fx_converter_session_name", "")
    passed = (str(reported_session).strip() == expected_session_name)
    score += add_check(
        "Session name for FX Converter Service is correct",
        passed,
        f"Expected: '{expected_session_name}', Got: '{reported_session}'. "
        f"sanitize('FX Converter Service') should produce 'fx_converter_service' "
        f"(lowercase, spaces→underscore, prefix cc_)"
    )
except Exception as e:
    score += add_check("Session name for FX Converter Service is correct", False, str(e))

# === CHECK 3: Tailing a non-started session returns exit code 6 ===
# The agent should have tried to tail 'payments' before starting it
# and captured exit code 6
try:
    tail_exit_code = audit.get("tail_before_start_exit_code", None)
    # Must be exactly 6 (integer or string)
    passed = (str(tail_exit_code).strip() == "6")
    score += add_check(
        "Tail on non-started session returns exit code 6",
        passed,
        f"Expected exit code 6 (session not running), Got: '{tail_exit_code}'"
    )
except Exception as e:
    score += add_check("Tail on non-started session returns exit code 6", False, str(e))

# === CHECK 4: payments alias session was started and stopped ===
# payments alias → /workspace/fintech_projects/payment-gateway
# session name: sanitize("payment-gateway") → "payment_gateway" → "cc_payment_gateway"
expected_payments_session = "cc_payment_gateway"
try:
    started = audit.get("payments_session_started", False)
    stopped = audit.get("payments_session_stopped", False)
    session_name = audit.get("payments_session_name", "")
    
    passed_start = bool(started)
    passed_stop = bool(stopped)
    passed_name = (str(session_name).strip() == expected_payments_session)
    
    passed = passed_start and passed_stop and passed_name
    score += add_check(
        "payments alias session started and stopped with correct name",
        passed,
        f"started={started}, stopped={stopped}, session_name='{session_name}' "
        f"(expected '{expected_payments_session}'). "
        f"sanitize('payment-gateway') → 'payment_gateway' → 'cc_payment_gateway'"
    )
except Exception as e:
    score += add_check("payments alias session started and stopped with correct name", False, str(e))

# === CHECK 5: send was used during the payments session ===
try:
    send_used = audit.get("send_used_during_payments_session", False)
    sent_text = audit.get("sent_text", "")
    passed = bool(send_used) and len(str(sent_text).strip()) > 0
    score += add_check(
        "send action was used during payments session",
        passed,
        f"send_used={send_used}, sent_text='{sent_text}'"
    )
except Exception as e:
    score += add_check("send action was used during payments session", False, str(e))

# === Final scoring ===
final_score = score / MAX_SCORE
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": round(final_score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2))