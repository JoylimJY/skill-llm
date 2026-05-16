import sys
import os
import json
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    workspace = Path(workspace)

    # ── Helper ────────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 1: subskills/churn-prediction/ directory exists
    # ══════════════════════════════════════════════════════════════════════════
    churn_dir = workspace / "subskills" / "churn-prediction"
    if churn_dir.is_dir():
        add("churn_prediction_subskill_dir_exists",
            True,
            f"Found subskills/churn-prediction/ at {churn_dir}")
    else:
        # Accept hyphen or underscore variation
        alt_dir = workspace / "subskills" / "churn_prediction"
        if alt_dir.is_dir():
            churn_dir = alt_dir
            add("churn_prediction_subskill_dir_exists",
                True,
                f"Found subskills/churn_prediction/ at {churn_dir}")
        else:
            add("churn_prediction_subskill_dir_exists",
                False,
                "Neither subskills/churn-prediction/ nor subskills/churn_prediction/ found.")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 2: A Python script exists inside the churn feature folder
    # ══════════════════════════════════════════════════════════════════════════
    try:
        py_scripts = list(churn_dir.glob("*.py")) if churn_dir.is_dir() else []
        if py_scripts:
            add("python_script_in_churn_folder",
                True,
                f"Found Python script(s) in churn folder: {[p.name for p in py_scripts]}")
        else:
            add("python_script_in_churn_folder",
                False,
                f"No .py files found directly in {churn_dir}")
    except Exception as e:
        add("python_script_in_churn_folder", False, f"Error checking for py scripts: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 3: A SKILL.md exists inside the churn feature folder
    # ══════════════════════════════════════════════════════════════════════════
    try:
        subskill_md = churn_dir / "SKILL.md" if churn_dir.is_dir() else None
        if subskill_md and subskill_md.is_file():
            content = subskill_md.read_text()
            if len(content.strip()) > 10:
                add("skill_md_in_churn_folder",
                    True,
                    f"SKILL.md found in churn folder with {len(content)} chars.")
            else:
                add("skill_md_in_churn_folder",
                    False,
                    "SKILL.md exists but is empty or trivially short.")
        else:
            add("skill_md_in_churn_folder",
                False,
                f"No SKILL.md found inside {churn_dir}")
    except Exception as e:
        add("skill_md_in_churn_folder", False, f"Error reading SKILL.md: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 4: A recommendation/result artifact (.json or .csv) exists in data/
    # ══════════════════════════════════════════════════════════════════════════
    try:
        data_dir = workspace / "data"
        # Look for any new artifact that seems related to churn (not pre-existing ones)
        pre_existing = {"segmentation_report_2024_01.json", "customer_segments.csv"}
        data_files = [f for f in data_dir.iterdir()
                      if f.is_file() and f.name not in pre_existing]
        churn_artifacts = [f for f in data_files
                           if f.suffix in (".json", ".csv", ".txt", ".tsv")]
        if churn_artifacts:
            add("churn_artifact_in_data_dir",
                True,
                f"Found new artifact(s) in data/: {[f.name for f in churn_artifacts]}")
        else:
            add("churn_artifact_in_data_dir",
                False,
                f"No new artifact files found in data/. Existing files: {[f.name for f in data_dir.iterdir() if f.is_file()]}")
    except Exception as e:
        add("churn_artifact_in_data_dir", False, f"Error scanning data/: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 5: No new one-off scripts added to the skill root
    # ══════════════════════════════════════════════════════════════════════════
    try:
        pre_existing_root_files = {
            "SKILL.md", "config.json",
            "churn_scratch.py",       # this was the pre-existing bad file (distractor)
            "draft_config_churn.json"
        }
        root_py_files = [f for f in workspace.glob("*.py")
                         if f.name not in pre_existing_root_files]
        root_json_files = [f for f in workspace.glob("*.json")
                           if f.name not in pre_existing_root_files]
        new_root_scripts = root_py_files + [
            f for f in root_json_files
            if not f.name.startswith("config")
        ]
        if not new_root_scripts:
            add("no_new_scripts_in_root",
                True,
                "No new one-off scripts or artifacts were added to the skill root.")
        else:
            add("no_new_scripts_in_root",
                False,
                f"New file(s) incorrectly placed in root: {[f.name for f in new_root_scripts]}")
    except Exception as e:
        add("no_new_scripts_in_root", False, f"Error checking root directory: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 6: The churn feature is in its own dedicated folder (not mixed)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        seg_dir = workspace / "subskills" / "segmentation"
        churn_scripts_in_seg = list(seg_dir.glob("*churn*")) if seg_dir.is_dir() else []
        if not churn_scripts_in_seg:
            add("churn_not_mixed_into_segmentation_folder",
                True,
                "Churn feature correctly isolated from segmentation folder.")
        else:
            add("churn_not_mixed_into_segmentation_folder",
                False,
                f"Churn files found inside segmentation/ folder: {[f.name for f in churn_scripts_in_seg]}")
    except Exception as e:
        add("churn_not_mixed_into_segmentation_folder", False, f"Error: {e}")

    # ── Scoring ───────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_path = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_path)