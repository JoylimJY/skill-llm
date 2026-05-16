#!/usr/bin/env python3
import sys
import os
import json
import subprocess
from pathlib import Path

def run(cmd, cwd=None):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=cwd)
    return result.stdout.strip(), result.stderr.strip(), result.returncode

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    base = Path(workspace) / "project_archive"
    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: Stale .log files (>30 days old) have been deleted
    # Expected: ep01_transcode_2024.log, ep02_transcode_2024.log, ep01_render_batch_jan.log removed
    # Recent logs must remain
    # -----------------------------------------------------------------------
    try:
        old_logs = [
            base / "logs/transcode/ep01_transcode_2024.log",
            base / "logs/transcode/ep02_transcode_2024.log",
            base / "logs/render/ep01_render_batch_jan.log",
        ]
        recent_logs = [
            base / "logs/transcode/ep03_transcode_latest.log",
            base / "logs/render/ep03_render_batch_latest.log",
            base / "logs/export/ep03_export.log",
        ]
        old_deleted = all(not p.exists() for p in old_logs)
        recent_kept = all(p.exists() for p in recent_logs)

        passed = old_deleted and recent_kept
        detail = []
        if not old_deleted:
            still_there = [str(p) for p in old_logs if p.exists()]
            detail.append(f"Stale logs NOT deleted: {still_there}")
        if not recent_kept:
            missing = [str(p) for p in recent_logs if not p.exists()]
            detail.append(f"Recent logs WRONGLY deleted: {missing}")
        if passed:
            total_score += 25
        checks.append({
            "name": "stale_logs_deleted_recent_kept",
            "passed": passed,
            "detail": "; ".join(detail) if detail else "All 3 stale logs deleted, 3 recent logs preserved."
        })
    except Exception as e:
        checks.append({"name": "stale_logs_deleted_recent_kept", "passed": False, "detail": f"Exception: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 2: All .tmp files deleted
    # Expected: all *.tmp files anywhere in project_archive are gone
    # -----------------------------------------------------------------------
    try:
        remaining_tmp = list(base.rglob("*.tmp"))
        passed = len(remaining_tmp) == 0
        detail = f"{len(remaining_tmp)} .tmp files remain: {[str(p) for p in remaining_tmp]}" if not passed else "All .tmp files deleted."
        if passed:
            total_score += 20
        checks.append({"name": "tmp_files_deleted", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "tmp_files_deleted", "passed": False, "detail": f"Exception: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 3: Empty directories removed
    # Expected: empty_batch_1, empty_batch_2, empty_job_99 are gone
    # -----------------------------------------------------------------------
    try:
        empty_dirs = [
            base / "cache/previews/empty_batch_1",
            base / "cache/previews/empty_batch_2",
            base / "temp/scratch/empty_job_99",
        ]
        empty_deleted = all(not d.exists() for d in empty_dirs)
        passed = empty_deleted
        detail = f"Empty dirs NOT removed: {[str(d) for d in empty_dirs if d.exists()]}" if not passed else "All empty directories removed."
        if passed:
            total_score += 15
        checks.append({"name": "empty_dirs_removed", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "empty_dirs_removed", "passed": False, "detail": f"Exception: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 4: Files with "Status: REVISION" have been moved to a quarantine directory
    # The quarantine dir can be anywhere under project_archive or workspace
    # Files: shot_011.md, shot_021.md, ep03_revision_notes.txt, ingest_tool.py,
    #        ep01_score.wav.meta, export_dcp.py (all contain "Status: REVISION")
    # We check: original locations are gone AND a quarantine-like dir exists with them
    # -----------------------------------------------------------------------
    try:
        original_revision_files = [
            base / "renders/episode_02/shot_011.md",
            base / "renders/episode_03/shot_021.md",
            base / "deliverables/review/ep03_revision_notes.txt",
            base / "assets/scripts/ingest_tool.py",
            base / "audio/music/ep01_score.wav.meta",
            base / "assets/scripts/export_dcp.py",
        ]
        # Find any directory named *quarantine* or *revision* under workspace
        quarantine_dirs = list(Path(workspace).rglob("*quarantine*")) + list(Path(workspace).rglob("*revision*"))
        quarantine_dirs = [d for d in quarantine_dirs if d.is_dir()]

        # Count how many original locations are now empty (files moved)
        moved_count = sum(1 for f in original_revision_files if not f.exists())
        # Count how many revision-status files exist anywhere in a quarantine dir
        quarantine_files_found = 0
        if quarantine_dirs:
            for qd in quarantine_dirs:
                for f in qd.rglob("*"):
                    if f.is_file():
                        try:
                            content = f.read_text(errors='ignore')
                            if "REVISION" in content:
                                quarantine_files_found += 1
                        except:
                            pass

        # Pass if at least 4 of the 6 revision files were moved and quarantine dir exists
        passed = moved_count >= 4 and len(quarantine_dirs) >= 1
        detail = (f"Moved {moved_count}/6 revision files from original locations. "
                  f"Quarantine dirs found: {[str(d) for d in quarantine_dirs]}. "
                  f"Revision files in quarantine: {quarantine_files_found}.")
        if passed:
            total_score += 20
        checks.append({"name": "revision_files_quarantined", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "revision_files_quarantined", "passed": False, "detail": f"Exception: {e}"})

    # -----------------------------------------------------------------------
    # CHECK 5: Audit report file exists with correct statistics
    # Expected: a file named "audit_report.txt" or "audit_report.json" anywhere in workspace
    # Must contain: count of large files (>1MB) = 4, count of .md files, extension breakdown
    # -----------------------------------------------------------------------
    try:
        report_files = list(Path(workspace).rglob("audit_report.txt")) + \
                       list(Path(workspace).rglob("audit_report.json"))
        if not report_files:
            checks.append({"name": "audit_report_exists_and_correct", "passed": False,
                           "detail": "No audit_report.txt or audit_report.json found anywhere in workspace."})
        else:
            report_path = report_files[0]
            content = report_path.read_text(errors='ignore')

            # Check for large files count: 4 files are >1MB (2 textures, 1 model, 1 mxf)
            # After deletions and moves, the large binary files should still be there
            large_file_check = "4" in content or "four" in content.lower()

            # Check that the report mentions file extensions or types
            has_extension_info = any(ext in content.lower() for ext in
                                     [".md", ".log", ".tmp", ".py", ".exr", ".obj", "extension", "type"])

            # Check report mentions directory size or total size
            has_size_info = any(kw in content.lower() for kw in
                                ["mb", "kb", "gb", "size", "bytes", "du"])

            passed = large_file_check and has_extension_info and has_size_info
            detail = (f"Report at {report_path}. "
                      f"Large file count mentioned(4): {large_file_check}. "
                      f"Extension info present: {has_extension_info}. "
                      f"Size info present: {has_size_info}.")
            if passed:
                total_score += 20
            checks.append({"name": "audit_report_exists_and_correct", "passed": passed, "detail": detail})
    except Exception as e:
        checks.append({"name": "audit_report_exists_and_correct", "passed": False, "detail": f"Exception: {e}"})

    # -----------------------------------------------------------------------
    # FINAL SCORE
    # -----------------------------------------------------------------------
    all_passed = all(c["passed"] for c in checks)
    final_score = round(total_score / 100.0, 2)

    result = {
        "passed": all_passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()