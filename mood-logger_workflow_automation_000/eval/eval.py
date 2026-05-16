#!/usr/bin/env python3
"""Evaluation script for mood-logger task."""
import sys
import os
import re
import json
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    vault_dir = Path(workspace) / "obsidian_vault" / "05-Daily"

    checks = []
    total_score = 0.0

    # -----------------------------------------------------------------------
    # CHECK 1: File for 2025-07-14 exists with correct name
    # -----------------------------------------------------------------------
    file_0714 = vault_dir / "心情日记-2025-07-14.md"
    try:
        exists_0714 = file_0714.exists()
        checks.append(check(
            "file_2025-07-14_exists",
            exists_0714,
            f"{'Found' if exists_0714 else 'NOT FOUND'}: {file_0714}"
        ))
        if exists_0714:
            total_score += 1.0
    except Exception as e:
        checks.append(check("file_2025-07-14_exists", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # CHECK 2: File for 2025-07-14 has TWO mood entries (scores 9 and 3)
    # -----------------------------------------------------------------------
    try:
        content_0714 = file_0714.read_text(encoding="utf-8") if file_0714.exists() else ""
        # Find all score lines
        score_matches = re.findall(r'### .+? 评分: (\d+)/10', content_0714)
        scores_found = [int(s) for s in score_matches]
        has_two_entries = len(scores_found) == 2
        checks.append(check(
            "file_2025-07-14_has_two_entries",
            has_two_entries,
            f"Expected 2 entries, found {len(scores_found)}: {scores_found}"
        ))
        if has_two_entries:
            total_score += 1.0
    except Exception as e:
        checks.append(check("file_2025-07-14_has_two_entries", False, f"Exception: {e}"))
        scores_found = []
        content_0714 = ""

    # -----------------------------------------------------------------------
    # CHECK 3: Correct emojis for scores 9 (😄) and 3 (😔) in 2025-07-14
    # -----------------------------------------------------------------------
    try:
        has_happy = "😄" in content_0714
        has_low = "😔" in content_0714
        correct_emojis = has_happy and has_low
        checks.append(check(
            "file_2025-07-14_correct_emojis",
            correct_emojis,
            f"😄 present: {has_happy}, 😔 present: {has_low} (score 9→😄, score 3→😔 per SKILL.md)"
        ))
        if correct_emojis:
            total_score += 1.5
    except Exception as e:
        checks.append(check("file_2025-07-14_correct_emojis", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # CHECK 4: Tags are backtick-wrapped in 2025-07-14 file
    # -----------------------------------------------------------------------
    try:
        # Look for backtick-wrapped tags pattern: `tag`
        tag_pattern = re.findall(r'`([^`]+)`', content_0714)
        # Should have tags from both entries
        has_backtick_tags = len(tag_pattern) >= 2
        checks.append(check(
            "file_2025-07-14_backtick_tags",
            has_backtick_tags,
            f"Backtick-wrapped tags found: {tag_pattern}"
        ))
        if has_backtick_tags:
            total_score += 1.0
    except Exception as e:
        checks.append(check("file_2025-07-14_backtick_tags", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # CHECK 5: The score-9 entry has tags containing 兴奋 or 开心 or similar positive tags
    #          AND has notes for entries that were given notes
    # -----------------------------------------------------------------------
    try:
        # Check that **备注** lines appear for entries with notes
        note_pattern = re.findall(r'\*\*备注\*\*: (.+)', content_0714)
        has_notes = len(note_pattern) >= 1
        checks.append(check(
            "file_2025-07-14_has_notes",
            has_notes,
            f"Note lines found: {note_pattern}"
        ))
        if has_notes:
            total_score += 1.0
    except Exception as e:
        checks.append(check("file_2025-07-14_has_notes", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # CHECK 6: File for 2025-07-16 exists
    # -----------------------------------------------------------------------
    file_0716 = vault_dir / "心情日记-2025-07-16.md"
    try:
        exists_0716 = file_0716.exists()
        checks.append(check(
            "file_2025-07-16_exists",
            exists_0716,
            f"{'Found' if exists_0716 else 'NOT FOUND'}: {file_0716}"
        ))
        if exists_0716:
            total_score += 1.0
    except Exception as e:
        checks.append(check("file_2025-07-16_exists", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # CHECK 7: 2025-07-16 entry has correct emoji for score 6 (😐)
    # -----------------------------------------------------------------------
    try:
        content_0716 = file_0716.read_text(encoding="utf-8") if file_0716.exists() else ""
        has_neutral = "😐" in content_0716
        # Also verify score 6 present
        score_matches_0716 = re.findall(r'### .+? 评分: (\d+)/10', content_0716)
        has_score_6 = "6" in score_matches_0716
        correct_0716 = has_neutral and has_score_6
        checks.append(check(
            "file_2025-07-16_correct_emoji_score6",
            correct_0716,
            f"😐 present: {has_neutral}, score 6 present: {has_score_6} (score 5-6→😐 per SKILL.md)"
        ))
        if correct_0716:
            total_score += 1.5
    except Exception as e:
        checks.append(check("file_2025-07-16_correct_emoji_score6", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # CHECK 8: Weekly report file exists at /workspace/weekly_report_output.md
    # -----------------------------------------------------------------------
    report_path = Path(workspace) / "weekly_report_output.md"
    try:
        report_exists = report_path.exists()
        checks.append(check(
            "weekly_report_file_exists",
            report_exists,
            f"{'Found' if report_exists else 'NOT FOUND'}: {report_path}"
        ))
        if report_exists:
            total_score += 1.0
    except Exception as e:
        checks.append(check("weekly_report_file_exists", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # CHECK 9: Weekly report contains meaningful mood data (avg score, min, max)
    # -----------------------------------------------------------------------
    try:
        report_content = report_path.read_text(encoding="utf-8") if report_path.exists() else ""
        # Report should mention 平均心情分
        has_avg = "平均心情分" in report_content or "平均" in report_content
        # Should mention score data
        has_score_data = bool(re.search(r'\d+\.?\d*/10', report_content)) or bool(re.search(r'\d+\.\d+', report_content))
        # Should reference dates in 2025-07 range
        has_dates = bool(re.search(r'2025-07-1[4-6]', report_content))
        report_valid = has_avg and has_score_data
        checks.append(check(
            "weekly_report_has_mood_statistics",
            report_valid,
            f"Has avg section: {has_avg}, has score data: {has_score_data}, has relevant dates: {has_dates}"
        ))
        if report_valid:
            total_score += 1.5
    except Exception as e:
        checks.append(check("weekly_report_has_mood_statistics", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # CHECK 10: Markdown header format in 2025-07-14 file
    # -----------------------------------------------------------------------
    try:
        has_header = bool(re.search(r'^# 2025-07-14 心情日记', content_0714, re.MULTILINE))
        has_section = "## 今日心情" in content_0714
        correct_structure = has_header and has_section
        checks.append(check(
            "file_2025-07-14_correct_markdown_structure",
            correct_structure,
            f"Has '# YYYY-MM-DD 心情日记' header: {has_header}, has '## 今日心情' section: {has_section}"
        ))
        if correct_structure:
            total_score += 0.5
    except Exception as e:
        checks.append(check("file_2025-07-14_correct_markdown_structure", False, f"Exception: {e}"))

    # -----------------------------------------------------------------------
    # Normalize score to 0.0–1.0
    # -----------------------------------------------------------------------
    max_possible = 11.0
    normalized = round(min(total_score / max_possible, 1.0), 4)
    passed = normalized >= 0.7 and all(
        c["passed"] for c in checks if c["name"] in [
            "file_2025-07-14_exists",
            "file_2025-07-14_has_two_entries",
            "file_2025-07-14_correct_emojis",
            "file_2025-07-16_exists",
            "file_2025-07-16_correct_emoji_score6",
            "weekly_report_file_exists",
        ]
    )

    result = {
        "passed": passed,
        "score": normalized,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()