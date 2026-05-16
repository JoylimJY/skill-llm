#!/usr/bin/env python3
"""
Evaluation script for the finml-toolkit audit trail task.
Usage: python3 eval_script.py /workspace
"""
import sys
import json
import os
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
score = 0.0

DATA_DIR = Path(os.path.expanduser("~/.local/share/finml-toolkit"))

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# ─── CHECK 1: All 7 required log entries exist in their respective log files ──
required_log_entries = [
    ("run.log",     "backtest strategy alpha-3"),
    ("check.log",   "validate portfolio weights"),
    ("convert.log", "csv to parquet format"),
    ("analyze.log", "correlation matrix on sector data"),
    ("compare.log", "strategy A vs strategy B returns"),
    ("config.log",  "set risk_threshold=0.05"),
    ("batch.log",   "process all Q4 earnings files"),
]

all_log_entries_found = True
missing = []
for log_name, expected_input in required_log_entries:
    log_file = DATA_DIR / log_name
    try:
        content = log_file.read_text()
        # Format: YYYY-MM-DD HH:MM|<input>
        pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}\|" + re.escape(expected_input) + r"$"
        if not re.search(pattern, content, re.MULTILINE):
            all_log_entries_found = False
            missing.append(f"{log_name}:{expected_input}")
    except Exception as e:
        all_log_entries_found = False
        missing.append(f"{log_name}: ERROR({e})")

if all_log_entries_found:
    score += 0.25
    checks.append(make_check(
        "All 7 pipeline steps logged to correct command-specific log files",
        True,
        "All entries found in correct log files with proper YYYY-MM-DD HH:MM|input format."
    ))
else:
    checks.append(make_check(
        "All 7 pipeline steps logged to correct command-specific log files",
        False,
        f"Missing or malformed entries: {missing}"
    ))

# ─── CHECK 2: history.log contains all 7 entries in YYYY-MM-DD HH:MM|cmd|input format ──
history_file = DATA_DIR / "history.log"
history_entries_ok = True
missing_history = []
required_history = [
    ("run",     "backtest strategy alpha-3"),
    ("check",   "validate portfolio weights"),
    ("convert", "csv to parquet format"),
    ("analyze", "correlation matrix on sector data"),
    ("compare", "strategy A vs strategy B returns"),
    ("config",  "set risk_threshold=0.05"),
    ("batch",   "process all Q4 earnings files"),
]
try:
    history_content = history_file.read_text()
    for cmd_name, expected_input in required_history:
        pattern = r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}\|" + re.escape(cmd_name) + r"\|" + re.escape(expected_input) + r"$"
        if not re.search(pattern, history_content, re.MULTILINE):
            history_entries_ok = False
            missing_history.append(f"{cmd_name}|{expected_input}")
except Exception as e:
    history_entries_ok = False
    missing_history.append(f"history.log: ERROR({e})")

if history_entries_ok:
    score += 0.15
    checks.append(make_check(
        "history.log contains all 7 entries with YYYY-MM-DD HH:MM|cmd|input format",
        True,
        "All 7 entries found in history.log with correct pipe-delimited three-field format."
    ))
else:
    checks.append(make_check(
        "history.log contains all 7 entries with YYYY-MM-DD HH:MM|cmd|input format",
        False,
        f"Missing entries in history.log: {missing_history}"
    ))

# ─── CHECK 3: export.json exists in DATA_DIR (NOT in workspace or exports/) ──
export_json = DATA_DIR / "export.json"
try:
    export_content = export_json.read_text()
    try:
        export_data = json.loads(export_content)
        has_entries = "entries" in export_data and isinstance(export_data["entries"], list)
        has_timestamp = "exported_at" in export_data
        
        # Check that the 7 required entries appear in the export
        entry_inputs = {e.get("input", "") for e in export_data.get("entries", [])}
        required_inputs = {
            "backtest strategy alpha-3",
            "validate portfolio weights",
            "csv to parquet format",
            "correlation matrix on sector data",
            "strategy A vs strategy B returns",
            "set risk_threshold=0.05",
            "process all Q4 earnings files",
        }
        missing_in_export = required_inputs - entry_inputs

        if has_entries and has_timestamp and not missing_in_export:
            score += 0.25
            checks.append(make_check(
                "export.json in DATA_DIR is valid JSON with all 7 pipeline entries",
                True,
                f"Valid export.json at {export_json} with {len(export_data['entries'])} entries including all required operations."
            ))
        else:
            detail_parts = []
            if not has_entries:
                detail_parts.append("Missing 'entries' array")
            if not has_timestamp:
                detail_parts.append("Missing 'exported_at' field")
            if missing_in_export:
                detail_parts.append(f"Missing inputs in export: {missing_in_export}")
            checks.append(make_check(
                "export.json in DATA_DIR is valid JSON with all 7 pipeline entries",
                False,
                "; ".join(detail_parts)
            ))
    except json.JSONDecodeError as je:
        checks.append(make_check(
            "export.json in DATA_DIR is valid JSON with all 7 pipeline entries",
            False,
            f"export.json is not valid JSON: {je}"
        ))
