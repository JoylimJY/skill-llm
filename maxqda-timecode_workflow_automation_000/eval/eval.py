import sys
import os
import json
import re

def evaluate(workspace: str):
    checks = []

    # Hardcoded target file paths (as created by gen_inputs_script)
    target_files = {
        "session_01_participantA.txt": os.path.join(
            workspace, "research_project/fieldwork_2023/interviews/raw/session_01_participantA.txt"),
        "session_02_participantB.txt": os.path.join(
            workspace, "research_project/fieldwork_2023/interviews/raw/session_02_participantB.txt"),
        "session_03_participantC.txt": os.path.join(
            workspace, "research_project/fieldwork_2024/interviews/raw/session_03_participantC.txt"),
        "focus_group_alpha.txt": os.path.join(
            workspace, "research_project/fieldwork_2024/interviews/raw/focus_group_alpha.txt"),
    }

    def read_file(path):
        with open(path, "rb") as f:
            raw = f.read()
        # Strip BOM if present
        if raw.startswith(b'\xef\xbb\xbf'):
            raw = raw[3:]
        return raw.decode("utf-8")

    def get_lines(path):
        try:
            content = read_file(path)
            return content.splitlines()
        except Exception as e:
            return None

    # -----------------------------------------------------------------------
    # FILE 1: session_01_participantA.txt
    # -----------------------------------------------------------------------
    try:
        lines = get_lines(target_files["session_01_participantA.txt"])
        assert lines is not None, "Could not read file"

        # Check 1a: First line (title) must be removed → first line should now be a timecode line
        first_line = lines[0] if lines else ""
        title_removed = first_line.startswith("[")
        checks.append({
            "name": "file1_title_removed",
            "passed": title_removed,
            "detail": f"First line is: '{first_line[:80]}'. Expected to start with '[' (title removed)."
        })

        # Check 1b: Timecode format [hh:mm:ss]Speaker, no space
        pattern = re.compile(r'^\[(\d{2}):(\d{2}):(\d{2})\](\S+)$')
        timecode_lines = [l for l in lines if l.strip() and not l.startswith("[") is False
                          and re.match(r'^\[', l)]
        
        # Validate specific known conversions
        # "提问者 00:02" → "[00:00:02]提问者"
        match_1 = "[00:00:02]提问者" in lines
        checks.append({
            "name": "file1_timecode_00:02_correct",
            "passed": match_1,
            "detail": f"Expected '[00:00:02]提问者' in file1 lines. Lines: {lines[:6]}"
        })

        # "提问者 01:30" → "[00:01:30]提问者"
        match_2 = "[00:01:30]提问者" in lines
        checks.append({
            "name": "file1_timecode_01:30_correct",
            "passed": match_2,
            "detail": f"Expected '[00:01:30]提问者' in file1."
        })

        # "回答者 00:45" → "[00:00:45]回答者"
        match_3 = "[00:00:45]回答者" in lines
        checks.append({
            "name": "file1_timecode_00:45_correct",
            "passed": match_3,
            "detail": f"Expected '[00:00:45]回答者' in file1."
        })

        # No space between ] and speaker
        bad_space = any(re.match(r'^\[\d{2}:\d{2}:\d{2}\] ', l) for l in lines)
        checks.append({
            "name": "file1_no_space_after_bracket",
            "passed": not bad_space,
            "detail": "No line should have a space between ']' and the speaker name."
        })

    except Exception as e:
        checks.append({"name": "file1_read_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # FILE 2: session_02_participantB.txt — HOUR ROLLOVER TESTS
    # -----------------------------------------------------------------------
    try:
        lines = get_lines(target_files["session_02_participantB.txt"])
        assert lines is not None, "Could not read file"

        # Title removed
        first_line = lines[0] if lines else ""
        title_removed = first_line.startswith("[")
        checks.append({
            "name": "file2_title_removed",
            "passed": title_removed,
            "detail": f"First line: '{first_line[:80]}'"
        })

        # "提问者2 59:30" → "[00:59:30]提问者2"
        match_sub60 = "[00:59:30]提问者2" in lines
        checks.append({
            "name": "file2_timecode_59:30_correct",
            "passed": match_sub60,
            "detail": f"Expected '[00:59:30]提问者2'. Lines: {lines}"
        })

        # "受访者B 61:15" → "[01:01:15]受访者B"
        match_61 = "[01:01:15]受访者B" in lines
        checks.append({
            "name": "file2_timecode_61:15_hour_rollover",
            "passed": match_61,
            "detail": f"Expected '[01:01:15]受访者B' (61 min → 1h 1m). Lines: {lines}"
        })

        # "提问者2 65:45" → "[01:05:45]提问者2"
        match_65 = "[01:05:45]提问者2" in lines
        checks.append({
            "name": "file2_timecode_65:45_hour_rollover",
            "passed": match_65,
            "detail": f"Expected '[01:05:45]提问者2' (65 min → 1h 5m). Lines: {lines}"
        })

        # "受访者B 68:00" → "[01:08:00]受访者B"
        match_68 = "[01:08:00]受访者B" in lines
        checks.append({
            "name": "file2_timecode_68:00_hour_rollover",
            "passed": match_68,
            "detail": f"Expected '[01:08:00]受访者B'. Lines: {lines}"
        })

        # "提问者2 72:33" → "[01:12:33]提问者2"
        match_72 = "[01:12:33]提问者2" in lines
        checks.append({
            "name": "file2_timecode_72:33_hour_rollover",
            "passed": match_72,
            "detail": f"Expected '[01:12:33]提问者2'. Lines: {lines}"
        })

        # "受访者B 73:50" → "[01:13:50]受访者B"
        match_73 = "[01:13:50]受访者B" in lines
        checks.append({
            "name": "file2_timecode_73:50_hour_rollover",
            "passed": match_73,
            "detail": f"Expected '[01:13:50]受访者B'. Lines: {lines}"
        })

    except Exception as e:
        checks.append({"name": "file2_read_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # FILE 3: session_03_participantC.txt — BOM FILE + HOUR ROLLOVER
    # -----------------------------------------------------------------------
    try:
        lines = get_lines(target_files["session_03_participantC.txt"])
        assert lines is not None, "Could not read file"

        # Title removed
        first_line = lines[0] if lines else ""
        title_removed = first_line.startswith("[")
        checks.append({
            "name": "file3_title_removed",
            "passed": title_removed,
            "detail": f"First line: '{first_line[:80]}'"
        })

        # BOM should not appear in output lines
        bom_present = any("\ufeff" in l for l in lines)
        checks.append({
            "name": "file3_bom_stripped",
            "passed": not bom_present,
            "detail": "BOM character should be stripped from all output lines."
        })

        # "Interviewer 00:00" → "[00:00:00]Interviewer"
        match_0 = "[00:00:00]Interviewer" in lines
        checks.append({
            "name": "file3_timecode_00:00_correct",
            "passed": match_0,
            "detail": f"Expected '[00:00:00]Interviewer'. Lines: {lines}"
        })

        # "Interviewer 60:10" → "[01:00:10]Interviewer"
        match_60 = "[01:00:10]Interviewer" in lines
        checks.append({
            "name": "file3_timecode_60:10_hour_rollover",
            "passed": match_60,
            "detail": f"Expected '[01:00:10]Interviewer' (60 min → 1h 0m). Lines: {lines}"
        })

        # "Participant_C 62:55" → "[01:02:55]Participant_C"
        match_62 = "[01:02:55]Participant_C" in lines
        checks.append({
            "name": "file3_timecode_62:55_hour_rollover",
            "passed": match_62,
            "detail": f"Expected '[01:02:55]Participant_C'. Lines: {lines}"
        })

    except Exception as e:
        checks.append({"name": "file3_read_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # FILE 4: focus_group_alpha.txt — Standard multi-speaker
    # -----------------------------------------------------------------------
    try:
        lines = get_lines(target_files["focus_group_alpha.txt"])
        assert lines is not None, "Could not read file"

        # Title removed
        first_line = lines[0] if lines else ""
        title_removed = first_line.startswith("[")
        checks.append({
            "name": "file4_title_removed",
            "passed": title_removed,
            "detail": f"First line: '{first_line[:80]}'"
        })

        # "主持人 00:10" → "[00:00:10]主持人"
        match_host = "[00:00:10]主持人" in lines
        checks.append({
            "name": "file4_timecode_00:10_correct",
            "passed": match_host,
            "detail": f"Expected '[00:00:10]主持人'. Lines: {lines[:6]}"
        })

        # "参与者甲 00:50" → "[00:00:50]参与者甲"
        match_jia = "[00:00:50]参与者甲" in lines
        checks.append({
            "name": "file4_timecode_00:50_correct",
            "passed": match_jia,
            "detail": f"Expected '[00:00:50]参与者甲'. Lines: {lines}"
        })

        # "参与者丙 04:00" → "[00:04:00]参与者丙"
        match_bing = "[00:04:00]参与者丙" in lines
        checks.append({
            "name": "file4_timecode_04:00_correct",
            "passed": match_bing,
            "detail": f"Expected '[00:04:00]参与者丙'. Lines: {lines}"
        })

        # "参与者乙 06:45" → "[00:06:45]参与者乙"
        match_yi = "[00:06:45]参与者乙" in lines
        checks.append({
            "name": "file4_timecode_06:45_correct",
            "passed": match_yi,
            "detail": f"Expected '[00:06:45]参与者乙'. Lines: {lines}"
        })

    except Exception as e:
        checks.append({"name": "file4_read_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # GLOBAL: Original files overwritten in-place (processed dir should be empty/unchanged)
    # -----------------------------------------------------------------------
    try:
        processed_placeholder = os.path.join(
            workspace, "research_project/fieldwork_2023/interviews/processed/placeholder.txt")
        placeholder_unchanged = True
        if os.path.exists(processed_placeholder):
            with open(processed_placeholder, "r") as f:
                content = f.read()
            placeholder_unchanged = "This directory is for processed transcripts." in content
        checks.append({
            "name": "processed_dir_not_touched",
            "passed": placeholder_unchanged,
            "detail": "The processed/ placeholder file should remain untouched."
        })
    except Exception as e:
        checks.append({"name": "processed_dir_check_error", "passed": False, "detail": str(e)})

    # -----------------------------------------------------------------------
    # Score calculation
    # -----------------------------------------------------------------------
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    passed = (passed_count == total)

    result = {
        "passed": passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)