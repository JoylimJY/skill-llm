#!/usr/bin/env python3
"""
Evaluation script for PinchBench task.

Checks:
1. benchmark.py was invoked with the correct --suite (comma-separated task IDs for the 4 required tasks)
2. --runs 3 was used (3 runs per task)
3. --no-upload was used (no leaderboard upload)
4. --timeout-multiplier 2 was used
5. Results JSON file exists in the specified output directory (benchmark_output/)
6. The JSON contains exactly the 4 required tasks
7. A summary file (benchmark_summary.json) was created with correct derived metrics
8. The summary correctly identifies tasks with score < 0.5 (failed tasks)
9. The summary includes the correct overall average
"""

import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    ws = Path(workspace)
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # -------------------------------------------------------------------------
    # The 4 required tasks for this benchmark run
    REQUIRED_TASKS = {
        "task_01_calendar",
        "task_05_summary",
        "task_19_spreadsheet_summary",
        "task_21_openclaw_comprehension",
    }
    PASSING_THRESHOLD = 0.5

    # -------------------------------------------------------------------------
    # CHECK 1: Find the results JSON in benchmark_output/ directory
    # -------------------------------------------------------------------------
    output_dir = ws / "pinchbench_skill" / "benchmark_output"
    json_files = list(output_dir.glob("*.json")) if output_dir.exists() else []
    
    # Also search recursively for any json files that look like benchmark results
    all_json = list(ws.rglob("*.json"))
    results_candidates = []
    for jf in all_json:
        # Skip the distractor old results file and summary files
        if "OLD_" in jf.name:
            continue
        if "summary" in jf.name.lower():
            continue
        if "context_store" in jf.name:
            continue
        try:
            with open(jf) as f:
                data = json.load(f)
            # Must have 'tasks' key and 'model' key to be a benchmark result
            if "tasks" in data and "model" in data and isinstance(data["tasks"], list):
                results_candidates.append((jf, data))
        except Exception:
            pass

    if not results_candidates:
        add_check("results_json_exists", False, "No benchmark results JSON file found. Expected in benchmark_output/ directory.")
    else:
        # Use the first/most-recent candidate
        results_path, results_data = results_candidates[0]
        add_check("results_json_exists", True, f"Found results file: {results_path.relative_to(ws)}")

        # -------------------------------------------------------------------------
        # CHECK 2: Correct tasks were run (exactly the 4 required tasks)
        # -------------------------------------------------------------------------
        try:
            actual_task_ids = set(t["task_id"] for t in results_data["tasks"])
            missing = REQUIRED_TASKS - actual_task_ids
            extra = actual_task_ids - REQUIRED_TASKS
            
            if missing:
                add_check("correct_tasks_run", False,
                    f"Missing required tasks: {sorted(missing)}. Actual tasks: {sorted(actual_task_ids)}")
            elif extra:
                add_check("correct_tasks_run", False,
                    f"Extra unexpected tasks in results: {sorted(extra)}. Only these 4 should have run: {sorted(REQUIRED_TASKS)}")
            else:
                add_check("correct_tasks_run", True,
                    f"Correct 4 tasks run: {sorted(actual_task_ids)}")
        except Exception as e:
            add_check("correct_tasks_run", False, f"Error reading task list: {e}")

        # -------------------------------------------------------------------------
        # CHECK 3: --runs 3 was used (3 runs per task)
        # -------------------------------------------------------------------------
        try:
            runs_per_task = results_data.get("runs_per_task", None)
            if runs_per_task == 3:
                add_check("runs_equals_3", True, f"runs_per_task = {runs_per_task} ✓")
            else:
                # Also check individual task grading runs arrays
                run_counts = [len(t["grading"]["runs"]) for t in results_data["tasks"] if "grading" in t and "runs" in t["grading"]]
                if run_counts and all(c == 3 for c in run_counts):
                    add_check("runs_equals_3", True, f"Each task has 3 runs (from grading.runs arrays) ✓")
                else:
                    add_check("runs_equals_3", False,
                        f"Expected runs_per_task=3, got runs_per_task={runs_per_task}. "
                        f"Individual run counts: {run_counts}. "
                        "The --runs 3 flag must be passed to benchmark.py.")
        except Exception as e:
            add_check("runs_equals_3", False, f"Error checking runs count: {e}")

        # -------------------------------------------------------------------------
        # CHECK 4: --no-upload was used
        # -------------------------------------------------------------------------
        try:
            metadata = results_data.get("metadata", {})
            uploaded = metadata.get("uploaded", True)  # Default True means upload happened
            if uploaded is False:
                add_check("no_upload_flag", True, "uploaded=false in metadata confirms --no-upload was used ✓")
            else:
                add_check("no_upload_flag", False,
                    "Results metadata shows uploaded=true. The --no-upload flag must be used to skip leaderboard submission.")
        except Exception as e:
            add_check("no_upload_flag", False, f"Error checking upload status: {e}")

        # -------------------------------------------------------------------------
        # CHECK 5: --timeout-multiplier 2 was used
        # -------------------------------------------------------------------------
        try:
            tm = results_data.get("timeout_multiplier", None)
            if tm == 2.0 or tm == 2:
                add_check("timeout_multiplier_2", True, f"timeout_multiplier = {tm} ✓")
            else:
                add_check("timeout_multiplier_2", False,
                    f"Expected timeout_multiplier=2.0, got {tm}. The --timeout-multiplier 2 flag must be passed.")
        except Exception as e:
            add_check("timeout_multiplier_2", False, f"Error checking timeout multiplier: {e}")

    # -------------------------------------------------------------------------
    # CHECK 6: Summary file (benchmark_summary.json) exists with correct content
    # -------------------------------------------------------------------------
    summary_candidates = list(ws.rglob("benchmark_summary.json"))
    
    if not summary_candidates:
        add_check("summary_file_exists", False,
            "benchmark_summary.json not found anywhere in workspace.")
        add_check("summary_failed_tasks_correct", False,
            "Cannot check: summary file missing.")
        add_check("summary_overall_average_correct", False,
            "Cannot check: summary file missing.")
    else:
        summary_path = summary_candidates[0]
        add_check("summary_file_exists", True,
            f"Found: {summary_path.relative_to(ws)}")
        
        try:
            with open(summary_path) as f:
                summary = json.load(f)
            
            # -------------------------------------------------------------------------
            # CHECK 7: Failed tasks (score < 0.5) correctly identified
            # -------------------------------------------------------------------------
            # From the mock benchmark.py with seed, for our 4 tasks with --runs 3 --timeout-multiplier 2:
            # task_01_calendar: base=0.72 -> passes
            # task_05_summary: base=0.43 -> fails  
            # task_19_spreadsheet_summary: base=0.76 -> passes
            # task_21_openclaw_comprehension: base=0.83 -> passes
            # So only task_05_summary should be in failed tasks
            
            # We need to check the actual results to determine ground truth
            if results_candidates:
                _, rd = results_candidates[0]
                actually_failed = sorted([
                    t["task_id"] for t in rd["tasks"]
                    if t.get("grading", {}).get("mean", 1.0) < PASSING_THRESHOLD
                ])
            else:
                # Fallback expected based on mock scores
                actually_failed = ["task_05_summary"]
            
            # Check summary has failed_tasks field
            failed_in_summary = summary.get("failed_tasks", None)
            if failed_in_summary is None:
                # Try alternative field names
                failed_in_summary = summary.get("failing_tasks",
                    summary.get("tasks_below_threshold",
                        summary.get("failed", None)))
            
            if failed_in_summary is None:
                add_check("summary_failed_tasks_correct", False,
                    f"summary JSON has no 'failed_tasks' field. Expected to list tasks with score < {PASSING_THRESHOLD}.")
            else:
                # Normalize to list of task IDs
                if isinstance(failed_in_summary, list):
                    # Could be list of strings or list of dicts
                    if failed_in_summary and isinstance(failed_in_summary[0], dict):
                        failed_ids = sorted(item.get("task_id", "") for item in failed_in_summary)
                    else:
                        failed_ids = sorted(str(x) for x in failed_in_summary)
                elif isinstance(failed_in_summary, dict):
                    failed_ids = sorted(failed_in_summary.keys())
                else:
                    failed_ids = []
                
                if failed_ids == actually_failed:
                    add_check("summary_failed_tasks_correct", True,
                        f"Failed tasks correctly identified: {failed_ids} ✓")
                else:
                    add_check("summary_failed_tasks_correct", False,
                        f"Failed tasks mismatch. Summary says: {failed_ids}, "
                        f"Expected (score < {PASSING_THRESHOLD}): {actually_failed}")
            
            # -------------------------------------------------------------------------
            # CHECK 8: Overall average is correct
            # -------------------------------------------------------------------------
            overall_in_summary = summary.get("overall_average",
                summary.get("average",
                    summary.get("mean_score",
                        summary.get("overall_mean", None))))
            
            if overall_in_summary is None:
                add_check("summary_overall_average_correct", False,
                    "summary JSON has no 'overall_average' (or 'average'/'mean_score') field.")
            else:
                try:
                    reported_avg = float(overall_in_summary)
                    
                    # Get ground truth from results
                    if results_candidates:
                        _, rd = results_candidates[0]
                        task_means = [t["grading"]["mean"] for t in rd["tasks"]]
                        true_avg = round(sum(task_means) / len(task_means), 4)
                    else:
                        true_avg = None
                    
                    if true_avg is not None:
                        # Allow 0.01 tolerance for rounding
                        if abs(reported_avg - true_avg) <= 0.01:
                            add_check("summary_overall_average_correct", True,
                                f"Overall average correct: {reported_avg:.4f} (expected ~{true_avg:.4f}) ✓")
                        else:
                            add_check("summary_overall_average_correct", False,
                                f"Overall average mismatch: summary says {reported_avg:.4f}, "
                                f"computed from results: {true_avg:.4f}")
                    else:
                        # Can't verify without results, give partial credit if it's plausible
                        if 0.0 <= reported_avg <= 1.0:
                            add_check("summary_overall_average_correct", True,
                                f"Overall average {reported_avg:.4f} is in valid range (results file not available to cross-check).")
                        else:
                            add_check("summary_overall_average_correct", False,
                                f"Overall average {reported_avg} is outside [0,1] range.")
                except (ValueError, TypeError) as e:
                    add_check("summary_overall_average_correct", False,
                        f"Could not parse overall_average as float: {overall_in_summary} — {e}")
        
        except json.JSONDecodeError as e:
            add_check("summary_failed_tasks_correct", False,
                f"benchmark_summary.json is not valid JSON: {e}")
            add_check("summary_overall_average_correct", False,
                "Cannot check: summary file is invalid JSON.")
        except Exception as e:
            add_check("summary_failed_tasks_correct", False, f"Unexpected error reading summary: {e}")
            add_check("summary_overall_average_correct", False, f"Unexpected error: {e}")

    # -------------------------------------------------------------------------
    # Final scoring
    # -------------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = all(c["passed"] for c in checks)

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return 0 if overall_passed else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    sys.exit(evaluate(sys.argv[1]))