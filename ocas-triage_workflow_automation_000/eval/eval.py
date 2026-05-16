import sys
import json
import re
from pathlib import Path
from datetime import datetime, timezone

def load_jsonl(path):
    records = []
    try:
        text = path.read_text().strip()
        if not text:
            return records
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return records

def check_iso8601(s):
    if not s or not isinstance(s, str):
        return False
    try:
        datetime.fromisoformat(s.replace("Z", "+00:00"))
        return True
    except Exception:
        return False

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    triage_dir = workspace / ".triage"
    queue_path = triage_dir / "queue.jsonl"
    signals_path = triage_dir / "signals.jsonl"
    decisions_path = triage_dir / "decisions.jsonl"
    journals_dir = triage_dir / "journals"

    queue_records = load_jsonl(queue_path)
    signals_records = load_jsonl(signals_path)
    decisions_records = load_jsonl(decisions_path)

    # ── Helper: get last state per task_id ──────────────────────────────────
    def last_state_map(records):
        m = {}
        for r in records:
            tid = r.get("task_id")
            if tid:
                m[tid] = r
        return m

    last_states = last_state_map(queue_records)

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 1: New task created and appended to queue.jsonl
    # The agent must create a new task for the Carrington v. Nexaline request.
    # We accept any task_id that is not one of the pre-existing ones.
    # ════════════════════════════════════════════════════════════════════════
    existing_ids = {"task-a-003", "task-b-002", "task-c-001"}
    new_task_records = [
        r for r in queue_records
        if r.get("task_id") and r["task_id"] not in existing_ids
        and "carrington" in (r.get("description", "") + r.get("task_id", "")).lower()
           or (r.get("task_id") and r["task_id"] not in existing_ids
               and r.get("routing_hint") == "mentor"
               and r.get("priority_score", 0) >= 70)
    ]

    # Broader: any new task_id not in existing_ids with priority_score >= 70
    all_new_tasks = [
        r for r in queue_records
        if r.get("task_id") and r["task_id"] not in existing_ids
    ]
    high_priority_new = [r for r in all_new_tasks if r.get("priority_score", 0) >= 70]

    check1_passed = len(high_priority_new) > 0
    checks.append({
        "name": "new_task_created_with_high_priority",
        "passed": check1_passed,
        "detail": (
            f"Found {len(high_priority_new)} new task(s) with priority_score >= 70 in queue.jsonl. "
            f"Required: at least 1. New task IDs: {[r.get('task_id') for r in all_new_tasks]}"
        )
    })
    if check1_passed:
        total_score += 15.0

    # Identify the new task
    new_task = high_priority_new[-1] if high_priority_new else (all_new_tasks[-1] if all_new_tasks else None)
    new_task_id = new_task.get("task_id") if new_task else None

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 2: New task priority_score is in 70–100 range (high band)
    # urgency=30, deadline_proximity=25, consequence_weight=20,
    # interruption_intent=15 → sum=90, clamped to 100 max → should be >=90
    # We accept 70–100 as valid (agent may compute slightly differently).
    # ════════════════════════════════════════════════════════════════════════
    new_task_score = new_task.get("priority_score", 0) if new_task else 0
    check2_passed = 70 <= new_task_score <= 100
    checks.append({
        "name": "new_task_priority_score_in_high_band_70_100",
        "passed": check2_passed,
        "detail": f"New task priority_score={new_task_score}. Must be 70–100 for high-priority band."
    })
    if check2_passed:
        total_score += 15.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 3: New task routing_hint is "mentor"
    # Scoring model: priority 70–100 → mentor routing
    # ════════════════════════════════════════════════════════════════════════
    new_task_routing = new_task.get("routing_hint") if new_task else None
    check3_passed = new_task_routing == "mentor"
    checks.append({
        "name": "new_task_routing_hint_is_mentor",
        "passed": check3_passed,
        "detail": f"New task routing_hint='{new_task_routing}'. Must be 'mentor' for priority 70–100."
    })
    if check3_passed:
        total_score += 10.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 4: Preemption occurred — task-a-003 checkpointed back to queued
    # New task score (>=70) exceeds task-a-003 score (62) by >25 → preemption fires
    # task-a-003 must have a later record with state="queued"
    # ════════════════════════════════════════════════════════════════════════
    task_a_records = [r for r in queue_records if r.get("task_id") == "task-a-003"]
    # Find the last state of task-a-003 after the new task was created
    # The latest record should be queued (checkpointed)
    task_a_final = task_a_records[-1] if task_a_records else None
    check4_passed = (
        task_a_final is not None
        and task_a_final.get("state") == "queued"
        and len(task_a_records) >= 3  # original queued + active + checkpointed back
    )
    checks.append({
        "name": "active_task_preempted_and_checkpointed_to_queued",
        "passed": check4_passed,
        "detail": (
            f"task-a-003 records: {len(task_a_records)}. "
            f"Last state: '{task_a_final.get('state') if task_a_final else None}'. "
            "Must have been checkpointed back to 'queued' after preemption."
        )
    })
    if check4_passed:
        total_score += 15.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 5: New task is active (state=active in latest queue record)
    # ════════════════════════════════════════════════════════════════════════
    new_task_queue_records = [r for r in queue_records if r.get("task_id") == new_task_id] if new_task_id else []
    new_task_final = new_task_queue_records[-1] if new_task_queue_records else None
    check5_passed = new_task_final is not None and new_task_final.get("state") == "active"
    checks.append({
        "name": "new_task_promoted_to_active_state",
        "passed": check5_passed,
        "detail": (
            f"New task_id='{new_task_id}' final state='{new_task_final.get('state') if new_task_final else None}'. "
            "Must be 'active'."
        )
    })
    if check5_passed:
        total_score += 10.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 6: No two tasks simultaneously active in the FINAL queue state
    # Evaluate by taking the latest record per task_id
    # ════════════════════════════════════════════════════════════════════════
    final_states = {}
    for r in queue_records:
        tid = r.get("task_id")
        if tid:
            final_states[tid] = r.get("state")
    active_count = sum(1 for s in final_states.values() if s == "active")
    check6_passed = active_count == 1
    checks.append({
        "name": "exactly_one_active_task_in_final_state",
        "passed": check6_passed,
        "detail": (
            f"Final active task count: {active_count}. "
            f"Active tasks: {[tid for tid, s in final_states.items() if s == 'active']}. "
            "Must be exactly 1."
        )
    })
    if check6_passed:
        total_score += 10.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 7: task_ready signal emitted in signals.jsonl for new task
    # Must include routing_hint=mentor and be for the new task
    # ════════════════════════════════════════════════════════════════════════
    task_ready_signals = [
        s for s in signals_records
        if s.get("signal") == "task_ready"
        and s.get("task_id") == new_task_id
    ]
    check7_passed = len(task_ready_signals) >= 1
    checks.append({
        "name": "task_ready_signal_emitted_for_new_task",
        "passed": check7_passed,
        "detail": (
            f"task_ready signals for new task '{new_task_id}': {len(task_ready_signals)}. "
            f"All signal task_ids: {[s.get('task_id') for s in signals_records if s.get('signal')=='task_ready']}"
        )
    })
    if check7_passed:
        total_score += 5.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 8: heartbeat_interval_seconds = 60 in task_ready signal
    # Priority score 70–100 → 60 seconds (THE KEY PROPRIETARY TRAP)
    # ════════════════════════════════════════════════════════════════════════
    best_signal = task_ready_signals[-1] if task_ready_signals else None
    heartbeat_val = best_signal.get("heartbeat_interval_seconds") if best_signal else None
    check8_passed = heartbeat_val == 60
    checks.append({
        "name": "heartbeat_interval_seconds_equals_60_for_high_priority",
        "passed": check8_passed,
        "detail": (
            f"heartbeat_interval_seconds={heartbeat_val}. "
            "Must be exactly 60 for priority score 70–100 (high band). "
            "This is the proprietary heartbeat injection rule from SKILL.md."
        )
    })
    if check8_passed:
        total_score += 10.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 9: heartbeat_rationale present and references high priority / 60s
    # ════════════════════════════════════════════════════════════════════════
    heartbeat_rationale = best_signal.get("heartbeat_rationale", "") if best_signal else ""
    rationale_ok = bool(heartbeat_rationale) and (
        "high" in heartbeat_rationale.lower()
        or "60" in heartbeat_rationale
        or "stall" in heartbeat_rationale.lower()
        or "1 minute" in heartbeat_rationale.lower()
    )
    checks.append({
        "name": "heartbeat_rationale_present_and_references_high_priority",
        "passed": rationale_ok,
        "detail": f"heartbeat_rationale='{heartbeat_rationale}'. Must reference high priority or 60s stall detection."
    })
    if rationale_ok:
        total_score += 5.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 10: DecisionRecord written to decisions.jsonl for preemption
    # Must have decision="preemption", displaced_task_id="task-a-003"
    # ════════════════════════════════════════════════════════════════════════
    preemption_records = [
        d for d in decisions_records
        if d.get("record_type") == "DecisionRecord"
        and d.get("decision") == "preemption"
    ]
    # Also accept records that clearly reference task-a-003 as displaced
    preemption_with_displaced = [
        d for d in preemption_records
        if d.get("displaced_task_id") == "task-a-003"
        or d.get("preempted_task_id") == "task-a-003"
        or "task-a-003" in str(d)
    ]
    check10_passed = len(preemption_with_displaced) >= 1
    checks.append({
        "name": "decision_record_written_for_preemption_of_task_a_003",
        "passed": check10_passed,
        "detail": (
            f"Preemption DecisionRecords found: {len(preemption_with_displaced)}. "
            f"All decisions.jsonl records: {len(decisions_records)}. "
            "Must have DecisionRecord with decision='preemption' referencing task-a-003."
        )
    })
    if check10_passed:
        total_score += 10.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 11: Journal entry created for preemption
    # Must exist a file in .triage/journals/ referencing the preemption event
    # ════════════════════════════════════════════════════════════════════════
    journal_files = list(journals_dir.glob("*")) if journals_dir.exists() else []
    journal_preemption_found = False
    for jf in journal_files:
        try:
            content = jf.read_text().lower()
            if "preempt" in content or "checkpoint" in content or "task-a-003" in content:
                journal_preemption_found = True
                break
        except Exception:
            pass
    checks.append({
        "name": "journal_entry_created_for_preemption",
        "passed": journal_preemption_found,
        "detail": (
            f"Journal files found: {[f.name for f in journal_files]}. "
            "At least one must reference preemption, checkpoint, or the displaced task ID. "
            "Required by: 'Preemption always produces a journal entry and DecisionRecord'."
        )
    })
    if journal_preemption_found:
        total_score += 5.0

    # ════════════════════════════════════════════════════════════════════════
    # CHECK 12: task_ready signal has valid ISO8601 emitted_at
    # ════════════════════════════════════════════════════════════════════════
    emitted_at = best_signal.get("emitted_at") if best_signal else None
    check12_passed = check_iso8601(emitted_at)
    checks.append({
        "name": "task_ready_signal_has_valid_iso8601_emitted_at",
        "passed": check12_passed,
        "detail": f"emitted_at='{emitted_at}'. Must be valid ISO8601 timestamp."
    })
    if check12_passed:
        total_score += 0.0  # Bonus quality check, no score weight

    # ════════════════════════════════════════════════════════════════════════
    # FINAL SCORING
    # ════════════════════════════════════════════════════════════════════════
    # Max possible: 15+15+10+15+10+10+5+10+5+10+5 = 110 (cap at 100)
    max_score = 100.0
    final_score = min(total_score / max_score, 1.0)

    # Overall pass: must hit core checks
    # Required: check1, check2, check3, check4, check5, check6, check8, check10
    core_checks = [
        checks[0]["passed"],  # new task created high priority
        checks[1]["passed"],  # priority 70-100
        checks[2]["passed"],  # routing_hint=mentor
        checks[3]["passed"],  # task-a-003 checkpointed
        checks[4]["passed"],  # new task active
        checks[5]["passed"],  # exactly 1 active
        checks[7]["passed"],  # heartbeat=60
        checks[9]["passed"],  # DecisionRecord for preemption
    ]
    overall_passed = all(core_checks)

    return {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))