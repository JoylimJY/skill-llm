#!/usr/bin/env python3
"""
Evaluation script for the workspace-audit task.
Usage: python eval.py /workspace
"""
import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime, timedelta

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []
total_score = 0.0

def check(name: str, passed: bool, detail: str, weight: float = 1.0):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return weight if passed else 0.0

def read_file(path: Path) -> str:
    try:
        return path.read_text(errors="replace")
    except Exception as e:
        return ""

# ─── 1. Broken link detected: projects/genomics/pipeline.md ─────────────────
# cron-004 references projects/genomics/pipeline.md which doesn't exist
# The agent must run `cron list`, parse messages, and flag this.
report_files = list(workspace.rglob("audit-report*")) + list(workspace.rglob("*audit*report*")) + list(workspace.rglob("AUDIT*"))
# Also check MEMORY.md and any new .md at root that looks like a report
possible_reports = report_files[:]
for f in workspace.glob("*.md"):
    content = f.read_text(errors="replace") if f.exists() else ""
    if "Workspace Audit" in content or "workspace audit" in content.lower():
        possible_reports.append(f)

report_content = ""
report_path = None
for rf in possible_reports:
    try:
        c = rf.read_text(errors="replace")
        if len(c) > len(report_content):
            report_content = c
            report_path = rf
    except Exception:
        pass

# ─── Check 1: Report exists ──────────────────────────────────────────────────
s = check(
    "report_exists",
    bool(report_content),
    f"Audit report found at: {report_path}" if report_content else "No audit report found (expected a file with 'Workspace Audit' content)"
)
total_score += s

# ─── Check 2: Broken link to pipeline.md flagged ────────────────────────────
broken_link_flagged = (
    "pipeline.md" in report_content or
    "genomics/pipeline" in report_content or
    "broken" in report_content.lower() and "pipeline" in report_content.lower()
)
s = check(
    "broken_link_pipeline_flagged",
    broken_link_flagged,
    "Report mentions broken link to projects/genomics/pipeline.md" if broken_link_flagged
    else "Report does NOT mention the broken cron link to projects/genomics/pipeline.md"
)
total_score += s

# ─── Check 3: Orphaned file detected ─────────────────────────────────────────
orphan_flagged = (
    "temp-calculations" in report_content or
    "temp_calculations" in report_content or
    "orphan" in report_content.lower() and "temp" in report_content.lower()
)
s = check(
    "orphaned_file_detected",
    orphan_flagged,
    "Report mentions orphaned file memory/temp-calculations.md" if orphan_flagged
    else "Report does NOT mention orphaned file memory/temp-calculations.md"
)
total_score += s

# ─── Check 4: Content drift detected between local-override sync pair ────────
# memory/reagents.md ## Approved Reagents vs projects/lab-protocols/approved-reagents.md ## Approved Reagents
drift_flagged = (
    ("drift" in report_content.lower() or "sync" in report_content.lower() or "mismatch" in report_content.lower())
    and ("reagent" in report_content.lower() or "approved" in report_content.lower())
)
s = check(
    "content_drift_reagents_detected",
    drift_flagged,
    "Report detects sync drift between reagents sections" if drift_flagged
    else "Report does NOT detect content drift between reagents sync pair (local-overrides requirement)"
)
total_score += s

# ─── Check 5: Daily notes older than 7 days archived ────────────────────────
archive_dir = workspace / "memory" / "archive"
archived_files = list(archive_dir.glob("*.md")) if archive_dir.exists() else []
archived_names = [f.name for f in archived_files]

# 2024-01-05 (20 days old), 2024-01-08 (14 days old), 2024-01-09 (13 days old) should be archived
old_daily_archived = (
    any("2024-01-05" in n for n in archived_names) and
    any("2024-01-08" in n for n in archived_names) and
    any("2024-01-09" in n for n in archived_names)
)
s = check(
    "old_daily_notes_archived",
    old_daily_archived,
    f"Old daily notes (01-05, 01-08, 01-09) found in archive: {archived_names}" if old_daily_archived
    else f"Old daily notes NOT fully archived. Archive contains: {archived_names}"
)
total_score += s

# ─── Check 6: Recent daily note NOT archived ─────────────────────────────────
recent_not_archived = not any("2024-01-15" in n for n in archived_names)
s = check(
    "recent_daily_note_not_archived",
    recent_not_archived,
    "2024-01-15 note correctly NOT archived (< 7 days old)" if recent_not_archived
    else "2024-01-15 note was incorrectly archived (it is < 7 days old)"
)
total_score += s

