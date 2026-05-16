import sys
import json
import re
from pathlib import Path

def load_state(workspace):
    state_path = Path(workspace) / "opengoat_state.json"
    with open(state_path, "r") as f:
        return json.load(f)

def run_checks(workspace):
    checks = []
    score_parts = []

    try:
        state = load_state(workspace)
    except Exception as e:
        checks.append({"name": "state_file_readable", "passed": False, "detail": f"Could not load state: {e}"})
        return checks, 0.0

    checks.append({"name": "state_file_readable", "passed": True, "detail": "State file loaded successfully"})

    tasks = state.get("tasks", {})

    # ── CHECK 1: TASK-001 must have been updated to "blocked" status ──────────
    task001 = tasks.get("TASK-001", {})
    task001_blocked = task001.get("status") == "blocked"
    checks.append({
        "name": "task001_status_blocked",
        "passed": task001_blocked,
        "detail": f"TASK-001 status is '{task001.get('status')}', expected 'blocked'"
    })
    score_parts.append(0.15 if task001_blocked else 0.0)

    # ── CHECK 2: TASK-001 must have at least one blocker added ───────────────
    task001_has_blocker = len(task001.get("blockers", [])) >= 1
    checks.append({
        "name": "task001_has_blocker",
        "passed": task001_has_blocker,
        "detail": f"TASK-001 blockers: {task001.get('blockers', [])}"
    })
    score_parts.append(0.10 if task001_has_blocker else 0.0)

    # ── CHECK 3: TASK-001 must have at least one worklog entry ───────────────
    task001_has_worklog = len(task001.get("worklogs", [])) >= 1
    checks.append({
        "name": "task001_has_worklog",
        "passed": task001_has_worklog,
        "detail": f"TASK-001 worklogs count: {len(task001.get('worklogs', []))}"
    })
    score_parts.append(0.10 if task001_has_worklog else 0.0)

    # ── CHECK 4: TASK-001 must have at least one artifact added ──────────────
    task001_has_artifact = len(task001.get("artifacts", [])) >= 1
    checks.append({
        "name": "task001_has_artifact",
        "passed": task001_has_artifact,
        "detail": f"TASK-001 artifacts count: {len(task001.get('artifacts', []))}"
    })
    score_parts.append(0.10 if task001_has_artifact else 0.0)

    # ── CHECK 5: At least 2 NEW tasks created (beyond TASK-001) ──────────────
    new_tasks = [t for tid, t in tasks.items() if tid != "TASK-001"]
    enough_new_tasks = len(new_tasks) >= 2
    checks.append({
        "name": "at_least_2_new_tasks_created",
        "passed": enough_new_tasks,
        "detail": f"New tasks created: {len(new_tasks)} (need >= 2)"
    })
    score_parts.append(0.10 if enough_new_tasks else 0.0)

    # ── CHECK 6: ALL new tasks assigned only to valid reportees or self ───────
    valid_agents = {
        "amazon-senior-manager",
        "logistics-ops-lead",
        "wms-engineering-lead",
        "warehouse-supervisor-1",
        "warehouse-supervisor-2",
        "wms-dev-1",
        "wms-dev-2",
    }
    invalid_assignments = [
        t for t in new_tasks
        if t.get("assignedTo") not in valid_agents
    ]
    all_valid_assignments = len(invalid_assignments) == 0
    checks.append({
        "name": "all_tasks_assigned_to_valid_reportees",
        "passed": all_valid_assignments,
        "detail": (
            "All assignments valid" if all_valid_assignments
            else f"Invalid assignees: {[t.get('assignedTo') for t in invalid_assignments]}"
        )
    })
    score_parts.append(0.15 if all_valid_assignments else 0.0)

    # ── CHECK 7: All new task titles follow "Verb: Deliverable" pattern ───────
    title_pattern = re.compile(r'^[A-Z][a-zA-Z]+:\s+.+')
    valid_titles = [t for t in new_tasks if title_pattern.match(t.get("title", ""))]
    titles_ok = len(valid_titles) == len(new_tasks) and len(new_tasks) > 0
    checks.append({
        "name": "task_titles_follow_verb_deliverable_pattern",
        "passed": titles_ok,
        "detail": (
            f"All {len(new_tasks)} titles valid" if titles_ok
            else f"Invalid titles: {[t.get('title') for t in new_tasks if not title_pattern.match(t.get('title', ''))]}"
        )
    })
    score_parts.append(0.10 if titles_ok else 0.0)

    # ── CHECK 8: All new task descriptions contain required sections ──────────
    required_sections = ["Context", "Deliverable", "Acceptance criteria"]
    def has_required_sections(desc):
        return all(sec.lower() in desc.lower() for sec in required_sections)

    tasks_with_good_desc = [t for t in new_tasks if has_required_sections(t.get("description", ""))]
    descs_ok = len(tasks_with_good_desc) == len(new_tasks) and len(new_tasks) > 0
    checks.append({
        "name": "task_descriptions_have_required_sections",
        "passed": descs_ok,
        "detail": (
            f"All {len(new_tasks)} descriptions have required sections" if descs_ok
            else f"{len(new_tasks) - len(tasks_with_good_desc)} task(s) missing sections. "
                 f"Bad tasks: {[t.get('taskId') for t in new_tasks if not has_required_sections(t.get('description', ''))]}"
        )
    })
    score_parts.append(0.10 if descs_ok else 0.0)

    # ── CHECK 9: New tasks have non-empty project paths ───────────────────────
    tasks_with_project = [t for t in new_tasks if t.get("project", "").strip()]
    projects_ok = len(tasks_with_project) == len(new_tasks) and len(new_tasks) > 0
    checks.append({
        "name": "all_new_tasks_have_project_path",
        "passed": projects_ok,
        "detail": (
            "All new tasks have project paths" if projects_ok
            else f"{len(new_tasks) - len(tasks_with_project)} task(s) missing project path"
        )
    })
    score_parts.append(0.05 if projects_ok else 0.0)

    # ── CHECK 10: actorId used consistently = "amazon-senior-manager" ────────
    correct_actor = [t for t in new_tasks if t.get("createdBy") == "amazon-senior-manager"]
    actor_ok = len(correct_actor) == len(new_tasks) and len(new_tasks) > 0
    checks.append({
        "name": "all_tasks_created_by_amazon_senior_manager",
        "passed": actor_ok,
        "detail": (
            "All tasks created by amazon-senior-manager" if actor_ok
            else f"Wrong actor IDs: {[t.get('createdBy') for t in new_tasks if t.get('createdBy') != 'amazon-senior-manager']}"
        )
    })
    score_parts.append(0.05 if actor_ok else 0.0)

    total_score = sum(score_parts)
    return checks, total_score

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks, score = run_checks(workspace)
    passed = score >= 0.70
    result = {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks,
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()