#!/usr/bin/env python3
"""
Evaluation script for the Claude Code Orchestrator task.
Usage: python3 eval.py <workspace_dir>
"""

import sys
import json
import os
import re
from pathlib import Path

def load_invocation_log():
    """Read the invocation log written by mock scripts."""
    log_path = Path("/tmp/skill_invocations.log")
    if not log_path.exists():
        return []
    return log_path.read_text().splitlines()

def check_start_invoked_correctly(lines):
    """
    Check that start-tmux-task.sh was called with all required flags:
    --label, --workdir, --prompt-file, --task
    """
    for line in lines:
        if "start-tmux-task.sh" in line:
            has_label = "--label=" in line and re.search(r"--label=\S+", line)
            has_workdir = "--workdir=" in line and re.search(r"--workdir=\S+", line)
            has_prompt_file = "--prompt-file=" in line and re.search(r"--prompt-file=\S+", line)
            has_task = "--task=" in line
            if has_label and has_workdir and has_prompt_file:
                return True, line
    return False, None

def extract_label_from_log(lines):
    """Extract the --label value used in start-tmux-task.sh call."""
    for line in lines:
        if "start-tmux-task.sh" in line:
            m = re.search(r"--label=([^\s]+)", line)
            if m:
                return m.group(1)
    return None

def check_prompt_file_has_wake(lines, workspace):
    """
    Check that the prompt file passed to start-tmux-task.sh contains the 
    mandatory wake.sh callback: bash {baseDir}/scripts/wake.sh "..." now
    """
    # Find the prompt file path from the start call
    for line in lines:
        if "start-tmux-task.sh" in line:
            m = re.search(r"--prompt-file=(\S+)", line)
            if m:
                pf = Path(m.group(1))
                if pf.exists():
                    content = pf.read_text()
                    # Must contain wake.sh and the timing word "now"
                    has_wake = "wake.sh" in content
                    has_now = bool(re.search(r"wake\.sh.*now", content, re.DOTALL))
                    return has_wake, has_now, str(pf), content
    return False, False, None, None

def check_status_checked(lines, label):
    """Check that status-tmux-task.sh was called with the correct label."""
    for line in lines:
        if "status-tmux-task.sh" in line:
            if label and f"--label={label}" in line:
                return True, line
            elif "status-tmux-task.sh" in line:
                # Accept any label in status check
                return True, line
    return False, None

def check_complete_invoked(lines, label):
    """
    Check that complete-tmux-task.sh was called with --label and --workdir.
    This is the mandatory fallback/completion path.
    """
    for line in lines:
        if "complete-tmux-task.sh" in line:
            has_label = "--label=" in line
            has_workdir = "--workdir=" in line
            if has_label and has_workdir:
                return True, line
            elif has_label:
                return True, line
    return False, None

def check_report_read_and_analysis_written(workspace, label):
    """
    Check that the agent read the completion report and wrote a task_analysis.json
    file somewhere in the workspace.
    """
    # Look for task_analysis.json anywhere in workspace
    workspace_path = Path(workspace)
    analysis_files = list(workspace_path.rglob("task_analysis.json"))
    
    if not analysis_files:
        return False, "task_analysis.json not found anywhere in workspace", None
    
    # Read the first one found
    analysis_file = analysis_files[0]
    try:
        content = analysis_file.read_text()
        data = json.loads(content)
    except json.JSONDecodeError as e:
        return False, f"task_analysis.json is not valid JSON: {e}", None
    except Exception as e:
        return False, f"Could not read task_analysis.json: {e}", None
    
    return True, str(analysis_file), data

def check_analysis_content(data):
    """
    Check that the task_analysis.json contains substantive content derived
    from the completion report (not just a placeholder).
    Required: references to the label/task, completed status, at least some 
    risk or next-step content.
    """
    if not isinstance(data, dict):
        return False, "task_analysis.json must be a JSON object"
    
    content_str = json.dumps(data).lower()
    
    checks = []
    
    # Must reference the label or the task description
    has_label_ref = (
        "factor-model-refactor" in content_str or 
        "factor_model" in content_str or
        "factor model" in content_str or
        "fama" in content_str
    )
    checks.append(("references_task", has_label_ref))
    
    # Must have a status/completion field
    has_status = any(k in data for k in ["status", "completion_status", "completed", "state"])
    checks.append(("has_status_field", has_status))
    
    # Must reference risks OR next_steps (from the report)
    has_risks_or_steps = (
        "risk" in content_str or 
        "next" in content_str or 
        "test" in content_str or
        "scipy" in content_str
    )
    checks.append(("has_risks_or_steps", has_risks_or_steps))
    
    # Must reference what files were modified (from the report)
    has_files = (
        "factor_model.py" in content_str or
        "files_modified" in content_str or
        "filesmodified" in content_str or
        "modified" in content_str
    )
    checks.append(("references_modified_files", has_files))
    
    passed = sum(1 for _, v in checks if v)
    all_pass = passed >= 3  # At least 3 of 4 substantive checks
    detail = f"Content checks passed: {passed}/4 — {checks}"
    return all_pass, detail

