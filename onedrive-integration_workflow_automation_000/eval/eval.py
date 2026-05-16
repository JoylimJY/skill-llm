#!/usr/bin/env python3
"""
Evaluation script for the onedrive-integration task.

Usage:
    eval_script.py <workspace_dir>
"""
import json
import os
import re
import sys
from pathlib import Path

def make_safe_name_expected(abs_path_str: str) -> str:
    """Replicate the canonical rename logic from copy_to_onedrive.py."""
    p = abs_path_str
    # strip leading slash
    if p.startswith("/"):
        p = p[1:]
    # replace path separators
    p = p.replace("/", "-").replace("\\", "-")
    # lowercase
    p = p.lower()
    # replace any char not in [a-z0-9._-] with -
    p = re.sub(r"[^a-z0-9._-]", "-", p)
    # collapse multiple dashes
    p = re.sub(r"-+", "-", p)
    return p

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    home = Path("/root")

    checks = []
    total_score = 0.0

    # ── Derived paths ──────────────────────────────────────────────────────────
    skill_dir = home / ".openclaw" / "skills" / "onedrive-integration"
    config_env = skill_dir / "config.env"
    fake_onedrive = workspace / "FakeOneDrive"

    # Source files (absolute resolved paths)
    src_f1 = (workspace / "CaseDocs" / "Matter 2024-Q3" / "Contracts & Agreements" / "Draft_NDA (Revised).md").resolve()
    src_f2 = (workspace / "LegalTeam" / "Research" / "CaseLaw_2023" / "SmithVsJones_Summary.txt").resolve()
    src_f3 = (workspace / "archive" / "old_filings" / "2022" / "motion_to_compel_v2.1_FINAL.pdf.txt").resolve()

    # Expected safe filenames
    exp_name_f1 = make_safe_name_expected(str(src_f1))
    exp_name_f2 = make_safe_name_expected(str(src_f2))
    exp_name_f3 = make_safe_name_expected(str(src_f3))

    # ── CHECK 1: config.env exists ────────────────────────────────────────────
    try:
        cfg_exists = config_env.exists()
        checks.append({
            "name": "config.env_exists",
            "passed": cfg_exists,
            "detail": f"config.env found at {config_env}" if cfg_exists else f"config.env missing at {config_env}"
        })
    except Exception as e:
        checks.append({"name": "config.env_exists", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 2: config.env has ONEDRIVE_ROOT set ─────────────────────────────
    cfg = {}
    try:
        if config_env.exists():
            for line in config_env.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, _, v = line.partition("=")
                    cfg[k.strip()] = v.strip().strip('"').strip("'")

        onedrive_root = cfg.get("ONEDRIVE_ROOT", "")
        root_set = bool(onedrive_root)
        checks.append({
            "name": "ONEDRIVE_ROOT_set",
            "passed": root_set,
            "detail": f"ONEDRIVE_ROOT={onedrive_root!r}" if root_set else "ONEDRIVE_ROOT not set in config.env"
        })
    except Exception as e:
        checks.append({"name": "ONEDRIVE_ROOT_set", "passed": False, "detail": f"Exception: {e}"})
        onedrive_root = ""

    # ── CHECK 3: Destination directory exists ─────────────────────────────────
    # The agent may use any valid OneDrive root, but it must be under FakeOneDrive
    # OR the agent may have used --onedrive-root flag; we accept any subdir under FakeOneDrive
    # We'll find the actual dest dir by looking for copied files
    try:
        subdir = cfg.get("ONEDRIVE_SUBDIR", "openclaw") or "openclaw"
        if onedrive_root:
            dest_dir = Path(onedrive_root) / subdir
        else:
            dest_dir = fake_onedrive / "openclaw"

        dest_exists = dest_dir.exists() and dest_dir.is_dir()
        # Also accept if files are found anywhere under FakeOneDrive
        if not dest_exists:
            all_files_in_od = list(fake_onedrive.rglob("*")) if fake_onedrive.exists() else []
            dest_exists = len([f for f in all_files_in_od if f.is_file()]) > 0

        checks.append({
            "name": "destination_directory_exists",
            "passed": dest_exists,
            "detail": f"Destination dir {dest_dir} exists: {dest_exists}"
        })
    except Exception as e:
        checks.append({"name": "destination_directory_exists", "passed": False, "detail": f"Exception: {e}"})
        dest_dir = fake_onedrive / "openclaw"

    # ── Helper: find a copied file by expected name anywhere under FakeOneDrive ──
    def find_copied_file(expected_name: str) -> Path | None:
        if not fake_onedrive.exists():
            return None
        for f in fake_onedrive.rglob(expected_name):
            return f
        return None

    # ── CHECK 4: File 1 copied with correct rename ────────────────────────────
    try:
        found_f1 = find_copied_file(exp_name_f1)
        f1_ok = found_f1 is not None
        checks.append({
            "name": "file1_copied_correct_name",
            "passed": f1_ok,
            "detail": f"Expected {exp_name_f1!r}, found at {found_f1}" if f1_ok
                      else f"Expected {exp_name_f1!r} not found under {fake_onedrive}"
        })
    except Exception as e:
        checks.append({"name": "file1_copied_correct_name", "passed": False, "detail": f"Exception: {e}"})
        found_f1 = None

    # ── CHECK 5: File 1 content preserved ────────────────────────────────────
    try:
        if found_f1 and found_f1.exists():
            orig_content = src_f1.read_text()
            copied_content = found_f1.read_text()
            content_ok = orig_content == copied_content
            checks.append({
                "name": "file1_content_preserved",
                "passed": content_ok,
                "detail": "Content matches" if content_ok else "Content mismatch"
            })
        else:
            checks.append({"name": "file1_content_preserved", "passed": False, "detail": "File not found, cannot check content"})
    except Exception as e:
        checks.append({"name": "file1_content_preserved", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 6: File 2 copied with correct rename ────────────────────────────
    try:
        found_f2 = find_copied_file(exp_name_f2)
        f2_ok = found_f2 is not None
        checks.append({
            "name": "file2_copied_correct_name",
            "passed": f2_ok,
            "detail": f"Expected {exp_name_f2!r}, found at {found_f2}" if f2_ok
                      else f"Expected {exp_name_f2!r} not found under {fake_onedrive}"
        })
    except Exception as e:
        checks.append({"name": "file2_copied_correct_name", "passed": False, "detail": f"Exception: {e}"})
        found_f2 = None

    # ── CHECK 7: File 2 content preserved ────────────────────────────────────
    try:
        if found_f2 and found_f2.exists():
            orig_content = src_f2.read_text()
            copied_content = found_f2.read_text()
            content_ok = orig_content == copied_content
            checks.append({
                "name": "file2_content_preserved",
                "passed": content_ok,
                "detail": "Content matches" if content_ok else "Content mismatch"
            })
        else:
            checks.append({"name": "file2_content_preserved", "passed": False, "detail": "File not found, cannot check content"})
    except Exception as e:
        checks.append({"name": "file2_content_preserved", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 8: File 3 copied with correct rename ────────────────────────────
    try:
        found_f3 = find_copied_file(exp_name_f3)
        f3_ok = found_f3 is not None
        checks.append({
            "name": "file3_copied_correct_name",
            "passed": f3_ok,
            "detail": f"Expected {exp_name_f3!r}, found at {found_f3}" if f3_ok
                      else f"Expected {exp_name_f3!r} not found under {fake_onedrive}"
        })
    except Exception as e:
        checks.append({"name": "file3_copied_correct_name", "passed": False, "detail": f"Exception: {e}"})
        found_f3 = None

    # ── CHECK 9: File 3 content preserved ────────────────────────────────────
    try:
        if found_f3 and found_f3.exists():
            orig_content = src_f3.read_text()
            copied_content = found_f3.read_text()
            content_ok = orig_content == copied_content
            checks.append({
                "name": "file3_content_preserved",
                "passed": content_ok,
                "detail": "Content matches" if content_ok else "Content mismatch"
            })
        else:
            checks.append({"name": "file3_content_preserved", "passed": False, "detail": "File not found, cannot check content"})
    except Exception as e:
        checks.append({"name": "file3_content_preserved", "passed": False, "detail": f"Exception: {e}"})

    # ── CHECK 10: Rename correctness — no naive rename (anti-trap check) ──────
    # Verify the filenames are NOT just the basename (common naive mistake)
    try:
        naive_names = ["draft_nda--revised-.md", "smithvsjones_summary.txt", "motion_to_compel_v2.1_final.pdf.txt",
                       "draft_nda (revised).md", "SmithVsJones_Summary.txt"]
        
        all_od_files = [f.name for f in fake_onedrive.rglob("*") if f.is_file()] if fake_onedrive.exists() else []
        
        # The correct filenames must include path components (contain multiple dashes from path segments)
        # Correct names should look like "workspace-casedocs-matter-2024-q3-..." 
        # They must NOT be just the basename
        correct_rename_used = all(
            any(exp in fname for fname in all_od_files)
            for exp in [exp_name_f1[:20], exp_name_f2[:20], exp_name_f3[:20]]
        ) if all_od_files else False
        
        # Simpler: just check the expected names are in the found files
        all_expected_found = (
            find_copied_file(exp_name_f1) is not None and
            find_copied_file(exp_name_f2) is not None and
            find_copied_file(exp_name_f3) is not None
        )
        
        checks.append({
            "name": "rename_includes_path_components",
            "passed": all_expected_found,
            "detail": (
                f"All files found with path-encoded names. "
                f"f1={exp_name_f1!r}, f2={exp_name_f2!r}, f3={exp_name_f3!r}"
            ) if all_expected_found else (
                f"Some files missing or incorrectly named. "
                f"Expected: {exp_name_f1!r}, {exp_name_f2!r}, {exp_name_f3!r}. "
                f"Found: {all_od_files}"
            )
        })
    except Exception as e:
        checks.append({"name": "rename_includes_path_components", "passed": False, "detail": f"Exception: {e}"})

    # ── Scoring ───────────────────────────────────────────────────────────────
    # Weight each check
    weights = {
        "config.env_exists": 0.05,
        "ONEDRIVE_ROOT_set": 0.05,
        "destination_directory_exists": 0.05,
        "file1_copied_correct_name": 0.15,
        "file1_content_preserved": 0.05,
        "file2_copied_correct_name": 0.15,
        "file2_content_preserved": 0.05,
        "file3_copied_correct_name": 0.15,
        "file3_content_preserved": 0.05,
        "rename_includes_path_components": 0.20,
    }

    score = sum(weights.get(c["name"], 0.0) for c in checks if c["passed"])
    passed = score >= 0.75

    result = {
        "passed": passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()