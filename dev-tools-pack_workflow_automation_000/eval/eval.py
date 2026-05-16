import sys
import json
import os
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace = Path(workspace)

    # --- Check 1: thread_draft_professional.txt exists ---
    prof_files = list(workspace.rglob("thread_draft_professional.txt"))
    has_prof = len(prof_files) > 0
    checks.append({
        "name": "thread_draft_professional.txt exists",
        "passed": has_prof,
        "detail": f"Found at: {prof_files[0]}" if has_prof else "File not found anywhere in workspace."
    })

    # --- Check 2: thread_draft_casual.txt exists ---
    casual_files = list(workspace.rglob("thread_draft_casual.txt"))
    has_casual = len(casual_files) > 0
    checks.append({
        "name": "thread_draft_casual.txt exists",
        "passed": has_casual,
        "detail": f"Found at: {casual_files[0]}" if has_casual else "File not found anywhere in workspace."
    })

    # --- Check 3: professional draft contains thread structure markers ---
    prof_has_structure = False
    prof_detail = "File missing, could not check."
    if has_prof:
        try:
            content = prof_files[0].read_text(errors="replace")
            markers = [
                "🧵 THREAD:",
                "(n=1)",
                "(n=2)",
                "(n=3)",
                "Thread Summary",
                "| Tweets |",
                "Suggested Hashtags",
            ]
            missing = [m for m in markers if m not in content]
            if not missing:
                prof_has_structure = True
                prof_detail = "All required structural markers present."
            else:
                prof_detail = f"Missing markers: {missing}"
        except Exception as e:
            prof_detail = f"Error reading file: {e}"
    checks.append({
        "name": "professional draft has full thread structure",
        "passed": prof_has_structure,
        "detail": prof_detail
    })

    # --- Check 4: casual draft contains thread structure markers ---
    casual_has_structure = False
    casual_detail = "File missing, could not check."
    if has_casual:
        try:
            content = casual_files[0].read_text(errors="replace")
            markers = [
                "🧵 THREAD:",
                "(n=1)",
                "(n=2)",
                "(n=3)",
                "Thread Summary",
                "| Tweets |",
                "Suggested Hashtags",
            ]
            missing = [m for m in markers if m not in content]
            if not missing:
                casual_has_structure = True
                casual_detail = "All required structural markers present."
            else:
                casual_detail = f"Missing markers: {missing}"
        except Exception as e:
            casual_detail = f"Error reading file: {e}"
    checks.append({
        "name": "casual draft has full thread structure",
        "passed": casual_has_structure,
        "detail": casual_detail
    })

    # --- Check 5: professional draft was generated from 'file' source mode ---
    # Evidence: the output line "📝 Generating thread from: file" must appear
    prof_file_mode = False
    prof_file_detail = "File missing, could not check."
    if has_prof:
        try:
            content = prof_files[0].read_text(errors="replace")
            if "Generating thread from: file" in content:
                prof_file_mode = True
                prof_file_detail = "Correct 'file' source mode detected in output."
            else:
                prof_file_detail = (
                    "Output does not contain 'Generating thread from: file'. "
                    "Agent may have used 'text' mode or incorrect invocation."
                )
        except Exception as e:
            prof_file_detail = f"Error reading file: {e}"
    checks.append({
        "name": "professional draft used 'file' source mode",
        "passed": prof_file_mode,
        "detail": prof_file_detail
    })

    # --- Check 6: casual draft was generated from 'text' source mode ---
    casual_text_mode = False
    casual_text_detail = "File missing, could not check."
    if has_casual:
        try:
            content = casual_files[0].read_text(errors="replace")
            if "Generating thread from: text" in content:
                casual_text_mode = True
                casual_text_detail = "Correct 'text' source mode detected in output."
            else:
                casual_text_detail = (
                    "Output does not contain 'Generating thread from: text'. "
                    "Agent may have used wrong source mode."
                )
        except Exception as e:
            casual_text_detail = f"Error reading file: {e}"
    checks.append({
        "name": "casual draft used 'text' source mode",
        "passed": casual_text_mode,
        "detail": casual_text_detail
    })

    # --- Check 7: professional draft contains "✅ Thread generated!" success marker ---
    prof_success = False
    prof_success_detail = "File missing."
    if has_prof:
        try:
            content = prof_files[0].read_text(errors="replace")
            if "Thread generated!" in content:
                prof_success = True
                prof_success_detail = "Success marker present."
            else:
                prof_success_detail = "Success marker '✅ Thread generated!' not found. Script may not have run to completion."
        except Exception as e:
            prof_success_detail = f"Error: {e}"
    checks.append({
        "name": "professional draft: script ran to completion",
        "passed": prof_success,
        "detail": prof_success_detail
    })

    # --- Check 8: casual draft contains "✅ Thread generated!" success marker ---
    casual_success = False
    casual_success_detail = "File missing."
    if has_casual:
        try:
            content = casual_files[0].read_text(errors="replace")
            if "Thread generated!" in content:
                casual_success = True
                casual_success_detail = "Success marker present."
            else:
                casual_success_detail = "Success marker '✅ Thread generated!' not found."
        except Exception as e:
            casual_success_detail = f"Error: {e}"
    checks.append({
        "name": "casual draft: script ran to completion",
        "passed": casual_success,
        "detail": casual_success_detail
    })

    # --- Check 9: professional draft contains the metrics table row for engagement rate ---
    prof_metrics = False
    prof_metrics_detail = "File missing."
    if has_prof:
        try:
            content = prof_files[0].read_text(errors="replace")
            if "Engagement Rate" in content and "3-5%" in content:
                prof_metrics = True
                prof_metrics_detail = "Engagement Rate row found in metrics table."
            else:
                prof_metrics_detail = "Metrics table row for 'Engagement Rate | ~3-5%' not found."
        except Exception as e:
            prof_metrics_detail = f"Error: {e}"
    checks.append({
        "name": "professional draft contains full metrics table",
        "passed": prof_metrics,
        "detail": prof_metrics_detail
    })

    # --- Check 10: The two output files are distinct (not copies of each other) ---
    # Since the script output is deterministic, this mainly checks that both were generated separately.
    # We just verify both exist and both are non-empty.
    both_nonempty = False
    both_nonempty_detail = "One or both files missing."
    if has_prof and has_casual:
        try:
            p_size = prof_files[0].stat().st_size
            c_size = casual_files[0].stat().st_size
            if p_size > 100 and c_size > 100:
                both_nonempty = True
                both_nonempty_detail = f"Both files non-empty: professional={p_size}B, casual={c_size}B."
            else:
                both_nonempty_detail = f"One or both files too small: professional={p_size}B, casual={c_size}B."
        except Exception as e:
            both_nonempty_detail = f"Error: {e}"
    checks.append({
        "name": "both output files are non-empty",
        "passed": both_nonempty,
        "detail": both_nonempty_detail
    })

    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)
    overall_passed = score >= 0.8

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)