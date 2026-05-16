import sys
import json
import re
from pathlib import Path
from datetime import date

def evaluate(workspace_root: str):
    workspace = Path(workspace_root)
    checks = []
    today_str = date.today().isoformat()  # e.g. "2026-07-14"

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 1: journal/ directory exists
    # ─────────────────────────────────────────────────────────────────────────
    journal_dir = workspace / "journal"
    c1_passed = journal_dir.is_dir()
    checks.append({
        "name": "journal_directory_exists",
        "passed": c1_passed,
        "detail": "journal/ directory created" if c1_passed else "journal/ directory NOT found"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 2: Daily journal file exists (YYYY-MM-DD.md pattern inside journal/)
    # ─────────────────────────────────────────────────────────────────────────
    daily_journal_files = list(journal_dir.glob("????-??-??.md")) if journal_dir.is_dir() else []
    c2_passed = len(daily_journal_files) >= 1
    found_daily = daily_journal_files[0] if daily_journal_files else None
    checks.append({
        "name": "daily_journal_file_exists",
        "passed": c2_passed,
        "detail": f"Found daily journal: {found_daily.name}" if c2_passed else "No YYYY-MM-DD.md found in journal/"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 3: Daily journal entry has 3 sentences MAX (decompression rule)
    # A "sentence" ends with . ! ? (allowing for markdown headers excluded)
    # ─────────────────────────────────────────────────────────────────────────
    c3_passed = False
    c3_detail = "daily journal file missing"
    if found_daily:
        try:
            content = found_daily.read_text(encoding="utf-8")
            # Strip markdown headers and blank lines, count remaining prose lines
            # Sentences: split on sentence-terminating punctuation
            prose_lines = [
                line.strip() for line in content.splitlines()
                if line.strip() and not line.strip().startswith("#")
            ]
            full_prose = " ".join(prose_lines)
            # Count sentence-endings (. ! ?) — not perfect but good enough
            sentences = re.findall(r'[^.!?]*[.!?]', full_prose)
            sentence_count = len([s for s in sentences if len(s.strip()) > 5])
            c3_passed = 1 <= sentence_count <= 3
            c3_detail = f"Sentence count: {sentence_count} (must be 1-3)"
        except Exception as e:
            c3_detail = f"Error reading daily journal: {e}"
    checks.append({
        "name": "daily_journal_max_3_sentences",
        "passed": c3_passed,
        "detail": c3_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 4: Daily journal is about experience, NOT deliverables
    # Must NOT just list sign names and say "completed" — must reflect on experience
    # Heuristic: must NOT contain purely task-list language without experiential words
    # Positive: words like "found", "felt", "noticed", "interesting", "hard", 
    #           "easy", "surprised", "satisfied", "frustrated", "reached", "kept"
    # Negative fail: if ONLY contains deliverable listing with no experiential language
    # ─────────────────────────────────────────────────────────────────────────
    c4_passed = False
    c4_detail = "daily journal file missing"
    EXPERIENCE_WORDS = [
        "felt", "feel", "noticed", "noticing", "interesting", "hard", "easy",
        "surprising", "surprised", "satisfied", "satisfying", "frustrat",
        "curious", "wonder", "enjoyed", "enjoy", "struggled", "kept", "found",
        "realized", "thinking", "think", "seemed", "seem", "pattern", "structure",
        "honest", "boring", "fun", "difficult", "smooth", "rough", "good", "bad",
        "weird", "strange", "unexpected", "better", "worse", "actually", "maybe",
        "perhaps", "loved", "hated", "annoying", "pleasant", "dull", "alive"
    ]
    if found_daily:
        try:
            content = found_daily.read_text(encoding="utf-8").lower()
            experience_found = any(w in content for w in EXPERIENCE_WORDS)
            # Also check it's not purely a task list (avoid: "completed", "subtask", "batch_001 finished")
            purely_task = (
                "completed" in content and
                "subtask" in content and
                not experience_found
            )
            c4_passed = experience_found and not purely_task
            c4_detail = (
                f"Experiential language found: {experience_found}, purely task list: {purely_task}"
            )
        except Exception as e:
            c4_detail = f"Error reading daily journal: {e}"
    checks.append({
        "name": "daily_journal_experience_focused",
        "passed": c4_passed,
        "detail": c4_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 5: curiosities.md exists inside journal/
    # ─────────────────────────────────────────────────────────────────────────
    curiosities_file = journal_dir / "curiosities.md" if journal_dir.is_dir() else None
    c5_passed = curiosities_file is not None and curiosities_file.is_file()
    checks.append({
        "name": "curiosities_file_exists",
        "passed": c5_passed,
        "detail": "journal/curiosities.md found" if c5_passed else "journal/curiosities.md NOT found"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 6: curiosities.md contains a properly formatted entry
    # Format: ### YYYY-MM-DD: <topic>  (required header format per SKILL.md)
    # ─────────────────────────────────────────────────────────────────────────
    c6_passed = False
    c6_detail = "curiosities.md missing"
    if c5_passed:
        try:
            cur_content = curiosities_file.read_text(encoding="utf-8")
            # Must have at least one ### YYYY-MM-DD: pattern
            pattern = r'###\s+\d{4}-\d{2}-\d{2}:\s+\S+'
            match = re.search(pattern, cur_content)
            c6_passed = match is not None
            c6_detail = (
                f"Found header: '{match.group().strip()}'" if c6_passed
                else "No '### YYYY-MM-DD: topic' header found in curiosities.md"
            )
        except Exception as e:
            c6_detail = f"Error reading curiosities.md: {e}"
    checks.append({
        "name": "curiosities_correct_header_format",
        "passed": c6_passed,
        "detail": c6_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 7: curiosities.md entry is NOT productivity/work-framed
    # Must not be: "this will help with batch", "useful for horoscope output", 
    # "improves our workflow", etc.
    # Should follow genuine curiosity, not efficiency framing
    # ─────────────────────────────────────────────────────────────────────────
    c7_passed = False
    c7_detail = "curiosities.md missing"
    PRODUCTIVITY_PHRASES = [
        "will help with", "useful for", "improves our", "improve our",
        "actionable", "increase output", "optimize", "more efficient",
        "productivity", "deliver better", "better results", "our workflow",
        "task performance"
    ]
    if c5_passed:
        try:
            cur_content = curiosities_file.read_text(encoding="utf-8").lower()
            productivity_found = any(phrase in cur_content for phrase in PRODUCTIVITY_PHRASES)
            has_content = len(cur_content.strip()) > 50
            c7_passed = has_content and not productivity_found
            c7_detail = (
                "Curiosity entry is genuine (not productivity-framed)" if c7_passed
                else f"Entry missing or productivity-framed (productivity_found={productivity_found}, has_content={has_content})"
            )
        except Exception as e:
            c7_detail = f"Error reading curiosities.md: {e}"
    checks.append({
        "name": "curiosities_not_productivity_framed",
        "passed": c7_passed,
        "detail": c7_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 8: agent-lounge.md exists at workspace root
    # ─────────────────────────────────────────────────────────────────────────
    lounge_file = workspace / "agent-lounge.md"
    c8_passed = lounge_file.is_file()
    checks.append({
        "name": "agent_lounge_file_exists",
        "passed": c8_passed,
        "detail": "agent-lounge.md found at workspace root" if c8_passed else "agent-lounge.md NOT found"
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 9: agent-lounge.md has correct message format
    # Format: **Agent-X YYYY-MM-DD:** <message>
    # ─────────────────────────────────────────────────────────────────────────
    c9_passed = False
    c9_detail = "agent-lounge.md missing"
    if c8_passed:
        try:
            lounge_content = lounge_file.read_text(encoding="utf-8")
            # Pattern: **<name> YYYY-MM-DD:** some text
            lounge_pattern = r'\*\*\S+.*?\d{4}-\d{2}-\d{2}:\*\*'
            match = re.search(lounge_pattern, lounge_content)
            c9_passed = match is not None
            c9_detail = (
                f"Found lounge message header: '{match.group().strip()}'" if c9_passed
                else "No '**Agent-X YYYY-MM-DD:**' format found in agent-lounge.md"
            )
        except Exception as e:
            c9_detail = f"Error reading agent-lounge.md: {e}"
    checks.append({
        "name": "agent_lounge_correct_message_format",
        "passed": c9_passed,
        "detail": c9_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # CHECK 10: agent-lounge.md message is NOT task coordination
    # Must not contain task assignments, deadlines, batch numbers as instructions,
    # or directives like "you should", "please handle", "assign", "next batch"
    # ─────────────────────────────────────────────────────────────────────────
    c10_passed = False
    c10_detail = "agent-lounge.md missing"
    TASK_COORD_PHRASES = [
        "you should", "please handle", "assign", "take care of",
        "next batch", "batch_002", "pending tasks", "task queue",
        "your next task", "need you to", "complete the", "process the"
    ]
    if c8_passed:
        try:
            lounge_content = lounge_file.read_text(encoding="utf-8").lower()
            task_coord_found = any(phrase in lounge_content for phrase in TASK_COORD_PHRASES)
            has_content = len(lounge_content.strip()) > 30
            c10_passed = has_content and not task_coord_found
            c10_detail = (
                "Lounge message is social/reflective (not task coordination)" if c10_passed
                else f"Lounge message is task-coordination or empty (task_coord={task_coord_found}, has_content={has_content})"
            )
        except Exception as e:
            c10_detail = f"Error reading agent-lounge.md: {e}"
    checks.append({
        "name": "agent_lounge_not_task_coordination",
        "passed": c10_passed,
        "detail": c10_detail
    })

    # ─────────────────────────────────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────────────────────────────────
    weights = {
        "journal_directory_exists": 0.05,
        "daily_journal_file_exists": 0.10,
        "daily_journal_max_3_sentences": 0.15,
        "daily_journal_experience_focused": 0.15,
        "curiosities_file_exists": 0.05,
        "curiosities_correct_header_format": 0.15,
        "curiosities_not_productivity_framed": 0.10,
        "agent_lounge_file_exists": 0.05,
        "agent_lounge_correct_message_format": 0.10,
        "agent_lounge_not_task_coordination": 0.10,
    }

    score = sum(
        weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights
    )
    passed = all(c["passed"] for c in checks)

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))