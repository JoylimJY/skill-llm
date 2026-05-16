#!/usr/bin/env python3
"""
Evaluation script for claude-relay task.
Checks:
1. projects.map is correctly formatted with both aliases
2. session_audit.json exists and contains required fields
3. Session names are correctly computed per sanitize() logic
4. Exit code 6 was observed for send-before-start
5. Start/send/stop operations succeeded for both projects
"""

import json
import sys
import re
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    
    # ── Helper ──────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        checks.append({"name": name, "passed": bool(passed), "detail": str(detail)})

    # ── Expected session names per sanitize() logic ──────────────────────────
    # sanitize("My-WebApp"):
    #   lower → "my-webapp"
    #   non-[a-z0-9_] → "_" : "my_webapp"
    #   strip leading "__": no change
    #   strip trailing "__": no change
    #   [:40]: "my_webapp"
    # session = "cc_my_webapp"
    EXPECTED_WEBAPP_SESSION = "cc_my_webapp"

    # sanitize("data--pipeline"):
    #   lower → "data--pipeline"
    #   non-[a-z0-9_] → "_": "data__pipeline"
    #   strip leading "__": no change (doesn't start with __)
    #   strip trailing "__": no change
    #   Wait — the sanitize strips __prefix and __suffix via bash:
    #   raw="${raw#__}" strips leading "__" prefix once
    #   raw="${raw%%__}" strips trailing "__" suffix (longest match from end... actually greedy trailing)
    #   "data__pipeline" — no leading __ so #__ no-ops; %%__ strips trailing __ → "data__pipeline"%%__ 
    #   Actually "data__pipeline" does NOT end with "__", it ends with "pipeline", so %%__ = no change
    #   Result: "cc_data__pipeline"
    EXPECTED_PIPELINE_SESSION = "cc_data__pipeline"

    # ── Check 1: projects.map format ─────────────────────────────────────────
    map_path = ws / "skills" / "claude-relay" / "projects.map"
    try:
        map_content = map_path.read_text()
        lines = [l.strip() for l in map_content.splitlines() if l.strip() and not l.strip().startswith('#')]
        
        webapp_alias_ok = False
        pipeline_alias_ok = False
        for line in lines:
            # Must be name=path format (AWK -F'=' $1==k)
            if '=' in line:
                parts = line.split('=', 1)
                key = parts[0].strip()
                val = parts[1].strip()
                if key == 'webapp' and val == '/workspace/projects/My-WebApp':
                    webapp_alias_ok = True
                if key == 'pipeline' and val == '/workspace/projects/data--pipeline':
                    pipeline_alias_ok = True
        
        add("projects.map: webapp alias correct", webapp_alias_ok,
            f"Expected 'webapp=/workspace/projects/My-WebApp' in {map_path}. Content:\n{map_content[:500]}")
        add("projects.map: pipeline alias correct", pipeline_alias_ok,
            f"Expected 'pipeline=/workspace/projects/data--pipeline' in {map_path}. Content:\n{map_content[:500]}")
    except Exception as e:
        add("projects.map: webapp alias correct", False, f"Could not read projects.map: {e}")
        add("projects.map: pipeline alias correct", False, f"Could not read projects.map: {e}")

    # ── Check 2: session_audit.json exists ───────────────────────────────────
    audit_files = list(ws.rglob("session_audit.json"))
    if not audit_files:
        add("session_audit.json exists", False, "File not found anywhere in workspace")
        # Cannot do further checks
        total = len(checks)
        passed_count = sum(1 for c in checks if c["passed"])
        return {
            "passed": False,
            "score": passed_count / max(total, 1),
            "checks": checks
        }
    
    audit_path = audit_files[0]
    add("session_audit.json exists", True, f"Found at {audit_path}")

    try:
        audit_data = json.loads(audit_path.read_text())
    except Exception as e:
        add("session_audit.json is valid JSON", False, f"JSON parse error: {e}")
        total = len(checks)
        passed_count = sum(1 for c in checks if c["passed"])
        return {
            "passed": False,
            "score": passed_count / max(total, 1),
            "checks": checks
        }
    
    add("session_audit.json is valid JSON", True, "Parsed successfully")

    # ── Check 3: Correct session name for webapp ─────────────────────────────
    # Look for the expected session name anywhere in the JSON
    audit_str = json.dumps(audit_data)
    
    webapp_session_present = EXPECTED_WEBAPP_SESSION in audit_str
    add("session_audit.json: webapp session name is cc_my_webapp",
        webapp_session_present,
        f"Expected '{EXPECTED_WEBAPP_SESSION}' in audit. Got keys: {list(audit_data.keys()) if isinstance(audit_data, dict) else type(audit_data)}")

    pipeline_session_present = EXPECTED_PIPELINE_SESSION in audit_str
    add("session_audit.json: pipeline session name is cc_data__pipeline",
        pipeline_session_present,
        f"Expected '{EXPECTED_PIPELINE_SESSION}' in audit. Got snippet: {audit_str[:300]}")

    # ── Check 4: Exit code 6 recorded for send-before-start ──────────────────
    # The agent must have attempted send on webapp before starting it → exit code 6
    exit_code_6_found = False
    try:
        audit_str_lower = audit_str.lower()
        # Look for exit code 6 or "session not running" in the audit
        if '"6"' in audit_str or ': 6' in audit_str or ':6' in audit_str or \
           'exit_code": 6' in audit_str or '"exit_code":6' in audit_str or \
           'exit code 6' in audit_str_lower or 'exitcode": 6' in audit_str or \
           'session not running' in audit_str_lower or \
           re.search(r'["\s]6["\s,}]', audit_str):
            exit_code_6_found = True
        # More lenient: just check if 6 appears as a value somewhere
        if not exit_code_6_found:
            def search_for_6(obj, depth=0):
                if depth > 10:
                    return False
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        if 'exit' in str(k).lower() or 'error' in str(k).lower() or 'code' in str(k).lower():
                            if v == 6 or v == '6':
                                return True
                        if search_for_6(v, depth+1):
                            return True
                elif isinstance(obj, list):
                    for item in obj:
                        if search_for_6(item, depth+1):
                            return True
                return False
            exit_code_6_found = search_for_6(audit_data)
    except Exception as e:
        pass
    
    add("session_audit.json: exit code 6 recorded for premature send",
        exit_code_6_found,
        f"Expected exit code 6 (session not running) to be recorded. Audit snippet: {audit_str[:400]}")

    # ── Check 5: start operations succeeded for both projects ─────────────────
    start_webapp_ok = 'session started' in audit_str.lower() or \
                      'session exists' in audit_str.lower() or \
                      ('"webapp"' in audit_str and 'start' in audit_str_lower and 
                       ('true' in audit_str_lower or 'success' in audit_str_lower or 'ok' in audit_str_lower))
    
    add("session_audit.json: webapp start succeeded",
        start_webapp_ok,
        f"Expected evidence of successful start for webapp. Snippet: {audit_str[:300]}")

    start_pipeline_ok = 'session started' in audit_str.lower() or \
                        ('"pipeline"' in audit_str and 'start' in audit_str_lower and
                         ('true' in audit_str_lower or 'success' in audit_str_lower or 'ok' in audit_str_lower))
    
    add("session_audit.json: pipeline start succeeded",
        start_pipeline_ok,
        f"Expected evidence of successful start for pipeline. Snippet: {audit_str[:300]}")

    # ── Check 6: stop operations documented ──────────────────────────────────
    stop_present = 'stop' in audit_str_lower or 'session stopped' in audit_str_lower or \
                   'killed' in audit_str_lower
    add("session_audit.json: stop operations documented",
        stop_present,
        f"Expected evidence of stop operations. Snippet: {audit_str[:300]}")

    # ── Check 7: tail output captured ────────────────────────────────────────
    tail_present = 'tail' in audit_str_lower or 'output' in audit_str_lower or \
                   'capture' in audit_str_lower or 'mock-claude' in audit_str_lower or \
                   'pane' in audit_str_lower
    add("session_audit.json: tail output captured",
        tail_present,
        f"Expected tail/output field in audit. Snippet: {audit_str[:300]}")

    # ── Check 8: CLAUDE_BIN env var used (mock_claude.sh) ────────────────────
    mock_used = 'mock_claude' in audit_str_lower or \
                (webapp_session_present and pipeline_session_present)
    add("mock_claude.sh used as CLAUDE_BIN (inferred from correct session ops)",
        mock_used,
        "If sessions were started correctly with mock_claude, this passes.")

    # ── Final scoring ─────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = passed_count / total

    # Must pass the core structural checks to overall pass
    core_checks = [
        "projects.map: webapp alias correct",
        "projects.map: pipeline alias correct",
        "session_audit.json exists",
        "session_audit.json: webapp session name is cc_my_webapp",
        "session_audit.json: pipeline session name is cc_data__pipeline",
        "session_audit.json: exit code 6 recorded for premature send",
    ]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)

    return {
        "passed": core_passed and score >= 0.75,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))