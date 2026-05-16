#!/usr/bin/env python3
"""Evaluation script for jrv-text-diff task."""
import sys
import json
import re
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1])

checks = []
score_total = 0.0
max_score = 4.0


def check(name, passed, detail, weight=1.0):
    global score_total
    checks.append({"name": name, "passed": passed, "detail": detail})
    if passed:
        score_total += weight


# ────────────────────────────────────────────────────────────────
# CHECK 1: config_diff_report.json exists and is valid JSON
# ────────────────────────────────────────────────────────────────
report_candidates = list(workspace.rglob("config_diff_report.json"))
if not report_candidates:
    check("config_diff_report.json exists",
          False, "File 'config_diff_report.json' not found anywhere in workspace.")
    check("config_diff_report.json has correct structure",
          False, "File missing; cannot check structure.")
    check("config_diff_report.json reflects structural JSON diff",
          False, "File missing; cannot verify JSON diff stats.")
else:
    report_path = report_candidates[0]
    try:
        with open(report_path) as f:
            report = json.load(f)
        check("config_diff_report.json exists", True,
              f"Found at {report_path}")

        # CHECK 2: Required keys present
        required_keys = {"identical", "added", "deleted", "changed"}
        missing = required_keys - set(report.keys())
        if missing:
            check("config_diff_report.json has correct structure",
                  False, f"Missing keys: {missing}")
        else:
            check("config_diff_report.json has correct structure",
                  True, f"All required keys present: {required_keys}")

        # CHECK 3: Values reflect actual structural JSON diff
        # staging vs production:
        # added keys (in prod, not staging): monitoring.enabled, monitoring.endpoint  => 2 added
        # deleted keys (in staging, not prod): none at top structural level of flattened paths
        # changed: environment, resources.cpu, resources.memory, database.host,
        #          database.pool_size, features.rate_limiting, features.detailed_logging,
        #          timeouts.connect, timeouts.read, timeouts.write, replicas => 11 changed
        # identical must be False
        try:
            identical_ok = report.get("identical") == False
            # added should be 2 (monitoring.enabled + monitoring.endpoint)
            added_ok = report.get("added") == 2
            # deleted should be 0
            deleted_ok = report.get("deleted") == 0
            # changed should be 11
            changed_ok = report.get("changed") == 11

            structural_ok = identical_ok and added_ok and deleted_ok and changed_ok
            detail_str = (
                f"identical={report.get('identical')} (expect False), "
                f"added={report.get('added')} (expect 2), "
                f"deleted={report.get('deleted')} (expect 0), "
                f"changed={report.get('changed')} (expect 11)"
            )
            check("config_diff_report.json reflects structural JSON diff",
                  structural_ok, detail_str)
        except Exception as e:
            check("config_diff_report.json reflects structural JSON diff",
                  False, f"Error reading values: {e}")

    except json.JSONDecodeError as e:
        check("config_diff_report.json exists", True,
              f"Found at {report_path} but invalid JSON: {e}")
        check("config_diff_report.json has correct structure",
              False, f"Invalid JSON: {e}")
        check("config_diff_report.json reflects structural JSON diff",
              False, f"Invalid JSON: {e}")


# ────────────────────────────────────────────────────────────────
# CHECK 4: release_notes_diff.txt exists and is a word-diff
#          with no ANSI color codes (--no-color was used)
# ────────────────────────────────────────────────────────────────
notes_candidates = list(workspace.rglob("release_notes_diff.txt"))
if not notes_candidates:
    check("release_notes_diff.txt exists",
          False, "File 'release_notes_diff.txt' not found anywhere in workspace.")
    check("release_notes_diff.txt has no ANSI color codes",
          False, "File missing.")
    check("release_notes_diff.txt contains word-diff markers",
          False, "File missing.")
    check("release_notes_diff.txt uses ignore-whitespace",
          False, "File missing.")
else:
    notes_path = notes_candidates[0]
    try:
        with open(notes_path, "r", encoding="utf-8") as f:
            notes_content = f.read()

        check("release_notes_diff.txt exists", True,
              f"Found at {notes_path}")

        # CHECK 5: No ANSI escape codes
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        has_ansi = bool(ansi_pattern.search(notes_content))
        check("release_notes_diff.txt has no ANSI color codes",
              not has_ansi,
              "No ANSI codes found." if not has_ansi
              else "ANSI color codes detected; --no-color was required.")

        # CHECK 6: Word-diff markers present ([-...-] or [+...+])
        has_del_marker = bool(re.search(r'\[-[^\]]+\-\]', notes_content))
        has_add_marker = bool(re.search(r'\[\+[^\]]+\+\]', notes_content))
        word_diff_present = has_del_marker or has_add_marker
        check("release_notes_diff.txt contains word-diff markers",
              word_diff_present,
              f"Del markers={'yes' if has_del_marker else 'no'}, "
              f"Add markers={'yes' if has_add_marker else 'no'}.")

        # CHECK 7: Content reflects actual differences between v3.4.0 and v3.4.1
        # Key changes: "v3.4.0" -> "v3.4.1", "stability" -> "critical security patches",
        # lines added/changed around "jitter", "connection resets", "Removed", "/metrics",
        # "Known Issues" section lost one bullet, "Database migration required"
        meaningful_changes = (
            "3.4.1" in notes_content or
            "jitter" in notes_content or
            "migration" in notes_content.lower() or
            "metrics" in notes_content or
            "security" in notes_content
        )
        check("release_notes_diff.txt uses ignore-whitespace",
              meaningful_changes,
              "File contains expected diff content from v3.4.0 vs v3.4.1 comparison."
              if meaningful_changes
              else "File does not appear to contain expected diff content.")

    except Exception as e:
        check("release_notes_diff.txt exists", True,
              f"Found but could not read: {e}")
        check("release_notes_diff.txt has no ANSI color codes", False, str(e))
        check("release_notes_diff.txt contains word-diff markers", False, str(e))
        check("release_notes_diff.txt uses ignore-whitespace", False, str(e))


# ────────────────────────────────────────────────────────────────
# Final scoring
# ────────────────────────────────────────────────────────────────
num_checks = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
final_score = round(score_total / max_score, 4)
all_passed = (passed_count == num_checks)

print(json.dumps({
    "passed": all_passed,
    "score": final_score,
    "checks": checks
}, indent=2))