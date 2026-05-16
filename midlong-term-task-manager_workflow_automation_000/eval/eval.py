import sys
import json
import re
from pathlib import Path
from datetime import date, datetime

def load_json_safe(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except Exception as e:
        return None, str(e)

def run_checks(workspace_str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0

    tasks_json_path = workspace / ".tasks" / "tasks.json"

    # ── LOAD tasks.json ──
    tasks_data, err = load_json_safe(tasks_json_path)
    if err:
        checks.append({"name": "tasks.json exists and is valid JSON", "passed": False, "detail": f"Error: {err}"})
        return False, 0.0, checks
    checks.append({"name": "tasks.json exists and is valid JSON", "passed": True, "detail": "File found and parsed successfully"})
    total_score += 0.05

    tasks = tasks_data.get("tasks", [])
    task_ids = [t.get("id", "") for t in tasks]

    # ── CHECK 1: Original task TSK-20260310-001 still present ──
    original = next((t for t in tasks if t.get("id") == "TSK-20260310-001"), None)
    if original:
        checks.append({"name": "Original task TSK-20260310-001 preserved", "passed": True, "detail": "Found in tasks list"})
        total_score += 0.05
    else:
        checks.append({"name": "Original task TSK-20260310-001 preserved", "passed": False, "detail": "Original task missing from tasks.json"})

    # ── CHECK 2: Original task progress updated to reflect 3/4 subtasks done (75%) ──
    if original:
        prog = original.get("progress", 0)
        # 3 of 4 subtasks are done: expect 75 (or acceptable range 74-76)
        prog_ok = 74 <= prog <= 76
        checks.append({
            "name": "TSK-20260310-001 progress updated to ~75%",
            "passed": prog_ok,
            "detail": f"Found progress={prog}, expected 75 (3/4 subtasks done)"
        })
        if prog_ok:
            total_score += 0.10

        # ── CHECK 3: The 3rd subtask '集成视觉里程计' is now marked done ──
        decomposed = original.get("decomposed", [])
        third_subtask = next((s for s in decomposed if "视觉里程计" in s.get("subtask", "")), None)
        if third_subtask and third_subtask.get("status") == "done":
            checks.append({"name": "Subtask '集成视觉里程计' marked done", "passed": True, "detail": "Status is 'done'"})
            total_score += 0.08
        else:
            detail = f"Subtask found: {third_subtask}" if third_subtask else "Subtask '集成视觉里程计' not found"
            checks.append({"name": "Subtask '集成视觉里程计' marked done", "passed": False, "detail": detail})

        # ── CHECK 4: status remains in_progress (not completed — one subtask still pending) ──
        status_ok = original.get("status") == "in_progress"
        checks.append({
            "name": "TSK-20260310-001 status remains 'in_progress'",
            "passed": status_ok,
            "detail": f"Found status='{original.get('status')}'"
        })
        if status_ok:
            total_score += 0.05
    else:
        for name in ["TSK-20260310-001 progress updated to ~75%",
                     "Subtask '集成视觉里程计' marked done",
                     "TSK-20260310-001 status remains 'in_progress'"]:
            checks.append({"name": name, "passed": False, "detail": "Original task missing"})

    # ── CHECK 5 & 6: Two new tasks added ──
    new_tasks = [t for t in tasks if t.get("id", "") != "TSK-20260310-001"]

    # Must have exactly 2 new tasks
    has_two_new = len(new_tasks) == 2
    checks.append({
        "name": "Exactly 2 new tasks added",
        "passed": has_two_new,
        "detail": f"Found {len(new_tasks)} new tasks (expected 2)"
    })
    if has_two_new:
        total_score += 0.08

    # ── CHECK 7: New task IDs follow format TSK-YYYYMMDD-NNN ──
    id_pattern = re.compile(r'^TSK-\d{8}-\d{3}$')
    valid_ids = [t for t in new_tasks if id_pattern.match(t.get("id", ""))]
    all_ids_valid = len(valid_ids) == len(new_tasks)
    checks.append({
        "name": "New task IDs follow TSK-YYYYMMDD-NNN format",
        "passed": all_ids_valid,
        "detail": f"Valid IDs: {[t.get('id') for t in valid_ids]}, All new IDs: {[t.get('id') for t in new_tasks]}"
    })
    if all_ids_valid and len(valid_ids) > 0:
        total_score += 0.10

    # ── CHECK 8: New tasks have required fields ──
    required_fields = ["id", "name", "description", "type", "priority", "status",
                        "created_at", "due_date", "decomposed", "progress",
                        "last_updated", "blocked_by", "depends_on", "tags"]
    tasks_with_all_fields = 0
    for t in new_tasks:
        missing = [f for f in required_fields if f not in t]
        if not missing:
            tasks_with_all_fields += 1
        else:
            checks.append({
                "name": f"Task {t.get('id','?')} has all required fields",
                "passed": False,
                "detail": f"Missing fields: {missing}"
            })
    if tasks_with_all_fields == len(new_tasks) and len(new_tasks) > 0:
        checks.append({
            "name": "All new tasks have required fields per schema",
            "passed": True,
            "detail": f"Both new tasks have all {len(required_fields)} required fields"
        })
        total_score += 0.10
    elif tasks_with_all_fields > 0:
        checks.append({
            "name": "All new tasks have required fields per schema",
            "passed": False,
            "detail": f"Only {tasks_with_all_fields}/{len(new_tasks)} tasks have all required fields"
        })

    # ── CHECK 9: New tasks have valid priority values ──
    valid_priorities = {"low", "medium", "high"}
    priority_ok = all(t.get("priority") in valid_priorities for t in new_tasks) if new_tasks else False
    checks.append({
        "name": "New tasks have valid priority (low|medium|high)",
        "passed": priority_ok,
        "detail": f"Priorities found: {[t.get('priority') for t in new_tasks]}"
    })
    if priority_ok:
        total_score += 0.05

    # ── CHECK 10: New tasks have decomposed subtasks ──
    tasks_with_subtasks = [t for t in new_tasks if isinstance(t.get("decomposed"), list) and len(t.get("decomposed", [])) > 0]
    decomp_ok = len(tasks_with_subtasks) == len(new_tasks) and len(new_tasks) > 0
    checks.append({
        "name": "New tasks have decomposed subtasks",
        "passed": decomp_ok,
        "detail": f"{len(tasks_with_subtasks)}/{len(new_tasks)} tasks have subtasks"
    })
    if decomp_ok:
        total_score += 0.07

    # ── CHECK 11: New tasks have valid status ──
    valid_statuses = {"pending", "in_progress", "blocked", "completed", "paused", "cancelled"}
    status_valid = all(t.get("status") in valid_statuses for t in new_tasks) if new_tasks else False
    checks.append({
        "name": "New tasks have valid status values",
        "passed": status_valid,
        "detail": f"Statuses: {[t.get('status') for t in new_tasks]}"
    })
    if status_valid:
        total_score += 0.05

    # ── CHECK 12: Daily log written to .tasks/logs/YYYY-MM-DD.md (NOT memory/) ──
    logs_dir = workspace / ".tasks" / "logs"
    log_files = list(logs_dir.glob("*.md")) if logs_dir.exists() else []
    # Must have at least one .md file matching date format
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}\.md$')
    valid_log_files = [f for f in log_files if date_pattern.match(f.name)]
    log_exists = len(valid_log_files) > 0
    checks.append({
        "name": "Daily log exists in .tasks/logs/YYYY-MM-DD.md",
        "passed": log_exists,
        "detail": f"Found log files: {[f.name for f in valid_log_files]}"
    })
    if log_exists:
        total_score += 0.10

    # ── CHECK 13: Log content references task IDs or progress ──
    if log_exists:
        log_content = ""
        for lf in valid_log_files:
            try:
                log_content += lf.read_text(encoding="utf-8")
            except Exception:
                pass
        # Should mention at least one task ID
        mentions_task = bool(re.search(r'TSK-\d{8}-\d{3}', log_content))
        checks.append({
            "name": "Daily log content references task IDs",
            "passed": mentions_task,
            "detail": f"Log content snippet: {log_content[:300]!r}"
        })
        if mentions_task:
            total_score += 0.07
    else:
        checks.append({"name": "Daily log content references task IDs", "passed": False, "detail": "No log file found"})

    # ── CHECK 14: No task data written to memory/ directory ──
    memory_dir = workspace / "memory"
    memory_files = list(memory_dir.glob("*.md")) if memory_dir.exists() else []
    # The original 2 distractor files were pre-existing; check that no NEW task-related content was written
    # We check if any memory/ .md file now contains TSK- IDs (agent wrongly wrote task data there)
    memory_corrupted = False
    for mf in memory_files:
        try:
            content = mf.read_text(encoding="utf-8")
            if re.search(r'TSK-\d{8}-\d{3}', content):
                memory_corrupted = True
                break
        except Exception:
            pass
    checks.append({
        "name": "Task data NOT written to memory/ directory (correct separation)",
        "passed": not memory_corrupted,
        "detail": "memory/ dir should not contain task IDs written by the agent" if not memory_corrupted else "memory/ dir contains task IDs — agent violated layer separation"
    })
    if not memory_corrupted:
        total_score += 0.05

    # ── Compute final pass ──
    # Must pass critical checks: tasks.json valid, 2 new tasks, correct ID format, daily log exists
    critical = [
        "tasks.json exists and is valid JSON",
        "Exactly 2 new tasks added",
        "New task IDs follow TSK-YYYYMMDD-NNN format",
        "Daily log exists in .tasks/logs/YYYY-MM-DD.md",
        "TSK-20260310-001 progress updated to ~75%",
    ]
    critical_passed = all(
        any(c["name"] == crit and c["passed"] for c in checks)
        for crit in critical
    )

    total_score = min(round(total_score, 3), 1.0)
    passed = critical_passed and total_score >= 0.55

    return passed, total_score, checks


def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    passed, score, checks = run_checks(workspace)
    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()