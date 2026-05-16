import sys
import os
import re
import json
from pathlib import Path
from datetime import datetime

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # ── Determine today's date ──────────────────────────────────────────────
    today_str = datetime.now().strftime("%Y-%m-%d")
    expected_log_path = Path(workspace) / "chat" / f"{today_str}.md"

    # CHECK 1: chat/ directory exists under workspace
    chat_dir = Path(workspace) / "chat"
    dir_exists = chat_dir.is_dir()
    checks.append({
        "name": "chat_directory_exists",
        "passed": dir_exists,
        "detail": f"Expected directory at {chat_dir}. Found: {dir_exists}"
    })
    if dir_exists:
        total_score += 0.10

    # CHECK 2: Daily log file exists with correct name
    file_exists = expected_log_path.is_file()
    checks.append({
        "name": "daily_log_file_exists",
        "passed": file_exists,
        "detail": f"Expected file at {expected_log_path}. Found: {file_exists}"
    })
    if file_exists:
        total_score += 0.10

    if not file_exists:
        # Look for any .md file in chat/ as partial credit hint
        md_files = list(chat_dir.glob("*.md")) if chat_dir.is_dir() else []
        checks.append({
            "name": "any_md_in_chat",
            "passed": len(md_files) > 0,
            "detail": f"Found these .md files in chat/: {[str(f) for f in md_files]}"
        })
        print(json.dumps({
            "passed": False,
            "score": total_score,
            "checks": checks
        }))
        return

    # Read content
    try:
        content = expected_log_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully."})
    total_score += 0.05

    # CHECK 3: Timestamp format [HH:MM:SS] present (proprietary trap)
    # The format requires [HH:MM:SS] on its own line
    timestamp_pattern = re.compile(r'^\[(\d{2}:\d{2}:\d{2})\]$', re.MULTILINE)
    timestamps_found = timestamp_pattern.findall(content)
    # We expect at least 4 entries
    has_4_timestamps = len(timestamps_found) >= 4
    checks.append({
        "name": "timestamp_format_correct_HH_MM_SS_brackets",
        "passed": len(timestamps_found) >= 1,
        "detail": f"Found {len(timestamps_found)} timestamp(s) matching [HH:MM:SS] on own line. Expected >= 4. Timestamps: {timestamps_found}"
    })
    if len(timestamps_found) >= 1:
        total_score += 0.10
    if has_4_timestamps:
        total_score += 0.05

    # CHECK 4: Turn 1 — User line present with correct prefix
    turn1_user = re.search(r"User: I can't log in", content)
    checks.append({
        "name": "turn1_user_message_present",
        "passed": bool(turn1_user),
        "detail": "Turn 1 user message about login issue." + (" Found." if turn1_user else " NOT found.")
    })
    if turn1_user:
        total_score += 0.10

    # CHECK 5: Turn 1 — Assistant line present
    turn1_asst = re.search(r"Assistant: I've reset your credentials", content)
    checks.append({
        "name": "turn1_assistant_message_present",
        "passed": bool(turn1_asst),
        "detail": "Turn 1 assistant reply about resetting credentials." + (" Found." if turn1_asst else " NOT found.")
    })
    if turn1_asst:
        total_score += 0.10

    # CHECK 6: Turn 2 — Both user and assistant present
    turn2_user = re.search(r"User: The temporary password worked", content)
    turn2_asst = re.search(r"Assistant: Your account permissions were misconfigured", content)
    checks.append({
        "name": "turn2_both_messages_present",
        "passed": bool(turn2_user) and bool(turn2_asst),
        "detail": f"Turn 2 user found: {bool(turn2_user)}, assistant found: {bool(turn2_asst)}"
    })
    if turn2_user and turn2_asst:
        total_score += 0.10

    # CHECK 7: Turn 3 — Assistant-only entry (NO User: line between its timestamp and Turn 4 timestamp)
    # Find the block for the assistant-only entry
    turn3_asst = re.search(r"Assistant: Escalation ticket #4821", content)
    checks.append({
        "name": "turn3_assistant_only_present",
        "passed": bool(turn3_asst),
        "detail": "Turn 3 assistant-only note about ticket #4821." + (" Found." if turn3_asst else " NOT found.")
    })
    if turn3_asst:
        total_score += 0.10

    # CHECK 8: Turn 3 block does NOT have a "User:" line before it (assistant-only constraint)
    # Extract the block around turn3
    # Strategy: find timestamp blocks and check the one containing escalation ticket
    # Split content into blocks by timestamp
    blocks = re.split(r'\n(?=\[\d{2}:\d{2}:\d{2}\])', content)
    turn3_block = None
    for block in blocks:
        if "Escalation ticket #4821" in block:
            turn3_block = block
            break

    if turn3_block is not None:
        # The block should NOT contain "User:" line
        has_no_user_in_turn3 = "User:" not in turn3_block
        checks.append({
            "name": "turn3_no_user_line_in_assistant_only_entry",
            "passed": has_no_user_in_turn3,
            "detail": f"Turn 3 block (assistant-only): {'Correctly omits User: line' if has_no_user_in_turn3 else 'INCORRECTLY contains User: line'}. Block: {repr(turn3_block[:200])}"
        })
        if has_no_user_in_turn3:
            total_score += 0.10
    else:
        checks.append({
            "name": "turn3_no_user_line_in_assistant_only_entry",
            "passed": False,
            "detail": "Could not locate Turn 3 block in content."
        })

    # CHECK 9: Turn 4 — Both present
    turn4_user = re.search(r"User: Is there an ETA on the billing issue", content)
    turn4_asst = re.search(r"Assistant: The finance team has been notified", content)
    checks.append({
        "name": "turn4_both_messages_present",
        "passed": bool(turn4_user) and bool(turn4_asst),
        "detail": f"Turn 4 user found: {bool(turn4_user)}, assistant found: {bool(turn4_asst)}"
    })
    if turn4_user and turn4_asst:
        total_score += 0.10

    # CHECK 10: Leading newline before each entry (proprietary format: \n[HH:MM:SS])
    # The file should have newlines before bracketed timestamps (except possibly the very first entry)
    newline_before_ts = re.findall(r'\n\[\d{2}:\d{2}:\d{2}\]', content)
    checks.append({
        "name": "leading_newline_before_timestamps",
        "passed": len(newline_before_ts) >= 3,
        "detail": f"Found {len(newline_before_ts)} occurrences of newline-before-timestamp. Expected >= 3 (all except possibly first)."
    })
    if len(newline_before_ts) >= 3:
        total_score += 0.05

    # CHECK 11: File is in correct location (not in a wrong subdirectory)
    # This is already enforced by expected_log_path, but let's verify no other stray files
    wrong_locations = []
    for candidate in Path(workspace).rglob(f"{today_str}.md"):
        if candidate != expected_log_path:
            wrong_locations.append(str(candidate))
    checks.append({
        "name": "log_file_only_in_correct_location",
        "passed": len(wrong_locations) == 0,
        "detail": f"Stray files found elsewhere: {wrong_locations}" if wrong_locations else "Log file is only in the correct location."
    })
    if len(wrong_locations) == 0:
        total_score += 0.05

    # Final pass determination
    required_checks = [
        "chat_directory_exists",
        "daily_log_file_exists",
        "timestamp_format_correct_HH_MM_SS_brackets",
        "turn1_user_message_present",
        "turn1_assistant_message_present",
        "turn3_assistant_only_present",
        "turn3_no_user_line_in_assistant_only_entry",
    ]
    required_passed = all(
        c["passed"] for c in checks if c["name"] in required_checks
    )
    overall_passed = required_passed and total_score >= 0.70

    print(json.dumps({
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 4),
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)