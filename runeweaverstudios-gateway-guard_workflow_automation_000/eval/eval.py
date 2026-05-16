#!/usr/bin/env python3
"""
Evaluation script for the Gateway Guard task.
Usage: python3 eval_script.py /workspace
"""
import json
import pathlib
import sys
import time

workspace = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("/workspace")
OPENCLAW_HOME = pathlib.Path("/root/.openclaw")
CONFIG_PATH   = OPENCLAW_HOME / "openclaw.json"
CONTINUE_STATE= OPENCLAW_HOME / "logs" / "gateway-guard.continue-state.json"
MOCK_LOG      = OPENCLAW_HOME / "logs" / "mock_openclaw_calls.log"
CONTINUE_FLAG = OPENCLAW_HOME / "logs" / "continue_delivered.flag"

checks = []

def check(name, passed, detail=""):
    checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})
    return bool(passed)


# ── CHECK 1: openclaw.json has gateway.auth with mode and token ────────────
try:
    cfg = json.loads(CONFIG_PATH.read_text())
    auth = cfg.get("gateway", {}).get("auth", {})
    mode = auth.get("mode")
    token = auth.get("token") if mode == "token" else auth.get("password")
    has_mode  = mode in ("token", "password")
    has_secret = bool(token)
    ok = has_mode and has_secret
    check(
        "openclaw.json has gateway.auth with mode and secret",
        ok,
        f"mode={mode!r} secret_present={has_secret} auth={auth}"
    )
except Exception as e:
    check("openclaw.json has gateway.auth with mode and secret", False, str(e))

# ── CHECK 2: gateway was actually restarted (openclaw CLI invoked correctly) ─
try:
    if not MOCK_LOG.exists():
        check("openclaw gateway stop was called", False, "mock_openclaw_calls.log not found")
        check("openclaw gateway start was called with correct args", False, "mock_openclaw_calls.log not found")
    else:
        log_text = MOCK_LOG.read_text()
        stop_called = "gateway stop" in log_text
        check("openclaw gateway stop was called", stop_called, log_text[:500])
        start_called = ("gateway started" in log_text or "EFFECT: gateway started" in log_text)
        check("openclaw gateway start was called", start_called, log_text[:500])
except Exception as e:
    check("openclaw gateway stop was called", False, str(e))
    check("openclaw gateway start was called", False, str(e))

# ── CHECK 3: gateway started with --auth token and a token value ────────────
try:
    log_text = MOCK_LOG.read_text() if MOCK_LOG.exists() else ""
    # Look for: gateway started port=17878 auth=token secret=tok_...
    import re
    pattern = r"EFFECT: gateway started port=17878 auth=token secret=(tok_[0-9a-f]+)"
    m = re.search(pattern, log_text)
    ok = bool(m)
    detail = m.group(0) if m else f"pattern not found in log: {log_text[:600]}"
    check("gateway started on correct port 17878 with token auth", ok, detail)
except Exception as e:
    check("gateway started on correct port 17878 with token auth", False, str(e))

# ── CHECK 4: token in running state matches token in config ─────────────────
try:
    cfg = json.loads(CONFIG_PATH.read_text())
    config_token = cfg.get("gateway", {}).get("auth", {}).get("token", "")
    log_text = MOCK_LOG.read_text() if MOCK_LOG.exists() else ""
    import re
    m = re.search(r"EFFECT: gateway started.*secret=(\S+)", log_text)
    running_token = m.group(1) if m else ""
    ok = bool(config_token) and config_token == running_token
    check(
        "token in config matches token used to start gateway",
        ok,
        f"config_token={config_token!r} running_token={running_token!r}"
    )
except Exception as e:
    check("token in config matches token used to start gateway", False, str(e))

# ── CHECK 5: continue-on-error was triggered (log error detected + delivered) ─
try:
    delivered = CONTINUE_FLAG.exists()
    check(
        "continue message was delivered after detecting run error",
        delivered,
        f"continue_delivered.flag exists: {delivered}"
    )
except Exception as e:
    check("continue message was delivered after detecting run error", False, str(e))

# ── CHECK 6: continue-state.json exists with last_trigger timestamp ─────────
try:
    if not CONTINUE_STATE.exists():
        check("continue-state.json written with last_trigger", False, "file not found")
    else:
        state = json.loads(CONTINUE_STATE.read_text())
        has_ts = "last_trigger" in state and isinstance(state["last_trigger"], (int, float)) and state["last_trigger"] > 0
        check(
            "continue-state.json written with last_trigger",
            has_ts,
            f"state={state}"
        )
except Exception as e:
    check("continue-state.json written with last_trigger", False, str(e))

# ── CHECK 7: gateway_health_report.json exists in workspace ─────────────────
try:
    candidates = list(workspace.rglob("gateway_health_report.json"))
    if not candidates:
        check("gateway_health_report.json exists in workspace", False, "file not found anywhere in workspace")
        report = None
    else:
        report_path = candidates[0]
        report = json.loads(report_path.read_text())
        check("gateway_health_report.json exists in workspace", True, str(report_path))
except Exception as e:
    check("gateway_health_report.json exists in workspace", False, str(e))
    report = None

# ── CHECK 8: gateway_health_report.json has required fields ─────────────────
try:
    if report is None:
        check("gateway_health_report.json has required fields", False, "report not loaded")
    else:
        required_keys = {"status_before", "status_after", "continue_triggered"}
        present_keys = set(report.keys())
        missing = required_keys - present_keys
        ok = len(missing) == 0
        check(
            "gateway_health_report.json has required fields",
            ok,
            f"present={present_keys} missing={missing}"
        )
except Exception as e:
    check("gateway_health_report.json has required fields", False, str(e))

# ── CHECK 9: report accurately reflects before/after status ─────────────────
try:
    if report is None:
        check("report status_before reflects initial not-ok state", False, "report not loaded")
        check("report status_after reflects ok state and continue_triggered=true", False, "report not loaded")
    else:
        # status_before should reflect a non-ok / mismatch / missing-auth state
        status_before = report.get("status_before", {})
        if isinstance(status_before, dict):
            before_ok = status_before.get("ok", True)  # should be False initially
            before_not_ok = not before_ok
        elif isinstance(status_before, str):
            before_not_ok = status_before.lower() in ("not_ok", "error", "mismatch", "missing", "false")
        else:
            before_not_ok = False
        check(
            "report status_before reflects initial not-ok/mismatch state",
            before_not_ok,
            f"status_before={status_before!r}"
        )
        # status_after should be ok
        status_after = report.get("status_after", {})
        if isinstance(status_after, dict):
            after_ok = status_after.get("ok", False)
        elif isinstance(status_after, str):
            after_ok = status_after.lower() in ("ok", "true")
        else:
            after_ok = False
        # continue_triggered must be truthy
        cont = report.get("continue_triggered")
        cont_ok = cont is True or cont == 1 or (isinstance(cont, str) and cont.lower() == "true")
        check(
            "report status_after reflects ok state and continue_triggered=true",
            after_ok and cont_ok,
            f"status_after={status_after!r} continue_triggered={cont!r}"
        )
except Exception as e:
    check("report accurately reflects before/after status", False, str(e))

# ── Scoring ──────────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = passed_count / total

final_passed = all(c["passed"] for c in checks)

result = {
    "passed": final_passed,
    "score": round(score, 4),
    "checks": checks,
}
print(json.dumps(result, indent=2))