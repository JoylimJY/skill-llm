import sys
import json
import os
import subprocess
from pathlib import Path

def run_checks(workspace):
    checks = []
    overall_passed = True

    # --- Locate audit_report.json ---
    report_path = None
    candidates = list(Path(workspace).rglob("audit_report.json"))
    if candidates:
        report_path = candidates[0]

    if not report_path or not report_path.exists():
        checks.append({"name": "audit_report_exists", "passed": False, "detail": "audit_report.json not found anywhere in workspace"})
        return checks, 0.0

    checks.append({"name": "audit_report_exists", "passed": True, "detail": f"Found at {report_path}"})

    # --- Parse audit_report.json ---
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "audit_report_parseable", "passed": False, "detail": f"JSON parse error: {e}"})
        return checks, 0.0

    checks.append({"name": "audit_report_parseable", "passed": True, "detail": "Valid JSON"})

    # Normalize: report may be a list or a dict with a results key
    scenarios = None
    if isinstance(report, list):
        scenarios = report
    elif isinstance(report, dict):
        for key in ["scenarios", "results", "operations", "audit", "entries"]:
            if key in report and isinstance(report[key], list):
                scenarios = report[key]
                break
        if scenarios is None:
            # Maybe the dict itself maps scenario IDs to results
            # Accept if keys like S01, S02... exist
            if "S01" in report:
                scenarios = [{"id": k, **v} if isinstance(v, dict) else {"id": k, "decision": v} for k, v in report.items()]

    if scenarios is None:
        checks.append({"name": "audit_report_structure", "passed": False, "detail": "Cannot find scenario list in audit_report.json. Expected list or dict with 'scenarios'/'results' key."})
        return checks, 0.0

    checks.append({"name": "audit_report_structure", "passed": True, "detail": f"Found {len(scenarios)} scenario entries"})

    # Build a lookup by scenario ID
    def get_decision(scenario):
        """Extract BLOCKED/ALLOWED decision from a scenario entry (case-insensitive)."""
        for key in ["decision", "result", "outcome", "status", "verdict", "action"]:
            if key in scenario:
                val = str(scenario[key]).strip().upper()
                if "BLOCK" in val or "DENY" in val or "DENIED" in val or "REJECT" in val:
                    return "BLOCKED"
                if "ALLOW" in val or "PERMIT" in val or "PASS" in val or "OK" in val or "SUCCESS" in val:
                    return "ALLOWED"
        return None

    scenario_map = {}
    for s in scenarios:
        if isinstance(s, dict) and "id" in s:
            scenario_map[s["id"]] = s

    # --- Expected decisions based on guard.mjs rules ---
    # Rule 1: Write on protected file => BLOCKED (always)
    # Rule 2: Edit on protected file with net line removal > 2 => BLOCKED
    # Rule 3: Write on non-protected => ALLOWED
    # Rule 4: Edit on non-protected => ALLOWED
    # Rule 5: Edit on protected with net removal <= 2 => ALLOWED
    #
    # Protected files: CLAUDE.md, SHARED-CONTEXT.md, SOUL.md, IDENTITY.md, CONTEXT.md, TOOLS.md, MEMORY.md
    # Protected patterns: memory, memories, journal, diary, daily log
    # agent-memory.md matches pattern "memory"

    expected = {
        # S01: Write on CLAUDE.md (protected exact name) => BLOCKED
        "S01": ("BLOCKED", "Write on protected CLAUDE.md must be BLOCKED"),
        # S02: Write on src/utils/sanitize.js (not protected) => ALLOWED
        "S02": ("ALLOWED", "Write on non-protected sanitize.js must be ALLOWED"),
        # S03: Edit on SOUL.md removing 2 net lines (old=3 lines, new=1 line => net removal=2) => ALLOWED (<=2 is allowed)
        "S03": ("ALLOWED", "Edit on SOUL.md removing exactly 2 net lines must be ALLOWED (threshold is >2)"),
        # S04: Edit on SOUL.md removing 3 net lines (old=3 lines, new=0 => net removal=3) => BLOCKED (>2)
        "S04": ("BLOCKED", "Edit on SOUL.md removing 3 net lines must be BLOCKED (>2 threshold)"),
        # S05: Edit on IDENTITY.md adding a line (net +1) => ALLOWED
        "S05": ("ALLOWED", "Edit on IDENTITY.md adding content must be ALLOWED"),
        # S06: Edit on agent-memory.md removing 1 net line (matches 'memory' pattern) => ALLOWED (<=2)
        "S06": ("ALLOWED", "Edit on agent-memory.md removing 1 net line must be ALLOWED (pattern-protected but removal<=2)"),
        # S07: Write on SOUL.md (protected exact name) => BLOCKED
        "S07": ("BLOCKED", "Write on protected SOUL.md must be BLOCKED"),
        # S08: Edit on tests/unit/button.test.js (not protected) => ALLOWED
        "S08": ("ALLOWED", "Edit on non-protected button.test.js must be ALLOWED"),
    }

    scenario_score = 0
    max_scenario_score = len(expected)

    for sid, (exp_decision, rationale) in expected.items():
        if sid not in scenario_map:
            checks.append({
                "name": f"scenario_{sid}",
                "passed": False,
                "detail": f"Scenario {sid} missing from report. Expected {exp_decision}. {rationale}"
            })
            overall_passed = False
            continue

        actual = get_decision(scenario_map[sid])
        if actual is None:
            checks.append({
                "name": f"scenario_{sid}",
                "passed": False,
                "detail": f"Could not parse decision for {sid}. Entry: {scenario_map[sid]}. Expected {exp_decision}."
            })
            overall_passed = False
            continue

        passed = (actual == exp_decision)
        if passed:
            scenario_score += 1
        else:
            overall_passed = False

        checks.append({
            "name": f"scenario_{sid}",
            "passed": passed,
            "detail": f"Expected {exp_decision}, got {actual}. {rationale}"
        })

    # --- Bonus: Check that the agent actually invoked guard.mjs (not just guessed) ---
    # We verify by checking if guarded protected files still have their original content
    # (i.e., Write operations were not actually applied to protected files)
    claude_path = Path(workspace) / "agent-config" / "CLAUDE.md"
    soul_path = Path(workspace) / "agent-config" / "SOUL.md"

    try:
        claude_content = claude_path.read_text()
        soul_content = soul_path.read_text()
        # Original content should contain key phrases
        claude_intact = "Never fabricate data" in claude_content and "Core Directives" in claude_content
        soul_intact = "Agent Soul" in soul_content and "Transparency in all actions" in soul_content
        files_intact = claude_intact and soul_intact
        checks.append({
            "name": "protected_files_not_mutated",
            "passed": files_intact,
            "detail": (
                "Protected files retain original content (CLAUDE.md and SOUL.md not overwritten)."
                if files_intact
                else "Protected files appear to have been modified, which should not happen in an audit-only task."
            )
        })
        if not files_intact:
            overall_passed = False
    except Exception as e:
        checks.append({"name": "protected_files_not_mutated", "passed": False, "detail": f"Error reading protected files: {e}"})
        overall_passed = False

    # Score: scenario decisions + file integrity check
    total_points = scenario_score + (1 if checks[-1]["passed"] else 0)
    max_points = max_scenario_score + 1
    score = round(total_points / max_points, 4)

    overall_passed = overall_passed and (scenario_score == max_scenario_score)
    return checks, score


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, score = run_checks(workspace)
    passed = all(c["passed"] for c in checks)
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()