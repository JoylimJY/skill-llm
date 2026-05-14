#!/usr/bin/env python3
import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str):
    workspace = Path(workspace)
    basedir = workspace / "project" / ".openclaw"
    logs_dir = basedir / "logs"
    scripts_dir = basedir / "scripts"
    sessions_dir = basedir / "sessions"

    checks = []
    total_score = 0.0
    max_score = 7.0

    # -----------------------------------------------------------------------
    # CHECK 1: A prompt file was created containing wake.sh callback
    # The file can be anywhere; find by searching for wake.sh content
    # -----------------------------------------------------------------------
    def check_prompt_file_with_wake():
        try:
            # Find any .txt, .md, or prompt-like file created by the agent
            candidate_files = list(workspace.rglob("*.txt")) + \
                              list(workspace.rglob("*.md")) + \
                              list(workspace.rglob("*.prompt")) + \
                              list(workspace.rglob("prompt*"))
            # Also search in /tmp
            tmp_candidates = list(Path("/tmp").glob("*.txt")) + \
                             list(Path("/tmp").glob("*.md")) + \
                             list(Path("/tmp").glob("*prompt*"))
            all_candidates = candidate_files + tmp_candidates

            wake_found = False
            valid_wake_syntax = False
            prompt_file_path = None

            for f in all_candidates:
                try:
                    content = f.read_text(errors='replace')
                    if "wake.sh" in content:
                        wake_found = True
                        prompt_file_path = str(f)
                        # Check for correct syntax: bash {something}/scripts/wake.sh "..." now
                        # Must have: bash ... wake.sh ... now
                        pattern = r'bash\s+.*scripts/wake\.sh\s+".+".*now'
                        if re.search(pattern, content):
                            valid_wake_syntax = True
                        break
                except Exception:
                    continue

            if not wake_found:
                return False, 0.0, f"No prompt file containing 'wake.sh' callback found. Searched {len(all_candidates)} files."
            if not valid_wake_syntax:
                return False, 0.5, f"Prompt file found at {prompt_file_path} contains 'wake.sh' but callback syntax is incorrect. Expected: bash .../scripts/wake.sh \"...\" now"
            return True, 1.0, f"Prompt file at {prompt_file_path} contains correct wake.sh callback with 'now' argument."
        except Exception as e:
            return False, 0.0, f"Exception during prompt file check: {e}"

    passed, score, detail = check_prompt_file_with_wake()
    checks.append({"name": "prompt_file_contains_wake_callback", "passed": passed, "detail": detail})
    total_score += score

    # -----------------------------------------------------------------------
    # CHECK 2: start-tmux-task.sh was invoked with all required flags
    # Required: --label, --workdir, --prompt-file (--task is optional per mock)
    # -----------------------------------------------------------------------
    def check_start_invocation():
        try:
            log_file = logs_dir / "start-invocations.log"
            if not log_file.exists():
                return False, 0.0, "start-tmux-task.sh was never invoked (no log file found)."

            content = log_file.read_text().strip()
            if not content:
                return False, 0.0, "start-invocations.log exists but is empty."

            lines = content.splitlines()
            last_invocation = lines[-1]

            has_label = "label=" in last_invocation and not last_invocation.split("label=")[1].startswith(" ")
            has_workdir = "workdir=" in last_invocation
            has_prompt_file = "prompt_file=" in last_invocation

            missing = []
            if not has_label:
                missing.append("--label")
            if not has_workdir:
                missing.append("--workdir")
            if not has_prompt_file:
                missing.append("--prompt-file")

            # Extract label value
            label_val = ""
            m = re.search(r'label=(\S+)', last_invocation)
            if m:
                label_val = m.group(1).split()[0]

            if missing:
                return False, 0.5, f"start-tmux-task.sh invoked but missing required flags: {missing}. Invocation: {last_invocation}"

            return True, 1.0, f"start-tmux-task.sh invoked correctly with label='{label_val}' and all required flags."
        except Exception as e:
            return False, 0.0, f"Exception checking start invocation: {e}"

    passed, score, detail = check_start_invocation()
    checks.append({"name": "start_task_invoked_correctly", "passed": passed, "detail": detail})
    total_score += score

    # -----------------------------------------------------------------------
    # CHECK 3: A session file was created by start script (implies correct execution)
    # -----------------------------------------------------------------------
    def check_session_file_created():
        try:
            session_files = list(sessions_dir.glob("*.json"))
            if not session_files:
                return False, 0.0, "No session state file found in sessions dir. start-tmux-task.sh may not have run successfully."

            session_file = session_files[0]
            data = json.loads(session_file.read_text())
            required_keys = {"label", "session", "status"}
            missing_keys = required_keys - set(data.keys())
            if missing_keys:
                return False, 0.5, f"Session file {session_file.name} missing keys: {missing_keys}"

            session_name = data.get("session", "")
            label = data.get("label", "")
            if not session_name.startswith("cc-"):
                return False, 0.5, f"Session name '{session_name}' does not follow cc-<label> convention."

            return True, 1.0, f"Session file created for label='{label}', session='{session_name}'."
        except Exception as e:
            return False, 0.0, f"Exception checking session file: {e}"

    passed, score, detail = check_session_file_created()
    checks.append({"name": "session_file_created", "passed": passed, "detail": detail})
    total_score += score

    # -----------------------------------------------------------------------
    # CHECK 4: status-tmux-task.sh was invoked with --label flag
    # -----------------------------------------------------------------------
    def check_status_invocation():
        try:
            log_file = logs_dir / "status-invocations.log"
            if not log_file.exists():
                return False, 0.0, "status-tmux-task.sh was never invoked."

            content = log_file.read_text().strip()
            if not content:
                return False, 0.0, "status-invocations.log is empty."

            if "label=" not in content:
                return False, 0.5, "status-tmux-task.sh was invoked but --label flag not provided."

            # Check that label value matches a session that was started
            session_files = list(sessions_dir.glob("*.json"))
            if session_files:
                label_in_session = json.loads(session_files[0].read_text()).get("label", "")
                if label_in_session and f"label={label_in_session}" in content:
                    return True, 1.0, f"status-tmux-task.sh correctly invoked with --label {label_in_session}."

            return True, 0.8, "status-tmux-task.sh invoked with --label flag (label value not cross-validated)."
        except Exception as e:
            return False, 0.0, f"Exception checking status invocation: {e}"

    passed, score, detail = check_status_invocation()
    checks.append({"name": "status_check_invoked", "passed": passed, "detail": detail})
    total_score += score

    # -----------------------------------------------------------------------
    # CHECK 5: complete-tmux-task.sh was invoked with --label AND --workdir
    # This triggers the completion report generation
    # -----------------------------------------------------------------------
    def check_complete_invocation():
        try:
            log_file = logs_dir / "complete-invocations.log"
            if not log_file.exists():
                return False, 0.0, "complete-tmux-task.sh was never invoked. Completion loop not executed."

            content = log_file.read_text().strip()
            if not content:
                return False, 0.0, "complete-invocations.log is empty."

            last_line = content.splitlines()[-1]
            has_label = "label=" in last_line
            has_workdir = "workdir=" in last_line

            if not has_label or not has_workdir:
                missing = []
                if not has_label: missing.append("--label")
                if not has_workdir: missing.append("--workdir")
                return False, 0.5, f"complete-tmux-task.sh invoked but missing: {missing}"

            return True, 1.0, f"complete-tmux-task.sh invoked with --label and --workdir. Invocation: {last_line}"
        except Exception as e:
            return False, 0.0, f"Exception checking complete invocation: {e}"

    passed, score, detail = check_complete_invocation()
    checks.append({"name": "complete_task_invoked_correctly", "passed": passed, "detail": detail})
    total_score += score

    # -----------------------------------------------------------------------
    # CHECK 6: Completion report JSON exists at correct path /tmp/cc-<label>-completion-report.json
    # -----------------------------------------------------------------------
    def check_completion_report_exists():
        try:
            # Find which label was used
            session_files = list(sessions_dir.glob("*.json"))
            if not session_files:
                # Try to infer from complete log
                log_file = logs_dir / "complete-invocations.log"
                if log_file.exists():
                    content = log_file.read_text()
                    m = re.search(r'label=(\S+)', content)
                    if m:
                        label = m.group(1)
                        report_path = Path(f"/tmp/cc-{label}-completion-report.json")
                        if report_path.exists():
                            return True, 1.0, f"Completion report found at {report_path}"
                return False, 0.0, "Cannot determine label to check completion report path."

            label = json.loads(session_files[0].read_text()).get("label", "")
            report_path = Path(f"/tmp/cc-{label}-completion-report.json")
            report_md_path = Path(f"/tmp/cc-{label}-completion-report.md")

            if not report_path.exists():
                return False, 0.0, f"Completion report not found at expected path: {report_path}"

            # Validate JSON structure
            data = json.loads(report_path.read_text())
            required_fields = {"label", "status", "summary", "filesModified", "testsRun", "testsPassed", "riskLevel"}
            missing = required_fields - set(data.keys())
            if missing:
                return False, 0.5, f"Report JSON at {report_path} missing fields: {missing}"

            md_note = " (MD report also present)" if report_md_path.exists() else " (MD report missing)"
            return True, 1.0, f"Completion report valid at {report_path}{md_note}. Status: {data.get('status')}"
        except Exception as e:
            return False, 0.0, f"Exception checking completion report: {e}"

    passed, score, detail = check_completion_report_exists()
    checks.append({"name": "completion_report_generated", "passed": passed, "detail": detail})
    total_score += score

    # -----------------------------------------------------------------------
    # CHECK 7: Agent produced a task_summary.json in workspace with analysis
    # derived from the completion report (mandatory deep-read + analysis step)
    # -----------------------------------------------------------------------
    def check_task_summary_json():
        try:
            summary_files = list(workspace.rglob("task_summary.json"))
            if not summary_files:
                return False, 0.0, "No task_summary.json found anywhere in workspace. Agent did not complete the analysis step."

            summary_file = summary_files[0]
            content = summary_file.read_text()
            data = json.loads(content)

            checks_inner = []

            # Must contain fields showing it read the completion report
            has_status_or_summary = any(k in data for k in ["status", "summary", "completed", "taskStatus", "completionStatus"])
            has_files_or_changes = any(k in data for k in ["filesModified", "files_modified", "changes", "modifiedFiles"])
            has_risk = any(k in data for k in ["riskLevel", "risk_level", "risk", "riskAssessment"])
            has_next_steps = any(k in data for k in ["nextSteps", "next_steps", "recommendations", "nextActions"])
            has_label = any(k in data for k in ["label", "taskLabel", "task_label", "taskName"])

            score_inner = 0.0
            details_inner = []

            if has_status_or_summary:
                score_inner += 0.25
                details_inner.append("has status/summary field")
            else:
                details_inner.append("MISSING status/summary field")

            if has_files_or_changes:
                score_inner += 0.25
                details_inner.append("has files/changes field")
            else:
                details_inner.append("MISSING files/changes field")

            if has_risk:
                score_inner += 0.25
                details_inner.append("has risk field")
            else:
                details_inner.append("MISSING risk field")

            if has_next_steps:
                score_inner += 0.25
                details_inner.append("has next_steps field")
            else:
                details_inner.append("MISSING next_steps field")

            passed_inner = score_inner >= 0.75
            detail_str = f"task_summary.json at {summary_file}: {'; '.join(details_inner)}"
            return passed_inner, score_inner, detail_str
        except json.JSONDecodeError as e:
            return False, 0.0, f"task_summary.json found but invalid JSON: {e}"
        except Exception as e:
            return False, 0.0, f"Exception checking task_summary.json: {e}"

    passed, score, detail = check_task_summary_json()
    checks.append({"name": "task_summary_json_produced", "passed": passed, "detail": detail})
    total_score += score

    # -----------------------------------------------------------------------
    # Final scoring
    # -----------------------------------------------------------------------
    final_score = round(total_score / max_score, 4)
    all_passed = all(c["passed"] for c in checks)

    result = {
        "passed": all_passed and final_score >= 0.80,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_path)