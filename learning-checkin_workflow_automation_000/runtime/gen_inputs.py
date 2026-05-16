import os
import json
import random
import shutil
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# Create a realistic deeply nested directory structure with distractor files
dirs = [
    "company/hr/onboarding",
    "company/hr/policies",
    "company/learning/tracks",
    "company/learning/materials/week1",
    "company/learning/materials/week2",
    "company/it/scripts",
    "company/it/configs",
    "reports/2024/q1",
    "reports/2024/q2",
    "tools/legacy",
    "tools/archive",
]

for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "company/hr/onboarding/welcome_pack.txt": "Welcome to the team! Please complete the mandatory training within 30 days.",
    "company/hr/policies/remote_work.md": "# Remote Work Policy\nEmployees may work remotely up to 3 days per week.",
    "company/hr/policies/learning_budget.json": json.dumps({"annual_budget_usd": 1500, "approval_required_above": 500}),
    "company/learning/tracks/data_science.md": "# Data Science Track\n- Python basics\n- Statistics\n- ML fundamentals",
    "company/learning/tracks/leadership.md": "# Leadership Track\n- Communication\n- Decision making\n- Team dynamics",
    "company/learning/materials/week1/intro_slides.txt": "Introduction to company values and mission.",
    "company/learning/materials/week1/quiz_answers.json": json.dumps({"q1": "b", "q2": "a", "q3": "c"}),
    "company/learning/materials/week2/deep_dive.txt": "Advanced topics for week 2 of onboarding.",
    "company/it/scripts/backup.sh": "#!/bin/bash\ntar -czf /tmp/backup.tar.gz /workspace/data",
    "company/it/configs/monitoring.json": json.dumps({"interval_minutes": 5, "alert_email": "it@company.com"}),
    "reports/2024/q1/completion_rates.json": json.dumps({"total_employees": 120, "completed": 98, "rate": 0.817}),
    "reports/2024/q2/completion_rates.json": json.dumps({"total_employees": 125, "completed": 110, "rate": 0.88}),
    "tools/legacy/old_tracker.py": "# Deprecated: use new system\nprint('This tool is deprecated')",
    "tools/archive/habit_tracker_v1.json": json.dumps({"version": "1.0", "deprecated": True, "replaced_by": "learning_checkin"}),
    "README_DO_NOT_USE.txt": "This workspace is for the new learning check-in system. See IT for setup instructions.",
}

for path, content in distractor_files.items():
    fpath = workspace / path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content, encoding="utf-8")

# Clone the actual learning-checkin skill from GitHub
skill_dir = workspace / "skills" / "learning-checkin"
skill_dir.mkdir(parents=True, exist_ok=True)

# Clone the repo
import subprocess
result = subprocess.run(
    ["git", "clone", "https://github.com/daizongyu/learning-checkin.git", str(skill_dir)],
    capture_output=True, text=True
)
if result.returncode != 0:
    print(f"WARNING: git clone failed: {result.stderr}")
    # Fallback: create a minimal stub so setup_script can handle it
    (skill_dir / ".clone_failed").write_text(result.stderr)
else:
    print(f"Cloned learning-checkin to {skill_dir}")

# Create a task instructions file (NOT a hint — just context for the evaluator reference)
task_context = {
    "skill_path": str(skill_dir),
    "learning_checkin_script": str(skill_dir / "learning_checkin.py"),
    "task_id": "learning_checkin_full_workflow",
}
(workspace / "company" / "it" / "configs" / "task_meta.json").write_text(
    json.dumps(task_context, indent=2), encoding="utf-8"
)

# Create a target output file placeholder (agent must create this)
# DO NOT create setup_report.json — agent must create it

print("Workspace generation complete.")
print(f"Skill directory: {skill_dir}")