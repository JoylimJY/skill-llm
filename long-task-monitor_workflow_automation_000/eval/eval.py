import sys
import json
import os
from pathlib import Path

def main(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    weight_sum = 0.0

    def check(name, weight, passed, detail):
        nonlocal total_score, weight_sum
        checks.append({"name": name, "passed": passed, "detail": detail})
        weight_sum += weight
        if passed:
            total_score += weight

    base_dir = Path.home() / ".openclaw" / "workspace" / "long-tasks"

    # ── Find all task directories (excluding the distractor task-deadbeef) ────
    try:
        task_dirs = [
            d for d in base_dir.iterdir()
            if d.is_dir() and d.name != "task-deadbeef" and (d / "task.json").exists()
        ]
    except Exception as e:
        check("task_directory_exists", 1.0, False, f"Could not list long-tasks dir: {e}")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    if not task_dirs:
        check("task_created", 2.0, False, "No new task directory found under ~/.openclaw/workspace/long-tasks/")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # Use the first non-distractor task
    task_dir = task_dirs[0]

    # ── Check 1: task.json exists and has correct schema ─────────────────────
    try:
        task_json_path = task_dir / "task.json"
        task = json.loads(task_json_path.read_text())
        required_fields = ["taskId", "description", "workerTask", "workerSessionKey",
                           "monitorSessionKey", "createdAt", "status", "monitorRound", "workerRestartCount"]
        missing = [f for f in required_fields if f not in task]
        check("task_json_schema", 1.5,
              len(missing) == 0,
              f"task.json has all required fields" if not missing else f"Missing fields: {missing}")
    except Exception as e:
        check("task_json_schema", 1.5, False, f"Could not read task.json: {e}")
        task = {}

    # ── Check 2: task describes a data preprocessing/training job ─────────────
    try:
        description = task.get("description", "")
        worker_task = task.get("workerTask", "")
        has_meaningful_content = len(description.strip()) > 5 and len(worker_task.strip()) > 5
        check("task_content_meaningful", 0.5,
              has_meaningful_content,
              f"description='{description}', workerTask='{worker_task}'")
    except Exception as e:
        check("task_content_meaningful", 0.5, False, str(e))

    # ── Check 3: workerSessionKey contains ':' (proprietary constraint) ───────
    try:
        wsk = task.get("workerSessionKey", "")
        has_colon = ":" in wsk
        is_nonempty = len(wsk.strip()) > 0
        check("worker_session_key_format", 2.0,
              has_colon and is_nonempty,
              f"workerSessionKey='{wsk}' — must be non-empty and contain ':' (e.g. agent:main:subagent:xxx)")
    except Exception as e:
        check("worker_session_key_format", 2.0, False, str(e))

    # ── Check 4: monitorSessionKey contains ':' (proprietary constraint) ──────
    try:
        msk = task.get("monitorSessionKey", "")
        has_colon = ":" in msk
        is_nonempty = len(msk.strip()) > 0
        check("monitor_session_key_format", 2.0,
              has_colon and is_nonempty,
              f"monitorSessionKey='{msk}' — must be non-empty and contain ':' (e.g. agent:main:subagent:yyy)")
    except Exception as e:
        check("monitor_session_key_format", 2.0, False, str(e))

    # ── Check 5: task status is 'running' or 'completed' after updates ────────
    try:
        status = task.get("status", "")
        check("task_status_updated", 1.0,
              status in ("running", "completed"),
              f"task status='{status}', expected 'running' or 'completed' after worker key update")
    except Exception as e:
        check("task_status_updated", 1.0, False, str(e))

    # ── Check 6: monitor-rounds directory exists ──────────────────────────────
    try:
        rounds_dir = task_dir / "monitor-rounds"
        check("monitor_rounds_dir_exists", 1.0,
              rounds_dir.is_dir(),
              f"monitor-rounds/ dir {'exists' if rounds_dir.is_dir() else 'MISSING'} at {rounds_dir}")
    except Exception as e:
        check("monitor_rounds_dir_exists", 1.0, False, str(e))

    # ── Check 7: current-round.json exists and has round/status fields ────────
    try:
        current_round_path = task_dir / "monitor-rounds" / "current-round.json"
        if current_round_path.exists():
            cr = json.loads(current_round_path.read_text())
            has_round = "round" in cr or "status" in cr or "recordedAt" in cr
            check("current_round_json_valid", 1.5,
                  has_round,
                  f"current-round.json content keys: {list(cr.keys())}")
        else:
            check("current_round_json_valid", 1.5, False,
                  f"current-round.json not found at {current_round_path}")
    except Exception as e:
        check("current_round_json_valid", 1.5, False, str(e))

    # ── Check 8: monitorRound > 0 in task.json ────────────────────────────────
    try:
        mr = task.get("monitorRound", 0)
        check("monitor_round_incremented", 1.0,
              int(mr) >= 1,
              f"monitorRound={mr}, expected >= 1 after at least one monitoring round")
    except Exception as e:
        check("monitor_round_incremented", 1.0, False, str(e))

    # ── Check 9: status.json exists (complete was called) ─────────────────────
    try:
        status_json_path = task_dir / "status.json"
        if status_json_path.exists():
            sj = json.loads(status_json_path.read_text())
            has_result = "result" in sj and len(str(sj.get("result", "")).strip()) > 0
            has_completed_at = "completedAt" in sj
            check("status_json_complete", 2.0,
                  has_result and has_completed_at,
                  f"status.json result='{sj.get('result','')}', completedAt={sj.get('completedAt','MISSING')}")
        else:
            check("status_json_complete", 2.0, False,
                  f"status.json not found — 'complete' command was never run")
    except Exception as e:
        check("status_json_complete", 2.0, False, str(e))

    # ── Check 10: final task.json status is 'completed' ──────────────────────
    try:
        # Re-read task.json in case it was updated by complete command
        task_final = json.loads((task_dir / "task.json").read_text())
        final_status = task_final.get("status", "")
        check("final_task_status_completed", 1.5,
              final_status == "completed",
              f"Final task status='{final_status}', expected 'completed'")
    except Exception as e:
        check("final_task_status_completed", 1.5, False, str(e))

    # ── Check 11: worker and monitor keys are DIFFERENT ───────────────────────
    try:
        task_final = json.loads((task_dir / "task.json").read_text())
        wsk2 = task_final.get("workerSessionKey", "")
        msk2 = task_final.get("monitorSessionKey", "")
        keys_different = wsk2 != msk2 and len(wsk2) > 0 and len(msk2) > 0
        check("worker_and_monitor_keys_differ", 1.0,
              keys_different,
              f"workerSessionKey='{wsk2}', monitorSessionKey='{msk2}' — must be distinct non-empty values")
    except Exception as e:
        check("worker_and_monitor_keys_differ", 1.0, False, str(e))

    # ── Compute final score ───────────────────────────────────────────────────
    score = round(total_score / weight_sum, 4) if weight_sum > 0 else 0.0
    passed = score >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in ("worker_session_key_format", "monitor_session_key_format",
                         "task_json_schema", "status_json_complete")
    )

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(ws)