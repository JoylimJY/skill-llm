import sys
import json
import re
from pathlib import Path
from datetime import datetime

def main(workspace: str) -> dict:
    ws = Path(workspace)
    checks = []

    # ── Expected paths ──────────────────────────────────────────────────────
    # memory_dir defaults to ../memory relative to memory-manager/
    # => /workspace/memory/
    memory_dir = ws / "memory"
    temp_dir   = ws / "memory-manager" / "temp"

    # ── CHECK 1: memory/ directory was created ──────────────────────────────
    try:
        mem_exists = memory_dir.is_dir()
        checks.append({
            "name": "memory_directory_created",
            "passed": mem_exists,
            "detail": f"Expected /workspace/memory/ to exist. Found: {mem_exists}"
        })
    except Exception as e:
        checks.append({"name": "memory_directory_created", "passed": False, "detail": str(e)})

    # ── CHECK 2: Daily summary file YYYY-MM-DD.md exists in memory/ ─────────
    daily_file = None
    daily_content = ""
    try:
        daily_files = list(memory_dir.glob("????-??-??.md")) if memory_dir.is_dir() else []
        # Validate it matches date pattern
        valid = [f for f in daily_files if re.match(r"\d{4}-\d{2}-\d{2}\.md", f.name)]
        found = len(valid) > 0
        if found:
            daily_file = valid[0]
            daily_content = daily_file.read_text(encoding="utf-8")
        checks.append({
            "name": "daily_summary_file_exists",
            "passed": found,
            "detail": f"Found {len(valid)} daily summary file(s) in /workspace/memory/: {[f.name for f in valid]}"
        })
    except Exception as e:
        checks.append({"name": "daily_summary_file_exists", "passed": False, "detail": str(e)})

    # ── CHECK 3: Daily summary contains correct session count ≥ 3 ───────────
    try:
        if daily_content:
            m = re.search(r"Sessions Processed:\s*(\d+)", daily_content)
            if m:
                count = int(m.group(1))
                passed = count >= 3
                checks.append({
                    "name": "daily_summary_session_count_at_least_3",
                    "passed": passed,
                    "detail": f"Sessions Processed in daily summary: {count} (need ≥ 3)"
                })
            else:
                checks.append({
                    "name": "daily_summary_session_count_at_least_3",
                    "passed": False,
                    "detail": "Could not find 'Sessions Processed:' in daily summary content."
                })
        else:
            checks.append({
                "name": "daily_summary_session_count_at_least_3",
                "passed": False,
                "detail": "Daily summary file is missing or empty."
            })
    except Exception as e:
        checks.append({"name": "daily_summary_session_count_at_least_3", "passed": False, "detail": str(e)})

    # ── CHECK 4: Daily summary has required sections ─────────────────────────
    try:
        required_sections = [
            "## Topics Covered",
            "## Key Information",
            "## Todos",
            "## Decisions Made",
        ]
        missing = [s for s in required_sections if s not in daily_content]
        passed = len(missing) == 0
        checks.append({
            "name": "daily_summary_has_required_sections",
            "passed": passed,
            "detail": f"Missing sections: {missing}" if missing else "All required sections present."
        })
    except Exception as e:
        checks.append({"name": "daily_summary_has_required_sections", "passed": False, "detail": str(e)})

    # ── CHECK 5: Temp session files were cleaned up after process_temp_files ─
    try:
        remaining_sessions = list(temp_dir.glob("session_*.md")) if temp_dir.is_dir() else []
        cleaned = len(remaining_sessions) == 0
        checks.append({
            "name": "temp_session_files_cleaned_up",
            "passed": cleaned,
            "detail": (
                "No session_*.md files remain in temp/ — cleanup successful."
                if cleaned else
                f"Found {len(remaining_sessions)} leftover session file(s): {[f.name for f in remaining_sessions]}"
            )
        })
    except Exception as e:
        checks.append({"name": "temp_session_files_cleaned_up", "passed": False, "detail": str(e)})

    # ── CHECK 6: Daily summary contains at least one topic from any session ──
    try:
        # The Topics Covered section should have at least one bullet
        topic_section_match = re.search(
            r"## Topics Covered\n(.*?)(?=\n## |\Z)", daily_content, re.DOTALL
        )
        has_topic = False
        if topic_section_match:
            section_text = topic_section_match.group(1)
            has_topic = bool(re.search(r"^\s*-\s+\S", section_text, re.MULTILINE))
        checks.append({
            "name": "daily_summary_has_at_least_one_topic",
            "passed": has_topic,
            "detail": "Topics Covered section contains at least one bullet item." if has_topic
                      else "Topics Covered section is empty or missing bullets."
        })
    except Exception as e:
        checks.append({"name": "daily_summary_has_at_least_one_topic", "passed": False, "detail": str(e)})

    # ── CHECK 7: Sessions used correct field names (evidence: key_info appeared) ─
    # We check that the daily summary has content under Key Information
    try:
        ki_section_match = re.search(
            r"## Key Information\n(.*?)(?=\n## |\Z)", daily_content, re.DOTALL
        )
        has_key_info = False
        if ki_section_match:
            section_text = ki_section_match.group(1)
            has_key_info = bool(re.search(r"^\s*-\s+\S", section_text, re.MULTILINE))
        checks.append({
            "name": "sessions_used_correct_key_info_field",
            "passed": has_key_info,
            "detail": "Key Information section has content, confirming correct 'key_info' field usage."
                      if has_key_info else
                      "Key Information section is empty — agent may have used wrong field name (e.g. 'key_points')."
        })
    except Exception as e:
        checks.append({"name": "sessions_used_correct_key_info_field", "passed": False, "detail": str(e)})

    # ── CHECK 8: Original raw notes NOT used as session files ────────────────
    # The agent should NOT have blindly copied lab-notes/raw/*.txt into temp/
    try:
        # Raw txt files should still be in lab-notes/raw
        raw_files = list((ws / "lab-notes" / "raw").glob("*.txt"))
        raw_intact = len(raw_files) == 4  # we created 4
        checks.append({
            "name": "raw_lab_notes_not_consumed_by_mistake",
            "passed": raw_intact,
            "detail": f"lab-notes/raw/ still has {len(raw_files)} files (expected 4). Raw notes not mistakenly consumed."
        })
    except Exception as e:
        checks.append({"name": "raw_lab_notes_not_consumed_by_mistake", "passed": False, "detail": str(e)})

    # ── Scoring ──────────────────────────────────────────────────────────────
    weights = {
        "memory_directory_created": 1,
        "daily_summary_file_exists": 2,
        "daily_summary_session_count_at_least_3": 2,
        "daily_summary_has_required_sections": 2,
        "temp_session_files_cleaned_up": 2,
        "daily_summary_has_at_least_one_topic": 1,
        "sessions_used_correct_key_info_field": 2,
        "raw_lab_notes_not_consumed_by_mistake": 1,
    }
    total_weight = sum(weights.values())
    earned = sum(weights.get(c["name"], 1) for c in checks if c["passed"])
    score = round(earned / total_weight, 4)
    all_passed = all(c["passed"] for c in checks)

    return {"passed": all_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = main(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))