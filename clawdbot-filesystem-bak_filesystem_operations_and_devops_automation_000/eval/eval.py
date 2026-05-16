#!/usr/bin/env python3
"""
Evaluation script for the filesystem skill task.
Usage: python3 eval.py /workspace
"""

import sys
import json
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0
max_score   = 4.0   # 4 checks, each worth 1 point

def check(name, passed, detail, weight=1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0


# -----------------------------------------------------------------------
# CHECK 1: analysis_report.json exists and has correct structure
# The agent must have run: filesystem analyze --path ./project ... --output analysis_report.json
#   (or redirected output to file) with --largest 5, producing top-5 list.
# -----------------------------------------------------------------------

def check_analysis_report():
    # Search for analysis_report.json anywhere in workspace
    candidates = list(workspace.rglob("analysis_report.json"))
    if not candidates:
        return check(
            "analysis_report.json exists",
            False,
            "analysis_report.json not found anywhere in workspace."
        )

    report_path = candidates[0]
    try:
        content = report_path.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as e:
        return check(
            "analysis_report.json exists",
            False,
            f"File found at {report_path} but could not parse JSON: {e}"
        )

    # Must have 'largest' key with at least 5 entries
    largest = data.get("largest", [])
    if not isinstance(largest, list) or len(largest) < 5:
        return check(
            "analysis_report.json exists",
            False,
            f"'largest' field missing or has fewer than 5 entries (got {len(largest)}). "
            f"Agent must use --largest 5 flag. Data keys present: {list(data.keys())}"
        )

    # Must have totalFiles and totalSize
    has_stats = "totalFiles" in data and "totalSize" in data
    if not has_stats:
        return check(
            "analysis_report.json exists",
            False,
            f"Report is missing 'totalFiles' or 'totalSize' fields. Found keys: {list(data.keys())}"
        )

    # Verify the largest files list is actually sorted descending
    sizes = [e.get("size", 0) for e in largest]
    is_sorted_desc = all(sizes[i] >= sizes[i+1] for i in range(len(sizes)-1))
    if not is_sorted_desc:
        return check(
            "analysis_report.json exists",
            False,
            f"'largest' list is not sorted descending by size. Sizes: {sizes}"
        )

    # Verify 5 largest entries contain at least one known large file
    large_file_names = {e.get("path","").split("/")[-1] for e in largest}
    known_large = {"bigcache.json", "dump.csv", "app-2024-01-09.log"}
    overlap = known_large & large_file_names
    if not overlap:
        return check(
            "analysis_report.json exists",
            False,
            f"Top-5 largest files don't include any expected large files. Got basenames: {large_file_names}"
        )

    return check(
        "analysis_report.json exists",
        True,
        f"Found at {report_path}. totalFiles={data['totalFiles']}, "
        f"top-5 include: {large_file_names}."
    )

total_score += check_analysis_report()


# -----------------------------------------------------------------------
# CHECK 2: search_results.txt (or similar) with ERROR/CRITICAL matches
# Agent must search log files for ERROR or CRITICAL using filesystem search
# with --content and --include "*.log" flags, save output to search_results.txt
# -----------------------------------------------------------------------

def check_search_results():
    # Search for search_results.txt anywhere in workspace
    candidates = list(workspace.rglob("search_results.txt"))
    if not candidates:
        return check(
            "search_results.txt exists with correct content",
            False,
            "search_results.txt not found anywhere in workspace."
        )

    results_path = candidates[0]
    try:
        content = results_path.read_text(encoding="utf-8")
    except Exception as e:
        return check(
            "search_results.txt exists with correct content",
            False,
            f"Could not read {results_path}: {e}"
        )

    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if len(lines) == 0:
        return check(
            "search_results.txt exists with correct content",
            False,
            "search_results.txt is empty."
        )

    # Must reference .log files (only log files searched via --include *.log)
    log_references = [l for l in lines if ".log" in l]
    if not log_references:
        return check(
            "search_results.txt exists with correct content",
            False,
            f"search_results.txt has {len(lines)} lines but none reference .log files. "
            "Agent must use --include '*.log' to restrict search to log files."
        )

    # Must contain ERROR or CRITICAL pattern hits
    error_hits = [l for l in lines if re.search(r'ERROR|CRITICAL', l, re.IGNORECASE)]
    if not error_hits:
        return check(
            "search_results.txt exists with correct content",
            False,
            f"No ERROR or CRITICAL matches found in search_results.txt. Lines: {lines[:5]}"
        )

    # Must NOT include .js or .json file matches (exclude non-log content)
    # The --include *.log should prevent this, but verify:
    non_log_refs = [l for l in lines if re.search(r'\.(js|json|md|csv|tmp):', l)]
    if non_log_refs:
        # Soft warning - still pass but note it
        detail_note = f"Warning: some non-log file references found: {non_log_refs[:2]}. "
    else:
        detail_note = ""

    # Must match across at least 2 different log files (showing real content search)
    log_files_hit = set()
    for l in log_references:
        m = re.match(r'([^\s:]+\.log)', l)
        if m:
            log_files_hit.add(os.path.basename(m.group(1)))

    if len(log_files_hit) < 2:
        return check(
            "search_results.txt exists with correct content",
            False,
            f"Matches found in fewer than 2 distinct log files (got: {log_files_hit}). "
            "app-2024-01-10.log and app-2024-01-11.log both contain ERROR/CRITICAL."
        )

    return check(
        "search_results.txt exists with correct content",
        True,
        f"{detail_note}Found {len(error_hits)} ERROR/CRITICAL match line(s) across "
        f"{len(log_files_hit)} log files: {log_files_hit}"
    )

total_score += check_search_results()


# -----------------------------------------------------------------------
# CHECK 3: Log files copied to archive/logs/ directory
# Agent must use filesystem copy --pattern "*.log" --to ./archive/logs/ --preserve
# -----------------------------------------------------------------------

def check_copied_logs():
    archive_logs = workspace / "archive" / "logs"

    if not archive_logs.exists():
        return check(
            "Log files copied to archive/logs/",
            False,
            f"Directory {archive_logs} does not exist. Agent must create it via filesystem copy --to ./archive/logs/"
        )

    copied_files = list(archive_logs.glob("*.log"))
    if not copied_files:
        return check(
            "Log files copied to archive/logs/",
            False,
            f"No .log files found in {archive_logs}"
        )

    # There are 5 .log files in project/logs (including subdirectory)
    # Minimum: the 4 in project/logs/ must be present
    copied_names = {f.name for f in copied_files}
    source_logs_dir = workspace / "project" / "logs"
    source_log_names = {f.name for f in source_logs_dir.rglob("*.log")}

    # Must have copied at least the 4 top-level logs
    top_level_logs = {f.name for f in source_logs_dir.glob("*.log")}
    missing = top_level_logs - copied_names
    if len(missing) > 1:
        return check(
            "Log files copied to archive/logs/",
            False,
            f"Expected log files missing from archive. Missing: {missing}. "
            f"Found in archive: {copied_names}"
        )

    return check(
        "Log files copied to archive/logs/",
        True,
        f"Found {len(copied_files)} .log file(s) in {archive_logs}: {copied_names}"
    )

total_score += check_copied_logs()


# -----------------------------------------------------------------------
# CHECK 4: filesystem tool was actually used (ops log or preserved timestamps)
# Verify via /tmp/filesystem_ops.log that the tool was invoked correctly.
# -----------------------------------------------------------------------

def check_tool_usage():
    ops_log = Path("/tmp/filesystem_ops.log")

    if not ops_log.exists():
        # Fallback: check if archive/logs files have timestamps matching source
        # (--preserve would do this)
        archive_logs = workspace / "archive" / "logs"
        source_logs  = workspace / "project" / "logs"
        if archive_logs.exists():
            for f in archive_logs.glob("*.log"):
                src = source_logs / f.name
                if src.exists():
                    src_mtime = src.stat().st_mtime
                    dst_mtime = f.stat().st_mtime
                    if abs(src_mtime - dst_mtime) < 2:
                        return check(
                            "filesystem CLI tool used with required flags",
                            True,
                            "Timestamp preservation verified (--preserve flag used). "
                            "ops log not found but copy behavior confirms tool usage."
                        )
        return check(
            "filesystem CLI tool used with required flags",
            False,
            "/tmp/filesystem_ops.log not found. The filesystem CLI tool may not have been used."
        )

    try:
        lines = ops_log.read_text(encoding="utf-8").strip().splitlines()
        ops   = [json.loads(l) for l in lines if l.strip()]
    except Exception as e:
        return check(
            "filesystem CLI tool used with required flags",
            False,
            f"Could not parse /tmp/filesystem_ops.log: {e}"
        )

    cmds_used = {op.get("cmd") for op in ops}

    # Must have used analyze
    analyze_ops = [op for op in ops if op.get("cmd") == "analyze"]
    has_analyze_with_largest = any(op.get("largestN", 0) >= 5 for op in analyze_ops)

    # Must have used search with content=True
    search_ops = [op for op in ops if op.get("cmd") == "search"]
    has_content_search = any(op.get("content") for op in search_ops)

    # Must have used copy (real, not just dry-run)
    copy_ops = [op for op in ops if op.get("cmd") == "copy"]
    has_real_copy = any(not op.get("dryRun", False) for op in copy_ops)
    has_preserve  = any(op.get("preserve") for op in copy_ops)

    issues = []
    if not has_analyze_with_largest:
        issues.append("analyze with --largest >= 5 not found in ops log")
    if not has_content_search:
        issues.append("search with --content not found in ops log")
    if not has_real_copy:
        issues.append("copy (non-dry-run) not found in ops log")
    if not has_preserve:
        issues.append("copy without --preserve flag (preservation required)")

    if issues:
        return check(
            "filesystem CLI tool used with required flags",
            False,
            f"Tool usage issues: {'; '.join(issues)}. "
            f"Commands seen: {cmds_used}. Ops: {ops}"
        )

    return check(
        "filesystem CLI tool used with required flags",
        True,
        f"All required subcommands verified in ops log: {cmds_used}. "
        f"analyze(--largest≥5)=True, search(--content)=True, copy(--preserve)=True"
    )

total_score += check_tool_usage()


# -----------------------------------------------------------------------
# Final output
# -----------------------------------------------------------------------

final_passed = all(c["passed"] for c in checks)
score_norm   = total_score / max_score

print(json.dumps({
    "passed": final_passed,
    "score":  round(score_norm, 3),
    "checks": checks
}, indent=2))