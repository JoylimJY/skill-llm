import json
import sys
import re
import os
from pathlib import Path
from datetime import datetime

def evaluate(workspace_root: str):
    checks = []
    workspace = Path(workspace_root)

    def check(name, condition, detail):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        return bool(condition)

    # ── 1. Config file exists at correct location ──────────────────────────────
    config_path = Path("/root/.openclaw/workspace/.memory-workflow-config")
    try:
        config_exists = config_path.exists()
        check("config_file_exists",
              config_exists,
              f"Config file at {config_path}: {'found' if config_exists else 'NOT FOUND'}")
    except Exception as e:
        check("config_file_exists", False, f"Exception: {e}")
        config_exists = False

    # ── 2. KEEP_DAYS=14 in config ──────────────────────────────────────────────
    try:
        if config_exists:
            config_text = config_path.read_text()
            keep_days_match = re.search(r'^\s*KEEP_DAYS\s*=\s*(\d+)', config_text, re.MULTILINE)
            if keep_days_match:
                keep_days_val = int(keep_days_match.group(1))
                check("config_keep_days_14",
                      keep_days_val == 14,
                      f"KEEP_DAYS={keep_days_val} (expected 14)")
            else:
                check("config_keep_days_14", False, "KEEP_DAYS not found in config")
        else:
            check("config_keep_days_14", False, "Config file missing")
    except Exception as e:
        check("config_keep_days_14", False, f"Exception: {e}")

    # ── 3. DAILY_SUMMARY_HOUR=21 in config ────────────────────────────────────
    try:
        if config_exists:
            config_text = config_path.read_text()
            hour_match = re.search(r'^\s*DAILY_SUMMARY_HOUR\s*=\s*(\d+)', config_text, re.MULTILINE)
            if hour_match:
                hour_val = int(hour_match.group(1))
                check("config_daily_hour_21",
                      hour_val == 21,
                      f"DAILY_SUMMARY_HOUR={hour_val} (expected 21)")
            else:
                check("config_daily_hour_21", False, "DAILY_SUMMARY_HOUR not found in config")
        else:
            check("config_daily_hour_21", False, "Config file missing")
    except Exception as e:
        check("config_daily_hour_21", False, f"Exception: {e}")

    # ── 4. Cron job installed for daily-summary.sh ─────────────────────────────
    try:
        crontab_result = os.popen("crontab -l 2>/dev/null").read()
        has_cron = "daily-summary.sh" in crontab_result
        check("cron_job_installed",
              has_cron,
              f"Cron contains daily-summary.sh: {has_cron}. Crontab: {crontab_result[:300]}")
    except Exception as e:
        check("cron_job_installed", False, f"Exception: {e}")

    # ── 5. Cron entry uses correct */1 * * * * format ─────────────────────────
    try:
        cron_format_ok = bool(re.search(r'\*/1\s+\*\s+\*\s+\*\s+\*.*daily-summary\.sh', crontab_result))
        check("cron_correct_schedule",
              cron_format_ok,
              f"Cron schedule */1 * * * * found: {cron_format_ok}")
    except Exception as e:
        check("cron_correct_schedule", False, f"Exception: {e}")

    # ── 6. Today's daily note exists in memory/ ────────────────────────────────
    today_str = datetime.now().strftime("%Y-%m-%d")
    daily_note_path = workspace / "memory" / f"{today_str}.md"
    try:
        note_exists = daily_note_path.exists()
        check("today_daily_note_exists",
              note_exists,
              f"Today's note at {daily_note_path}: {'found' if note_exists else 'NOT FOUND'}")
    except Exception as e:
        check("today_daily_note_exists", False, f"Exception: {e}")
        note_exists = False

    # ── 7. Daily note has correct H1 heading with today's date ────────────────
    try:
        if note_exists:
            note_text = daily_note_path.read_text()
            heading_ok = bool(re.search(rf'^#\s+{re.escape(today_str)}\s*[-–]\s*每日摘要', note_text, re.MULTILINE))
            check("daily_note_heading_correct",
                  heading_ok,
                  f"H1 heading with '{today_str} - 每日摘要': {heading_ok}")
        else:
            check("daily_note_heading_correct", False, "Daily note missing")
    except Exception as e:
        check("daily_note_heading_correct", False, f"Exception: {e}")

    # ── 8. Daily note contains all 4 required sections ────────────────────────
    try:
        if note_exists:
            note_text = daily_note_path.read_text()
            required_sections = [
                r'##\s+📋\s+今日重点',
                r'##\s+💬\s+重要对话',
                r'##\s+🎯\s+关键决策',
                r'##\s+📝\s+待办更新',
            ]
            missing = []
            for pattern in required_sections:
                if not re.search(pattern, note_text):
                    missing.append(pattern)
            check("daily_note_all_sections",
                  len(missing) == 0,
                  f"Missing sections: {missing if missing else 'none'}")
        else:
            check("daily_note_all_sections", False, "Daily note missing")
    except Exception as e:
        check("daily_note_all_sections", False, f"Exception: {e}")

    # ── 9. Daily note contains auto-generated footer with timestamp ───────────
    try:
        if note_exists:
            note_text = daily_note_path.read_text()
            footer_ok = bool(re.search(r'\*自动生成时间：\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\*', note_text))
            check("daily_note_footer_timestamp",
                  footer_ok,
                  f"Footer with '自动生成时间：YYYY-MM-DD HH:MM:SS' found: {footer_ok}")
        else:
            check("daily_note_footer_timestamp", False, "Daily note missing")
    except Exception as e:
        check("daily_note_footer_timestamp", False, f"Exception: {e}")

    # ── 10. Daily note footer contains 记录者 line ─────────────────────────────
    try:
        if note_exists:
            note_text = daily_note_path.read_text()
            recorder_ok = bool(re.search(r'\*记录者：.+\*', note_text))
            check("daily_note_footer_recorder",
                  recorder_ok,
                  f"Footer with '记录者：...' found: {recorder_ok}")
        else:
            check("daily_note_footer_recorder", False, "Daily note missing")
    except Exception as e:
        check("daily_note_footer_recorder", False, f"Exception: {e}")

    # ── 11. MEMORY.md exists and has meaningful content ────────────────────────
    memory_md_path = workspace / "MEMORY.md"
    try:
        mem_exists = memory_md_path.exists()
        check("memory_md_exists", mem_exists,
              f"MEMORY.md at {memory_md_path}: {'found' if mem_exists else 'NOT FOUND'}")
    except Exception as e:
        check("memory_md_exists", False, f"Exception: {e}")
        mem_exists = False

    # ── 12. MEMORY.md contains user profile (Alex Chen / team lead info) ───────
    try:
        if mem_exists:
            mem_text = memory_md_path.read_text()
            # Must have some non-trivial content about the user (name, role, or preference)
            has_user_info = bool(re.search(r'Alex|Chen|Portfolio Manager|团队|偏好|待办|preference|红茶|tea|任务', mem_text, re.IGNORECASE))
            check("memory_md_user_profile",
                  has_user_info,
                  f"MEMORY.md contains user/team profile info: {has_user_info}")
        else:
            check("memory_md_user_profile", False, "MEMORY.md missing")
    except Exception as e:
        check("memory_md_user_profile", False, f"Exception: {e}")

    # ── 13. MEMORY.md contains a TODO / pending task entry ────────────────────
    try:
        if mem_exists:
            mem_text = memory_md_path.read_text()
            has_todo = bool(re.search(r'待办|TODO|todo|\[ \]|\[x\]|task|任务', mem_text, re.IGNORECASE))
            check("memory_md_has_todo",
                  has_todo,
                  f"MEMORY.md contains TODO/待办 entry: {has_todo}")
        else:
            check("memory_md_has_todo", False, "MEMORY.md missing")
    except Exception as e:
        check("memory_md_has_todo", False, f"Exception: {e}")

    # ── 14. daily-summary.log exists (script was actually invoked) ─────────────
    log_path = workspace / "logs" / "daily-summary.log"
    try:
        log_exists = log_path.exists()
        check("daily_summary_log_exists",
              log_exists,
              f"Log at {log_path}: {'found' if log_exists else 'NOT FOUND'}")
    except Exception as e:
        check("daily_summary_log_exists", False, f"Exception: {e}")

    # ── 15. No .daily-summary-pending marker remains (script consumed it) ─────
    pending_file = workspace / ".daily-summary-pending"
    try:
        marker_gone = not pending_file.exists()
        check("pending_marker_consumed",
              marker_gone,
              f".daily-summary-pending removed after script ran: {marker_gone}")
    except Exception as e:
        check("pending_marker_consumed", False, f"Exception: {e}")

    # ── Score calculation ──────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    return {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "args", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))