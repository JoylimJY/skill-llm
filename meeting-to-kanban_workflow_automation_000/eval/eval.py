#!/usr/bin/env python3
"""
Evaluation script for the NucleoTrack meeting-to-kanban task.

Checks:
  1. kanban_board.csv exists and has correct schema columns
  2. CSV uses only valid column labels from board-columns.yaml
  3. Unresolved owners/dates are marked as "unresolved" (not blank/null/N/A)
  4. At least one task carries [ASSUMPTION] note
  5. manager_summary.md exists and contains meaningful content
  6. owners_table.md (or .csv) exists and references task IDs + owners
  7. open_questions.md (or .txt) exists and contains OPEN: marker lines
  8. At least one blocker is captured in the CSV
  9. The "Done" column is used (de-identification pipeline was completed)
 10. The "Waiting" column is used (blocked items exist)
"""

import csv
import json
import sys
import re
from pathlib import Path

REQUIRED_CSV_COLS = ["task_id", "title", "column", "owner", "due_date", "blockers", "notes"]
VALID_COLUMNS = {"Backlog", "Next", "Doing", "Waiting", "Done"}
UNRESOLVED_MARKER = "unresolved"
ASSUMPTION_PREFIX = "[ASSUMPTION]"
OPEN_QUESTIONS_MARKER = "OPEN:"


def find_file(workspace: Path, name: str) -> Path | None:
    hits = list(workspace.rglob(name))
    if hits:
        return hits[0]
    return None


def find_file_pattern(workspace: Path, pattern: str) -> Path | None:
    hits = list(workspace.rglob(pattern))
    if hits:
        return hits[0]
    return None


