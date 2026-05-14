#!/usr/bin/env python3
"""
Generate the sandbox workspace for the onedrive-integration eval task.
"""
import os
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── 1. Create the skill directory structure ──────────────────────────────────
SKILL_DIR = Path.home() / ".openclaw" / "skills" / "onedrive-integration"
SCRIPTS_DIR = SKILL_DIR / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# config.env.example (do NOT create config.env — agent must do that)
(SKILL_DIR / "config.env.example").write_text(textwrap.dedent("""\
    # Copy this file to config.env and fill in your values.
    # ONEDRIVE_ROOT is required.
    # ONEDRIVE_SUBDIR defaults to 'openclaw' if not set.
    ONEDRIVE_ROOT=/mnt/c/Users/YourWindowsUser/OneDrive
    # ONEDRIVE_SUBDIR=openclaw
"""))

# The canonical copy_to_onedrive.py script
copy_script = textwrap.dedent(r'''#!/usr/bin/env python3
"""
copy_to_onedrive.py — canonical OneDrive copy script for onedrive-integration skill.
"""
import argparse
import os
import re
import shutil
import sys
from pathlib import Path


def load_config(config_path: Path) -> dict:
    cfg = {}
    if config_path.exists():
        for line in config_path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()
    return cfg


def path_to_safe_name(src: str) -> str:
    """Convert an absolute path to a safe filename per rename rules."""
    # strip leading /
    name = src.lstrip("/")
    # replace path separators with -
    name = name.replace("/", "-").replace("\\", "-")
    # lowercase
    name = name.lower()
    # replace any non [a-z0-9._-] with -
    name = re.sub(r"[^a-z0-9._-]", "-", name)
    # collapse multiple -
    name = re.sub(r"-{2,}", "-", name)
    return name


def main():
    default_config = (
        Path.home() / ".openclaw" / "skills" / "onedrive-integration" / "config.env"
    )

    parser = argparse.ArgumentParser(description="Copy files to OneDrive folder.")
    parser.add_argument("paths", nargs="+", help="Source file paths to copy.")
    parser.add_argument("--onedrive-root", default=None, help="Override ONEDRIVE_ROOT.")
    parser.add_argument("--subdir", default=None, help="Override ONEDRIVE_SUBDIR.")
    parser.add_argument("--config", default=str(default_config), help="Path to config.env.")
    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    onedrive_root = args.onedrive_root or cfg.get("ONEDRIVE_ROOT") or os.environ.get("ONEDRIVE_ROOT")
    subdir = args.subdir or cfg.get("ONEDRIVE_SUBDIR") or "openclaw"

    if not onedrive_root:
        print("ERROR: ONEDRIVE_ROOT is not set. Please configure config.env.", file=sys.stderr)
        sys.exit(1)

    dest_dir = Path(onedrive_root) / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)

    for src_str in args.paths:
        src = Path(src_str).resolve()
        if not src.exists():
            print(f"WARNING: {src} does not exist, skipping.", file=sys.stderr)
            continue
        safe_name = path_to_safe_name(str(src))
        dest = dest_dir / safe_name
        shutil.copy2(str(src), str(dest))
        print(str(dest))


if __name__ == "__main__":
    main()
''')

