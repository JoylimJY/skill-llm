#!/usr/bin/env python3
"""
Evaluation script for the claude-relay configuration and audit task.
Usage: python3 eval.py <workspace_dir>
"""

import sys
import os
import json
import subprocess
import re
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])
    skill_dir = workspace / "skills" / "claude-relay"
    projects_root = workspace / "dev_projects"
    relay_sh = skill_dir / "scripts" / "relay.sh"

    checks = []

    # ── CHECK 1: projects.map exists and is not the broken original ──────────
    def check_projects_map_exists():
        map_path = skill_dir / "projects.map"
        if not map_path.exists():
            return False, "projects.map not found at skills/claude-relay/projects.map"
        content = map_path.read_text()
        # Must not contain the broken arrow format
        if " -> " in content:
            return False, "projects.map still contains broken '-> ' format entries"
        return True, f"projects.map exists ({len(content)} bytes)"

    checks.append(run_check("projects.map_exists_and_not_broken", check_projects_map_exists))

    # ── CHECK 2: projects.map has correct format entries for required aliases ─
    REQUIRED_ALIASES = {
        "pay-gw":   str(projects_root / "payment-gateway"),
        "auth-svc": str(projects_root / "user-auth-service"),
        "pipeline": str(projects_root / "data-pipeline"),
    }

    def check_map_format_and_aliases():
        map_path = skill_dir / "projects.map"
        if not map_path.exists():
            return False, "projects.map not found"
        content = map_path.read_text()
        found = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            parts = line.split("=", 1)
            alias = parts[0].strip()
            path = parts[1].strip()
            found[alias] = path

        missing = []
        wrong_path = []
        for alias, expected_path in REQUIRED_ALIASES.items():
            if alias not in found:
                missing.append(alias)
            elif found[alias].rstrip("/") != expected_path.rstrip("/"):
                wrong_path.append(f"{alias}: got '{found[alias]}', expected '{expected_path}'")

        if missing:
            return False, f"Missing required aliases: {missing}"
        if wrong_path:
            return False, f"Wrong paths in map: {wrong_path}"
        return True, f"All required aliases found with correct paths: {list(REQUIRED_ALIASES.keys())}"

    checks.append(run_check("projects_map_correct_aliases", check_map_format_and_aliases))

    # ── CHECK 3: relay.sh can resolve pay-gw alias and returns correct session name ──
    def check_session_name_pay_gw():
        if not relay_sh.exists():
            return False, "relay.sh not found"
        env = os.environ.copy()
        env["CLAUDE_RELAY_MAP"] = str(skill_dir / "projects.map")
        env["CLAUDE_RELAY_ROOT"] = str(projects_root)

        result = subprocess.run(
            ["bash", str(relay_sh), "session", "pay-gw"],
            capture_output=True, text=True, env=env
        )
        if result.returncode != 0:
            return False, f"relay.sh session pay-gw failed (rc={result.returncode}): {result.stderr.strip()}"
        session_name = result.stdout.strip()
        # Expected: cc_payment-gateway (basename of /workspace/dev_projects/payment-gateway)
        expected = "cc_payment-gateway"
        if session_name == expected:
            return True, f"Correct session name: '{session_name}'"
        # Also accept sanitized variants
        if re.match(r'^cc_payment.gateway$', session_name):
            return True, f"Acceptable sanitized session name: '{session_name}'"
        return False, f"Wrong session name: got '{session_name}', expected '{expected}'"

    checks.append(run_check("session_name_pay_gw", check_session_name_pay_gw))

    # ── CHECK 4: relay.sh can resolve auth-svc alias and returns correct session name ──
    def check_session_name_auth_svc():
        if not relay_sh.exists():
            return False, "relay.sh not found"
        env = os.environ.copy()
        env["CLAUDE_RELAY_MAP"] = str(skill_dir / "projects.map")
        env["CLAUDE_RELAY_ROOT"] = str(projects_root)

        result = subprocess.run(
            ["bash", str(relay_sh), "session", "auth-svc"],
            capture_output=True, text=True, env=env
        )
        if result.returncode != 0:
            return False, f"relay.sh session auth-svc failed (rc={result.returncode}): {result.stderr.strip()}"
        session_name = result.stdout.strip()
        expected = "cc_user-auth-service"
        if session_name == expected:
            return True, f"Correct session name: '{session_name}'"
        if re.match(r'^cc_user.auth.service$', session_name):
            return True, f"Acceptable sanitized session name: '{session_name}'"
        return False, f"Wrong session name: got '{session_name}', expected '{expected}'"

    checks.append(run_check("session_name_auth_svc", check_session_name_auth_svc))

    # ── CHECK 5: relay.sh returns exit code 6 when sending to stopped session ─
    def check_exit_code_6_on_stopped_session():
        if not relay_sh.exists():
            return False, "relay.sh not found"
        env = os.environ.copy()
        env["CLAUDE_RELAY_MAP"] = str(skill_dir / "projects.map")
        env["CLAUDE_RELAY_ROOT"] = str(projects_root)
        # Ensure the session is not running
        session_name = "cc_data-pipeline"
        subprocess.run(["tmux", "kill-session", "-t", session_name], 
                      capture_output=True, env=env)

        result = subprocess.run(
            ["bash", str(relay_sh), "send", "pipeline", "hello"],
            capture_output=True, text=True, env=env
        )
        if result.returncode == 6:
            return True, f"Correctly returned exit code 6 for send on stopped session"
        return False, f"Expected exit code 6, got {result.returncode}. stderr: {result.stderr.strip()}"

    checks.append(run_check("exit_code_6_stopped_session", check_exit_code_6_on_stopped_session))

    # ── CHECK 6: relay_audit.json exists and has required fields ─────────────
    def check_audit_json_exists():
        # Search for relay_audit.json anywhere in workspace
        found_files = list(workspace.rglob("relay_audit.json"))
        if not found_files:
            return False, "relay_audit.json not found anywhere in workspace"
        audit_path = found_files[0]
        try:
            data = json.loads(audit_path.read_text())
        except json.JSONDecodeError as e:
            return False, f"relay_audit.json is not valid JSON: {e}"
        return True, f"relay_audit.json found at {audit_path}"

    checks.append(run_check("relay_audit_json_exists", check_audit_json_exists))

    # ── CHECK 7: relay_audit.json contains correct session names ─────────────
    def check_audit_json_session_names():
        found_files = list(workspace.rglob("relay_audit.json"))
        if not found_files:
            return False, "relay_audit.json not found"
        try:
            data = json.loads(found_files[0].read_text())
        except Exception as e:
            return False, f"Could not parse relay_audit.json: {e}"

        audit_str = json.dumps(data)

        # Must mention the correct session names derived from basename sanitization
        required_session_names = ["cc_payment-gateway", "cc_user-auth-service", "cc_data-pipeline"]
        # Also accept underscore-sanitized variants
        alt_names = ["cc_payment_gateway", "cc_user_auth_service", "cc_data_pipeline"]

        found_sessions = []
        for req, alt in zip(required_session_names, alt_names):
            if req in audit_str or alt in audit_str:
                found_sessions.append(req)

        if len(found_sessions) == 3:
            return True, f"All 3 correct session names found in relay_audit.json"
        missing = [r for r in required_session_names if r not in found_sessions and 
                   r.replace("-","_") not in audit_str]
        return False, f"Missing session names in audit JSON. Found: {found_sessions}, Missing: {missing}"

    checks.append(run_check("audit_json_correct_session_names", check_audit_json_session_names))

    # ── CHECK 8: relay_audit.json documents the exit-code-6 error finding ────
    def check_audit_json_error_code():
        found_files = list(workspace.rglob("relay_audit.json"))
        if not found_files:
            return False, "relay_audit.json not found"
        try:
            data = json.loads(found_files[0].read_text())
        except Exception as e:
            return False, f"Could not parse relay_audit.json: {e}"
        audit_str = json.dumps(data)
        # Must reference exit code 6 or "session not running" concept
        if "6" in audit_str and ("session" in audit_str.lower() or "stopped" in audit_str.lower() or "not running" in audit_str.lower()):
            return True, "relay_audit.json documents exit code 6 / stopped session condition"
        if "exit_code" in audit_str.lower() or "error_code" in audit_str.lower():
            # Check if value 6 is present
            if re.search(r'"[^"]*(?:exit|error)[^"]*"\s*:\s*6', audit_str, re.IGNORECASE):
                return True, "relay_audit.json documents exit code 6"
        return False, f"relay_audit.json does not appear to document exit code 6 for stopped session. Content preview: {audit_str[:300]}"

    checks.append(run_check("audit_json_documents_error_code_6", check_audit_json_error_code))

    # ── CHECK 9: CLAUDE_RELAY_MAP env var was used (not hardcoded path) ───────
    def check_env_var_usage():
        # Verify the agent set CLAUDE_RELAY_MAP to point to the skill's projects.map
        # We test this by seeing if the relay.sh resolves correctly when given the env var
        env = os.environ.copy()
        env["CLAUDE_RELAY_MAP"] = str(skill_dir / "projects.map")
        env["CLAUDE_RELAY_ROOT"] = str(projects_root)

        result = subprocess.run(
            ["bash", str(relay_sh), "session", "pipeline"],
            capture_output=True, text=True, env=env
        )
        if result.returncode != 0:
            return False, f"'pipeline' alias resolution failed even with CLAUDE_RELAY_MAP set correctly. rc={result.returncode}, stderr={result.stderr.strip()}"
        session_name = result.stdout.strip()
        if "data-pipeline" in session_name or "data_pipeline" in session_name:
            return True, f"CLAUDE_RELAY_MAP resolves 'pipeline' alias to data-pipeline correctly: session='{session_name}'"
        return False, f"Unexpected session name for 'pipeline' alias: '{session_name}'"

    checks.append(run_check("pipeline_alias_resolves_correctly", check_env_var_usage))

    # ── CHECK 10: The broken projects.map entries were removed/replaced ───────
    def check_broken_entries_removed():
        map_path = skill_dir / "projects.map"
        if not map_path.exists():
            return False, "projects.map not found"
        content = map_path.read_text()
        
        bad_patterns = [
            (" -> ", "arrow format '-> ' still present"),
            ("payment-gw ->", "old arrow-format payment-gw entry still present"),
            ("/nonexistent/old/path", "stale nonexistent path still present"),
            ("/wrong/case/path", "FRONTEND wrong path still present"),
            ("/also/wrong/path", "wrong path for user-auth still present"),
        ]
        violations = []
        for pattern, desc in bad_patterns:
            if pattern in content:
                violations.append(desc)
        if violations:
            return False, f"Broken entries still in projects.map: {violations}"
        return True, "All broken entries removed from projects.map"

    checks.append(run_check("broken_map_entries_removed", check_broken_entries_removed))

    # ── Scoring ────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()