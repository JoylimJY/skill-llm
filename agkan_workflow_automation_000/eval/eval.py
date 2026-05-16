import subprocess
import json
import sys
from pathlib import Path

def run_agkan(cmd, cwd):
    """Run an agkan command and return stdout."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, cwd=cwd
    )
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # -------------------------------------------------------------------------
    # 1. Get all tasks in JSON format
    # -------------------------------------------------------------------------
    stdout, stderr, rc = run_agkan("agkan task list --all --json", workspace)
    try:
        all_tasks_data = json.loads(stdout)
        all_tasks = all_tasks_data.get("tasks", [])
    except Exception as e:
        all_tasks_data = {}
        all_tasks = []

    # -------------------------------------------------------------------------
    # Helper: find task by title keyword
    # -------------------------------------------------------------------------
    def find_task(keyword):
        keyword_lower = keyword.lower()
        for t in all_tasks:
            if keyword_lower in (t.get("title") or "").lower():
                return t
        return None

    # -------------------------------------------------------------------------
    # 2. Check parent/epic task
    # -------------------------------------------------------------------------
    parent_task = find_task("payment service hardening")
    if parent_task is None:
        # Try broader search
        for t in all_tasks:
            if t.get("parent_id") is None and "payment" in (t.get("title") or "").lower() and "hardening" in (t.get("title") or "").lower():
                parent_task = t
                break

    parent_exists = parent_task is not None
    score = add_check(
        "Parent epic task exists",
        parent_exists,
        f"Found parent task: {parent_task.get('title') if parent_task else 'NOT FOUND'}",
        weight=1.0
    )
    total_score += score

    if parent_task:
        parent_status_ok = parent_task.get("status") == "backlog"
        score = add_check(
            "Parent task has correct status (backlog)",
            parent_status_ok,
            f"Parent status: {parent_task.get('status')}",
            weight=1.0
        )
        total_score += score

        parent_author_ok = (parent_task.get("author") or "").lower() == "sprint-planner"
        score = add_check(
            "Parent task has correct author (sprint-planner)",
            parent_author_ok,
            f"Parent author: {parent_task.get('author')}",
            weight=1.0
        )
        total_score += score
    else:
        checks.append({"name": "Parent task has correct status (backlog)", "passed": False, "detail": "Parent task not found"})
        checks.append({"name": "Parent task has correct author (sprint-planner)", "passed": False, "detail": "Parent task not found"})

    # -------------------------------------------------------------------------
    # 3. Check subtasks exist and have correct statuses
    # -------------------------------------------------------------------------
    subtask_keywords = {
        "idempotency": {"expected_status": "in_progress", "label": "Fix duplicate charge bug (idempotency)"},
        "jwt": {"expected_status": "ready", "label": "Remove hardcoded JWT secret"},
        "rate limit": {"expected_status": "backlog", "label": "Add rate limiting"},
        "unit test": {"expected_status": "backlog", "label": "Write unit tests for PaymentHandler"},
    }

    found_subtasks = {}
    for keyword, info in subtask_keywords.items():
        task = find_task(keyword)
        if task is None:
            # Try alternative spellings
            for alt in [keyword.replace(" ", ""), keyword.split()[0]]:
                task = find_task(alt)
                if task:
                    break
        found_subtasks[keyword] = task

    # Check subtask 1: idempotency / duplicate charge bug
    st1 = found_subtasks.get("idempotency")
    st1_exists = st1 is not None
    score = add_check(
        "Subtask 1 (duplicate charge/idempotency) exists",
        st1_exists,
        f"Found: {st1.get('title') if st1 else 'NOT FOUND'}",
        weight=1.0
    )
    total_score += score

    if st1:
        st1_status_ok = st1.get("status") == "in_progress"
        score = add_check(
            "Subtask 1 status is in_progress",
            st1_status_ok,
            f"Status: {st1.get('status')}",
            weight=1.0
        )
        total_score += score

        # Check subtask 1 is a child of parent
        if parent_task:
            st1_parent_ok = st1.get("parent_id") == parent_task.get("id")
            score = add_check(
                "Subtask 1 is child of parent task",
                st1_parent_ok,
                f"Subtask1 parent_id={st1.get('parent_id')}, parent task id={parent_task.get('id')}",
                weight=1.0
            )
            total_score += score
    else:
        checks.append({"name": "Subtask 1 status is in_progress", "passed": False, "detail": "Subtask 1 not found"})
        checks.append({"name": "Subtask 1 is child of parent task", "passed": False, "detail": "Subtask 1 not found"})

    # Check subtask 2: JWT secret
    st2 = found_subtasks.get("jwt")
    st2_exists = st2 is not None
    score = add_check(
        "Subtask 2 (JWT/hardcoded secret) exists",
        st2_exists,
        f"Found: {st2.get('title') if st2 else 'NOT FOUND'}",
        weight=1.0
    )
    total_score += score

    if st2:
        st2_status_ok = st2.get("status") == "ready"
        score = add_check(
            "Subtask 2 status is ready",
            st2_status_ok,
            f"Status: {st2.get('status')}",
            weight=1.0
        )
        total_score += score

    # Check subtask 3: rate limiting
    st3 = found_subtasks.get("rate limit")
    st3_exists = st3 is not None
    score = add_check(
        "Subtask 3 (rate limiting) exists",
        st3_exists,
        f"Found: {st3.get('title') if st3 else 'NOT FOUND'}",
        weight=1.0
    )
    total_score += score

    if st3:
        st3_status_ok = st3.get("status") == "backlog"
        score = add_check(
            "Subtask 3 status is backlog",
            st3_status_ok,
            f"Status: {st3.get('status')}",
            weight=1.0
        )
        total_score += score

    # Check subtask 4: unit tests
    st4 = found_subtasks.get("unit test")
    st4_exists = st4 is not None
    score = add_check(
        "Subtask 4 (unit tests) exists",
        st4_exists,
        f"Found: {st4.get('title') if st4 else 'NOT FOUND'}",
        weight=1.0
    )
    total_score += score

    if st4:
        st4_status_ok = st4.get("status") == "backlog"
        score = add_check(
            "Subtask 4 status is backlog",
            st4_status_ok,
            f"Status: {st4.get('status')}",
            weight=1.0
        )
        total_score += score

    # -------------------------------------------------------------------------
    # 4. Check blocking relationships (THE PROPRIETARY TRAP - direction matters)
    # -------------------------------------------------------------------------
    # Subtask 1 blocks Subtask 4 (idempotency fix must happen before unit tests)
    if st1 and st4:
        stdout_block, _, _ = run_agkan(f"agkan task block list {st1.get('id')} --json", workspace)
        try:
            block_data = json.loads(stdout_block)
            blocking_ids = [t.get("id") for t in block_data.get("blocking", [])]
            st1_blocks_st4 = st4.get("id") in blocking_ids
        except Exception as e:
            st1_blocks_st4 = False
        score = add_check(
            "Subtask 1 blocks Subtask 4 (idempotency → unit tests)",
            st1_blocks_st4,
            f"Subtask1 (id={st1.get('id')}) blocking ids: {blocking_ids if 'blocking_ids' in dir() else 'error'}, Subtask4 id={st4.get('id')}",
            weight=1.5
        )
        total_score += score
    else:
        checks.append({
            "name": "Subtask 1 blocks Subtask 4 (idempotency → unit tests)",
            "passed": False,
            "detail": "One or both subtasks not found"
        })

    # Subtask 2 blocks Subtask 3 (JWT fix must happen before rate limiting)
    if st2 and st3:
        stdout_block, _, _ = run_agkan(f"agkan task block list {st2.get('id')} --json", workspace)
        try:
            block_data = json.loads(stdout_block)
            blocking_ids_2 = [t.get("id") for t in block_data.get("blocking", [])]
            st2_blocks_st3 = st3.get("id") in blocking_ids_2
        except Exception as e:
            st2_blocks_st3 = False
        score = add_check(
            "Subtask 2 blocks Subtask 3 (JWT → rate limiting)",
            st2_blocks_st3,
            f"Subtask2 (id={st2.get('id')}) blocking ids: {blocking_ids_2 if 'blocking_ids_2' in dir() else 'error'}, Subtask3 id={st3.get('id')}",
            weight=1.5
        )
        total_score += score
    else:
        checks.append({
            "name": "Subtask 2 blocks Subtask 3 (JWT → rate limiting)",
            "passed": False,
            "detail": "One or both subtasks not found"
        })

    # -------------------------------------------------------------------------
    # 5. Check tags (THE MAIN PROPRIETARY TRAP - canonical tag priority order)
    # -------------------------------------------------------------------------
    # Subtask 1 should have "bug" tag (priority 1 - highest)
    if st1:
        stdout_tags, _, _ = run_agkan(f"agkan tag show {st1.get('id')}", workspace)
        st1_has_bug_tag = "bug" in stdout_tags.lower()
        score = add_check(
            "Subtask 1 has 'bug' tag (canonical priority 1)",
            st1_has_bug_tag,
            f"Tags output: {stdout_tags[:200]}",
            weight=1.5
        )
        total_score += score

    # Subtask 2 should have "security" tag (priority 2)
    if st2:
        stdout_tags2, _, _ = run_agkan(f"agkan tag show {st2.get('id')}", workspace)
        st2_has_security_tag = "security" in stdout_tags2.lower()
        score = add_check(
            "Subtask 2 has 'security' tag (canonical priority 2)",
            st2_has_security_tag,
            f"Tags output: {stdout_tags2[:200]}",
            weight=1.5
        )
        total_score += score

    # Subtask 3 should have "improvement" tag (priority 3)
    if st3:
        stdout_tags3, _, _ = run_agkan(f"agkan tag show {st3.get('id')}", workspace)
        st3_has_improvement_tag = "improvement" in stdout_tags3.lower()
        score = add_check(
            "Subtask 3 has 'improvement' tag (canonical priority 3)",
            st3_has_improvement_tag,
            f"Tags output: {stdout_tags3[:200]}",
            weight=1.5
        )
        total_score += score

    # Subtask 4 should have "test" tag (priority 4)
    if st4:
        stdout_tags4, _, _ = run_agkan(f"agkan tag show {st4.get('id')}", workspace)
        st4_has_test_tag = "test" in stdout_tags4.lower()
        score = add_check(
            "Subtask 4 has 'test' tag (canonical priority 4)",
            st4_has_test_tag,
            f"Tags output: {stdout_tags4[:200]}",
            weight=1.5
        )
        total_score += score

    # -------------------------------------------------------------------------
    # 6. Check metadata priorities (proprietary: critical/high/medium/low via meta set)
    # -------------------------------------------------------------------------
    if st1:
        stdout_meta1, _, _ = run_agkan(f"agkan task meta get {st1.get('id')} priority", workspace)
        st1_priority_ok = "critical" in stdout_meta1.lower()
        score = add_check(
            "Subtask 1 metadata priority is 'critical'",
            st1_priority_ok,
            f"Meta output: {stdout_meta1[:200]}",
            weight=1.5
        )
        total_score += score

    if st2:
        stdout_meta2, _, _ = run_agkan(f"agkan task meta get {st2.get('id')} priority", workspace)
        st2_priority_ok = "high" in stdout_meta2.lower()
        score = add_check(
            "Subtask 2 metadata priority is 'high'",
            st2_priority_ok,
            f"Meta output: {stdout_meta2[:200]}",
            weight=1.0
        )
        total_score += score

    if st3:
        stdout_meta3, _, _ = run_agkan(f"agkan task meta get {st3.get('id')} priority", workspace)
        st3_priority_ok = "high" in stdout_meta3.lower()
        score = add_check(
            "Subtask 3 metadata priority is 'high'",
            st3_priority_ok,
            f"Meta output: {stdout_meta3[:200]}",
            weight=1.0
        )
        total_score += score

    if st4:
        stdout_meta4, _, _ = run_agkan(f"agkan task meta get {st4.get('id')} priority", workspace)
        st4_priority_ok = "medium" in stdout_meta4.lower()
        score = add_check(
            "Subtask 4 metadata priority is 'medium'",
            st4_priority_ok,
            f"Meta output: {stdout_meta4[:200]}",
            weight=1.0
        )
        total_score += score

    # -------------------------------------------------------------------------
    # 7. Check sprint_summary.json file exists and is valid
    # -------------------------------------------------------------------------
    summary_files = list(Path(workspace).rglob("sprint_summary.json"))
    summary_file_exists = len(summary_files) > 0
    score = add_check(
        "sprint_summary.json file exists",
        summary_file_exists,
        f"Found at: {summary_files[0] if summary_files else 'NOT FOUND'}",
        weight=1.0
    )
    total_score += score

    if summary_file_exists:
        try:
            with open(summary_files[0]) as f:
                summary_data = json.load(f)

            # Must contain tasks array (raw agkan JSON export)
            has_tasks_key = "tasks" in summary_data
            score = add_check(
                "sprint_summary.json contains 'tasks' key (valid agkan JSON export)",
                has_tasks_key,
                f"Keys present: {list(summary_data.keys())}",
                weight=1.0
            )
            total_score += score

            if has_tasks_key:
                summary_task_count = len(summary_data["tasks"])
                has_all_tasks = summary_task_count >= 5  # at least parent + 4 subtasks
                score = add_check(
                    "sprint_summary.json contains all tasks (>=5 tasks)",
                    has_all_tasks,
                    f"Task count in summary: {summary_task_count}",
                    weight=1.0
                )
                total_score += score

        except json.JSONDecodeError as e:
            checks.append({"name": "sprint_summary.json is valid JSON", "passed": False, "detail": f"JSON parse error: {e}"})
        except Exception as e:
            checks.append({"name": "sprint_summary.json readable", "passed": False, "detail": f"Error: {e}"})

    # -------------------------------------------------------------------------
    # 8. Verify tag list uses canonical names (not ad-hoc names)
    # -------------------------------------------------------------------------
    stdout_taglist, _, _ = run_agkan("agkan tag list --json", workspace)
    try:
        tag_list_data = json.loads(stdout_taglist)
        tag_names = [t.get("name", "").lower() for t in tag_list_data.get("tags", [])]
        canonical_tags = {"bug", "security", "improvement", "test", "performance", "refactor", "docs"}
        # All tags in system should be from canonical list
        non_canonical = [n for n in tag_names if n and n not in canonical_tags]
        tags_are_canonical = len(non_canonical) == 0
        score = add_check(
            "All tags used are from the canonical tag list",
            tags_are_canonical,
            f"Tag names in system: {tag_names}, Non-canonical: {non_canonical}",
            weight=1.0
        )
        total_score += score
    except Exception as e:
        checks.append({"name": "All tags used are from the canonical tag list", "passed": False, "detail": f"Error parsing tag list: {e}"})

    # -------------------------------------------------------------------------
    # Compute final score
    # -------------------------------------------------------------------------
    # Max possible score
    max_score = (
        1.0 +  # parent exists
        1.0 +  # parent status
        1.0 +  # parent author
        1.0 +  # st1 exists
        1.0 +  # st1 status
        1.0 +  # st1 parent
        1.0 +  # st2 exists
        1.0 +  # st2 status
        1.0 +  # st3 exists
        1.0 +  # st3 status
        1.0 +  # st4 exists
        1.0 +  # st4 status
        1.5 +  # block st1→st4
        1.5 +  # block st2→st3
        1.5 +  # bug tag st1
        1.5 +  # security tag st2
        1.5 +  # improvement tag st3
        1.5 +  # test tag st4
        1.5 +  # meta critical st1
        1.0 +  # meta high st2
        1.0 +  # meta high st3
        1.0 +  # meta medium st4
        1.0 +  # summary exists
        1.0 +  # summary has tasks key
        1.0 +  # summary has >=5 tasks
        1.0    # canonical tags only
    )

    normalized_score = round(total_score / max_score, 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": normalized_score >= 0.80,
        "score": normalized_score,
        "checks": checks
    }

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()