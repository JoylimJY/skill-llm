import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str) -> dict:
    workspace = Path(workspace_dir)
    checks = []

    # -------------------------------------------------------------------------
    # CHECK 1: FOCUS-LOG.md exists (archival happened)
    # -------------------------------------------------------------------------
    focus_log_path = workspace / "FOCUS-LOG.md"
    focus_log_exists = focus_log_path.exists()
    checks.append({
        "name": "FOCUS-LOG.md exists",
        "passed": focus_log_exists,
        "detail": "FOCUS-LOG.md was created at workspace root" if focus_log_exists else "FOCUS-LOG.md not found at workspace root"
    })

    focus_log_content = ""
    if focus_log_exists:
        try:
            focus_log_content = focus_log_path.read_text()
        except Exception as e:
            checks.append({
                "name": "FOCUS-LOG.md readable",
                "passed": False,
                "detail": f"Could not read FOCUS-LOG.md: {e}"
            })

    # -------------------------------------------------------------------------
    # CHECK 2: FOCUS-LOG.md contains archived entry for "Database Migration to PostgreSQL"
    # The format must be: ## [Project Name] — COMPLETED YYYY-MM-DD
    # -------------------------------------------------------------------------
    archive_header_pattern = re.compile(
        r'##\s+Database Migration to PostgreSQL\s*[—–-]+\s*COMPLETED\s+\d{4}-\d{2}-\d{2}',
        re.IGNORECASE
    )
    archive_header_found = bool(archive_header_pattern.search(focus_log_content))
    checks.append({
        "name": "FOCUS-LOG.md contains correct archive header for old project",
        "passed": archive_header_found,
        "detail": (
            "Found '## Database Migration to PostgreSQL — COMPLETED YYYY-MM-DD' header in FOCUS-LOG.md"
            if archive_header_found
            else f"Did not find required archive header pattern in FOCUS-LOG.md. Content snippet: {focus_log_content[:300]!r}"
        )
    })

    # -------------------------------------------------------------------------
    # CHECK 3: FOCUS-LOG.md contains Duration field
    # -------------------------------------------------------------------------
    duration_pattern = re.compile(r'\*\*Duration:\*\*', re.IGNORECASE)
    duration_found = bool(duration_pattern.search(focus_log_content))
    checks.append({
        "name": "FOCUS-LOG.md archived entry has **Duration:** field",
        "passed": duration_found,
        "detail": "Found **Duration:** field in FOCUS-LOG.md" if duration_found else "Missing **Duration:** field in FOCUS-LOG.md"
    })

    # -------------------------------------------------------------------------
    # CHECK 4: FOCUS-LOG.md contains Outcome field
    # -------------------------------------------------------------------------
    outcome_pattern = re.compile(r'\*\*Outcome:\*\*', re.IGNORECASE)
    outcome_found = bool(outcome_pattern.search(focus_log_content))
    checks.append({
        "name": "FOCUS-LOG.md archived entry has **Outcome:** field",
        "passed": outcome_found,
        "detail": "Found **Outcome:** field in FOCUS-LOG.md" if outcome_found else "Missing **Outcome:** field in FOCUS-LOG.md"
    })

    # -------------------------------------------------------------------------
    # CHECK 5: New FOCUS.md exists at workspace root
    # -------------------------------------------------------------------------
    focus_path = workspace / "FOCUS.md"
    focus_exists = focus_path.exists()
    checks.append({
        "name": "FOCUS.md exists at workspace root",
        "passed": focus_exists,
        "detail": "FOCUS.md found at workspace root" if focus_exists else "FOCUS.md not found at workspace root"
    })

    focus_content = ""
    if focus_exists:
        try:
            focus_content = focus_path.read_text()
        except Exception as e:
            checks.append({
                "name": "FOCUS.md readable",
                "passed": False,
                "detail": f"Could not read FOCUS.md: {e}"
            })

    # -------------------------------------------------------------------------
    # CHECK 6: New FOCUS.md does NOT contain the old project name (it was replaced)
    # -------------------------------------------------------------------------
    old_project_in_new_focus = "Database Migration to PostgreSQL" in focus_content
    checks.append({
        "name": "FOCUS.md does not contain old project (was replaced, not appended)",
        "passed": not old_project_in_new_focus,
        "detail": (
            "FOCUS.md correctly does not contain old project content"
            if not old_project_in_new_focus
            else "FOCUS.md still references old 'Database Migration to PostgreSQL' project — old focus was not cleared"
        )
    })

    # -------------------------------------------------------------------------
    # CHECK 7: New FOCUS.md has the required header format: # FOCUS — [Project Name]
    # -------------------------------------------------------------------------
    header_pattern = re.compile(r'^#\s+FOCUS\s*[—–-]+\s*\S+', re.MULTILINE)
    header_found = bool(header_pattern.search(focus_content))
    checks.append({
        "name": "FOCUS.md has correct header format '# FOCUS — [Project Name]'",
        "passed": header_found,
        "detail": (
            "Found '# FOCUS — [Project Name]' header"
            if header_found
            else f"Missing required header format. Got content snippet: {focus_content[:200]!r}"
        )
    })

    # -------------------------------------------------------------------------
    # CHECK 8: New FOCUS.md has **Started:** field
    # -------------------------------------------------------------------------
    started_pattern = re.compile(r'\*\*Started:\*\*\s*\d{4}-\d{2}-\d{2}', re.IGNORECASE)
    started_found = bool(started_pattern.search(focus_content))
    checks.append({
        "name": "FOCUS.md has **Started:** YYYY-MM-DD field",
        "passed": started_found,
        "detail": "Found **Started:** field with date" if started_found else "Missing or malformed **Started:** field"
    })

    # -------------------------------------------------------------------------
    # CHECK 9: New FOCUS.md has **Status:** field with valid value
    # -------------------------------------------------------------------------
    status_pattern = re.compile(r'\*\*Status:\*\*\s*(active|paused|blocked)', re.IGNORECASE)
    status_match = status_pattern.search(focus_content)
    status_found = bool(status_match)
    checks.append({
        "name": "FOCUS.md has valid **Status:** (active|paused|blocked)",
        "passed": status_found,
        "detail": (
            f"Found **Status:** {status_match.group(1)}" if status_found
            else "Missing or invalid **Status:** field (must be active, paused, or blocked)"
        )
    })

    # -------------------------------------------------------------------------
    # CHECK 10: New FOCUS.md has **Context:** field
    # -------------------------------------------------------------------------
    context_pattern = re.compile(r'\*\*Context:\*\*\s*.+', re.IGNORECASE)
    context_found = bool(context_pattern.search(focus_content))
    checks.append({
        "name": "FOCUS.md has **Context:** field",
        "passed": context_found,
        "detail": "Found **Context:** field" if context_found else "Missing **Context:** field"
    })

    # -------------------------------------------------------------------------
    # CHECK 11: New FOCUS.md has ## Objective section
    # -------------------------------------------------------------------------
    objective_pattern = re.compile(r'^##\s+Objective', re.MULTILINE | re.IGNORECASE)
    objective_found = bool(objective_pattern.search(focus_content))
    checks.append({
        "name": "FOCUS.md has ## Objective section",
        "passed": objective_found,
        "detail": "Found ## Objective section" if objective_found else "Missing ## Objective section"
    })

    # -------------------------------------------------------------------------
    # CHECK 12: New FOCUS.md has ## Plan section with at least one checklist item
    # -------------------------------------------------------------------------
    plan_pattern = re.compile(r'^##\s+Plan', re.MULTILINE | re.IGNORECASE)
    plan_found = bool(plan_pattern.search(focus_content))
    checklist_pattern = re.compile(r'- \[[ x]\]', re.IGNORECASE)
    checklist_found = bool(checklist_pattern.search(focus_content))
    plan_ok = plan_found and checklist_found
    checks.append({
        "name": "FOCUS.md has ## Plan section with checklist items (- [ ] or - [x])",
        "passed": plan_ok,
        "detail": (
            "Found ## Plan section with checklist items"
            if plan_ok
            else f"Plan section present: {plan_found}, Checklist items present: {checklist_found}"
        )
    })

    # -------------------------------------------------------------------------
    # CHECK 13: New FOCUS.md has ## Active State section with non-empty content
    # -------------------------------------------------------------------------
    active_state_pattern = re.compile(
        r'^##\s+Active State\s*\n+(.*?)(?=\n##|\Z)',
        re.MULTILINE | re.DOTALL | re.IGNORECASE
    )
    active_state_match = active_state_pattern.search(focus_content)
    active_state_content = active_state_match.group(1).strip() if active_state_match else ""
    active_state_ok = bool(active_state_match) and len(active_state_content) > 10
    checks.append({
        "name": "FOCUS.md has ## Active State section with substantive content",
        "passed": active_state_ok,
        "detail": (
            f"Found ## Active State with content: {active_state_content[:80]!r}"
            if active_state_ok
            else "Missing ## Active State section or it is empty (this section is required and sacred)"
        )
    })

    # -------------------------------------------------------------------------
    # CHECK 14: New FOCUS.md has ## Blockers section
    # -------------------------------------------------------------------------
    blockers_pattern = re.compile(r'^##\s+Blockers', re.MULTILINE | re.IGNORECASE)
    blockers_found = bool(blockers_pattern.search(focus_content))
    checks.append({
        "name": "FOCUS.md has ## Blockers section",
        "passed": blockers_found,
        "detail": "Found ## Blockers section" if blockers_found else "Missing ## Blockers section"
    })

    # -------------------------------------------------------------------------
    # CHECK 15: New FOCUS.md is under 50 lines
    # -------------------------------------------------------------------------
    if focus_content:
        line_count = len(focus_content.splitlines())
        under_50_lines = line_count < 50
        checks.append({
            "name": "FOCUS.md is under 50 lines",
            "passed": under_50_lines,
            "detail": f"FOCUS.md has {line_count} lines ({'OK' if under_50_lines else 'EXCEEDS 50-line limit'})"
        })
    else:
        checks.append({
            "name": "FOCUS.md is under 50 lines",
            "passed": False,
            "detail": "FOCUS.md is empty or unreadable"
        })

    # -------------------------------------------------------------------------
    # Scoring
    # -------------------------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 4) if total_checks > 0 else 0.0
    all_passed = passed_checks == total_checks

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "script_invocation", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))