except FileNotFoundError:
    # Check if agent wrongly put it in workspace
    wrong_locations = list(workspace.rglob("export.json"))
    detail = f"export.json not found at {export_json}."
    if wrong_locations:
        detail += f" Found at wrong location(s): {wrong_locations}"
    checks.append(make_check(
        "export.json in DATA_DIR is valid JSON with all 7 pipeline entries",
        False,
        detail
    ))
except Exception as e:
    checks.append(make_check(
        "export.json in DATA_DIR is valid JSON with all 7 pipeline entries",
        False,
        f"Unexpected error reading export.json: {e}"
    ))

# ─── CHECK 4: pipeline_stats.txt exists in workspace and contains stats output ──
stats_files = list(workspace.rglob("pipeline_stats.txt"))
if stats_files:
    try:
        stats_content = stats_files[0].read_text()
        # Must contain "TOTAL" and at least some command names from our logged operations
        has_total = "TOTAL" in stats_content
        has_run = "run" in stats_content.lower()
        has_analyze = "analyze" in stats_content.lower()
        has_entries_count = bool(re.search(r'\d+\s+entr', stats_content, re.IGNORECASE))
        
        if has_total and has_run and has_analyze:
            score += 0.20
            checks.append(make_check(
                "pipeline_stats.txt contains valid stats output",
                True,
                f"Found at {stats_files[0]}. Contains TOTAL and per-command counts."
            ))
        else:
            missing_parts = []
            if not has_total:
                missing_parts.append("'TOTAL' line missing")
            if not has_run:
                missing_parts.append("'run' entries missing")
            if not has_analyze:
                missing_parts.append("'analyze' entries missing")
            checks.append(make_check(
                "pipeline_stats.txt contains valid stats output",
                False,
                f"Stats file incomplete. Issues: {missing_parts}. Content preview: {stats_content[:200]}"
            ))
    except Exception as e:
        checks.append(make_check(
            "pipeline_stats.txt contains valid stats output",
            False,
            f"Error reading pipeline_stats.txt: {e}"
        ))
else:
    checks.append(make_check(
        "pipeline_stats.txt contains valid stats output",
        False,
        "pipeline_stats.txt not found anywhere in workspace."
    ))

# ─── CHECK 5: search_results.txt exists and contains a match for "portfolio" ──
search_files = list(workspace.rglob("search_results.txt"))
if search_files:
    try:
        search_content = search_files[0].read_text()
        # Must contain the "validate portfolio weights" entry
        has_portfolio_hit = "portfolio" in search_content.lower()
        has_validate = "validate portfolio weights" in search_content.lower()
        
        if has_portfolio_hit and has_validate:
            score += 0.15
            checks.append(make_check(
                "search_results.txt contains search output with 'portfolio' hits",
                True,
                f"Found at {search_files[0]}. Contains 'validate portfolio weights' match."
            ))
        else:
            checks.append(make_check(
                "search_results.txt contains search output with 'portfolio' hits",
                False,
                f"search_results.txt missing expected matches. has_portfolio={has_portfolio_hit}, has_validate={has_validate}. Content: {search_content[:300]}"
            ))
    except Exception as e:
        checks.append(make_check(
            "search_results.txt contains search output with 'portfolio' hits",
            False,
            f"Error reading search_results.txt: {e}"
        ))
else:
    checks.append(make_check(
        "search_results.txt contains search output with 'portfolio' hits",
        False,
        "search_results.txt not found anywhere in workspace."
    ))

# ─── Final Score ──────────────────────────────────────────────────────────────
passed = score >= 0.75

result = {
    "passed": passed,
    "score": round(score, 4),
    "checks": checks
}

print(json.dumps(result, indent=2))