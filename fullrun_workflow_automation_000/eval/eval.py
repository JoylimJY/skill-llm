import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    
    # -------------------------------------------------------------------------
    # CHECK 1: install.sh was run — .claude/fullrun/scripts/ directory exists
    # -------------------------------------------------------------------------
    fullrun_scripts_dir = Path(workspace) / ".claude" / "fullrun" / "scripts"
    c1_passed = fullrun_scripts_dir.is_dir()
    checks.append({
        "name": "install_run_scripts_dir_exists",
        "passed": c1_passed,
        "detail": f".claude/fullrun/scripts/ {'exists' if c1_passed else 'MISSING — install.sh was not run'}"
    })

    # -------------------------------------------------------------------------
    # CHECK 2: Scripts were correctly installed (main.sh, fullrun.sh, cron-manager.sh)
    # -------------------------------------------------------------------------
    required_scripts = ["main.sh", "fullrun.sh", "cron-manager.sh"]
    missing_scripts = [s for s in required_scripts if not (fullrun_scripts_dir / s).exists()]
    c2_passed = len(missing_scripts) == 0
    checks.append({
        "name": "installed_scripts_present",
        "passed": c2_passed,
        "detail": f"All required scripts present" if c2_passed else f"Missing: {missing_scripts}"
    })

    # -------------------------------------------------------------------------
    # CHECK 3: settings.local.json was created with the permission rule
    # -------------------------------------------------------------------------
    settings_path = Path(workspace) / ".claude" / "settings.local.json"
    c3_passed = False
    c3_detail = "settings.local.json not found"
    try:
        if settings_path.exists():
            with open(settings_path) as f:
                settings = json.load(f)
            allow_rules = settings.get("permissions", {}).get("allow", [])
            if "Bash(.claude/fullrun/scripts/*)" in allow_rules:
                c3_passed = True
                c3_detail = "Permission rule 'Bash(.claude/fullrun/scripts/*)' present"
            else:
                c3_detail = f"Permission rule missing. Found rules: {allow_rules}"
    except Exception as e:
        c3_detail = f"Error reading settings.local.json: {e}"
    checks.append({
        "name": "settings_permission_rule",
        "passed": c3_passed,
        "detail": c3_detail
    })

    # -------------------------------------------------------------------------
    # CHECK 4: checklist.md exists with at least 3 tasks defined
    # -------------------------------------------------------------------------
    checklist_path = Path(workspace) / "checklist.md"
    c4_passed = False
    c4_detail = "checklist.md not found"
    checklist_tasks_total = 0
    try:
        if checklist_path.exists():
            content = checklist_path.read_text()
            # Count all tasks (both complete and incomplete)
            all_tasks = re.findall(r'^\- \[[ x]\]', content, re.MULTILINE)
            checklist_tasks_total = len(all_tasks)
            if checklist_tasks_total >= 3:
                c4_passed = True
                c4_detail = f"checklist.md found with {checklist_tasks_total} tasks"
            else:
                c4_detail = f"checklist.md found but only {checklist_tasks_total} task(s) — need at least 3"
    except Exception as e:
        c4_detail = f"Error reading checklist.md: {e}"
    checks.append({
        "name": "checklist_created_with_tasks",
        "passed": c4_passed,
        "detail": c4_detail
    })

    # -------------------------------------------------------------------------
    # CHECK 5: All tasks in checklist.md are marked complete [x] (none remain [ ])
    # -------------------------------------------------------------------------
    c5_passed = False
    c5_detail = "checklist.md not found or unreadable"
    try:
        if checklist_path.exists():
            content = checklist_path.read_text()
            incomplete = re.findall(r'^\- \[ \]', content, re.MULTILINE)
            completed = re.findall(r'^\- \[x\]', content, re.MULTILINE)
            if len(incomplete) == 0 and len(completed) >= 3:
                c5_passed = True
                c5_detail = f"All {len(completed)} tasks marked [x] (complete). No incomplete [ ] tasks."
            else:
                c5_detail = f"Incomplete tasks remaining: {len(incomplete)}. Completed: {len(completed)}."
    except Exception as e:
        c5_detail = f"Error reading checklist.md: {e}"
    checks.append({
        "name": "all_tasks_marked_complete",
        "passed": c5_passed,
        "detail": c5_detail
    })

    # -------------------------------------------------------------------------
    # CHECK 6: .claude-status.txt exists and contains exactly "2"
    # -------------------------------------------------------------------------
    status_path = Path(workspace) / ".claude-status.txt"
    c6_passed = False
    c6_detail = ".claude-status.txt not found"
    try:
        if status_path.exists():
            status_val = status_path.read_text().strip()
            if status_val == "2":
                c6_passed = True
                c6_detail = ".claude-status.txt contains '2' (all tasks completed state)"
            else:
                c6_detail = f".claude-status.txt contains '{status_val}' — expected '2'"
    except Exception as e:
        c6_detail = f"Error reading .claude-status.txt: {e}"
    checks.append({
        "name": "status_file_is_2_completed",
        "passed": c6_passed,
        "detail": c6_detail
    })

    # -------------------------------------------------------------------------
    # CHECK 7: .fullrun.log exists and contains execution evidence
    # -------------------------------------------------------------------------
    log_path = Path(workspace) / ".fullrun.log"
    c7_passed = False
    c7_detail = ".fullrun.log not found"
    try:
        if log_path.exists():
            log_content = log_path.read_text()
            # Must contain evidence of task execution and completion
            has_status_2 = "Status set to: 2" in log_content or "status=2" in log_content.lower() or "status set to: 2" in log_content.lower()
            has_execution = "task" in log_content.lower() or "executing" in log_content.lower() or "completed" in log_content.lower()
            if has_status_2 and has_execution:
                c7_passed = True
                c7_detail = ".fullrun.log contains execution and completion evidence"
            elif has_execution:
                c7_detail = ".fullrun.log has execution evidence but missing status=2 completion marker"
            else:
                c7_detail = f".fullrun.log exists but lacks execution evidence. Content preview: {log_content[:200]}"
    except Exception as e:
        c7_detail = f"Error reading .fullrun.log: {e}"
    checks.append({
        "name": "fullrun_log_has_execution_evidence",
        "passed": c7_passed,
        "detail": c7_detail
    })

    # -------------------------------------------------------------------------
    # CHECK 8: Task completion markers use the EXACT correct format [x] not [X] or [✓]
    # -------------------------------------------------------------------------
    c8_passed = False
    c8_detail = "checklist.md not found"
    try:
        if checklist_path.exists():
            content = checklist_path.read_text()
            # Check for incorrect markers (uppercase X, check marks, etc.)
            wrong_uppercase = re.findall(r'^\- \[X\]', content, re.MULTILINE)
            wrong_check = re.findall(r'^\- \[✓\]', content, re.MULTILINE)
            correct_markers = re.findall(r'^\- \[x\]', content, re.MULTILINE)
            if len(wrong_uppercase) == 0 and len(wrong_check) == 0 and len(correct_markers) >= 3:
                c8_passed = True
                c8_detail = f"All {len(correct_markers)} tasks use correct lowercase [x] format"
            else:
                issues = []
                if wrong_uppercase:
                    issues.append(f"{len(wrong_uppercase)} tasks use [X] (uppercase)")
                if wrong_check:
                    issues.append(f"{len(wrong_check)} tasks use [✓]")
                if len(correct_markers) < 3:
                    issues.append(f"Only {len(correct_markers)} correct [x] markers (need 3+)")
                c8_detail = "Format issues: " + "; ".join(issues)
    except Exception as e:
        c8_detail = f"Error reading checklist.md: {e}"
    checks.append({
        "name": "task_markers_correct_format",
        "passed": c8_passed,
        "detail": c8_detail
    })

    # -------------------------------------------------------------------------
    # SCORE CALCULATION
    # -------------------------------------------------------------------------
    # Weights: critical checks have higher weight
    weights = {
        "install_run_scripts_dir_exists": 0.15,
        "installed_scripts_present": 0.10,
        "settings_permission_rule": 0.10,
        "checklist_created_with_tasks": 0.15,
        "all_tasks_marked_complete": 0.20,
        "status_file_is_2_completed": 0.20,
        "fullrun_log_has_execution_evidence": 0.05,
        "task_markers_correct_format": 0.05,
    }

    weighted_score = sum(
        weights.get(c["name"], 0) * (1.0 if c["passed"] else 0.0)
        for c in checks
    )

    # Must pass all critical checks (1,4,5,6) to overall pass
    critical = ["install_run_scripts_dir_exists", "checklist_created_with_tasks",
                "all_tasks_marked_complete", "status_file_is_2_completed"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)
    
    overall_passed = critical_passed and weighted_score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(weighted_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace_path = sys.argv[1]
    result = evaluate(workspace_path)
    print(json.dumps(result, indent=2))