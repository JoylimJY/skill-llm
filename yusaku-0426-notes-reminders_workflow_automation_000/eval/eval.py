import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    max_score = 4

    # ── Helper ──────────────────────────────────────────────────────────────
    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── 1. Note was added correctly ─────────────────────────────────────────
    notes_db_path = Path(workspace) / "data" / "notes_db.json"
    try:
        with open(notes_db_path, "r", encoding="utf-8") as f:
            notes_db = json.load(f)
        notes = notes_db.get("notes", [])
        # Must contain a note with the exact title "Sprint 42 Kickoff"
        matching = [n for n in notes if n.get("title") == "Sprint 42 Kickoff"]
        if matching:
            note = matching[0]
            content = note.get("content", "")
            # Content must mention the authentication module refactor and tech debt items
            content_ok = (
                "authentication" in content.lower() or "authentication module" in content.lower()
            ) and (
                "#112" in content or "112" in content
            )
            total_score += add_check(
                "note_title_correct",
                True,
                f"Found note with title 'Sprint 42 Kickoff'. Content preview: {content[:80]}"
            )
            total_score += add_check(
                "note_content_correct",
                content_ok,
                f"Note content {'contains' if content_ok else 'MISSING'} expected references. Content: {content[:120]}"
            )
        else:
            total_score += add_check("note_title_correct", False, f"No note with title 'Sprint 42 Kickoff' found. Titles: {[n.get('title') for n in notes]}")
            total_score += add_check("note_content_correct", False, "Note not found, cannot check content.")
    except Exception as e:
        total_score += add_check("note_title_correct", False, f"Exception reading notes_db.json: {e}")
        total_score += add_check("note_content_correct", False, f"Exception reading notes_db.json: {e}")

    # ── 2. Reminder was added with correct format and channel ───────────────
    reminders_db_path = Path(workspace) / "data" / "reminders_db.json"
    try:
        with open(reminders_db_path, "r", encoding="utf-8") as f:
            reminders_db = json.load(f)
        reminders = reminders_db.get("reminders", [])
        # Must contain a reminder with message "スプリント計画ミーティングの準備"
        matching_r = [r for r in reminders if r.get("message") == "スプリント計画ミーティングの準備"]
        if matching_r:
            reminder = matching_r[0]
            remind_at = reminder.get("remind_at", "")
            channel = reminder.get("channel", "")
            # ISO 8601 with +09:00 timezone (Asia/Tokyo)
            import re
            iso_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$')
            tz_ok = bool(iso_pattern.match(remind_at))
            channel_ok = channel == "C1BSPRNT42X"
            reminder_format_ok = tz_ok and channel_ok
            total_score += add_check(
                "reminder_added_correctly",
                reminder_format_ok,
                f"remind_at='{remind_at}' tz_ok={tz_ok}, channel='{channel}' channel_ok={channel_ok}"
            )
        else:
            total_score += add_check(
                "reminder_added_correctly",
                False,
                f"No reminder with message 'スプリント計画ミーティングの準備' found. Messages: {[r.get('message') for r in reminders]}"
            )
    except Exception as e:
        total_score += add_check("reminder_added_correctly", False, f"Exception reading reminders_db.json: {e}")

    # ── 3. fired_notifications.txt exists and contains correct format ───────
    # Search for fired_notifications.txt in workspace root or subdirectories
    notif_candidates = list(Path(workspace).rglob("fired_notifications.txt"))
    if notif_candidates:
        notif_path = notif_candidates[0]
        try:
            with open(notif_path, "r", encoding="utf-8") as f:
                notif_content = f.read()
            # Must contain the exact format: リマインダー: スプリント計画ミーティングの準備
            expected_line = "リマインダー: スプリント計画ミーティングの準備"
            format_ok = expected_line in notif_content
            total_score += add_check(
                "fired_notification_format",
                format_ok,
                f"File found at {notif_path}. Contains expected line: {format_ok}. File content: {repr(notif_content[:200])}"
            )
        except Exception as e:
            total_score += add_check("fired_notification_format", False, f"Exception reading fired_notifications.txt: {e}")
    else:
        total_score += add_check(
            "fired_notification_format",
            False,
            "fired_notifications.txt not found anywhere in workspace."
        )

    # ── Final scoring ────────────────────────────────────────────────────────
    score = total_score / max_score
    passed = score >= 0.75 and all(c["passed"] for c in checks)

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))