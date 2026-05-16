import sys
import json
import subprocess
import re
from pathlib import Path
from datetime import datetime

workspace = Path(sys.argv[1])
project_dir = workspace / "genomics-pipeline"

checks = []

def add_check(name: str, passed: bool, detail: str):
    checks.append({"name": name, "passed": passed, "detail": detail})

# ── CHECK 1: task.json — task-5 must be passes:true, others unchanged ─────────
try:
    task_json_path = project_dir / "task.json"
    task_data = json.loads(task_json_path.read_text())
    tasks_by_id = {t["id"]: t for t in task_data["tasks"]}

    # task-5 must be marked passes: true
    task5 = tasks_by_id.get("task-5", {})
    task5_passed = task5.get("passes") is True
    add_check(
        "task-5 marked passes:true in task.json",
        task5_passed,
        f"task-5 passes={task5.get('passes')} (expected True)" if not task5_passed else "Correct"
    )

    # No other previously-false task should have been changed to true
    should_still_be_false = ["task-4", "task-6", "task-7"]
    wrongly_completed = [tid for tid in should_still_be_false if tasks_by_id.get(tid, {}).get("passes") is True]
    add_check(
        "No blocked tasks (task-4/6/7) prematurely marked passes:true",
        len(wrongly_completed) == 0,
        f"Wrongly completed tasks: {wrongly_completed}" if wrongly_completed else "Correct"
    )

    # Previously-true tasks remain true
    should_still_be_true = ["task-1", "task-2", "task-3"]
    wrongly_reset = [tid for tid in should_still_be_true if tasks_by_id.get(tid, {}).get("passes") is not True]
    add_check(
        "Previously completed tasks (task-1/2/3) remain passes:true",
        len(wrongly_reset) == 0,
        f"Wrongly reset tasks: {wrongly_reset}" if wrongly_reset else "Correct"
    )

    # 'passes' field must exist (not renamed to e.g. 'completed', 'done', 'status')
    all_have_passes = all("passes" in t for t in task_data["tasks"])
    add_check(
        "All tasks use 'passes' field (not renamed)",
        all_have_passes,
        "All tasks have 'passes' key" if all_have_passes else "Some tasks missing 'passes' key"
    )

except Exception as e:
    add_check("task.json readable and valid", False, f"Exception: {e}")

# ── CHECK 2: progress.txt — new entry(ies) appended with correct format ───────
try:
    progress_path = project_dir / "progress.txt"
    progress_text = progress_path.read_text()
    lines = [l.strip() for l in progress_text.splitlines() if l.strip()]

    # Format: [YYYY-MM-DD HH:MM:SS] some text
    timestamp_pattern = re.compile(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] .+')

    # All lines must match the format
    malformed = [l for l in lines if not timestamp_pattern.match(l)]
    add_check(
        "All progress.txt lines match [YYYY-MM-DD HH:MM:SS] format",
        len(malformed) == 0,
        f"Malformed lines: {malformed[:3]}" if malformed else "All lines correctly formatted"
    )

    # There must be MORE lines than the original 9
    original_line_count = 9
    new_lines = [l for l in lines if l not in [
        "[2024-03-10 09:00:00] Started session",
        "[2024-03-10 09:05:00] Initialized project directory and git repository",
        "[2024-03-10 09:10:00] Completed task: Download and index reference genome (task-1)",
        "[2024-03-10 09:11:00] Committed: task-1 complete",
        "[2024-03-10 09:30:00] Started session",
        "[2024-03-10 09:35:00] Completed task: Run FastQC quality control (task-2)",
        "[2024-03-10 09:36:00] Committed: task-2 complete",
        "[2024-03-10 09:55:00] Started session",
        "[2024-03-10 10:00:00] Completed task: Trim adapter sequences using Trimmomatic (task-3)",
        "[2024-03-10 10:01:00] Committed: task-3 complete",
    ]]
    add_check(
        "New entries appended to progress.txt",
        len(new_lines) >= 1,
        f"Found {len(new_lines)} new line(s): {new_lines[:3]}" if new_lines else "No new entries found"
    )

    # New entries must mention task-5 or multiqc (case-insensitive)
    task5_mentioned = any(
        re.search(r'task-5|multiqc|multi.?qc|qc.*report|aggregate.*report', l, re.IGNORECASE)
        for l in new_lines
    )
    add_check(
        "progress.txt new entry references task-5 or MultiQC work",
        task5_mentioned,
        f"New lines: {new_lines[:5]}" if not task5_mentioned else "task-5/MultiQC reference found"
    )

except Exception as e:
    add_check("progress.txt readable and valid", False, f"Exception: {e}")

# ── CHECK 3: Output artifact created for task-5 ───────────────────────────────
try:
    # task-5 requires: results/reports/multiqc_report.html
    multiqc_report = project_dir / "results" / "reports" / "multiqc_report.html"
    artifact_exists = multiqc_report.exists()
    add_check(
        "Task-5 output artifact exists: results/reports/multiqc_report.html",
        artifact_exists,
        f"File found at {multiqc_report}" if artifact_exists else f"File not found: {multiqc_report}"
    )
    if artifact_exists:
        size = multiqc_report.stat().st_size
        add_check(
            "multiqc_report.html is non-empty",
            size > 0,
            f"File size: {size} bytes"
        )
except Exception as e:
    add_check("Output artifact check", False, f"Exception: {e}")

# ── CHECK 4: Git commit made after task-5 work ────────────────────────────────
try:
    result = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=project_dir, capture_output=True, text=True, check=True
    )
    log_lines = [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]

    # Must have MORE than the 1 initial commit
    add_check(
        "New git commit exists after initial scaffold commit",
        len(log_lines) > 1,
        f"Total commits: {len(log_lines)}. Log: {log_lines[:3]}"
    )

    # Most recent commit message should reference task-5
    if len(log_lines) > 1:
        latest_msg = log_lines[0]
        task5_in_commit = bool(re.search(r'task-5|multiqc|multi.?qc|qc.*report', latest_msg, re.IGNORECASE))
        add_check(
            "Latest git commit message references task-5 or MultiQC",
            task5_in_commit,
            f"Latest commit: '{latest_msg}'"
        )
    else:
        add_check("Latest git commit message references task-5 or MultiQC", False, "No new commits found")

    # Verify task.json and progress.txt are included in the new commit
    if len(log_lines) > 1:
        diff_result = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=project_dir, capture_output=True, text=True, check=True
        )
        changed_files = diff_result.stdout.strip()
        task_json_committed = "task.json" in changed_files
        progress_committed = "progress.txt" in changed_files
        add_check(
            "task.json committed in latest git commit",
            task_json_committed,
            f"Files in HEAD: {changed_files[:200]}"
        )
        add_check(
            "progress.txt committed in latest git commit",
            progress_committed,
            f"Files in HEAD: {changed_files[:200]}"
        )

except Exception as e:
    add_check("Git commit check", False, f"Exception: {e}")

# ── SCORE ─────────────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = all(c["passed"] for c in checks)

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, indent=2))