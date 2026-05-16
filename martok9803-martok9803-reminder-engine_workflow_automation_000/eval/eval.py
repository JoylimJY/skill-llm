import sys
import json
import re
from pathlib import Path

def load_store(workspace):
    store_path = Path(workspace) / ".cron_store.json"
    try:
        with open(store_path) as f:
            return json.load(f)
    except Exception as e:
        return None

def evaluate(workspace):
    checks = []
    store = load_store(workspace)

    if store is None:
        checks.append({"name": "cron_store_accessible", "passed": False, "detail": "Could not read .cron_store.json"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "cron_store_accessible", "passed": True, "detail": "Store loaded successfully"})

    jobs = store.get("jobs", [])
    call_log = store.get("call_log", [])

    # =========================================================
    # CHECK 1: A recurring weekday standup reminder was created
    # Must use schedule.kind="cron", have a tz field,
    # sessionTarget="main", payload.kind="systemEvent",
    # and payload.text starts with "Reminder:"
    # Weekday 9:15 AM -> cron expr should encode weekdays (Mon-Fri) and 9:15
    # =========================================================
    recurring_jobs = [
        j for j in jobs
        if j.get("schedule", {}).get("kind") == "cron"
        and j.get("jobId") not in ("job_abc123", "job_xyz789")
    ]

    standup_job = None
    for j in recurring_jobs:
        text = j.get("payload", {}).get("text", "").lower()
        if "standup" in text or "stand up" in text or "stand-up" in text:
            standup_job = j
            break

    if standup_job is None:
        # Try broader match: any new cron job with weekday scheduling
        for j in recurring_jobs:
            expr = j.get("schedule", {}).get("expr", "")
            # Check for 9:15 pattern and weekday restriction
            if "15" in expr and "9" in expr:
                standup_job = j
                break

    check_standup_exists = standup_job is not None
    checks.append({
        "name": "recurring_standup_created",
        "passed": check_standup_exists,
        "detail": f"Found recurring standup job: {standup_job['jobId'] if standup_job else 'None'}"
    })

    if standup_job:
        # Check schedule.kind == "cron"
        kind_ok = standup_job.get("schedule", {}).get("kind") == "cron"
        checks.append({
            "name": "standup_schedule_kind_is_cron",
            "passed": kind_ok,
            "detail": f"schedule.kind = {standup_job.get('schedule', {}).get('kind')}"
        })

        # Check tz is set
        tz = standup_job.get("schedule", {}).get("tz", "")
        tz_ok = bool(tz) and len(tz) > 0
        checks.append({
            "name": "standup_has_tz_field",
            "passed": tz_ok,
            "detail": f"schedule.tz = '{tz}'"
        })

        # Check tz is America/New_York or equivalent
        tz_correct = "new_york" in tz.lower() or "america/new_york" in tz.lower() or tz == "America/New_York"
        checks.append({
            "name": "standup_tz_is_new_york",
            "passed": tz_correct,
            "detail": f"schedule.tz = '{tz}' (expected America/New_York)"
        })

        # Check sessionTarget == "main"
        session_ok = standup_job.get("sessionTarget") == "main"
        checks.append({
            "name": "standup_session_target_main",
            "passed": session_ok,
            "detail": f"sessionTarget = '{standup_job.get('sessionTarget')}'"
        })

        # Check payload.kind == "systemEvent"
        payload_kind_ok = standup_job.get("payload", {}).get("kind") == "systemEvent"
        checks.append({
            "name": "standup_payload_kind_systemEvent",
            "passed": payload_kind_ok,
            "detail": f"payload.kind = '{standup_job.get('payload', {}).get('kind')}'"
        })

        # Check payload.text starts with "Reminder:"
        payload_text = standup_job.get("payload", {}).get("text", "")
        reminder_prefix_ok = payload_text.startswith("Reminder:")
        checks.append({
            "name": "standup_payload_text_reminder_prefix",
            "passed": reminder_prefix_ok,
            "detail": f"payload.text = '{payload_text[:80]}'"
        })

        # Check payload text mentions standup
        standup_mention_ok = "standup" in payload_text.lower() or "stand up" in payload_text.lower() or "stand-up" in payload_text.lower()
        checks.append({
            "name": "standup_payload_mentions_standup",
            "passed": standup_mention_ok,
            "detail": f"payload.text = '{payload_text[:80]}'"
        })

        # Check cron expr encodes weekdays (Mon-Fri) and time 9:15
        expr = standup_job.get("schedule", {}).get("expr", "")
        # Standard cron: "15 9 * * 1-5" or "15 9 * * MON-FRI" etc.
        expr_has_915 = bool(re.search(r'\b15\s+9\b', expr) or re.search(r'\b9\s+15\b', expr))
        # Check weekday restriction: 1-5 or MON-FRI or similar
        expr_weekday_ok = bool(
            re.search(r'1-5', expr) or 
            re.search(r'mon.*fri', expr.lower()) or
            re.search(r'1,2,3,4,5', expr)
        )
        checks.append({
            "name": "standup_cron_expr_time_915",
            "passed": expr_has_915,
            "detail": f"cron expr = '{expr}' (need 15 9 pattern)"
        })
        checks.append({
            "name": "standup_cron_expr_weekday_only",
            "passed": expr_weekday_ok,
            "detail": f"cron expr = '{expr}' (need weekday restriction 1-5 or MON-FRI)"
        })
    else:
        # Add failing placeholder checks
        for check_name in [
            "standup_schedule_kind_is_cron", "standup_has_tz_field", "standup_tz_is_new_york",
            "standup_session_target_main", "standup_payload_kind_systemEvent",
            "standup_payload_text_reminder_prefix", "standup_payload_mentions_standup",
            "standup_cron_expr_time_915", "standup_cron_expr_weekday_only"
        ]:
            checks.append({"name": check_name, "passed": False, "detail": "No standup job found"})

    # =========================================================
    # CHECK 2: Snooze of job_abc123 was implemented as cancel + recreate
    # - job_abc123 must NO LONGER exist in jobs list (cancelled)
    # - A new one-shot job (schedule.kind="at") must exist with time 14:30
    #   and payload referencing deployment checklist
    # =========================================================

    # Check job_abc123 was removed
    remaining_abc = [j for j in jobs if j.get("jobId") == "job_abc123"]
    abc_removed = len(remaining_abc) == 0
    checks.append({
        "name": "original_deployment_job_cancelled",
        "passed": abc_removed,
        "detail": f"job_abc123 {'removed' if abc_removed else 'still present'} in jobs"
    })

    # Check a DELETE call was made for job_abc123 in the call log
    delete_abc_calls = [
        c for c in call_log
        if c.get("method") == "DELETE" and "job_abc123" in c.get("endpoint", "")
    ]
    delete_called = len(delete_abc_calls) > 0
    checks.append({
        "name": "snooze_used_cancel_api_call",
        "passed": delete_called,
        "detail": f"DELETE /cron/remove/job_abc123 called: {delete_called} ({len(delete_abc_calls)} times)"
    })

    # Check a new one-shot job was created for deployment checklist at 14:30
    new_oneshot_jobs = [
        j for j in jobs
        if j.get("schedule", {}).get("kind") == "at"
        and j.get("jobId") not in ("job_abc123", "job_xyz789")
    ]

    snooze_job = None
    for j in new_oneshot_jobs:
        text = j.get("payload", {}).get("text", "").lower()
        sched_time = j.get("schedule", {}).get("time", "")
        if ("deployment" in text or "checklist" in text) and "14:30" in sched_time:
            snooze_job = j
            break
        # Also accept if time has 14:30
        if "14:30" in sched_time and ("deployment" in text or "checklist" in text):
            snooze_job = j
            break

    if snooze_job is None:
        # Try relaxed: any new at-job with 14:30
        for j in new_oneshot_jobs:
            sched_time = j.get("schedule", {}).get("time", "")
            if "14:30" in sched_time:
                snooze_job = j
                break

    snooze_recreated = snooze_job is not None
    checks.append({
        "name": "snooze_new_oneshot_job_created",
        "passed": snooze_recreated,
        "detail": f"New one-shot job at 14:30 found: {snooze_job['jobId'] if snooze_job else 'None'}"
    })

    if snooze_job:
        # Check schedule.kind == "at"
        at_kind_ok = snooze_job.get("schedule", {}).get("kind") == "at"
        checks.append({
            "name": "snooze_schedule_kind_is_at",
            "passed": at_kind_ok,
            "detail": f"schedule.kind = {snooze_job.get('schedule', {}).get('kind')}"
        })

        # Check sessionTarget == "main"
        session_ok2 = snooze_job.get("sessionTarget") == "main"
        checks.append({
            "name": "snooze_session_target_main",
            "passed": session_ok2,
            "detail": f"sessionTarget = '{snooze_job.get('sessionTarget')}'"
        })

        # Check payload.kind == "systemEvent"
        payload_kind_ok2 = snooze_job.get("payload", {}).get("kind") == "systemEvent"
        checks.append({
            "name": "snooze_payload_kind_systemEvent",
            "passed": payload_kind_ok2,
            "detail": f"payload.kind = '{snooze_job.get('payload', {}).get('kind')}'"
        })

        # Check payload.text starts with "Reminder:"
        snooze_text = snooze_job.get("payload", {}).get("text", "")
        snooze_prefix_ok = snooze_text.startswith("Reminder:")
        checks.append({
            "name": "snooze_payload_text_reminder_prefix",
            "passed": snooze_prefix_ok,
            "detail": f"payload.text = '{snooze_text[:80]}'"
        })
    else:
        for check_name in [
            "snooze_schedule_kind_is_at", "snooze_session_target_main",
            "snooze_payload_kind_systemEvent", "snooze_payload_text_reminder_prefix"
        ]:
            checks.append({"name": check_name, "passed": False, "detail": "No snooze job found"})

    # =========================================================
    # CHECK 3: cron.list was called (agent read existing jobs)
    # =========================================================
    list_calls = [c for c in call_log if c.get("method") == "GET" and "/cron/list" in c.get("endpoint", "")]
    list_called = len(list_calls) > 0
    checks.append({
        "name": "cron_list_was_called",
        "passed": list_called,
        "detail": f"GET /cron/list called {len(list_calls)} time(s)"
    })

    # =========================================================
    # CHECK 4: job_xyz789 (weekly report) was NOT accidentally removed
    # =========================================================
    xyz_still_present = any(j.get("jobId") == "job_xyz789" for j in jobs)
    checks.append({
        "name": "weekly_report_job_untouched",
        "passed": xyz_still_present,
        "detail": f"job_xyz789 {'present' if xyz_still_present else 'REMOVED - should not have been touched'}"
    })

    # =========================================================
    # Scoring
    # =========================================================
    # Weight critical checks higher
    critical_checks = [
        "recurring_standup_created",
        "standup_schedule_kind_is_cron",
        "standup_has_tz_field",
        "standup_tz_is_new_york",
        "standup_session_target_main",
        "standup_payload_kind_systemEvent",
        "standup_payload_text_reminder_prefix",
        "original_deployment_job_cancelled",
        "snooze_used_cancel_api_call",
        "snooze_new_oneshot_job_created",
        "snooze_schedule_kind_is_at",
        "snooze_session_target_main",
        "snooze_payload_kind_systemEvent",
        "snooze_payload_text_reminder_prefix",
    ]

    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    passed_count = len(passed_checks)

    critical_passed = sum(
        1 for c in checks
        if c["name"] in critical_checks and c["passed"]
    )
    critical_total = len(critical_checks)

    # Score = weighted: 70% critical, 30% all
    score = 0.0
    if critical_total > 0:
        score = 0.7 * (critical_passed / critical_total) + 0.3 * (passed_count / total)
    
    score = round(score, 4)
    overall_passed = critical_passed >= int(critical_total * 0.85) and passed_count >= int(total * 0.75)

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))