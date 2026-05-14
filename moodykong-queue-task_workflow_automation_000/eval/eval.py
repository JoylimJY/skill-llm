import sys
import json
import datetime
from pathlib import Path

def main(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0
    weights = {}

    def check(name, weight, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        weights[name] = weight
        return passed

    # ── 1. config.env must exist and have required keys ───────────────
    config_path = ws / "config.env"
    cfg = {}
    try:
        text = config_path.read_text()
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()

        required_keys = ["WORKSPACE_DIR", "TASKS_DIR", "BATCH_SIZE", "LOCK_STALE_MINUTES",
                         "CRON_EXPR", "CRON_TZ", "DELIVERY_MODE", "AGENT_ID"]
        missing = [k for k in required_keys if k not in cfg or not cfg[k]]
        if missing:
            check("config.env_has_required_keys", 1.5, False,
                  f"Missing or empty keys: {missing}")
        else:
            check("config.env_has_required_keys", 1.5, True,
                  f"All required keys present: {required_keys}")
    except Exception as e:
        check("config.env_has_required_keys", 1.5, False, f"Could not read config.env: {e}")

    # Derive task dir from config (or fallback to expected defaults)
    workspace_dir = cfg.get("WORKSPACE_DIR", str(ws))
    tasks_dir = cfg.get("TASKS_DIR", "tasks")
    slug = "compound-screen-2024"
    task_path = Path(workspace_dir) / tasks_dir / slug

    # ── 2. lock.json must be cleared ─────────────────────────────────
    lock_path = task_path / "lock.json"
    try:
        if lock_path.exists():
            check("stale_lock_cleared", 1.5, False,
                  f"lock.json still present at {lock_path}. clear-stale-lock was not run.")
        else:
            check("stale_lock_cleared", 1.5, True,
                  "lock.json has been correctly removed by clear-stale-lock.")
    except Exception as e:
        check("stale_lock_cleared", 1.5, False, f"Error checking lock: {e}")

    # ── 3. queue.jsonl must exist and contain new compounds ──────────
    queue_path = task_path / "queue.jsonl"
    queue_items = []
    try:
        if not queue_path.exists():
            check("queue_jsonl_exists", 1.5, False, f"queue.jsonl not found at {queue_path}")
        else:
            lines = [l.strip() for l in queue_path.read_text().splitlines() if l.strip()]
            if not lines:
                check("queue_jsonl_exists", 1.5, False, "queue.jsonl is empty")
            else:
                queue_items = [json.loads(l) for l in lines]
                check("queue_jsonl_exists", 1.5, True,
                      f"queue.jsonl has {len(queue_items)} entries")
    except Exception as e:
        check("queue_jsonl_exists", 1.5, False, f"Error reading queue.jsonl: {e}")

    # ── 4. queue items must have idempotency keys ─────────────────────
    try:
        if not queue_items:
            check("queue_items_have_idempotency_keys", 1.5, False,
                  "No queue items to check for idempotency keys.")
        else:
            # Each item must have some form of idempotency key
            # The skill requires: "Keep idempotency keys task-defined"
            # Acceptable: field named idempotency_key, or compound_id used as key, or a key field
            def has_idem_key(item):
                return any(k in item for k in ("idempotency_key", "id", "compound_id", "key"))
            all_have = all(has_idem_key(it) for it in queue_items)
            missing_count = sum(1 for it in queue_items if not has_idem_key(it))
            if all_have:
                check("queue_items_have_idempotency_keys", 1.5, True,
                      f"All {len(queue_items)} items have idempotency keys.")
            else:
                check("queue_items_have_idempotency_keys", 1.5, False,
                      f"{missing_count}/{len(queue_items)} items missing idempotency keys.")
    except Exception as e:
        check("queue_items_have_idempotency_keys", 1.5, False, f"Error: {e}")

    # ── 5. New compounds (CMP-0022 to CMP-0051) appear in queue ──────
    try:
        expected_ids = {f"CMP-{i:04d}" for i in range(22, 52)}
        if not queue_items:
            check("new_compounds_in_queue", 2.0, False, "Queue is empty; no compounds found.")
        else:
            found_ids = set()
            for it in queue_items:
                for field in ("compound_id", "idempotency_key", "id"):
                    if field in it:
                        found_ids.add(it[field])
                        break
            overlap = expected_ids & found_ids
            if len(overlap) >= 25:  # at least 25 of 30 new compounds
                check("new_compounds_in_queue", 2.0, True,
                      f"{len(overlap)}/30 new compounds found in queue.")
            else:
                check("new_compounds_in_queue", 2.0, False,
                      f"Only {len(overlap)}/30 new compounds in queue. Found: {sorted(found_ids)[:5]}...")
    except Exception as e:
        check("new_compounds_in_queue", 2.0, False, f"Error: {e}")

    # ── 6. progress.json must exist and be updated ───────────────────
    progress_path = task_path / "progress.json"
    try:
        if not progress_path.exists():
            check("progress_json_updated", 1.0, False,
                  f"progress.json not found at {progress_path}")
        else:
            prog = json.loads(progress_path.read_text())
            # Must have been updated (last_updated should be more recent than the stale 2024-01-15)
            last_updated_str = prog.get("last_updated", "")
            try:
                last_updated = datetime.datetime.fromisoformat(last_updated_str)
                stale_date = datetime.datetime(2024, 1, 16)  # anything after Jan 15 is fresh
                if last_updated > stale_date:
                    check("progress_json_updated", 1.0, True,
                          f"progress.json last_updated={last_updated_str} (fresh)")
                else:
                    check("progress_json_updated", 1.0, False,
                          f"progress.json last_updated={last_updated_str} appears stale (pre-2024-01-16)")
            except Exception:
                # If last_updated is missing or unparseable, still give partial credit if slug is right
                if prog.get("slug") == slug:
                    check("progress_json_updated", 1.0, True,
                          f"progress.json exists with correct slug. last_updated parse failed: {last_updated_str}")
                else:
                    check("progress_json_updated", 1.0, False,
                          f"progress.json has wrong slug or bad last_updated: {prog}")
    except Exception as e:
        check("progress_json_updated", 1.0, False, f"Error reading progress.json: {e}")

    # ── 7. done.jsonl and failed.jsonl must still exist (preserved) ──
    try:
        done_path = task_path / "done.jsonl"
        failed_path = task_path / "failed.jsonl"
        done_ok = done_path.exists() and bool(done_path.read_text().strip())
        failed_ok = failed_path.exists() and bool(failed_path.read_text().strip())
        if done_ok and failed_ok:
            done_count = len([l for l in done_path.read_text().splitlines() if l.strip()])
            check("append_only_logs_preserved", 0.5, True,
                  f"done.jsonl ({done_count} entries) and failed.jsonl preserved correctly.")
        else:
            check("append_only_logs_preserved", 0.5, False,
                  f"done.jsonl present+nonempty={done_ok}, failed.jsonl present+nonempty={failed_ok}")
    except Exception as e:
        check("append_only_logs_preserved", 0.5, False, f"Error: {e}")

    # ── Compute final score ───────────────────────────────────────────
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"])
    score = round(earned / total_weight, 4) if total_weight > 0 else 0.0
    passed = score >= 0.75

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)