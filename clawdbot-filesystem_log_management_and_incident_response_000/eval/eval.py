#!/usr/bin/env python3
"""
Evaluation script for the log audit task.
Checks:
  1. analysis_report.json exists and was produced via `filesystem analyze --format json`
     (contains expected keys: total_files, file_types, largest_files)
  2. quarantine/ directory exists with ONLY .log files copied via `filesystem copy --preserve`
  3. Timestamps are preserved in quarantine/ files (--preserve flag check)
  4. The quarantine contains the correct subset of .log files that have ERROR/CRITICAL content
     OR all .log files from logs/ (acceptable if agent used pattern-only copy)
"""

import sys
import json
import os
import stat
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    passed_all = True

    # ── Check 1: analysis_report.json exists ────────────────────────────────
    report_files = list(ws.rglob("analysis_report.json"))
    if not report_files:
        checks.append({
            "name": "analysis_report.json exists",
            "passed": False,
            "detail": "No file named analysis_report.json found anywhere in the workspace."
        })
        passed_all = False
    else:
        checks.append({
            "name": "analysis_report.json exists",
            "passed": True,
            "detail": f"Found at: {report_files[0]}"
        })

    # ── Check 2: analysis_report.json is valid JSON with correct structure ───
    report_data = None
    if report_files:
        try:
            with open(report_files[0]) as f:
                report_data = json.load(f)
            # Must have total_files key (from analyze --stats --format json)
            has_total_files = "total_files" in report_data
            checks.append({
                "name": "analysis_report.json has total_files key",
                "passed": has_total_files,
                "detail": f"Keys present: {list(report_data.keys())[:8]}"
            })
            if not has_total_files:
                passed_all = False
        except Exception as e:
            checks.append({
                "name": "analysis_report.json has total_files key",
                "passed": False,
                "detail": f"Failed to parse JSON: {e}"
            })
            passed_all = False

    # ── Check 3: file_types present (--types flag was used) ─────────────────
    if report_data is not None:
        has_types = "file_types" in report_data
        checks.append({
            "name": "analysis_report.json contains file_types (--types flag)",
            "passed": has_types,
            "detail": "file_types key present" if has_types else "file_types key missing — agent may not have used --types flag"
        })
        if not has_types:
            passed_all = False

    # ── Check 4: largest_files present (--largest N flag was used) ──────────
    if report_data is not None:
        has_largest = "largest_files" in report_data
        checks.append({
            "name": "analysis_report.json contains largest_files (--largest flag)",
            "passed": has_largest,
            "detail": "largest_files key present" if has_largest else "largest_files key missing — agent may not have used --largest flag"
        })
        if not has_largest:
            passed_all = False

    # ── Check 5: total_files count is realistic (covers the logs/ directory) ─
    if report_data is not None and "total_files" in report_data:
        tf = report_data["total_files"]
        # We created at least 20 files in logs/; accept anything in range 10..100
        count_ok = isinstance(tf, int) and 10 <= tf <= 100
        checks.append({
            "name": "total_files count is plausible for logs/ directory",
            "passed": count_ok,
            "detail": f"total_files = {tf} (expected 10–100 for the logs/ directory)"
        })
        if not count_ok:
            passed_all = False

    # ── Check 6: quarantine/ directory exists ───────────────────────────────
    quarantine_candidates = [ws / "quarantine"] + list(ws.rglob("quarantine"))
    quarantine_dir = None
    for qc in quarantine_candidates:
        if qc.is_dir():
            quarantine_dir = qc
            break

    if quarantine_dir is None:
        checks.append({
            "name": "quarantine/ directory exists",
            "passed": False,
            "detail": "No directory named 'quarantine' found in workspace."
        })
        passed_all = False
    else:
        checks.append({
            "name": "quarantine/ directory exists",
            "passed": True,
            "detail": f"Found at: {quarantine_dir}"
        })

    # ── Check 7: quarantine/ contains .log files ────────────────────────────
    if quarantine_dir is not None:
        log_files_in_q = list(quarantine_dir.rglob("*.log"))
        has_logs = len(log_files_in_q) >= 3
        checks.append({
            "name": "quarantine/ contains .log files (>=3)",
            "passed": has_logs,
            "detail": f"Found {len(log_files_in_q)} .log files: {[f.name for f in log_files_in_q]}"
        })
        if not has_logs:
            passed_all = False

    # ── Check 8: quarantine/ does NOT contain non-log files (e.g., .json, .txt, .gz) ──
    if quarantine_dir is not None:
        all_q_files = [f for f in quarantine_dir.rglob("*") if f.is_file()]
        non_log_files = [f for f in all_q_files if not f.name.endswith(".log")]
        no_non_logs = len(non_log_files) == 0
        checks.append({
            "name": "quarantine/ contains ONLY .log files (no .json/.txt/.gz etc.)",
            "passed": no_non_logs,
            "detail": f"Non-log files in quarantine: {[f.name for f in non_log_files]}" if non_log_files else "Clean — only .log files"
        })
        if not no_non_logs:
            passed_all = False

    # ── Check 9: Timestamps preserved in quarantine (--preserve flag) ───────
    if quarantine_dir is not None:
        log_files_in_q = list(quarantine_dir.rglob("*.log"))
        if log_files_in_q:
            # Check that mtime of quarantine file matches original source
            logs_source = ws / "logs"
            original_logs = {f.name: f for f in logs_source.rglob("*.log")}
            preserved_count = 0
            checked_count = 0
            for qf in log_files_in_q:
                orig = original_logs.get(qf.name)
                if orig:
                    checked_count += 1
                    orig_mtime = orig.stat().st_mtime
                    q_mtime = qf.stat().st_mtime
                    # Allow 2-second tolerance
                    if abs(orig_mtime - q_mtime) < 2.0:
                        preserved_count += 1

            ts_ok = checked_count > 0 and preserved_count == checked_count
            checks.append({
                "name": "Timestamps preserved in quarantine files (--preserve flag)",
                "passed": ts_ok,
                "detail": f"{preserved_count}/{checked_count} files have matching timestamps from source logs/"
            })
            if not ts_ok:
                passed_all = False
        else:
            checks.append({
                "name": "Timestamps preserved in quarantine files (--preserve flag)",
                "passed": False,
                "detail": "No .log files in quarantine to check."
            })
            passed_all = False

    # ── Check 10: quarantine contains files from ERROR/CRITICAL logs ─────────
    # The key files that must be in quarantine (they contain ERROR/CRITICAL content)
    required_error_logs = {"error.log", "app.log", "api-server.log", "worker.log", "postgres.log"}
    if quarantine_dir is not None:
        q_names = {f.name for f in quarantine_dir.rglob("*.log")}
        overlap = required_error_logs & q_names
        has_error_logs = len(overlap) >= 3
        checks.append({
            "name": "quarantine/ contains at least 3 of the known ERROR/CRITICAL log files",
            "passed": has_error_logs,
            "detail": f"Found error-containing logs: {overlap}. Required at least 3 of: {required_error_logs}"
        })
        if not has_error_logs:
            passed_all = False

    # ── Final score ──────────────────────────────────────────────────────────
    num_passed = sum(1 for c in checks if c["passed"])
    score = round(num_passed / len(checks), 3) if checks else 0.0

    return {
        "passed": passed_all,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))