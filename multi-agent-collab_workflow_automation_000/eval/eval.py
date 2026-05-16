import sys
import json
import re
from pathlib import Path
from datetime import datetime

def make_result(checks):
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks) if checks else 0.0
    overall = score >= 0.75  # Must pass at least 75% of checks
    return {"passed": overall, "score": round(score, 3), "checks": checks}

def check(name, condition, detail):
    return {"name": name, "passed": bool(condition), "detail": detail}

def main(workspace_dir):
    ws = Path(workspace_dir)
    project = ws / "datapulse-etl"
    checks = []

    # ── CHECK 1: TASK.md — completed tasks moved to "Recent Completed" ──────
    try:
        task_content = (project / "TASK.md").read_text()
        # The three completed tasks should appear under Recent Completed
        recently_completed_match = re.search(
            r"##\s+Recent Completed(.*?)(?:##|\Z)", task_content, re.DOTALL | re.IGNORECASE
        )
        recent_section = recently_completed_match.group(1) if recently_completed_match else ""
        
        has_kafka = "kafka consumer" in recent_section.lower() or "kafka" in recent_section.lower()
        has_dedup = "dedup" in recent_section.lower() or "unit test" in recent_section.lower()
        has_deploy = "deploy" in recent_section.lower() or "staging" in recent_section.lower()
        
        moved_ok = has_kafka and has_dedup and has_deploy
        checks.append(check(
            "task_completed_items_moved",
            moved_ok,
            f"Recent Completed section present={bool(recently_completed_match)}, kafka={has_kafka}, dedup={has_dedup}, deploy={has_deploy}. Section content: {recent_section[:300]!r}"
        ))
        
        # The completed tasks should NOT remain as [x] in "In Progress"
        in_progress_match = re.search(
            r"##\s+In Progress(.*?)(?:##|\Z)", task_content, re.DOTALL | re.IGNORECASE
        )
        in_progress_section = in_progress_match.group(1) if in_progress_match else ""
        no_done_in_progress = "[x]" not in in_progress_section
        checks.append(check(
            "task_no_completed_in_in_progress",
            no_done_in_progress,
            f"In-Progress section should not contain [x] items. Section: {in_progress_section[:200]!r}"
        ))
    except Exception as e:
        checks.append(check("task_completed_items_moved", False, f"Error reading TASK.md: {e}"))
        checks.append(check("task_no_completed_in_in_progress", False, f"Error: {e}"))

    # ── CHECK 2: TASK.md — new items in In Progress or Backlog ──────────────
    try:
        task_content = (project / "TASK.md").read_text()
        has_dlq = "dead-letter" in task_content.lower() or "dead letter" in task_content.lower() or "dlq" in task_content.lower()
        has_prometheus = "prometheus" in task_content.lower() or "alerting" in task_content.lower()
        checks.append(check(
            "task_new_backlog_items_present",
            has_dlq and has_prometheus,
            f"New backlog items: dlq={has_dlq}, prometheus={has_prometheus}"
        ))
    except Exception as e:
        checks.append(check("task_new_backlog_items_present", False, f"Error: {e}"))

    # ── CHECK 3: CHANGELOG.md — all entries have #tag AND by <identity> ─────
    try:
        changelog_content = (project / "CHANGELOG.md").read_text()
        # Extract non-empty, non-comment lines
        lines = [l.strip() for l in changelog_content.splitlines()
                 if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("<!--")]
        
        if not lines:
            checks.append(check("changelog_entries_exist", False, "No CHANGELOG entries found"))
        else:
            checks.append(check("changelog_entries_exist", True, f"Found {len(lines)} changelog entries"))
        
        # Check each entry has a #tag
        tag_pattern = re.compile(r"#\w+")
        identity_pattern = re.compile(r"by\s+(opus|sonnet|flash|gpt4o?|gpt-4|haiku|claude|engineer|lead|maintainer)", re.IGNORECASE)
        
        entries_with_tag = [l for l in lines if tag_pattern.search(l)]
        entries_with_identity = [l for l in lines if identity_pattern.search(l)]
        
        all_have_tag = len(entries_with_tag) == len(lines) and len(lines) > 0
        all_have_identity = len(entries_with_identity) == len(lines) and len(lines) > 0
        
        checks.append(check(
            "changelog_all_entries_have_tag",
            all_have_tag,
            f"{len(entries_with_tag)}/{len(lines)} entries have #tag. Missing tag in: {[l for l in lines if not tag_pattern.search(l)][:3]}"
        ))
        checks.append(check(
            "changelog_all_entries_have_identity",
            all_have_identity,
            f"{len(entries_with_identity)}/{len(lines)} entries have 'by <identity>'. Missing identity: {[l for l in lines if not identity_pattern.search(l)][:3]}"
        ))
        
        # Check one-line format (no multi-line entries)
        # A valid entry should be a single line with date, description, tag, identity
        date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}")
        dated_lines = [l for l in lines if date_pattern.match(l)]
        checks.append(check(
            "changelog_one_line_per_entry_with_date",
            len(dated_lines) >= len(lines) * 0.9,  # 90% must have date prefix
            f"{len(dated_lines)}/{len(lines)} entries have YYYY-MM-DD date prefix"
        ))
    except Exception as e:
        checks.append(check("changelog_entries_exist", False, f"Error: {e}"))
        checks.append(check("changelog_all_entries_have_tag", False, f"Error: {e}"))
        checks.append(check("changelog_all_entries_have_identity", False, f"Error: {e}"))
        checks.append(check("changelog_one_line_per_entry_with_date", False, f"Error: {e}"))

    # ── CHECK 4: CONTEXT.md — bloom filter decision recorded ────────────────
    try:
        context_content = (project / "CONTEXT.md").read_text()
        has_bloom = "bloom filter" in context_content.lower() or "bloomfilter" in context_content.lower()
        has_memory_reason = ("memory" in context_content.lower() or "80%" in context_content or
                             "false-positive" in context_content.lower() or "redis" in context_content.lower())
        checks.append(check(
            "context_bloom_filter_decision_recorded",
            has_bloom and has_memory_reason,
            f"CONTEXT.md bloom_filter={has_bloom}, memory_reason={has_memory_reason}. Content snippet: {context_content[:400]!r}"
        ))
    except Exception as e:
        checks.append(check("context_bloom_filter_decision_recorded", False, f"Error reading CONTEXT.md: {e}"))

    # ── CHECK 5: WEEKLY-REPORT.md — exists and has required sections ─────────
    try:
        wr_candidates = list((project).glob("WEEKLY-REPORT.md"))
        if not wr_candidates:
            wr_candidates = list(ws.rglob("WEEKLY-REPORT.md"))
            # exclude template
            wr_candidates = [p for p in wr_candidates if "agent-sync/templates" not in str(p) and "datapulse-etl" in str(p) or "datapulse" in str(p)]
        
        if not wr_candidates:
            # try workspace root
            wr_candidates = [ws / "datapulse-etl" / "WEEKLY-REPORT.md"]
        
        wr_path = project / "WEEKLY-REPORT.md"
        if not wr_path.exists():
            # search more broadly
            all_wr = list(ws.rglob("WEEKLY-REPORT.md"))
            non_template = [p for p in all_wr if "templates" not in str(p)]
            wr_path = non_template[0] if non_template else wr_path
        
        wr_content = wr_path.read_text()
        
        has_changelog_by_tags = bool(re.search(r"(CHANGELOG by #tags|by #tag|#tag aggregat|tag.*aggregat)", wr_content, re.IGNORECASE))
        has_pattern_section = bool(re.search(r"Pattern Discovery|pattern.*discover|candidate skill", wr_content, re.IGNORECASE))
        
        checks.append(check(
            "weekly_report_exists",
            True,
            f"WEEKLY-REPORT.md found at {wr_path}"
        ))
        checks.append(check(
            "weekly_report_has_tag_aggregation",
            has_changelog_by_tags,
            f"Weekly report tag aggregation section present: {has_changelog_by_tags}. Snippet: {wr_content[:500]!r}"
        ))
        checks.append(check(
            "weekly_report_has_pattern_discovery",
            has_pattern_section,
            f"Weekly report Pattern Discovery section present: {has_pattern_section}"
        ))
    except Exception as e:
        checks.append(check("weekly_report_exists", False, f"WEEKLY-REPORT.md not found or error: {e}"))
        checks.append(check("weekly_report_has_tag_aggregation", False, f"Error: {e}"))
        checks.append(check("weekly_report_has_pattern_discovery", False, f"Error: {e}"))

    # ── CHECK 6: Candidate skills identified (3+ occurrences) ───────────────
    try:
        wr_path = project / "WEEKLY-REPORT.md"
        if not wr_path.exists():
            all_wr = list(ws.rglob("WEEKLY-REPORT.md"))
            non_template = [p for p in all_wr if "templates" not in str(p)]
            wr_path = non_template[0] if non_template else wr_path
        
        wr_content = wr_path.read_text()
        changelog_content = (project / "CHANGELOG.md").read_text()
        
        # Count tags in the FINAL changelog
        all_lines = [l.strip() for l in changelog_content.splitlines()
                     if l.strip() and not l.strip().startswith("#") and not l.strip().startswith("<!--")]
        tag_counts = {}
        for line in all_lines:
            tags = re.findall(r"#(\w+)", line)
            for t in tags:
                tag_counts[t] = tag_counts.get(t, 0) + 1
        
        candidate_tags = {t for t, c in tag_counts.items() if c >= 3}
        
        # Check that weekly report mentions candidate tags
        candidate_mentioned = any(t.lower() in wr_content.lower() for t in candidate_tags)
        candidate_skill_marked = bool(re.search(r"CANDIDATE SKILL|candidate skill", wr_content, re.IGNORECASE))
        
        checks.append(check(
            "weekly_report_candidate_skills_identified",
            (candidate_mentioned or not candidate_tags) and candidate_skill_marked,
            f"Tags with 3+ occurrences: {tag_counts}. Candidate tags: {candidate_tags}. "
            f"Mentioned in WR: {candidate_mentioned}. CANDIDATE SKILL marker: {candidate_skill_marked}"
        ))
    except Exception as e:
        checks.append(check("weekly_report_candidate_skills_identified", False, f"Error: {e}"))

    # ── CHECK 7: Archive — old changelog data moved to archive/ ─────────────
    try:
        archive_dir = project / "archive"
        archive_files = list(archive_dir.glob("*.md")) if archive_dir.exists() else []
        has_archive = len(archive_files) > 0
        checks.append(check(
            "old_changelog_archived",
            has_archive,
            f"Archive directory has {len(archive_files)} files: {[f.name for f in archive_files]}"
        ))
    except Exception as e:
        checks.append(check("old_changelog_archived", False, f"Error checking archive: {e}"))

    # ── CHECK 8: llms.txt updated for project ───────────────────────────────
    try:
        llms_path = project / "llms.txt"
        if llms_path.exists():
            llms_content = llms_path.read_text()
            has_project_name = "datapulse" in llms_content.lower() or "DataPulse" in llms_content
            checks.append(check(
                "llms_txt_created_with_project_name",
                has_project_name,
                f"llms.txt exists and references project name: {has_project_name}. Content: {llms_content[:200]!r}"
            ))
        else:
            checks.append(check(
                "llms_txt_created_with_project_name",
                False,
                "llms.txt not found in datapulse-etl/"
            ))
    except Exception as e:
        checks.append(check("llms_txt_created_with_project_name", False, f"Error: {e}"))

    result = make_result(checks)
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    main(workspace)