import sys
import json
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
home = Path(os.path.expanduser("~"))
loop_dir = home / "loop"

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

# ── CHECK 1: Directory structure created ────────────────────────────────────
try:
    history_dir = loop_dir / "history"
    dir_ok = loop_dir.is_dir() and history_dir.is_dir()
    check(
        "loop_directory_structure_created",
        dir_ok,
        f"~/loop exists: {loop_dir.is_dir()}, ~/loop/history exists: {history_dir.is_dir()}"
    )
except Exception as e:
    check("loop_directory_structure_created", False, f"Exception: {e}")

# ── CHECK 2: active.json or history file exists (loop was initialized) ───────
try:
    active_json = loop_dir / "active.json"
    history_files = list((loop_dir / "history").glob("*.json")) if (loop_dir / "history").is_dir() else []
    
    loop_was_initialized = active_json.exists() or len(history_files) > 0
    check(
        "loop_initialized_with_json",
        loop_was_initialized,
        f"active.json exists: {active_json.exists()}, history files: {[f.name for f in history_files]}"
    )
except Exception as e:
    check("loop_initialized_with_json", False, f"Exception: {e}")

# ── CHECK 3: History file contains multiple iterations ───────────────────────
try:
    history_dir = loop_dir / "history"
    history_files = list(history_dir.glob("*.json")) if history_dir.is_dir() else []
    
    if not history_files:
        check("history_contains_iterations", False, "No history JSON files found in ~/loop/history/")
    else:
        # Try to find a file that contains iteration records
        found_iterations = False
        iteration_count = 0
        best_file = None
        
        for hf in history_files:
            try:
                content = json.loads(hf.read_text())
                # Could be a list of iterations or a dict with iterations key
                if isinstance(content, list):
                    # Each element might be an iteration
                    if len(content) >= 2:
                        found_iterations = True
                        iteration_count = len(content)
                        best_file = hf.name
                        break
                elif isinstance(content, dict):
                    # Check for iterations array
                    for key in ["iterations", "attempts", "history", "log"]:
                        if key in content and isinstance(content[key], list) and len(content[key]) >= 2:
                            found_iterations = True
                            iteration_count = len(content[key])
                            best_file = hf.name
                            break
                    if found_iterations:
                        break
            except Exception:
                continue
        
        check(
            "history_contains_iterations",
            found_iterations,
            f"Found {iteration_count} iterations in {best_file}" if found_iterations else
            f"Files present ({[f.name for f in history_files]}) but no multi-iteration records found"
        )
except Exception as e:
    check("history_contains_iterations", False, f"Exception: {e}")

# ── CHECK 4: Iteration count respects max_iterations=7 (≤7, >0) ─────────────
try:
    history_dir = loop_dir / "history"
    history_files = list(history_dir.glob("*.json")) if history_dir.is_dir() else []
    
    max_iterations_respected = False
    detail_msg = "No history files found"
    
    for hf in history_files:
        try:
            content = json.loads(hf.read_text())
            iters = None
            
            if isinstance(content, list):
                iters = content
            elif isinstance(content, dict):
                for key in ["iterations", "attempts", "history", "log"]:
                    if key in content and isinstance(content[key], list):
                        iters = content[key]
                        break
                # Also check top-level iteration_count or max_iterations fields
                if iters is None:
                    # Maybe it's a flat dict with iteration_number
                    pass
            
            if iters is not None:
                n = len(iters)
                # Must be <= 7 (the task-specified max) and > 0
                # Also must be <= 10 (the skill's hard limit)
                if 0 < n <= 7:
                    max_iterations_respected = True
                    detail_msg = f"Found {n} iterations in {hf.name} — within the specified max of 7"
                    break
                elif n > 10:
                    detail_msg = f"Found {n} iterations — VIOLATES hard limit of 10"
                elif n > 7:
                    detail_msg = f"Found {n} iterations — exceeds specified max of 7 (allowed up to 10 by hard limit, but task said 7)"
                    # Partial credit: still within hard limit
                    max_iterations_respected = (n <= 10)
                    break
        except Exception:
            continue
    
    check(
        "max_iterations_respected",
        max_iterations_respected,
        detail_msg
    )
except Exception as e:
    check("max_iterations_respected", False, f"Exception: {e}")