# ─── Check 7: OLD-PROTOCOLS.md demoted (HOT → WARM) ─────────────────────────
# OLD-PROTOCOLS.md has zero references and is 45 days old → should be demoted
# Demotion means: removed from MEMORY.md summary (it was never there, but demotion should be reported)
# OR the report mentions it
memory_content = read_file(workspace / "MEMORY.md")
old_proto_demoted = (
    "OLD-PROTOCOLS" in report_content or
    "old-protocols" in report_content.lower() or
    ("demot" in report_content.lower() and "protocol" in report_content.lower())
)
s = check(
    "old_protocols_demoted_reported",
    old_proto_demoted,
    "Report mentions demotion of OLD-PROTOCOLS.md" if old_proto_demoted
    else "Report does NOT mention demotion of OLD-PROTOCOLS.md (zero refs, 45 days old → HOT→WARM)"
)
total_score += s

# ─── Check 8: compound-x-summary.md promoted (WARM → HOT) ───────────────────
# compound-x-summary.md: referenced by STATUS.md, experiment-log.md, buffer-prep.md (3 refs),
# has ## Summary section, modified 2 days ago → should be promoted
promoted_flagged = (
    "compound-x-summary" in report_content or
    "compound_x_summary" in report_content or
    ("promot" in report_content.lower() and "summary" in report_content.lower()) or
    ("promot" in report_content.lower() and "compound" in report_content.lower())
)
# Also check MEMORY.md was updated with a summary line
memory_promoted = (
    "compound-x-summary" in memory_content or
    "Compound-X Summary" in memory_content
)
promotion_ok = promoted_flagged or memory_promoted
s = check(
    "compound_x_summary_promoted",
    promotion_ok,
    "Promotion of memory/compound-x-summary.md detected in report or MEMORY.md" if promotion_ok
    else "Promotion of memory/compound-x-summary.md NOT detected (3 refs, has ## Summary, recent → WARM→HOT)"
)
total_score += s

# ─── Check 9: MEMORY.md current phase sync checked ──────────────────────────
# local-overrides: projects/compound-x/STATUS.md ## Current Phase → MEMORY.md ## Current Phase
# Both say "Phase 2 — Lead Optimisation" so they should be in sync (no drift here)
phase_sync_checked = (
    "Current Phase" in report_content or
    "phase" in report_content.lower() and "sync" in report_content.lower() or
    "All in sync" in report_content or
    "in sync" in report_content.lower()
)
s = check(
    "local_override_phase_sync_checked",
    phase_sync_checked,
    "Report addresses the Current Phase sync pair from local-overrides" if phase_sync_checked
    else "Report does NOT address the Current Phase local-override sync pair"
)
total_score += s

# ─── Check 10: Report has correct structure ──────────────────────────────────
has_dependencies_section = "Dependencies" in report_content or "dependencies" in report_content.lower()
has_cleaned_section = "Cleaned" in report_content or "cleaned" in report_content.lower()
has_tier_section = "Tier" in report_content or "tier" in report_content.lower() or "Promot" in report_content or "Demot" in report_content
has_health_section = "Health" in report_content or "health" in report_content.lower()
has_sync_section = "Sync" in report_content or "sync" in report_content.lower() or "Override" in report_content

structure_ok = sum([has_dependencies_section, has_cleaned_section, has_tier_section, has_health_section, has_sync_section]) >= 4
s = check(
    "report_structure_correct",
    structure_ok,
    f"Report has required sections: deps={has_dependencies_section}, cleaned={has_cleaned_section}, tier={has_tier_section}, health={has_health_section}, sync={has_sync_section}"
    if structure_ok else
    f"Report missing required sections: deps={has_dependencies_section}, cleaned={has_cleaned_section}, tier={has_tier_section}, health={has_health_section}, sync={has_sync_section}"
)
total_score += s

# ─── Check 11: pinned file reagents.md NOT archived ──────────────────────────
# memory/reagents.md is in local-overrides ## pinned → must NOT be moved to archive
reagents_still_warm = (workspace / "memory" / "reagents.md").exists()
reagents_not_in_archive = not (workspace / "memory" / "archive" / "reagents.md").exists()
reagents_pinned_ok = reagents_still_warm and reagents_not_in_archive
s = check(
    "pinned_reagents_not_archived",
    reagents_pinned_ok,
    "memory/reagents.md remains in memory/ (not archived) as required by pinned override" if reagents_pinned_ok
    else f"memory/reagents.md incorrectly handled: in memory/={reagents_still_warm}, in archive/={not reagents_not_in_archive}"
)
total_score += s

# ─── Check 12: Report has date ───────────────────────────────────────────────
date_present = bool(re.search(r'\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}|January|February|March|April|May|June|July|August|September|October|November|December', report_content))
s = check(
    "report_has_date",
    date_present,
    "Report contains a date reference" if date_present else "Report does not contain any date"
)
total_score += s

# ─── Final score ─────────────────────────────────────────────────────────────
max_score = 12.0
final_score = round(total_score / max_score, 3)
passed = final_score >= 0.65

output = {
    "passed": passed,
    "score": final_score,
    "checks": checks
}
print(json.dumps(output, indent=2))