def evaluate(workspace_str: str) -> dict:
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0
    max_score = 10.0

    # ── 1. kanban_board.csv existence ──────────────────────────────────────
    csv_path = find_file(workspace, "kanban_board.csv")
    if csv_path is None:
        checks.append({"name": "kanban_board.csv exists", "passed": False,
                        "detail": "File 'kanban_board.csv' not found anywhere in workspace."})
    else:
        checks.append({"name": "kanban_board.csv exists", "passed": True,
                        "detail": str(csv_path)})
        total_score += 1.0

    # ── 2. CSV schema columns ───────────────────────────────────────────────
    tasks = []
    if csv_path:
        try:
            with open(csv_path, newline="") as fh:
                reader = csv.DictReader(fh)
                header = reader.fieldnames or []
                tasks = list(reader)
            missing_cols = [c for c in REQUIRED_CSV_COLS if c not in header]
            if missing_cols:
                checks.append({"name": "CSV has required schema columns", "passed": False,
                                "detail": f"Missing columns: {missing_cols}"})
            else:
                checks.append({"name": "CSV has required schema columns", "passed": True,
                                "detail": f"All {len(REQUIRED_CSV_COLS)} required columns present."})
                total_score += 1.0
        except Exception as exc:
            checks.append({"name": "CSV has required schema columns", "passed": False,
                            "detail": f"Error reading CSV: {exc}"})
    else:
        checks.append({"name": "CSV has required schema columns", "passed": False,
                        "detail": "CSV file missing; cannot check columns."})

    # ── 3. Only valid column labels used ───────────────────────────────────
    if tasks:
        try:
            bad_cols = {t["column"] for t in tasks if t.get("column") not in VALID_COLUMNS}
            if bad_cols:
                checks.append({"name": "Only valid column labels used", "passed": False,
                                "detail": f"Invalid column values found: {bad_cols}. "
                                          f"Allowed: {VALID_COLUMNS}"})
            else:
                checks.append({"name": "Only valid column labels used", "passed": True,
                                "detail": "All task column values match the board-columns.yaml schema."})
                total_score += 1.0
        except Exception as exc:
            checks.append({"name": "Only valid column labels used", "passed": False,
                            "detail": f"Error: {exc}"})
    else:
        checks.append({"name": "Only valid column labels used", "passed": False,
                        "detail": "No tasks to evaluate (CSV missing or empty)."})

    # ── 4. Unresolved markers used (not blank/null/N/A) ────────────────────
    if tasks:
        try:
            blank_owner = [t["task_id"] for t in tasks
                           if t.get("owner", "").strip().lower() in ("", "none", "n/a", "tbd", "null")]
            blank_date  = [t["task_id"] for t in tasks
                           if t.get("due_date", "").strip().lower() in ("", "none", "n/a", "tbd", "null")]
            if blank_owner or blank_date:
                checks.append({"name": "Unresolved fields marked as 'unresolved'", "passed": False,
                                "detail": f"Tasks with blank/null owner: {blank_owner}; "
                                          f"blank/null due_date: {blank_date}. "
                                          f"Must use the string '{UNRESOLVED_MARKER}'."})
            else:
                # Check that "unresolved" actually appears (some tasks must be unresolved per transcript)
                has_unresolved_owner = any(t.get("owner") == UNRESOLVED_MARKER for t in tasks)
                has_unresolved_date  = any(t.get("due_date") == UNRESOLVED_MARKER for t in tasks)
                if has_unresolved_owner or has_unresolved_date:
                    checks.append({"name": "Unresolved fields marked as 'unresolved'", "passed": True,
                                    "detail": "At least one task correctly uses 'unresolved' marker."})
                    total_score += 1.0
                else:
                    checks.append({"name": "Unresolved fields marked as 'unresolved'", "passed": False,
                                    "detail": "No 'unresolved' markers found. Transcript has tasks "
                                              "with no owner/date – those must be marked 'unresolved'."})
        except Exception as exc:
            checks.append({"name": "Unresolved fields marked as 'unresolved'", "passed": False,
                            "detail": f"Error: {exc}"})
    else:
        checks.append({"name": "Unresolved fields marked as 'unresolved'", "passed": False,
                        "detail": "No tasks to check."})

    # ── 5. [ASSUMPTION] notes present ──────────────────────────────────────
    if tasks:
        try:
            assumption_tasks = [t["task_id"] for t in tasks
                                 if ASSUMPTION_PREFIX in t.get("notes", "")]
            if assumption_tasks:
                checks.append({"name": "Explicit [ASSUMPTION] notes present", "passed": True,
                                "detail": f"Found {len(assumption_tasks)} task(s) with assumption notes: "
                                          f"{assumption_tasks[:5]}"})
                total_score += 1.0
            else:
                checks.append({"name": "Explicit [ASSUMPTION] notes present", "passed": False,
                                "detail": f"No notes contain '{ASSUMPTION_PREFIX}'. "
                                          "Tasks with missing owner/date must carry explicit assumption notes."})
        except Exception as exc:
            checks.append({"name": "Explicit [ASSUMPTION] notes present", "passed": False,
                            "detail": f"Error: {exc}"})
    else:
        checks.append({"name": "Explicit [ASSUMPTION] notes present", "passed": False,
                        "detail": "No tasks to check."})

    # ── 6. manager_summary.md exists and is non-trivial ────────────────────
    summary_path = find_file(workspace, "manager_summary.md")
    if summary_path is None:
        # accept .txt fallback
        summary_path = find_file(workspace, "manager_summary.txt")
    if summary_path is None:
        checks.append({"name": "manager_summary.md exists and is non-trivial", "passed": False,
                        "detail": "File 'manager_summary.md' (or .txt) not found."})
    else:
        try:
            content = summary_path.read_text()
            word_count = len(content.split())
            if word_count < 30:
                checks.append({"name": "manager_summary.md exists and is non-trivial", "passed": False,
                                "detail": f"Summary is too short ({word_count} words). "
                                          "Must contain a meaningful multi-sentence overview."})
            else:
                checks.append({"name": "manager_summary.md exists and is non-trivial", "passed": True,
                                "detail": f"Summary has {word_count} words at {summary_path}."})
                total_score += 1.0
        except Exception as exc:
            checks.append({"name": "manager_summary.md exists and is non-trivial", "passed": False,
                            "detail": f"Error reading summary: {exc}"})

    # ── 7. owners table exists ──────────────────────────────────────────────
    owners_path = (find_file(workspace, "owners_table.md")
                   or find_file(workspace, "owners_table.csv")
                   or find_file(workspace, "owners_due_dates.md")
                   or find_file(workspace, "owners_due_dates.csv"))
    if owners_path is None:
        checks.append({"name": "owners_table file exists", "passed": False,
                        "detail": "No owners table file found (expected owners_table.md/.csv or similar)."})
    else:
        try:
            content = owners_path.read_text()
            has_task_id = bool(re.search(r"T\d{3}", content))
            has_owner   = bool(re.search(r"[A-Z][a-z]+ [A-Z][a-z]+|unresolved", content))
            if has_task_id and has_owner:
                checks.append({"name": "owners_table file exists", "passed": True,
                                "detail": f"Owners table found with task IDs and owner names at {owners_path}."})
                total_score += 1.0
            else:
                checks.append({"name": "owners_table file exists", "passed": False,
                                "detail": f"Owners table at {owners_path} lacks task IDs or owner names."})
        except Exception as exc:
            checks.append({"name": "owners_table file exists", "passed": False,
                            "detail": f"Error reading owners table: {exc}"})

    # ── 8. open questions file with OPEN: marker ───────────────────────────
    oq_path = (find_file(workspace, "open_questions.md")
               or find_file(workspace, "open_questions.txt"))
    if oq_path is None:
        checks.append({"name": "open_questions file with OPEN: marker", "passed": False,
                        "detail": "No open_questions file found."})
    else:
        try:
            content = oq_path.read_text()
            open_lines = [l for l in content.splitlines() if OPEN_QUESTIONS_MARKER in l]
            if open_lines:
                checks.append({"name": "open_questions file with OPEN: marker", "passed": True,
                                "detail": f"Found {len(open_lines)} line(s) with '{OPEN_QUESTIONS_MARKER}' "
                                          f"marker at {oq_path}."})
                total_score += 1.0
            else:
                checks.append({"name": "open_questions file with OPEN: marker", "passed": False,
                                "detail": f"File exists at {oq_path} but no lines contain "
                                          f"'{OPEN_QUESTIONS_MARKER}'. The schema requires this prefix."})
        except Exception as exc:
            checks.append({"name": "open_questions file with OPEN: marker", "passed": False,
                            "detail": f"Error: {exc}"})

    # ── 9. At least one blocker captured ───────────────────────────────────
    if tasks:
        try:
            blocker_tasks = [t["task_id"] for t in tasks if t.get("blockers", "").strip()]
            if blocker_tasks:
                checks.append({"name": "At least one blocker captured in CSV", "passed": True,
                                "detail": f"Tasks with blockers: {blocker_tasks}"})
                total_score += 1.0
            else:
                checks.append({"name": "At least one blocker captured in CSV", "passed": False,
                                "detail": "No blockers found in CSV. Transcript contains at least "
                                          "two explicit blockers."})
        except Exception as exc:
            checks.append({"name": "At least one blocker captured in CSV", "passed": False,
                            "detail": f"Error: {exc}"})
    else:
        checks.append({"name": "At least one blocker captured in CSV", "passed": False,
                        "detail": "No tasks to check."})

    # ── 10. Done and Waiting columns both used ─────────────────────────────
    if tasks:
        try:
            cols_used = {t.get("column") for t in tasks}
            has_done    = "Done" in cols_used
            has_waiting = "Waiting" in cols_used
            if has_done and has_waiting:
                checks.append({"name": "Both 'Done' and 'Waiting' columns used", "passed": True,
                                "detail": f"Columns used: {cols_used}"})
                total_score += 1.0
            else:
                missing = []
                if not has_done:
                    missing.append("Done")
                if not has_waiting:
                    missing.append("Waiting")
                checks.append({"name": "Both 'Done' and 'Waiting' columns used", "passed": False,
                                "detail": f"Missing columns in CSV data: {missing}. "
                                          "The transcript has both a completed item and blocked items."})
        except Exception as exc:
            checks.append({"name": "Both 'Done' and 'Waiting' columns used", "passed": False,
                            "detail": f"Error: {exc}"})
    else:
        checks.append({"name": "Both 'Done' and 'Waiting' columns used", "passed": False,
                        "detail": "No tasks to check."})

    passed = total_score >= 7.0  # need 7/10 to pass
    score  = round(total_score / max_score, 2)

    return {
        "passed": passed,
        "score": score,
        "checks": checks,
    }


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: eval.py <workspace_path>"}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))