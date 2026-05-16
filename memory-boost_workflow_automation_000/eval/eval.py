import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace_str):
    workspace = Path(workspace_str)
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    
    checks = []
    total_score = 0.0
    max_score = 0.0

    # ------------------------------------------------------------------ #
    # Helper
    # ------------------------------------------------------------------ #
    def add_check(name, passed, detail, weight=1.0):
        nonlocal total_score, max_score
        checks.append({"name": name, "passed": passed, "detail": detail})
        max_score += weight
        if passed:
            total_score += weight

    # ================================================================== #
    # CHECK 1: Today's daily log file exists at correct path
    # ================================================================== #
    today_log_path = workspace / "memory" / f"{today_str}.md"
    try:
        if today_log_path.exists():
            today_log = today_log_path.read_text()
            add_check(
                "daily_log_exists",
                True,
                f"Found today's session log at memory/{today_str}.md",
                weight=2.0
            )
        else:
            # Search for any file with today's date in memory dir
            candidates = list((workspace / "memory").glob(f"{today_str}*"))
            if candidates:
                today_log = candidates[0].read_text()
                add_check(
                    "daily_log_exists",
                    True,
                    f"Found today's log at {candidates[0].name}",
                    weight=2.0
                )
            else:
                add_check(
                    "daily_log_exists",
                    False,
                    f"No daily log found for today ({today_str}) in memory/ directory",
                    weight=2.0
                )
                today_log = ""
    except Exception as e:
        add_check("daily_log_exists", False, f"Error reading today's log: {e}", weight=2.0)
        today_log = ""

    # ================================================================== #
    # CHECK 2: Today's log has required sections (## Completed, ## In Progress, ## Notes)
    # ================================================================== #
    try:
        has_completed = bool(re.search(r"##\s+Completed", today_log))
        has_in_progress = bool(re.search(r"##\s+In Progress", today_log))
        has_notes = bool(re.search(r"##\s+Notes", today_log))
        all_sections = has_completed and has_in_progress and has_notes
        add_check(
            "daily_log_has_required_sections",
            all_sections,
            f"Sections found — Completed: {has_completed}, In Progress: {has_in_progress}, Notes: {has_notes}",
            weight=1.5
        )
    except Exception as e:
        add_check("daily_log_has_required_sections", False, f"Error checking sections: {e}", weight=1.5)

    # ================================================================== #
    # CHECK 3: Today's log records the DB migration completion
    # ================================================================== #
    try:
        migration_keywords = ["migration", "mongo", "postgresql", "postgres", "migrate"]
        log_lower = today_log.lower()
        mentions_migration = any(kw in log_lower for kw in migration_keywords)
        # Should be under Completed section
        completed_section_match = re.search(r"##\s+Completed(.*?)(?=##|\Z)", today_log, re.DOTALL | re.IGNORECASE)
        if completed_section_match:
            completed_text = completed_section_match.group(1).lower()
            mentions_in_completed = any(kw in completed_text for kw in migration_keywords)
        else:
            mentions_in_completed = False
        
        add_check(
            "daily_log_records_migration_completion",
            mentions_migration,
            f"Migration mentioned in log: {mentions_migration}, in Completed section: {mentions_in_completed}",
            weight=1.5
        )
    except Exception as e:
        add_check("daily_log_records_migration_completion", False, f"Error: {e}", weight=1.5)

    # ================================================================== #
    # CHECK 4: MEMORY.md exists and is readable
    # ================================================================== #
    memory_md_path = workspace / "MEMORY.md"
    try:
        memory_md = memory_md_path.read_text()
        add_check("memory_md_exists", True, "MEMORY.md found and readable", weight=1.0)
    except Exception as e:
        add_check("memory_md_exists", False, f"Could not read MEMORY.md: {e}", weight=1.0)
        memory_md = ""

    # ================================================================== #
    # CHECK 5: MEMORY.md has the 3 mandatory top-level sections with emoji headers
    # ================================================================== #
    try:
        has_active_projects = bool(re.search(r"##\s+🎯\s+Active Projects", memory_md))
        has_user_prefs = bool(re.search(r"##\s+👤\s+User Preferences", memory_md))
        has_decisions = bool(re.search(r"##\s+📚\s+Important Decisions", memory_md))
        all_present = has_active_projects and has_user_prefs and has_decisions
        add_check(
            "memory_md_has_emoji_sections",
            all_present,
            f"🎯 Active Projects: {has_active_projects}, 👤 User Preferences: {has_user_prefs}, 📚 Important Decisions: {has_decisions}",
            weight=2.0
        )
    except Exception as e:
        add_check("memory_md_has_emoji_sections", False, f"Error: {e}", weight=2.0)

    # ================================================================== #
    # CHECK 6: MEMORY.md Active Projects table updated — DB Migration marked as complete (✅ or Done/Completed)
    # ================================================================== #
    try:
        active_projects_match = re.search(
            r"##\s+🎯\s+Active Projects(.*?)(?=##|\Z)", memory_md, re.DOTALL
        )
        if active_projects_match:
            ap_text = active_projects_match.group(1)
            # Look for DB Migration row with completed/done status
            migration_row_match = re.search(
                r"\|\s*.*[Mm]igrat.*\|.*\|.*\|.*\|", ap_text
            )
            if migration_row_match:
                migration_row = migration_row_match.group(0)
                is_completed = bool(re.search(
                    r"(✅|[Cc]omplete[d]?|[Dd]one|🟢)", migration_row
                ))
                add_check(
                    "memory_md_migration_status_updated",
                    is_completed,
                    f"Migration row found: '{migration_row.strip()}', marked complete: {is_completed}",
                    weight=2.0
                )
            else:
                # Maybe the migration row was removed (project done) — also acceptable
                # Check if it's simply not in In Progress anymore
                in_progress_migration = bool(re.search(r"[Mm]igrat.*🟡", ap_text))
                add_check(
                    "memory_md_migration_status_updated",
                    not in_progress_migration,
                    f"No migration row found in Active Projects; no 'in-progress' migration entry: {not in_progress_migration}",
                    weight=2.0
                )
        else:
            add_check(
                "memory_md_migration_status_updated",
                False,
                "Active Projects section not found in MEMORY.md",
                weight=2.0
            )
    except Exception as e:
        add_check("memory_md_migration_status_updated", False, f"Error: {e}", weight=2.0)

    # ================================================================== #
    # CHECK 7: MEMORY.md Important Decisions — new decision added with today's date
    # ================================================================== #
    try:
        decisions_match = re.search(
            r"##\s+📚\s+Important Decisions(.*?)(?=##|\Z)", memory_md, re.DOTALL
        )
        if decisions_match:
            decisions_text = decisions_match.group(1)
            # Check today's date header appears
            has_today_header = bool(re.search(
                rf"###\s+{re.escape(today_str)}", decisions_text
            ))
            # Check decision has both **Decision:** and **Reason:** fields
            has_decision_field = bool(re.search(r"\*\*Decision:\*\*", decisions_text))
            has_reason_field = bool(re.search(r"\*\*Reason:\*\*", decisions_text))
            # Check migration-related content in new decision
            mentions_mongo_or_migration = bool(re.search(
                r"(mongo|migrat|postgresql|postgres)", decisions_text, re.IGNORECASE
            ))
            
            passed = has_today_header and has_decision_field and has_reason_field
            add_check(
                "memory_md_new_decision_with_reason",
                passed,
                (f"Today's date header (###): {has_today_header}, "
                 f"**Decision:** field: {has_decision_field}, "
                 f"**Reason:** field: {has_reason_field}, "
                 f"Migration content: {mentions_mongo_or_migration}"),
                weight=3.0
            )
        else:
            add_check(
                "memory_md_new_decision_with_reason",
                False,
                "📚 Important Decisions section not found",
                weight=3.0
            )
    except Exception as e:
        add_check("memory_md_new_decision_with_reason", False, f"Error: {e}", weight=3.0)

    # ================================================================== #
    # CHECK 8: MEMORY_INDEX.md exists and is updated
    # ================================================================== #
    index_path = workspace / "MEMORY_INDEX.md"
    try:
        index_md = index_path.read_text()
        add_check("memory_index_exists", True, "MEMORY_INDEX.md found", weight=1.0)
    except Exception as e:
        add_check("memory_index_exists", False, f"Could not read MEMORY_INDEX.md: {e}", weight=1.0)
        index_md = ""

    # ================================================================== #
    # CHECK 9: MEMORY_INDEX.md project status reflects migration completion
    # ================================================================== #
    try:
        if index_md:
            migration_in_index = bool(re.search(r"[Mm]igrat", index_md))
            migration_done_in_index = bool(re.search(
                r"[Mm]igrat.*(✅|[Cc]omplete[d]?|[Dd]one|🟢)", index_md
            ))
            # Acceptable: either migration shown as done, or removed from active list
            # Check if "In Progress" still shown for migration  
            still_in_progress = bool(re.search(r"[Mm]igrat.*🟡", index_md))
            updated = migration_done_in_index or not still_in_progress
            add_check(
                "memory_index_migration_status_updated",
                updated,
                (f"Migration in index: {migration_in_index}, "
                 f"Marked complete: {migration_done_in_index}, "
                 f"Still in-progress: {still_in_progress}"),
                weight=1.5
            )
        else:
            add_check(
                "memory_index_migration_status_updated",
                False,
                "MEMORY_INDEX.md is empty or missing",
                weight=1.5
            )
    except Exception as e:
        add_check("memory_index_migration_status_updated", False, f"Error: {e}", weight=1.5)

    # ================================================================== #
    # CHECK 10: MEMORY.md has an Active Projects table (pipe-delimited)
    # ================================================================== #
    try:
        # Validate the table format (has header, separator, data rows)
        has_table = bool(re.search(
            r"\|\s*Project\s*\|.*Status.*\|.*Links.*\|.*Last Updated.*\|", memory_md
        ))
        add_check(
            "memory_md_active_projects_table_format",
            has_table,
            f"Active Projects table with correct columns found: {has_table}",
            weight=1.5
        )
    except Exception as e:
        add_check("memory_md_active_projects_table_format", False, f"Error: {e}", weight=1.5)

    # ================================================================== #
    # CHECK 11: Last Updated in MEMORY_INDEX.md reflects today (freshness)
    # ================================================================== #
    try:
        if index_md:
            has_today_updated = bool(re.search(re.escape(today_str), index_md))
            add_check(
                "memory_index_last_updated_today",
                has_today_updated,
                f"MEMORY_INDEX.md contains today's date ({today_str}): {has_today_updated}",
                weight=1.0
            )
        else:
            add_check(
                "memory_index_last_updated_today",
                False,
                "MEMORY_INDEX.md missing",
                weight=1.0
            )
    except Exception as e:
        add_check("memory_index_last_updated_today", False, f"Error: {e}", weight=1.0)

    # ================================================================== #
    # FINAL SCORING
    # ================================================================== #
    score = round(total_score / max_score, 4) if max_score > 0 else 0.0
    all_critical = all(
        c["passed"] for c in checks
        if c["name"] in [
            "daily_log_exists",
            "memory_md_has_emoji_sections",
            "memory_md_new_decision_with_reason",
            "daily_log_has_required_sections",
        ]
    )
    passed = all_critical and score >= 0.70

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))