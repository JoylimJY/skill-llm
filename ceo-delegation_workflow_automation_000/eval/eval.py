#!/usr/bin/env python3
import sys
import json
from pathlib import Path

def load_invocations(workspace: Path):
    log_path = workspace / "tool_logs" / "invocations.jsonl"
    if not log_path.exists():
        return []
    invocations = []
    with open(log_path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    invocations.append(json.loads(line))
                except Exception:
                    pass
    # Sort by unix timestamp
    invocations.sort(key=lambda x: x.get("unix_ts", 0))
    return invocations

def get_tool_calls(invocations, tool_name):
    return [inv for inv in invocations if inv.get("tool") == tool_name]

def extract_param(inv, *keys):
    """Try to extract a parameter from args dict using multiple possible key names."""
    args = inv.get("args", {})
    for k in keys:
        if k in args:
            return args[k]
    # Also try raw_args parsing
    raw = inv.get("raw_args", [])
    for i, arg in enumerate(raw):
        if arg.lstrip("-") in keys:
            if i + 1 < len(raw):
                return raw[i + 1]
    return None

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []
    
    try:
        invocations = load_invocations(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "load_invocations", "passed": False, "detail": f"Failed to load tool logs: {e}"}]
        }))
        return

    memory_calls = get_tool_calls(invocations, "memory_search")
    spawn_calls = get_tool_calls(invocations, "sessions_spawn")
    monitor_calls = get_tool_calls(invocations, "sessions_list") + get_tool_calls(invocations, "sessions_history")
    
    # ── CHECK 1: memory_search was called at all ──────────────────────────────
    check1_passed = len(memory_calls) >= 1
    checks.append({
        "name": "memory_search_called",
        "passed": check1_passed,
        "detail": f"memory_search called {len(memory_calls)} time(s). Expected ≥1 call per the RAG search step."
    })

    # ── CHECK 2: memory_search called BEFORE first sessions_spawn ─────────────
    if check1_passed and len(spawn_calls) >= 1:
        first_memory_ts = memory_calls[0].get("unix_ts", float("inf"))
        first_spawn_ts = spawn_calls[0].get("unix_ts", 0)
        check2_passed = first_memory_ts < first_spawn_ts
        checks.append({
            "name": "memory_search_before_spawn",
            "passed": check2_passed,
            "detail": (
                f"memory_search at t={first_memory_ts:.3f}, first sessions_spawn at t={first_spawn_ts:.3f}. "
                f"memory_search must precede all sessions_spawn calls."
            )
        })
    else:
        checks.append({
            "name": "memory_search_before_spawn",
            "passed": False,
            "detail": "Cannot verify ordering: either memory_search or sessions_spawn was never called."
        })

    # ── CHECK 3: At least 2 sessions_spawn calls (executor + reviewer) ─────────
    check3_passed = len(spawn_calls) >= 2
    checks.append({
        "name": "dual_agent_spawn",
        "passed": check3_passed,
        "detail": f"sessions_spawn called {len(spawn_calls)} time(s). Requires ≥2: one executor, one independent reviewer."
    })

    # ── CHECK 4: Executor uses opus model ──────────────────────────────────────
    if len(spawn_calls) >= 1:
        # The first spawn should be the executor (writing task → opus)
        first_spawn = spawn_calls[0]
        model_val = extract_param(first_spawn, "model")
        if model_val is None:
            model_val = ""
        model_val_lower = str(model_val).lower()
        # Accept "opus", "claude-opus", or the full model name
        executor_uses_opus = any(kw in model_val_lower for kw in ["opus", "claude-opus-4-5", "claude-opus"])
        checks.append({
            "name": "executor_uses_opus_model",
            "passed": executor_uses_opus,
            "detail": (
                f"First sessions_spawn (executor) model='{model_val}'. "
                f"Writing/creative tasks must use opus or claude-opus-4-5-thinking per the model selection guide."
            )
        })
    else:
        checks.append({
            "name": "executor_uses_opus_model",
            "passed": False,
            "detail": "No sessions_spawn calls found; cannot verify executor model."
        })

    # ── CHECK 5: Reviewer uses glm model ──────────────────────────────────────
    if len(spawn_calls) >= 2:
        # The last spawn should be the reviewer (acceptance → glm)
        reviewer_spawn = spawn_calls[-1]
        model_val = extract_param(reviewer_spawn, "model")
        if model_val is None:
            model_val = ""
        model_val_lower = str(model_val).lower()
        reviewer_uses_glm = any(kw in model_val_lower for kw in ["glm", "iflow", "glm-4", "flash", "gemini"])
        checks.append({
            "name": "reviewer_uses_glm_model",
            "passed": reviewer_uses_glm,
            "detail": (
                f"Last sessions_spawn (reviewer) model='{model_val}'. "
                f"Acceptance/review tasks must use glm (iflow/glm-4.6) to save cost per model selection guide."
            )
        })
    else:
        checks.append({
            "name": "reviewer_uses_glm_model",
            "passed": False,
            "detail": "Fewer than 2 sessions_spawn calls; cannot verify reviewer model."
        })

    # ── CHECK 6: Executor and reviewer have DIFFERENT labels ─────────────────
    if len(spawn_calls) >= 2:
        first_label = extract_param(spawn_calls[0], "label")
        last_label = extract_param(spawn_calls[-1], "label")
        labels_differ = (first_label != last_label) and (first_label is not None) and (last_label is not None)
        checks.append({
            "name": "executor_reviewer_different_labels",
            "passed": labels_differ,
            "detail": (
                f"Executor label='{first_label}', Reviewer label='{last_label}'. "
                f"The executor and reviewer must be different agents with distinct labels."
            )
        })
    else:
        checks.append({
            "name": "executor_reviewer_different_labels",
            "passed": False,
            "detail": "Fewer than 2 sessions_spawn calls; cannot verify label distinctness."
        })

    # ── CHECK 7: Executor spawn includes runTimeoutSeconds ≥ 300 ──────────────
    if len(spawn_calls) >= 1:
        first_spawn = spawn_calls[0]
        rts = extract_param(first_spawn, "runTimeoutSeconds", "run_timeout_seconds", "timeout")
        rts_ok = False
        rts_detail = f"runTimeoutSeconds='{rts}'."
        if rts is not None:
            try:
                rts_int = int(str(rts))
                rts_ok = rts_int >= 300
                rts_detail = f"runTimeoutSeconds={rts_int}. Must be ≥300 for long-running writing tasks (>30s rule)."
            except ValueError:
                rts_detail = f"runTimeoutSeconds='{rts}' is not a valid integer."
        else:
            rts_detail = "runTimeoutSeconds not found in executor spawn args. Required for tasks >30s per strict resource management rules."
        checks.append({
            "name": "executor_has_timeout",
            "passed": rts_ok,
            "detail": rts_detail
        })
    else:
        checks.append({
            "name": "executor_has_timeout",
            "passed": False,
            "detail": "No sessions_spawn calls; cannot verify runTimeoutSeconds."
        })

    # ── CHECK 8: Progress monitoring call made between executor and reviewer ──
    if len(spawn_calls) >= 2 and len(monitor_calls) >= 1:
        first_spawn_ts = spawn_calls[0].get("unix_ts", 0)
        last_spawn_ts = spawn_calls[-1].get("unix_ts", float("inf"))
        monitoring_between = any(
            first_spawn_ts < m.get("unix_ts", 0) < last_spawn_ts
            for m in monitor_calls
        )
        checks.append({
            "name": "progress_monitoring_between_spawns",
            "passed": monitoring_between,
            "detail": (
                f"Found {len(monitor_calls)} monitoring call(s) (sessions_list/sessions_history). "
                f"At least one must occur between executor spawn (t={first_spawn_ts:.3f}) "
                f"and reviewer spawn (t={last_spawn_ts:.3f})."
            )
        })
    else:
        checks.append({
            "name": "progress_monitoring_between_spawns",
            "passed": False,
            "detail": (
                f"sessions_list or sessions_history must be called between executor and reviewer spawns. "
                f"Monitor calls found: {len(monitor_calls)}, spawn calls found: {len(spawn_calls)}."
            )
        })

    # ── CHECK 9: Reviewer spawn references the review/acceptance task context ─
    if len(spawn_calls) >= 2:
        reviewer_spawn = spawn_calls[-1]
        task_text = extract_param(reviewer_spawn, "task", "description", "prompt")
        if task_text is None:
            task_text = " ".join(str(v) for v in reviewer_spawn.get("args", {}).values())
        task_text_lower = str(task_text).lower()
        review_keywords = ["review", "check", "verify", "验收", "assess", "quality", "accept", "inspect", "audit"]
        reviewer_has_review_task = any(kw in task_text_lower for kw in review_keywords)
        checks.append({
            "name": "reviewer_task_is_acceptance",
            "passed": reviewer_has_review_task,
            "detail": (
                f"Reviewer spawn task text: '{str(task_text)[:200]}'. "
                f"The reviewer agent's task must explicitly involve review/quality-check/acceptance."
            )
        })
    else:
        checks.append({
            "name": "reviewer_task_is_acceptance",
            "passed": False,
            "detail": "Fewer than 2 sessions_spawn calls; cannot verify reviewer task content."
        })

    # ── Score calculation ──────────────────────────────────────────────────────
    weights = {
        "memory_search_called": 1.0,
        "memory_search_before_spawn": 1.5,
        "dual_agent_spawn": 2.0,
        "executor_uses_opus_model": 1.5,
        "reviewer_uses_glm_model": 1.5,
        "executor_reviewer_different_labels": 1.5,
        "executor_has_timeout": 1.0,
        "progress_monitoring_between_spawns": 1.5,
        "reviewer_task_is_acceptance": 1.0,
    }
    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)
    passed = score >= 0.75 and all(
        c["passed"] for c in checks
        if c["name"] in {"dual_agent_spawn", "executor_uses_opus_model", "reviewer_uses_glm_model", "executor_reviewer_different_labels"}
    )

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()