def check_list_tasks_used(lines):
    """Bonus: check if list-tasks.sh --json was used for structured introspection."""
    for line in lines:
        if "list-tasks.sh" in line:
            return True, line
    return False, None


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    workspace = sys.argv[1]
    checks = []
    
    # Load invocation log
    invocation_lines = load_invocation_log()

    # ---- CHECK 1: start-tmux-task.sh called with required flags ----
    try:
        ok, match_line = check_start_invoked_correctly(invocation_lines)
        checks.append({
            "name": "start_task_invoked_with_all_required_flags",
            "passed": ok,
            "detail": f"Match: {match_line}" if ok else 
                      f"start-tmux-task.sh not called with --label, --workdir, --prompt-file. Log lines: {invocation_lines[:10]}"
        })
    except Exception as e:
        checks.append({"name": "start_task_invoked_with_all_required_flags", "passed": False, "detail": str(e)})

    # ---- CHECK 2: prompt file contains wake.sh callback with "now" ----
    label = extract_label_from_log(invocation_lines)
    try:
        has_wake, has_now, pf_path, pf_content = check_prompt_file_has_wake(invocation_lines, workspace)
        wake_ok = has_wake and has_now
        checks.append({
            "name": "prompt_file_contains_wake_sh_callback_with_now",
            "passed": wake_ok,
            "detail": (
                f"Prompt file {pf_path}: wake.sh={has_wake}, 'now' timing={has_now}" if pf_path
                else "Could not find prompt file path in invocation log"
            )
        })
    except Exception as e:
        checks.append({"name": "prompt_file_contains_wake_sh_callback_with_now", "passed": False, "detail": str(e)})

    # ---- CHECK 3: status-tmux-task.sh was called ----
    try:
        ok, match_line = check_status_checked(invocation_lines, label)
        checks.append({
            "name": "status_check_performed",
            "passed": ok,
            "detail": f"Match: {match_line}" if ok else "status-tmux-task.sh not found in invocation log"
        })
    except Exception as e:
        checks.append({"name": "status_check_performed", "passed": False, "detail": str(e)})

    # ---- CHECK 4: complete-tmux-task.sh called with label + workdir ----
    try:
        ok, match_line = check_complete_invoked(invocation_lines, label)
        checks.append({
            "name": "completion_script_invoked_with_label_and_workdir",
            "passed": ok,
            "detail": f"Match: {match_line}" if ok else 
                      "complete-tmux-task.sh not called or missing required flags"
        })
    except Exception as e:
        checks.append({"name": "completion_script_invoked_with_label_and_workdir", "passed": False, "detail": str(e)})

    # ---- CHECK 5: completion report exists (generated by complete-tmux-task.sh) ----
    try:
        if label:
            report_path = Path(f"/tmp/cc-{label}-completion-report.json")
        else:
            # Try to find any report
            import glob
            reports = glob.glob("/tmp/cc-*-completion-report.json")
            report_path = Path(reports[0]) if reports else Path("/tmp/no-report")
        
        report_exists = report_path.exists()
        checks.append({
            "name": "completion_report_json_exists",
            "passed": report_exists,
            "detail": f"Report at {report_path}: exists={report_exists}"
        })
    except Exception as e:
        checks.append({"name": "completion_report_json_exists", "passed": False, "detail": str(e)})

    # ---- CHECK 6: task_analysis.json written to workspace ----
    try:
        ok, detail, analysis_data = check_report_read_and_analysis_written(workspace, label)
        checks.append({
            "name": "task_analysis_json_written_to_workspace",
            "passed": ok,
            "detail": detail
        })
    except Exception as e:
        checks.append({"name": "task_analysis_json_written_to_workspace", "passed": False, "detail": str(e)})
        analysis_data = None

    # ---- CHECK 7: task_analysis.json has substantive content from report ----
    try:
        if analysis_data is not None:
            ok, detail = check_analysis_content(analysis_data)
        else:
            ok, detail = False, "No analysis data to check (file missing or invalid)"
        checks.append({
            "name": "task_analysis_content_reflects_completion_report",
            "passed": ok,
            "detail": detail
        })
    except Exception as e:
        checks.append({"name": "task_analysis_content_reflects_completion_report", "passed": False, "detail": str(e)})

    # ---- CHECK 8 (bonus): list-tasks.sh --json used for structured introspection ----
    try:
        ok, match_line = check_list_tasks_used(invocation_lines)
        checks.append({
            "name": "list_tasks_json_used_for_introspection",
            "passed": ok,
            "detail": f"Match: {match_line}" if ok else "list-tasks.sh not found in invocation log"
        })
    except Exception as e:
        checks.append({"name": "list_tasks_json_used_for_introspection", "passed": False, "detail": str(e)})

    # ---- Scoring ----
    # Checks 1-7 are mandatory (weight 1.0 each), check 8 is bonus (0.5)
    mandatory = checks[:7]
    bonus = checks[7:]
    
    mandatory_passed = sum(1 for c in mandatory if c["passed"])
    bonus_passed = sum(0.5 for c in bonus if c["passed"])
    
    total_weight = len(mandatory) + 0.5 * len(bonus)
    score = (mandatory_passed + bonus_passed) / total_weight
    
    # Must pass at least 5/7 mandatory to overall pass
    overall_passed = mandatory_passed >= 5 and score >= 0.6

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()