# ── CHECK 5: Each iteration records what failed (failure logging) ─────────────
try:
    history_dir = loop_dir / "history"
    history_files = list(history_dir.glob("*.json")) if history_dir.is_dir() else []
    
    has_failure_logging = False
    detail_msg = "No history files"
    
    failure_keywords = ["fail", "error", "not converge", "convergence", "exit", "attempt", "reason", "result", "status"]
    
    for hf in history_files:
        try:
            raw = hf.read_text().lower()
            matches = sum(1 for kw in failure_keywords if kw in raw)
            if matches >= 2:
                has_failure_logging = True
                detail_msg = f"{hf.name} contains {matches} failure-related keywords"
                break
        except Exception:
            continue
    
    # Also check learnings.md
    learnings = loop_dir / "learnings.md"
    if not has_failure_logging and learnings.exists():
        raw = learnings.read_text().lower()
        matches = sum(1 for kw in failure_keywords if kw in raw)
        if matches >= 2:
            has_failure_logging = True
            detail_msg = f"learnings.md contains {matches} failure-related keywords"
    
    check("failure_details_logged_per_iteration", has_failure_logging, detail_msg)
except Exception as e:
    check("failure_details_logged_per_iteration", False, f"Exception: {e}")

# ── CHECK 6: Failure summary produced (max reached without success) ───────────
try:
    # The scoring script always fails, so agent must produce a summary
    # Look for summary in: history json, learnings.md, or any file in loop/
    summary_found = False
    detail_msg = "No failure summary found"
    
    summary_keywords = [
        "summary", "all attempt", "common fail", "manual intervention",
        "recommend", "pattern", "exhausted", "max", "could not", "did not converge",
        "debrief", "conclusion"
    ]
    
    # Check all files in ~/loop/
    for fpath in loop_dir.rglob("*"):
        if fpath.is_file():
            try:
                raw = fpath.read_text().lower()
                matches = sum(1 for kw in summary_keywords if kw in raw)
                if matches >= 2:
                    summary_found = True
                    detail_msg = f"Summary found in {fpath.relative_to(loop_dir)} with {matches} summary keywords"
                    break
            except Exception:
                continue
    
    check("failure_summary_produced", summary_found, detail_msg)
except Exception as e:
    check("failure_summary_produced", False, f"Exception: {e}")

# ── CHECK 7: learnings.md updated with cross-loop patterns ───────────────────
try:
    learnings = loop_dir / "learnings.md"
    
    if not learnings.exists():
        check("learnings_md_updated", False, "~/loop/learnings.md does not exist")
    else:
        content = learnings.read_text().strip()
        if len(content) < 30:
            check("learnings_md_updated", False, f"learnings.md exists but is nearly empty ({len(content)} chars)")
        else:
            check("learnings_md_updated", True, f"learnings.md has {len(content)} chars of cross-loop patterns")
except Exception as e:
    check("learnings_md_updated", False, f"Exception: {e}")

# ── CHECK 8: Loop record moved/archived to history (not stuck in active) ─────
try:
    active_json = loop_dir / "active.json"
    history_files = list((loop_dir / "history").glob("*.json")) if (loop_dir / "history").is_dir() else []
    
    # After completion (max reached), active loop should be gone or empty,
    # and history should have the completed record
    if active_json.exists():
        try:
            active_data = json.loads(active_json.read_text())
            # active.json might be empty dict/list or contain completed loops
            if isinstance(active_data, dict) and len(active_data) == 0:
                active_empty = True
            elif isinstance(active_data, list) and len(active_data) == 0:
                active_empty = True
            else:
                active_empty = False
        except Exception:
            active_empty = False
        
        if active_empty and len(history_files) > 0:
            check("loop_archived_to_history", True, "active.json is empty and history files exist")
        elif len(history_files) > 0:
            check("loop_archived_to_history", True,
                  f"History has {len(history_files)} file(s); active.json present but loop completion logged in history")
        else:
            check("loop_archived_to_history", False, "active.json still has data but no history files found")
    else:
        if len(history_files) > 0:
            check("loop_archived_to_history", True,
                  f"active.json gone and {len(history_files)} history file(s) present")
        else:
            check("loop_archived_to_history", False, "No active.json and no history files")
except Exception as e:
    check("loop_archived_to_history", False, f"Exception: {e}")

# ── Final scoring ─────────────────────────────────────────────────────────────
passed_count = sum(1 for c in checks if c["passed"])
total = len(checks)
score = round(passed_count / total, 4)
overall_passed = passed_count >= 6  # Must pass at least 6/8 checks

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))