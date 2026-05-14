#!/usr/bin/env python3
"""
Evaluation script for onedrive-integration task.
Usage: python3 eval_script.py /workspace
"""
import json
import re
import sys
from pathlib import Path

def path_to_expected_name(src_str: str) -> str:
    """
    Reproduce the canonical rename logic from the SKILL.md spec:
    1. strip leading /
    2. replace / and \\ with -
    3. lowercase
    4. replace any non [a-z0-9._-] with -
    5. collapse multiple -
    """
    name = src_str.lstrip("/")
    name = name.replace("/", "-").replace("\\", "-")
    name = name.lower()
    name = re.sub(r"[^a-z0-9._-]", "-", name)
    name = re.sub(r"-{2,}", "-", name)
    return name


def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

    checks = []

    # ── Check 1: config.env exists and has ONEDRIVE_ROOT set ─────────────────
    config_path = Path.home() / ".openclaw" / "skills" / "onedrive-integration" / "config.env"
    config_ok = False
    onedrive_root_val = None
    subdir_val = "openclaw"  # default per spec

    try:
        if not config_path.exists():
            raise FileNotFoundError(f"config.env not found at {config_path}")
        cfg_text = config_path.read_text()
        cfg = {}
        for line in cfg_text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip()

        if "ONEDRIVE_ROOT" not in cfg or not cfg["ONEDRIVE_ROOT"]:
            raise ValueError("ONEDRIVE_ROOT is not set in config.env")

        onedrive_root_val = cfg["ONEDRIVE_ROOT"]
        if "ONEDRIVE_SUBDIR" in cfg and cfg["ONEDRIVE_SUBDIR"]:
            subdir_val = cfg["ONEDRIVE_SUBDIR"]

        # Verify ONEDRIVE_ROOT points to the mock onedrive directory
        expected_root = str(workspace / "mock_onedrive")
        if Path(onedrive_root_val).resolve() != Path(expected_root).resolve():
            raise ValueError(
                f"ONEDRIVE_ROOT='{onedrive_root_val}' does not point to expected '{expected_root}'"
            )

        config_ok = True
        checks.append({
            "name": "config_env_valid",
            "passed": True,
            "detail": f"config.env found with ONEDRIVE_ROOT={onedrive_root_val}, ONEDRIVE_SUBDIR={subdir_val}"
        })
    except Exception as e:
        checks.append({
            "name": "config_env_valid",
            "passed": False,
            "detail": str(e)
        })

    # ── Determine destination directory ──────────────────────────────────────
    if onedrive_root_val:
        dest_dir = Path(onedrive_root_val) / subdir_val
    else:
        dest_dir = workspace / "mock_onedrive" / "openclaw"

    # ── Check 2: destination directory was created ────────────────────────────
    try:
        if not dest_dir.exists():
            raise FileNotFoundError(f"Destination directory does not exist: {dest_dir}")
        checks.append({
            "name": "destination_dir_created",
            "passed": True,
            "detail": f"Destination directory exists: {dest_dir}"
        })
    except Exception as e:
        checks.append({
            "name": "destination_dir_created",
            "passed": False,
            "detail": str(e)
        })

    # ── Define the three source files and their expected renamed destinations ─
    source_files = [
        str(workspace / "lab_data" / "2024 Reports" / "Analysis_Output" / "Final Report (v2).md"),
        str(workspace / "lab_data" / "RawData" / "Experiment_01" / "sensor_readings.csv"),
        str(workspace / "lab_data" / "Notes & Drafts" / "todo.txt"),
    ]

    # ── Check 3, 4, 5: Each file copied with correct proprietary rename ───────
    all_copies_ok = True
    for src_str in source_files:
        src_path = Path(src_str)
        expected_name = path_to_expected_name(src_str)
        expected_dest = dest_dir / expected_name

        check_name = f"file_copied__{src_path.name.replace(' ', '_')}"

        try:
            if not expected_dest.exists():
                # Search for any file with this name anywhere under mock_onedrive
                # to give a more helpful error message
                found_files = list((workspace / "mock_onedrive").rglob("*")) if (workspace / "mock_onedrive").exists() else []
                found_names = [f.name for f in found_files if f.is_file()]
                raise FileNotFoundError(
                    f"Expected renamed file not found: '{expected_name}' at '{expected_dest}'. "
                    f"Files found in mock_onedrive: {found_names}"
                )

            # Verify content matches source
            src_content = src_path.read_text()
            dest_content = expected_dest.read_text()
            if src_content != dest_content:
                raise ValueError(
                    f"File content mismatch for '{expected_name}': "
                    f"source has {len(src_content)} chars, dest has {len(dest_content)} chars"
                )

            checks.append({
                "name": check_name,
                "passed": True,
                "detail": f"'{src_path.name}' correctly copied as '{expected_name}'"
            })
        except Exception as e:
            all_copies_ok = False
            checks.append({
                "name": check_name,
                "passed": False,
                "detail": str(e)
            })

    # ── Check 6: No files were copied with wrong names (e.g. bare basename) ──
    try:
        if dest_dir.exists():
            dest_files = {f.name for f in dest_dir.iterdir() if f.is_file()}
            bad_names = []
            bare_basenames = {"Final Report (v2).md", "sensor_readings.csv", "todo.txt",
                              "final report (v2).md"}
            for bad in bare_basenames:
                if bad in dest_files:
                    bad_names.append(bad)

            if bad_names:
                raise ValueError(
                    f"Files were copied with bare basenames instead of path-encoded names: {bad_names}"
                )
            checks.append({
                "name": "no_bare_basename_copies",
                "passed": True,
                "detail": f"No files copied with bare basenames. Destination contains: {sorted(dest_files)}"
            })
        else:
            checks.append({
                "name": "no_bare_basename_copies",
                "passed": False,
                "detail": "Destination directory does not exist, cannot verify."
            })
    except Exception as e:
        checks.append({
            "name": "no_bare_basename_copies",
            "passed": False,
            "detail": str(e)
        })

    # ── Compute final score ───────────────────────────────────────────────────
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
    return 0 if overall_passed else 1


if __name__ == "__main__":
    sys.exit(main())