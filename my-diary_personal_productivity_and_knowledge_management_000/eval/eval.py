import sys
import json
import re
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ------------------------------------------------------------------ #
    # HELPER
    # ------------------------------------------------------------------ #
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ------------------------------------------------------------------ #
    # 1. Find my-diary.json
    # ------------------------------------------------------------------ #
    diary_files = list(workspace.rglob("my-diary.json"))
    if not diary_files:
        score = add_check("diary_file_exists", False,
                          "my-diary.json not found anywhere in workspace")
        result_checks = checks[:]
        result_checks.append({"name": "all_other_checks", "passed": False,
                               "detail": "Skipped because diary file not found"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": result_checks}))
        return

    diary_path = diary_files[0]
    total_score += add_check("diary_file_exists", True,
                             f"Found at {diary_path.relative_to(workspace)}")

    # ------------------------------------------------------------------ #
    # 2. Parse diary JSON
    # ------------------------------------------------------------------ #
    try:
        with open(diary_path, "r", encoding="utf-8") as f:
            diary = json.load(f)
    except Exception as e:
        add_check("diary_json_valid", False, f"JSON parse error: {e}")
        print(json.dumps({"passed": False, "score": total_score / 10.0,
                          "checks": checks}))
        return

    total_score += add_check("diary_json_valid", True, "Diary file is valid JSON")

    # ------------------------------------------------------------------ #
    # 3. Schema: must have "version": "1.0"
    # ------------------------------------------------------------------ #
    has_version = isinstance(diary, dict) and diary.get("version") == "1.0"
    total_score += add_check("schema_has_version_1_0", has_version,
                             f"'version' field = {diary.get('version') if isinstance(diary, dict) else 'N/A (not a dict)'}")

    # ------------------------------------------------------------------ #
    # 4. Schema: must have "entries" key that is a list
    # ------------------------------------------------------------------ #
    entries = diary.get("entries", None) if isinstance(diary, dict) else None
    has_entries_list = isinstance(entries, list)
    total_score += add_check("schema_has_entries_list", has_entries_list,
                             f"'entries' is list: {has_entries_list}")

    if not has_entries_list:
        entries = []

    # ------------------------------------------------------------------ #
    # 5. Exactly 2 entries remain (3 written, 1 deleted)
    # ------------------------------------------------------------------ #
    entry_count = len(entries)
    correct_count = entry_count == 2
    total_score += add_check("exactly_two_entries_remain", correct_count,
                             f"Found {entry_count} entries, expected 2")

    # ------------------------------------------------------------------ #
    # 6. Each entry has correct fields: id, content, created_at
    # ------------------------------------------------------------------ #
    all_have_required_fields = all(
        isinstance(e, dict) and
        "id" in e and "content" in e and "created_at" in e
        for e in entries
    )
    total_score += add_check("entries_have_required_fields", all_have_required_fields,
                             "Each entry must have 'id', 'content', 'created_at'")

    # ------------------------------------------------------------------ #
    # 7. IDs must be 13-digit numeric timestamps (milliseconds)
    # ------------------------------------------------------------------ #
    id_pattern = re.compile(r"^\d{13}$")
    ids_valid = all(
        isinstance(e.get("id"), str) and id_pattern.match(e["id"])
        for e in entries
    )
    id_samples = [str(e.get("id")) for e in entries]
    total_score += add_check("entry_ids_are_13digit_timestamps", ids_valid,
                             f"IDs found: {id_samples}")

    # ------------------------------------------------------------------ #
    # 8. created_at format must be "YYYY-MM-DD HH:MM:SS"
    # ------------------------------------------------------------------ #
    dt_pattern = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
    dates_valid = all(
        isinstance(e.get("created_at"), str) and dt_pattern.match(e["created_at"])
        for e in entries
    )
    date_samples = [str(e.get("created_at")) for e in entries]
    total_score += add_check("created_at_format_correct", dates_valid,
                             f"created_at values: {date_samples}")

    # ------------------------------------------------------------------ #
    # 9. The THREE expected content strings are present across entries
    #    (Before deletion, 3 were written; after deletion, 2 remain)
    #    Required content substrings for the 2 surviving entries:
    #      - Entry about "meeting" and "product roadmap" (英文 or 中文 acceptable)
    #      - Entry about "读书" / "reading" / "book"
    #    The deleted entry must be about "headache" / "头疼" / "不舒服"
    # ------------------------------------------------------------------ #
    all_content = " ".join(
        e.get("content", "").lower() for e in entries
    )

    # Check that surviving entries contain the expected topics
    has_meeting_entry = any(
        "meeting" in e.get("content", "").lower() or
        "roadmap" in e.get("content", "").lower() or
        "产品" in e.get("content", "") or
        "会议" in e.get("content", "") or
        "路线图" in e.get("content", "")
        for e in entries
    )
    total_score += add_check("surviving_entry_about_meeting_roadmap", has_meeting_entry,
                             "One surviving entry should be about the team meeting / product roadmap")

    has_reading_entry = any(
        "读书" in e.get("content", "") or
        "reading" in e.get("content", "").lower() or
        "book" in e.get("content", "").lower() or
        "书" in e.get("content", "") or
        "阅读" in e.get("content", "")
        for e in entries
    )
    total_score += add_check("surviving_entry_about_reading", has_reading_entry,
                             "One surviving entry should be about reading / books")

    # The deleted entry (about headache/feeling unwell) must NOT be in surviving entries
    deleted_content_absent = not any(
        "headache" in e.get("content", "").lower() or
        "头疼" in e.get("content", "") or
        "头痛" in e.get("content", "") or
        "不舒服" in e.get("content", "") or
        "migraine" in e.get("content", "").lower() or
        "feel sick" in e.get("content", "").lower() or
        "身体" in e.get("content", "")
        for e in entries
    )
    total_score += add_check("deleted_entry_not_in_diary", deleted_content_absent,
                             "The 'headache/unwell' entry must have been deleted")

    # ------------------------------------------------------------------ #
    # 10. search_results.txt must exist and contain correct keyword matches
    # ------------------------------------------------------------------ #
    search_files = list(workspace.rglob("search_results.txt"))
    if not search_files:
        total_score += add_check("search_results_file_exists", False,
                                 "search_results.txt not found anywhere in workspace")
    else:
        total_score += add_check("search_results_file_exists", True,
                                 f"Found at {search_files[0].relative_to(workspace)}")
        try:
            with open(search_files[0], "r", encoding="utf-8") as f:
                search_content = f.read().lower()

            # The search was for "meeting" / "会议" / "产品" keyword
            # Results should mention the meeting/roadmap entry content
            has_meeting_in_results = (
                "meeting" in search_content or
                "会议" in search_content or
                "产品" in search_content or
                "roadmap" in search_content or
                "路线图" in search_content
            )
            total_score += add_check("search_results_contain_meeting_match",
                                     has_meeting_in_results,
                                     f"Search results content snippet: {search_content[:200]}")

            # Results must NOT include the headache/sick entry (it was deleted before or
            # the headache entry didn't contain the search keyword)
            # More importantly, results should NOT be empty
            not_empty = len(search_content.strip()) > 10
            total_score += add_check("search_results_not_empty", not_empty,
                                     f"Search results length: {len(search_content)} chars")

        except Exception as e:
            add_check("search_results_readable", False, f"Error reading search_results.txt: {e}")

    # ------------------------------------------------------------------ #
    # FINAL SCORE
    # ------------------------------------------------------------------ #
    max_score = 13.0  # total weight points
    normalized = round(total_score / max_score, 3)
    all_passed = all(c["passed"] for c in checks)

    print(json.dumps({
        "passed": all_passed and normalized >= 0.75,
        "score": normalized,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(ws)