#!/usr/bin/env python3
"""
Evaluation script for the context-budgeting task.
Checks that the agent:
  1. Overwrote memory/hot/HOT_MEMORY.md with fresh, non-stale content
  2. Included all three mandatory fields: Status, Key Decision, Next Step
  3. Included substantive content from the actual pipeline session
  4. Executed gc_and_checkpoint.sh (proven by sentinel file .gc_ran)
  5. The sentinel was written AFTER the HOT_MEMORY was updated
     (mtime of .gc_ran >= mtime of HOT_MEMORY.md)
"""

import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    workspace = Path(workspace)

    hot_memory_path = workspace / "memory" / "hot" / "HOT_MEMORY.md"
    sentinel_path   = workspace / "memory" / "hot" / ".gc_ran"

    # ── Check 1: HOT_MEMORY.md exists and is not the stale original ──────────
    try:
        content = hot_memory_path.read_text(encoding="utf-8")
        is_stale = "STALE - DO NOT USE" in content or "2024-07-14" in content
        if is_stale:
            checks.append({
                "name": "hot_memory_updated",
                "passed": False,
                "detail": "HOT_MEMORY.md still contains the original stale content. Agent must overwrite it with current session checkpoint."
            })
        else:
            checks.append({
                "name": "hot_memory_updated",
                "passed": True,
                "detail": f"HOT_MEMORY.md has been updated (stale markers absent). Length: {len(content)} chars."
            })
    except FileNotFoundError:
        checks.append({
            "name": "hot_memory_updated",
            "passed": False,
            "detail": "memory/hot/HOT_MEMORY.md not found."
        })
        content = ""

    # ── Check 2: Mandatory field — Status ────────────────────────────────────
    try:
        has_status = bool(
            re.search(r'(^#{1,3}\s*Status|^\*\*Status\*\*|^Status\s*:)', content, re.IGNORECASE | re.MULTILINE)
        )
        checks.append({
            "name": "field_status_present",
            "passed": has_status,
            "detail": "Found 'Status' field in HOT_MEMORY.md." if has_status else "Missing required 'Status' field in HOT_MEMORY.md."
        })
    except Exception as e:
        checks.append({"name": "field_status_present", "passed": False, "detail": str(e)})

    # ── Check 3: Mandatory field — Key Decision ───────────────────────────────
    try:
        has_key_decision = bool(
            re.search(r'(^#{1,3}\s*Key Decision|^\*\*Key Decision\*\*|^Key Decision\s*:)', content, re.IGNORECASE | re.MULTILINE)
        )
        checks.append({
            "name": "field_key_decision_present",
            "passed": has_key_decision,
            "detail": "Found 'Key Decision' field in HOT_MEMORY.md." if has_key_decision else "Missing required 'Key Decision' field in HOT_MEMORY.md."
        })
    except Exception as e:
        checks.append({"name": "field_key_decision_present", "passed": False, "detail": str(e)})

    # ── Check 4: Mandatory field — Next Step ──────────────────────────────────
    try:
        has_next_step = bool(
            re.search(r'(^#{1,3}\s*Next Step|^\*\*Next Step\*\*|^Next Step\s*:)', content, re.IGNORECASE | re.MULTILINE)
        )
        checks.append({
            "name": "field_next_step_present",
            "passed": has_next_step,
            "detail": "Found 'Next Step' field in HOT_MEMORY.md." if has_next_step else "Missing required 'Next Step' field in HOT_MEMORY.md."
        })
    except Exception as e:
        checks.append({"name": "field_next_step_present", "passed": False, "detail": str(e)})

    # ── Check 5: Content is substantive & session-relevant ────────────────────
    try:
        # Must reference something from the actual pipeline session
        session_signals = [
            r'4[,.]8\d\d',           # record counts like 4,820,891
            r'anomal',               # anomaly model reference
            r'duplic',               # duplicate records
            r'audit',                # audit log
            r'pipeline',             # pipeline reference
            r'promoted?',            # prod promotion
            r'worker',               # worker reference
            r'fx\s*rate|currency',   # FX rates
        ]
        matched = [s for s in session_signals if re.search(s, content, re.IGNORECASE)]
        substantive = len(matched) >= 2
        checks.append({
            "name": "content_substantive_and_relevant",
            "passed": substantive,
            "detail": f"HOT_MEMORY.md references {len(matched)} session-specific signals: {matched}" if substantive
                      else f"HOT_MEMORY.md content appears generic or empty. Only {len(matched)} session signals found: {matched}"
        })
    except Exception as e:
        checks.append({"name": "content_substantive_and_relevant", "passed": False, "detail": str(e)})

    # ── Check 6: Sentinel file exists (gc_and_checkpoint.sh was run) ──────────
    try:
        sentinel_content = sentinel_path.read_text(encoding="utf-8")
        checks.append({
            "name": "gc_script_executed",
            "passed": True,
            "detail": f"Sentinel file .gc_ran found. Content: {sentinel_content.strip()[:200]}"
        })
    except FileNotFoundError:
        checks.append({
            "name": "gc_script_executed",
            "passed": False,
            "detail": (
                "Sentinel file memory/hot/.gc_ran not found. "
                "The agent must execute skills/context-budgeting/scripts/gc_and_checkpoint.sh "
                "AFTER updating HOT_MEMORY.md to finalize compaction."
            )
        })

    # ── Check 7: Ordering — HOT_MEMORY updated before gc script ran ──────────
    try:
        if not hot_memory_path.exists():
            raise FileNotFoundError("HOT_MEMORY.md missing")
        if not sentinel_path.exists():
            raise FileNotFoundError(".gc_ran missing")

        mtime_hot   = hot_memory_path.stat().st_mtime
        mtime_sent  = sentinel_path.stat().st_mtime

        # Sentinel must have been created at or after HOT_MEMORY was written
        correct_order = mtime_sent >= mtime_hot - 1.0  # 1s tolerance
        checks.append({
            "name": "correct_ordering_checkpoint_before_gc",
            "passed": correct_order,
            "detail": (
                f"HOT_MEMORY.md mtime={mtime_hot:.2f}, .gc_ran mtime={mtime_sent:.2f}. "
                + ("Script ran after checkpoint update — correct." if correct_order
                   else "Script ran BEFORE checkpoint update — mandatory ordering violated.")
            )
        })
    except FileNotFoundError as e:
        checks.append({
            "name": "correct_ordering_checkpoint_before_gc",
            "passed": False,
            "detail": f"Cannot verify ordering: {e}"
        })
    except Exception as e:
        checks.append({
            "name": "correct_ordering_checkpoint_before_gc",
            "passed": False,
            "detail": f"Ordering check error: {e}"
        })

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "hot_memory_updated":                     0.15,
        "field_status_present":                   0.15,
        "field_key_decision_present":             0.15,
        "field_next_step_present":                0.15,
        "content_substantive_and_relevant":       0.15,
        "gc_script_executed":                     0.15,
        "correct_ordering_checkpoint_before_gc":  0.10,
    }
    total_score = sum(
        weights.get(c["name"], 0.0) for c in checks if c["passed"]
    )
    all_passed = all(c["passed"] for c in checks)

    return {
        "passed": all_passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "No workspace path provided."}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))