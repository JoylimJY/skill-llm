import sys
import json
import os
from pathlib import Path
from datetime import datetime, timezone

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def run_checks(workspace_str):
    workspace = Path(workspace_str)
    home = Path.home()
    queue_path = home / ".openclaw" / "tasks" / "task-queue.json"
    heartbeat_path = workspace / "HEARTBEAT.md"

    checks = []
    all_passed = True

    def check(name, passed, detail):
        nonlocal all_passed
        if not passed:
            all_passed = False
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── Load queue file ──────────────────────────────────────────────────────
    queue = None
    try:
        queue = load_json(queue_path)
    except FileNotFoundError:
        check("queue_file_exists", False, f"Queue file not found at {queue_path}")
        return checks, all_passed
    except json.JSONDecodeError as e:
        check("queue_file_valid_json", False, f"Queue file is invalid JSON: {e}")
        return checks, all_passed

    check("queue_file_exists", True, f"Queue file found at {queue_path}")
    check("queue_file_valid_json", True, "Queue file is valid JSON")

    # ── Top-level schema fields ──────────────────────────────────────────────
    check(
        "schema_version_field",
        queue.get("version") == "1.0",
        f"Expected version='1.0', got: {queue.get('version')!r}"
    )
    check(
        "schema_maxConcurrent",
        queue.get("maxConcurrent") == 2,
        f"Expected maxConcurrent=2, got: {queue.get('maxConcurrent')!r}"
    )
    check(
        "schema_maxRetries",
        queue.get("maxRetries") == 3,
        f"Expected maxRetries=3, got: {queue.get('maxRetries')!r}"
    )
    check(
        "schema_archiveDays",
        queue.get("archiveDays") == 7,
        f"Expected archiveDays=7, got: {queue.get('archiveDays')!r}"
    )
    check(
        "schema_taskRunnerDir",
        "taskRunnerDir" in queue,
        f"Missing 'taskRunnerDir' field in queue root. Got keys: {list(queue.keys())}"
    )

    # ── Task array ───────────────────────────────────────────────────────────
    tasks = queue.get("tasks", [])
    check(
        "tasks_array_exists",
        isinstance(tasks, list),
        f"Expected 'tasks' to be a list, got: {type(tasks)}"
    )

    # ── T-02 must be skipped ─────────────────────────────────────────────────
    t02 = next((t for t in tasks if t.get("id") == "T-02"), None)
    if t02 is None:
        check("t02_present", False, "T-02 not found in tasks array")
    else:
        check("t02_present", True, "T-02 found in tasks array")
        check(
            "t02_skipped",
            t02.get("status") == "skipped",
            f"Expected T-02 status='skipped', got: {t02.get('status')!r}"
        )

    # ── T-01 must remain done ─────────────────────────────────────────────────
    t01 = next((t for t in tasks if t.get("id") == "T-01"), None)
    if t01 is None:
        check("t01_preserved", False, "T-01 not found — pre-existing tasks must be preserved")
    else:
        check("t01_preserved", True, "T-01 still present in queue")
        check(
            "t01_status_unchanged",
            t01.get("status") == "done",
            f"T-01 should still be 'done', got: {t01.get('status')!r}"
        )

    # ── New tasks: must have at least 4 new tasks (T-03 through T-06) ────────
    new_task_ids = [t.get("id") for t in tasks if t.get("id") not in ("T-01", "T-02")]
    check(
        "new_tasks_added",
        len(new_task_ids) >= 4,
        f"Expected at least 4 new tasks, found {len(new_task_ids)}: {new_task_ids}"
    )

    # ── lastId must be updated to account for all new tasks ──────────────────
    last_id = queue.get("lastId", "")
    try:
        last_num = int(last_id.split("-")[1]) if last_id and "-" in last_id else 0
        check(
            "lastId_updated",
            last_num >= 6,
            f"lastId should be at least T-06 (4 new tasks from T-03 onward), got: {last_id!r}"
        )
    except Exception as e:
        check("lastId_updated", False, f"Could not parse lastId={last_id!r}: {e}")

    # ── New tasks: ID format T-NN ─────────────────────────────────────────────
    id_format_ok = all(
        (isinstance(tid, str) and tid.startswith("T-") and tid[2:].isdigit())
        for tid in new_task_ids
    )
    check(
        "new_task_id_format",
        id_format_ok,
        f"All new task IDs must follow 'T-NN' format. Got: {new_task_ids}"
    )

    # ── New task ID sequential continuity from T-03 ───────────────────────────
    if new_task_ids:
        try:
            nums = sorted(int(tid.split("-")[1]) for tid in new_task_ids)
            expected = list(range(3, 3 + len(nums)))
            check(
                "new_task_ids_sequential",
                nums == expected,
                f"New task IDs must be sequential from T-03. Expected nums {expected}, got {nums}"
            )
        except Exception as e:
            check("new_task_ids_sequential", False, f"Error checking ID sequence: {e}")

    # ── Required fields on each new task ─────────────────────────────────────
    required_task_fields = [
        "id", "description", "goal", "type", "status",
        "retries", "maxRetries", "subagent_session", "strategies_tried",
        "deliverable", "deliverable_path", "blocked_reason", "user_action_required",
        "added_at", "started_at", "completed_at"
    ]
    new_tasks = [t for t in tasks if t.get("id") not in ("T-01", "T-02")]
    missing_fields_report = []
    for task in new_tasks:
        missing = [f for f in required_task_fields if f not in task]
        if missing:
            missing_fields_report.append(f"{task.get('id')}: missing {missing}")
    check(
        "new_tasks_have_required_fields",
        len(missing_fields_report) == 0,
        f"Missing fields: {missing_fields_report}" if missing_fields_report else "All required fields present"
    )

    # ── New tasks: retries=0, strategies_tried=[], status=pending or running ──
    retries_ok = all(t.get("retries") == 0 for t in new_tasks)
    check(
        "new_tasks_retries_zero",
        retries_ok,
        f"All new tasks should start with retries=0. Got: {[(t.get('id'), t.get('retries')) for t in new_tasks]}"
    )

    strategies_ok = all(t.get("strategies_tried") == [] for t in new_tasks)
    check(
        "new_tasks_strategies_tried_empty",
        strategies_ok,
        f"All new tasks should start with strategies_tried=[]. Got: {[(t.get('id'), t.get('strategies_tried')) for t in new_tasks]}"
    )

    # ── New tasks: status must be pending or running (DISPATCHER may have run) ─
    valid_statuses = {"pending", "running", "done", "blocked"}
    status_ok = all(t.get("status") in valid_statuses for t in new_tasks)
    check(
        "new_tasks_valid_status",
        status_ok,
        f"New tasks must have valid status. Got: {[(t.get('id'), t.get('status')) for t in new_tasks]}"
    )

    # ── DISPATCHER: maxConcurrent=2 must be respected ────────────────────────
    running_tasks = [t for t in tasks if t.get("status") == "running"]
    check(
        "dispatcher_maxconcurrent_respected",
        len(running_tasks) <= 2,
        f"At most 2 tasks can be running simultaneously (maxConcurrent=2). Found {len(running_tasks)} running: {[t.get('id') for t in running_tasks]}"
    )

    # ── Task type classification ──────────────────────────────────────────────
    # The prompt asks to add 4 tasks: post to #platform-alerts (messaging),
    # create a runbook file (file-creation), run a disk-usage script (code-execution),
    # and look up the latest K8s version (info-lookup)
    type_map = {}
    for task in new_tasks:
        type_map[task.get("id")] = task.get("type")

    valid_types = {"messaging", "file-creation", "code-execution", "info-lookup",
                   "agent-delegation", "reminder-scheduling", "unknown"}
    types_valid = all(v in valid_types for v in type_map.values())
    check(
        "new_tasks_have_valid_types",
        types_valid,
        f"All new tasks must have a valid type. Got: {type_map}"
    )

    # At least one task should be classified as messaging (the Slack/channel post task)
    has_messaging = any(t.get("type") == "messaging" for t in new_tasks)
    check(
        "messaging_type_assigned",
        has_messaging,
        f"At least one new task should be type='messaging' (post to #platform-alerts). Types found: {list(type_map.values())}"
    )

    # At least one task should be file-creation
    has_file_creation = any(t.get("type") == "file-creation" for t in new_tasks)
    check(
        "file_creation_type_assigned",
        has_file_creation,
        f"At least one new task should be type='file-creation' (runbook doc). Types found: {list(type_map.values())}"
    )

    # At least one task should be code-execution
    has_code_exec = any(t.get("type") == "code-execution" for t in new_tasks)
    check(
        "code_execution_type_assigned",
        has_code_exec,
        f"At least one new task should be type='code-execution' (disk-usage script). Types found: {list(type_map.values())}"
    )

    # At least one task should be info-lookup
    has_info_lookup = any(t.get("type") == "info-lookup" for t in new_tasks)
    check(
        "info_lookup_type_assigned",
        has_info_lookup,
        f"At least one new task should be type='info-lookup' (K8s version lookup). Types found: {list(type_map.values())}"
    )

    # ── HEARTBEAT.md must contain Task Runner Dispatcher entry ───────────────
    try:
        heartbeat_content = heartbeat_path.read_text()
        has_task_runner_entry = "Task Runner Dispatcher" in heartbeat_content
        check(
            "heartbeat_has_task_runner_entry",
            has_task_runner_entry,
            "HEARTBEAT.md must contain '## Task Runner Dispatcher' block" if not has_task_runner_entry
            else "HEARTBEAT.md contains Task Runner Dispatcher entry"
        )

        # Must reference the queue file
        has_queue_ref = "task-queue.json" in heartbeat_content
        check(
            "heartbeat_references_queue_file",
            has_queue_ref,
            "HEARTBEAT.md Task Runner entry must reference task-queue.json"
            if not has_queue_ref else "HEARTBEAT.md references task-queue.json"
        )

        # Must mention DISPATCHER mode
        has_dispatcher_ref = "DISPATCHER" in heartbeat_content or "dispatcher" in heartbeat_content.lower()
        check(
            "heartbeat_references_dispatcher",
            has_dispatcher_ref,
            "HEARTBEAT.md must reference DISPATCHER mode"
            if not has_dispatcher_ref else "HEARTBEAT.md references dispatcher"
        )

    except FileNotFoundError:
        check("heartbeat_has_task_runner_entry", False, f"HEARTBEAT.md not found at {heartbeat_path}")

    # ── added_at fields are valid ISO 8601 ────────────────────────────────────
    added_at_ok = True
    bad_dates = []
    for task in new_tasks:
        added_at = task.get("added_at")
        if not added_at:
            added_at_ok = False
            bad_dates.append(f"{task.get('id')}: missing added_at")
            continue
        try:
            datetime.fromisoformat(added_at.replace("Z", "+00:00"))
        except Exception:
            added_at_ok = False
            bad_dates.append(f"{task.get('id')}: invalid added_at={added_at!r}")
    check(
        "new_tasks_added_at_valid",
        added_at_ok,
        f"Invalid added_at dates: {bad_dates}" if bad_dates else "All added_at dates are valid ISO 8601"
    )

    # ── maxRetries on new tasks must be 3 ────────────────────────────────────
    max_retries_ok = all(t.get("maxRetries") == 3 for t in new_tasks)
    check(
        "new_tasks_maxRetries_correct",
        max_retries_ok,
        f"All new tasks must have maxRetries=3. Got: {[(t.get('id'), t.get('maxRetries')) for t in new_tasks]}"
    )

    return checks, all_passed


def main():
    if len(sys.argv) < 2:
        workspace = "/workspace"
    else:
        workspace = sys.argv[1]

    checks, all_passed = run_checks(workspace)

    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = passed_count / total if total > 0 else 0.0

    result = {
        "passed": all_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()