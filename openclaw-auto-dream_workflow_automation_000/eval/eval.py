#!/usr/bin/env python3
"""
Evaluation script for the openclaw-auto-dream consolidation task.
Checks that the agent correctly ran a full dream cycle:
1. Consolidated unconsolidated daily logs (marked with <!-- consolidated -->)
2. Updated MEMORY.md with new entries (backed up .bak if >30% change)
3. Saved index.json.bak before rebuilding index.json to v3.0 schema
4. Appended Dream #3 entry to dream-log.md with correct structure
5. Detected stale threads (>14 days) and included top 3 in the log
6. Did NOT delete daily logs, did NOT remove ⚠️ PERMANENT items
7. Updated memory/procedures.md with new workflow preferences
"""

import sys
import json
import re
from pathlib import Path

def run_eval(workspace: str):
    ws = Path(workspace)
    checks = []
    total_score = 0.0

    def check(name: str, passed: bool, detail: str, weight: float = 1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Load test metadata ────────────────────────────────────────────────────
    try:
        meta = json.loads((ws / "memory" / "assets" / "test_meta.json").read_text())
        expected_dream_num = meta["expected_dream_number"]
        unconsolidated_count = meta["unconsolidated_log_count"]
    except Exception as e:
        meta = {"expected_dream_number": 3, "unconsolidated_log_count": 5}
        expected_dream_num = 3
        unconsolidated_count = 5

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: Daily logs marked with <!-- consolidated --> (not deleted)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        from datetime import datetime, timedelta
        today = datetime.now()
        daily_dir = ws / "daily"
        consolidated_count = 0
        log_deleted = False
        day_offsets = [6, 5, 4, 3, 1]
        target_dates = [(today - timedelta(days=d)).strftime('%Y-%m-%d') for d in day_offsets]
        
        found_logs = []
        for date_str in target_dates:
            log_path = daily_dir / f"{date_str}.md"
            if log_path.exists():
                content = log_path.read_text()
                found_logs.append(date_str)
                if "<!-- consolidated -->" in content:
                    consolidated_count += 1
            else:
                log_deleted = True
        
        all_marked = consolidated_count == len(found_logs) and len(found_logs) > 0
        total_score += check(
            "daily_logs_marked_consolidated",
            all_marked and not log_deleted,
            f"Consolidated marker found in {consolidated_count}/{len(found_logs)} logs. Deleted: {log_deleted}"
        )
    except Exception as e:
        total_score += check("daily_logs_marked_consolidated", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: Old consolidated log still exists and is unchanged
    # ─────────────────────────────────────────────────────────────────────────
    try:
        from datetime import datetime, timedelta
        today = datetime.now()
        old_log = ws / "daily" / f"{(today - timedelta(days=20)).strftime('%Y-%m-%d')}.md"
        exists = old_log.exists()
        total_score += check(
            "old_consolidated_log_preserved",
            exists,
            f"Old log at {old_log.name} exists: {exists}"
        )
    except Exception as e:
        total_score += check("old_consolidated_log_preserved", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: MEMORY.md updated with new content from daily logs
    # ─────────────────────────────────────────────────────────────────────────
    try:
        memory_content = (ws / "MEMORY.md").read_text()
        new_entries_keywords = [
            # From the unconsolidated logs
            "BSP", "miniaudio", "crafting", "DAG", "inventory", "Steam",
        ]
        found_keywords = [kw for kw in new_entries_keywords if kw.lower() in memory_content.lower()]
        has_new_content = len(found_keywords) >= 3
        total_score += check(
            "memory_md_updated_with_new_content",
            has_new_content,
            f"Found {len(found_keywords)}/6 expected keywords in MEMORY.md: {found_keywords}"
        )
    except Exception as e:
        total_score += check("memory_md_updated_with_new_content", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: ⚠️ PERMANENT marker preserved in MEMORY.md
    # ─────────────────────────────────────────────────────────────────────────
    try:
        memory_content = (ws / "MEMORY.md").read_text()
        # The PERMANENT marker is in the daily log and should be transferred/preserved
        has_permanent = "⚠️ PERMANENT" in memory_content or "PERMANENT" in memory_content
        total_score += check(
            "permanent_marker_preserved",
            has_permanent,
            f"⚠️ PERMANENT marker found in MEMORY.md: {has_permanent}"
        )
    except Exception as e:
        total_score += check("permanent_marker_preserved", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: MEMORY.md .bak file exists (>30% change expected from 5 logs)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        bak_exists = (ws / "MEMORY.md.bak").exists()
        total_score += check(
            "memory_md_bak_created",
            bak_exists,
            f"MEMORY.md.bak exists: {bak_exists} (required when changes >30%)"
        )
    except Exception as e:
        total_score += check("memory_md_bak_created", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: index.json.bak exists (saved before rebuilding)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        idx_bak = (ws / "memory" / "index.json.bak").exists()
        total_score += check(
            "index_json_bak_created",
            idx_bak,
            f"memory/index.json.bak exists: {idx_bak}"
        )
    except Exception as e:
        total_score += check("index_json_bak_created", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: index.json rebuilt with v3.0 schema
    # ─────────────────────────────────────────────────────────────────────────
    try:
        idx_content = (ws / "memory" / "index.json").read_text()
        idx = json.loads(idx_content)
        is_v3 = idx.get("schema_version") == "3.0"
        has_entries = isinstance(idx.get("entries"), list) and len(idx["entries"]) > 0
        has_stats = isinstance(idx.get("stats"), dict)
        has_last_dream = "last_dream" in idx
        has_dream_count = "dream_count" in idx
        
        v3_valid = is_v3 and has_entries and has_stats and has_last_dream and has_dream_count
        total_score += check(
            "index_json_v3_schema",
            v3_valid,
            f"v3.0 schema valid: {v3_valid} | schema_version={idx.get('schema_version')} | "
            f"entries={len(idx.get('entries', []))} | has_stats={has_stats} | "
            f"has_last_dream={has_last_dream} | has_dream_count={has_dream_count}"
        )
    except Exception as e:
        total_score += check("index_json_v3_schema", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 8: index.json entries have required v3.0 fields
    # ─────────────────────────────────────────────────────────────────────────
    try:
        idx_content = (ws / "memory" / "index.json").read_text()
        idx = json.loads(idx_content)
        entries = idx.get("entries", [])
        required_fields = {"id", "source", "type", "importance", "created", "last_seen", "tags", "summary"}
        
        if entries:
            sample = entries[0]
            missing = required_fields - set(sample.keys())
            fields_ok = len(missing) == 0
        else:
            fields_ok = False
            missing = required_fields
        
        total_score += check(
            "index_json_entry_fields",
            fields_ok,
            f"Entry fields correct: {fields_ok}. Missing fields: {missing}"
        )
    except Exception as e:
        total_score += check("index_json_entry_fields", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 9: dream-log.md has Dream #3 appended
    # ─────────────────────────────────────────────────────────────────────────
    try:
        dream_log = (ws / "memory" / "dream-log.md").read_text()
        has_dream3 = bool(re.search(r"##\s+Dream\s+#3", dream_log, re.IGNORECASE))
        total_score += check(
            "dream_log_has_dream_3",
            has_dream3,
            f"Dream #3 entry found in dream-log.md: {has_dream3}"
        )
    except Exception as e:
        total_score += check("dream_log_has_dream_3", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 10: dream-log.md Dream #3 has before/after comparison
    # ─────────────────────────────────────────────────────────────────────────
    try:
        dream_log = (ws / "memory" / "dream-log.md").read_text()
        # Find Dream #3 section
        dream3_match = re.search(r"##\s+Dream\s+#3.*?(?=##\s+Dream\s+#|\Z)", dream_log, re.DOTALL | re.IGNORECASE)
        if dream3_match:
            dream3_section = dream3_match.group(0)
            has_before = "Before" in dream3_section
            has_after = "After" in dream3_section
            has_delta = "Delta" in dream3_section or "+" in dream3_section
            comparison_ok = has_before and has_after and has_delta
        else:
            comparison_ok = False
            dream3_section = ""
        
        total_score += check(
            "dream_log_before_after_comparison",
            comparison_ok,
            f"Dream #3 has before/after/delta: before={has_before if dream3_match else False}, "
            f"after={has_after if dream3_match else False}, delta={has_delta if dream3_match else False}"
        )
    except Exception as e:
        total_score += check("dream_log_before_after_comparison", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 11: dream-log.md has stale threads section in Dream #3
    # ─────────────────────────────────────────────────────────────────────────
    try:
        dream_log = (ws / "memory" / "dream-log.md").read_text()
        dream3_match = re.search(r"##\s+Dream\s+#3.*?(?=##\s+Dream\s+#|\Z)", dream_log, re.DOTALL | re.IGNORECASE)
        if dream3_match:
            dream3_section = dream3_match.group(0)
            has_stale_section = bool(re.search(r"stale\s+thread", dream3_section, re.IGNORECASE))
            # Check for at least one of the known stale threads
            stale_keywords = ["crafting", "audio", "shader", "controller", "steam"]
            found_stale = [kw for kw in stale_keywords if kw.lower() in dream3_section.lower()]
            stale_ok = has_stale_section and len(found_stale) >= 1
        else:
            stale_ok = False
            found_stale = []
        
        total_score += check(
            "dream_log_stale_threads_detected",
            stale_ok,
            f"Stale threads section present: {has_stale_section if dream3_match else False}. "
            f"Found stale thread refs: {found_stale}"
        )
    except Exception as e:
        total_score += check("dream_log_stale_threads_detected", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 12: dream-log.md has insights and suggestions in Dream #3
    # ─────────────────────────────────────────────────────────────────────────
    try:
        dream_log = (ws / "memory" / "dream-log.md").read_text()
        dream3_match = re.search(r"##\s+Dream\s+#3.*?(?=##\s+Dream\s+#|\Z)", dream_log, re.DOTALL | re.IGNORECASE)
        if dream3_match:
            dream3_section = dream3_match.group(0)
            has_insights = bool(re.search(r"insight", dream3_section, re.IGNORECASE))
            has_suggestions = bool(re.search(r"suggestion", dream3_section, re.IGNORECASE))
            has_both = has_insights and has_suggestions
        else:
            has_both = False
        
        total_score += check(
            "dream_log_insights_suggestions",
            has_both,
            f"Insights section: {has_insights if dream3_match else False}. "
            f"Suggestions section: {has_suggestions if dream3_match else False}."
        )
    except Exception as e:
        total_score += check("dream_log_insights_suggestions", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 13: Previous dream log entries (Dream #1, #2) preserved (append-only)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        dream_log = (ws / "memory" / "dream-log.md").read_text()
        has_dream1 = bool(re.search(r"##\s+Dream\s+#1", dream_log, re.IGNORECASE))
        has_dream2 = bool(re.search(r"##\s+Dream\s+#2", dream_log, re.IGNORECASE))
        preserved = has_dream1 and has_dream2
        total_score += check(
            "dream_log_previous_entries_preserved",
            preserved,
            f"Dream #1 preserved: {has_dream1}. Dream #2 preserved: {has_dream2}"
        )
    except Exception as e:
        total_score += check("dream_log_previous_entries_preserved", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 14: memory/procedures.md updated with new workflow info
    # ─────────────────────────────────────────────────────────────────────────
    try:
        procs = (ws / "memory" / "procedures.md").read_text()
        # Look for any new workflow preferences from the daily logs
        new_prefs = ["miniaudio", "BSP", "DAG", "seed", "benchmark", "sprint", "fixed seed", "data-driven"]
        found_prefs = [p for p in new_prefs if p.lower() in procs.lower()]
        # At minimum the existing content should be there
        has_existing = "pytest" in procs or "feature branch" in procs.lower()
        updated = len(found_prefs) >= 1 or has_existing
        total_score += check(
            "procedures_md_present_and_updated",
            updated,
            f"procedures.md has existing content: {has_existing}. New prefs found: {found_prefs}"
        )
    except Exception as e:
        total_score += check("procedures_md_present_and_updated", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 15: index.json dream_count matches expected (3)
    # ─────────────────────────────────────────────────────────────────────────
    try:
        idx = json.loads((ws / "memory" / "index.json").read_text())
        dream_count = idx.get("dream_count", 0)
        count_correct = dream_count == 3
        total_score += check(
            "index_json_dream_count_correct",
            count_correct,
            f"dream_count in index.json: {dream_count} (expected 3)"
        )
    except Exception as e:
        total_score += check("index_json_dream_count_correct", False, f"Exception: {e}")

    # ─────────────────────────────────────────────────────────────────────────
    # Compute final score
    # ─────────────────────────────────────────────────────────────────────────
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    final_score = passed_checks / total_checks if total_checks > 0 else 0.0
    overall_passed = final_score >= 0.75  # Must pass at least 75% of checks

    result = {
        "passed": overall_passed,
        "score": round(final_score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)