script_path = SCRIPTS_DIR / "copy_to_onedrive.py"
script_path.write_text(copy_script)
script_path.chmod(script_path.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

# onboard.sh stub
onboard_sh = SCRIPTS_DIR / "onboard.sh"
onboard_sh.write_text(textwrap.dedent("""\
    #!/usr/bin/env bash
    echo "Interactive onboarding: please set ONEDRIVE_ROOT in config.env"
"""))
onboard_sh.chmod(onboard_sh.stat().st_mode | stat.S_IEXEC)

# ── 2. Create the mock OneDrive root (empty, agent should NOT pre-populate) ──
MOCK_ONEDRIVE = WORKSPACE / "mock_onedrive"
MOCK_ONEDRIVE.mkdir(parents=True, exist_ok=True)
# Leave it empty — agent must trigger directory creation via config

# ── 3. Create realistic, messy source files in deeply nested directories ─────

# File 1: path with spaces and parentheses (tricky rename)
report_dir = WORKSPACE / "lab_data" / "2024 Reports" / "Analysis_Output"
report_dir.mkdir(parents=True, exist_ok=True)
(report_dir / "Final Report (v2).md").write_text(textwrap.dedent("""\
    # Final Analysis Report (Version 2)
    
    ## Summary
    This report summarizes the Q3 2024 lab analysis results.
    
    ## Findings
    - Sample A: Positive correlation (r=0.87)
    - Sample B: No significant effect (p=0.34)
    - Sample C: Outlier detected at t=142s
    
    ## Conclusion
    Further investigation recommended for Sample C anomaly.
    Recommend sharing with field team via mobile for immediate review.
"""))

# File 2: nested path with underscores and digits (moderate rename)
raw_dir = WORKSPACE / "lab_data" / "RawData" / "Experiment_01"
raw_dir.mkdir(parents=True, exist_ok=True)
(raw_dir / "sensor_readings.csv").write_text(textwrap.dedent("""\
    timestamp,sensor_id,value,unit
    2024-03-01T08:00:00Z,S001,23.4,celsius
    2024-03-01T08:05:00Z,S001,23.6,celsius
    2024-03-01T08:10:00Z,S002,101.2,kPa
    2024-03-01T08:15:00Z,S002,101.5,kPa
    2024-03-01T08:20:00Z,S003,0.87,pH
"""))

# File 3: path with ampersand and spaces (very tricky rename)
notes_dir = WORKSPACE / "lab_data" / "Notes & Drafts"
notes_dir.mkdir(parents=True, exist_ok=True)
(notes_dir / "todo.txt").write_text(textwrap.dedent("""\
    TODO LIST - Lab Coordinator
    ===========================
    [x] Submit Q3 report to PI
    [ ] Review sensor calibration logs
    [ ] Share findings with remote collaborators via WhatsApp
    [ ] Order new reagents (batch #2024-C)
    [ ] Update lab notebook
"""))

# ── 4. Create distractor files to test contextual awareness ──────────────────
distractors = [
    WORKSPACE / "lab_data" / "archive" / "old_report_2023.pdf.bak",
    WORKSPACE / "lab_data" / "archive" / "experiment_log_jan.xlsx.bak",
    WORKSPACE / "lab_data" / "RawData" / "Experiment_01" / "calibration.log",
    WORKSPACE / "lab_data" / "RawData" / "Experiment_02" / "sensor_readings.csv",
    WORKSPACE / "lab_data" / "RawData" / "Experiment_02" / "notes.txt",
    WORKSPACE / "lab_data" / "Scripts" / "process_data.py",
    WORKSPACE / "lab_data" / "Scripts" / "plot_results.py",
    WORKSPACE / "lab_data" / "2024 Reports" / "Analysis_Output" / "intermediate_v1.md",
    WORKSPACE / "lab_data" / "2024 Reports" / "draft_outline.txt",
    WORKSPACE / "lab_data" / "Notes & Drafts" / "meeting_notes_2024_02.txt",
    WORKSPACE / "lab_data" / "Notes & Drafts" / "hypothesis_draft.md",
]

for d in distractors:
    d.parent.mkdir(parents=True, exist_ok=True)
    if not d.exists():
        d.write_text(f"Distractor file: {d.name}\nThis is not the file you need to copy.\n")

# ── 5. Write a task brief for the agent (no hints about implementation) ───────
(WORKSPACE / "task_brief.txt").write_text(textwrap.dedent("""\
    TASK BRIEF
    ==========
    Lab Coordinator Request:
    
    I need to share three specific lab files with the remote team via WhatsApp/Telegram.
    The files are too long to paste directly in chat. Please set up the file-sharing
    integration and copy the following files to the shared folder:
    
    1. /workspace/lab_data/2024 Reports/Analysis_Output/Final Report (v2).md
    2. /workspace/lab_data/RawData/Experiment_01/sensor_readings.csv
    3. /workspace/lab_data/Notes & Drafts/todo.txt
    
    The shared OneDrive folder root is: /workspace/mock_onedrive
    Use the default subfolder name.
    
    Once done, I should be able to find all three files in the shared folder.
"""))

print("Workspace generation complete.")
print(f"Skill dir: {SKILL_DIR}")
print(f"Mock OneDrive: {MOCK_ONEDRIVE}")
print(f"Source files created in: {WORKSPACE / 'lab_data'}")