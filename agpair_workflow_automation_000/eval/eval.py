#!/usr/bin/env python3
"""
Evaluation script for the agpair delegation workflow task.
Checks that the agent followed ALL required gates from SKILL.md:
1. Ran agpair doctor --repo-path
2. Ran agpair daemon status
3. Dispatched a task (agpair task start)
4. Checked active-waits before semantic action
5. Checked task status
6. Retrieved logs with --limit 20
7. Issued exactly one semantic 'approve' action
8. Wrote a delegation_report.md file to the workspace
"""
import sys
import json
import re
from pathlib import Path

def load_invocations(log_path: Path):
    invocations = []
    if not log_path.exists():
        return invocations
    for line in log_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            invocations.append(entry.get("args", []))
        except Exception:
            pass
    return invocations

def check_invocation(invocations, pred, description):
    for inv in invocations:
        if pred(inv):
            return True, description
    return False, description

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    state_dir = Path("/tmp/agpair_state")
    invocations_log = state_dir / "invocations.log"
    task_state_file = state_dir / "task_state.json"

    checks = []
    total_score = 0.0

    # Load invocations
    invocations = load_invocations(invocations_log)

    # --- Check 1: agpair doctor --repo-path was called ---
    def is_doctor(inv):
        return len(inv) >= 1 and inv[0] == "doctor" and "--repo-path" in inv

    passed, _ = check_invocation(invocations, is_doctor, "agpair doctor --repo-path called")
    checks.append({
        "name": "preflight_doctor_called",
        "passed": passed,
        "detail": "agpair doctor --repo-path <path> must be called as preflight" if not passed else
                  "doctor preflight check confirmed"
    })
    if passed: total_score += 1.5

    # --- Check 2: agpair daemon status was called ---
    def is_daemon_status(inv):
        return len(inv) >= 2 and inv[0] == "daemon" and inv[1] == "status"

    passed, _ = check_invocation(invocations, is_daemon_status, "agpair daemon status called")
    checks.append({
        "name": "preflight_daemon_status_called",
        "passed": passed,
        "detail": "agpair daemon status must be called as preflight" if not passed else
                  "daemon status preflight check confirmed"
    })
    if passed: total_score += 1.5

    # --- Check 3: agpair task start was called ---
    def is_task_start(inv):
        return len(inv) >= 2 and inv[0] == "task" and inv[1] == "start"

    passed, _ = check_invocation(invocations, is_task_start, "agpair task start called")
    checks.append({
        "name": "task_dispatched",
        "passed": passed,
        "detail": "agpair task start must be called to dispatch the refactoring task" if not passed else
                  "task dispatch confirmed"
    })
    if passed: total_score += 1.5

    # --- Check 4: repo path was passed to task start (or doctor) ---
    def task_start_has_repo(inv):
        return (len(inv) >= 2 and inv[0] == "task" and inv[1] == "start" and
                "--repo-path" in inv)

    passed_repo, _ = check_invocation(invocations, task_start_has_repo, "task start has --repo-path")
    # Also accept doctor having the payments_service path
    def doctor_has_payments_path(inv):
        if inv[0] != "doctor":
            return False
        idx = inv.index("--repo-path") if "--repo-path" in inv else -1
        if idx == -1 or idx + 1 >= len(inv):
            return False
        path = inv[idx + 1]
        return "payments_service" in path or "workspace" in path

    passed_repo2, _ = check_invocation(invocations, doctor_has_payments_path, "doctor has payments path")
    passed = passed_repo or passed_repo2
    checks.append({
        "name": "repo_path_specified",
        "passed": passed,
        "detail": "payments_service repo path must be passed to either task start or doctor" if not passed else
                  "repo path correctly specified"
    })
    if passed: total_score += 1.0

    # --- Check 5: active-waits was polled ---
    def is_active_waits(inv):
        return (len(inv) >= 3 and inv[0] == "task" and inv[1] == "active-waits")

    passed, _ = check_invocation(invocations, is_active_waits, "agpair task active-waits polled")
    checks.append({
        "name": "active_waits_polled",
        "passed": passed,
        "detail": "agpair task active-waits must be checked before issuing semantic actions" if not passed else
                  "active-waits polling confirmed"
    })
    if passed: total_score += 1.5

    # --- Check 6: task status was checked ---
    def is_task_status(inv):
        return len(inv) >= 2 and inv[0] == "task" and inv[1] == "status"

    passed, _ = check_invocation(invocations, is_task_status, "agpair task status checked")
    checks.append({
        "name": "task_status_checked",
        "passed": passed,
        "detail": "agpair task status <TASK_ID> must be checked before semantic action" if not passed else
                  "task status check confirmed"
    })
    if passed: total_score += 1.0

    # --- Check 7: task logs retrieved with --limit ---
    def is_task_logs_with_limit(inv):
        return (len(inv) >= 2 and inv[0] == "task" and inv[1] == "logs" and
                "--limit" in inv)

    passed_limit, _ = check_invocation(invocations, is_task_logs_with_limit, "task logs with --limit")
    
    # Check that limit value is 20 (as required by SKILL.md)
    limit_value_correct = False
    for inv in invocations:
        if len(inv) >= 2 and inv[0] == "task" and inv[1] == "logs" and "--limit" in inv:
            idx = inv.index("--limit")
            if idx + 1 < len(inv):
                try:
                    if int(inv[idx + 1]) == 20:
                        limit_value_correct = True
                        break
                except ValueError:
                    pass

    # Check task state for logs_limit_used
    logs_limit_from_state = None
    if task_state_file.exists():
        try:
            state = json.loads(task_state_file.read_text())
            logs_limit_from_state = state.get("logs_limit_used")
        except Exception:
            pass

    passed = passed_limit
    detail = "agpair task logs <TASK_ID> --limit 20 must be called" if not passed_limit else \
             f"task logs called with --limit; limit value 20: {limit_value_correct}; state recorded limit: {logs_limit_from_state}"
    checks.append({
        "name": "task_logs_with_limit_20",
        "passed": passed_limit and limit_value_correct,
        "detail": detail
    })
    if passed_limit and limit_value_correct:
        total_score += 1.5
    elif passed_limit:
        total_score += 0.5

    # --- Check 8: Exactly one semantic action: approve ---
    def is_approve(inv):
        return (inv[0] == "approve") or \
               (len(inv) >= 3 and inv[0] == "task" and inv[1] == "approve")

    def is_reject(inv):
        return (inv[0] == "reject") or \
               (len(inv) >= 3 and inv[0] == "task" and inv[1] == "reject")

    def is_continue(inv):
        return (inv[0] == "continue") or \
               (len(inv) >= 3 and inv[0] == "task" and inv[1] == "continue")

    def is_retry(inv):
        return (inv[0] == "retry") or \
               (len(inv) >= 3 and inv[0] == "task" and inv[1] == "retry")

    approve_calls = [inv for inv in invocations if is_approve(inv)]
    reject_calls  = [inv for inv in invocations if is_reject(inv)]
    cont_calls    = [inv for inv in invocations if is_continue(inv)]
    retry_calls   = [inv for inv in invocations if is_retry(inv)]

    all_semantic = approve_calls + reject_calls + cont_calls + retry_calls
    approved_correctly = len(approve_calls) == 1
    one_semantic_only  = len(all_semantic) == 1

    checks.append({
        "name": "exactly_one_approve_semantic_action",
        "passed": approved_correctly and one_semantic_only,
        "detail": f"Expected exactly 1 'approve' action. Found: approve={len(approve_calls)}, "
                  f"reject={len(reject_calls)}, continue={len(cont_calls)}, retry={len(retry_calls)}"
    })
    if approved_correctly and one_semantic_only:
        total_score += 2.0
    elif approved_correctly:
        total_score += 1.0  # approved but also issued other actions

    # --- Check 9: Task state shows COMMITTED ---
    committed = False
    if task_state_file.exists():
        try:
            state = json.loads(task_state_file.read_text())
            committed = state.get("status") == "COMMITTED"
            semantic_action = state.get("semantic_action")
        except Exception:
            semantic_action = None
    
    checks.append({
        "name": "task_reached_committed_state",
        "passed": committed,
        "detail": f"Task state should be COMMITTED after approve. "
                  f"Actual status from state file: {state.get('status', 'UNKNOWN') if task_state_file.exists() else 'state file missing'}"
    })
    if committed: total_score += 1.0

    # --- Check 10: Doctor was called BEFORE task start (ordering) ---
    doctor_first_idx = None
    task_start_idx = None
    for i, inv in enumerate(invocations):
        if doctor_first_idx is None and is_doctor(inv):
            doctor_first_idx = i
        if task_start_idx is None and is_task_start(inv):
            task_start_idx = i

    preflight_before_dispatch = (
        doctor_first_idx is not None and
        task_start_idx is not None and
        doctor_first_idx < task_start_idx
    )
    checks.append({
        "name": "preflight_before_dispatch_ordering",
        "passed": preflight_before_dispatch,
        "detail": f"doctor must be called before task start. "
                  f"doctor at index {doctor_first_idx}, task start at index {task_start_idx}"
    })
    if preflight_before_dispatch: total_score += 1.0

    # --- Check 11: delegation_report.md exists in workspace ---
    report_files = list(Path(workspace).rglob("delegation_report.md"))
    report_exists = len(report_files) > 0
    report_detail = f"Found {len(report_files)} delegation_report.md file(s)"
    
    report_has_task_id = False
    report_has_status = False
    if report_exists:
        try:
            content = report_files[0].read_text().lower()
            # Should mention approval/approved/committed
            report_has_status = any(w in content for w in ["approved", "committed", "approve"])
            # Should mention task id or antigravity
            report_has_task_id = any(w in content for w in ["task-", "antigravity", "task_id", "agpair"])
            report_detail += f"; mentions approval: {report_has_status}; mentions task/antigravity: {report_has_task_id}"
        except Exception as e:
            report_detail += f"; error reading report: {e}"

    checks.append({
        "name": "delegation_report_md_created",
        "passed": report_exists,
        "detail": report_detail
    })
    if report_exists: total_score += 0.5
    
    checks.append({
        "name": "delegation_report_md_content_quality",
        "passed": report_exists and report_has_status and report_has_task_id,
        "detail": f"Report should mention the task outcome and task/antigravity reference. "
                  f"has_approval_mention={report_has_status}, has_task_ref={report_has_task_id}"
    })
    if report_exists and report_has_status and report_has_task_id:
        total_score += 0.5

    # Max possible score: 1.5+1.5+1.5+1.0+1.5+1.0+1.5+2.0+1.0+1.0+0.5+0.5 = 15.0
    max_score = 15.0
    normalized_score = round(total_score / max_score, 4)

    # Overall pass: must pass the critical checks
    critical_checks = [
        "preflight_doctor_called",
        "preflight_daemon_status_called",
        "task_dispatched",
        "active_waits_polled",
        "task_status_checked",
        "exactly_one_approve_semantic_action",
        "task_reached_committed_state",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    overall_passed = critical_passed and normalized_score >= 0.6

    result = {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()