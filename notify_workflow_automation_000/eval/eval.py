import json
import sys
import re
from pathlib import Path

def find_output_file(workspace: Path):
    candidates = list(workspace.rglob("notification_dispatch_plan.json"))
    if not candidates:
        return None
    return candidates[0]

def score_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []

    # ── Locate the output file ────────────────────────────────────────────────
    plan_file = find_output_file(workspace)
    if plan_file is None:
        checks.append(score_check("output_file_exists", False, "notification_dispatch_plan.json not found anywhere in workspace"))
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append(score_check("output_file_exists", True, f"Found at {plan_file}"))

    try:
        raw = plan_file.read_text(encoding="utf-8")
        plan = json.loads(raw)
    except Exception as e:
        checks.append(score_check("output_file_parseable", False, f"JSON parse error: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}
    checks.append(score_check("output_file_parseable", True, "Valid JSON"))

    raw_lower = raw.lower()

    # ── Helper: find dispatch entry for event id ──────────────────────────────
    def find_entries_for(event_ids):
        """Return all entries in the plan that reference any of the given event IDs."""
        results = []
        def walk(obj):
            if isinstance(obj, dict):
                text = json.dumps(obj).lower()
                if any(eid.lower() in text for eid in event_ids):
                    results.append(obj)
                    return
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for item in obj:
                    walk(item)
        walk(plan)
        return results

    def plan_text_for(event_ids):
        entries = find_entries_for(event_ids)
        return json.dumps(entries).lower()

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 1: E07 debug event → LOG ONLY, no notification channel
    # ══════════════════════════════════════════════════════════════════════════
    try:
        e07_text = plan_text_for(["e07"])
        # Must mention log only / no notification
        is_log_only = (
            ("log" in e07_text and "only" in e07_text) or
            ("log_only" in e07_text) or
            ("log-only" in e07_text) or
            ("no notification" in e07_text) or
            ("never notify" in e07_text) or
            ("do not notify" in e07_text) or
            ("not notif" in e07_text)
        )
        # Must NOT assign a real channel (push/sms/email/telegram/slack/chat)
        bad_channel = any(ch in e07_text for ch in ["push", "sms", "email", "telegram", "slack", "\"chat\""])
        passed_e07 = is_log_only and not bad_channel
        checks.append(score_check(
            "E07_debug_log_only",
            passed_e07,
            f"E07 debug event. log_only={is_log_only}, bad_channel_assigned={bad_channel}. Snippet: {e07_text[:300]}"
        ))
    except Exception as ex:
        checks.append(score_check("E07_debug_log_only", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 2: E01 security alert (level 5) during quiet hours → MUST send immediately (breaks quiet hours)
    # via push + primary chat (telegram for alice)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        e01_text = plan_text_for(["e01"])
        is_immediate = ("immediate" in e01_text) or ("now" in e01_text) or ("break" in e01_text and "quiet" in e01_text) or ("24/7" in e01_text)
        has_push = "push" in e01_text
        has_chat = any(ch in e01_text for ch in ["telegram", "chat", "primary"])
        breaks_quiet = ("break" in e01_text and "quiet" in e01_text) or ("critical" in e01_text and ("quiet" not in e01_text or "break" in e01_text)) or ("level 5" in e01_text) or ("never" in e01_text and "quiet" in e01_text) or is_immediate
        passed_e01 = has_push and has_chat and is_immediate
        checks.append(score_check(
            "E01_security_alert_breaks_quiet_hours",
            passed_e01,
            f"E01 level-5 alert. immediate={is_immediate}, push={has_push}, chat={has_chat}. Snippet: {e01_text[:400]}"
        ))
    except Exception as ex:
        checks.append(score_check("E01_security_alert_breaks_quiet_hours", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 3: E03+E04+E05 → BATCHING (3 events, same project=alpha, within 3 min window < 5 min)
    # Must be combined into ONE message, not three separate ones
    # ══════════════════════════════════════════════════════════════════════════
    try:
        batch_text = plan_text_for(["e03", "e04", "e05"])
        # Check they appear in a batched/combined entry
        # The plan should mention all three (or reference "3 deployments" / "alpha" project combined)
        mentions_batched = (
            "batch" in batch_text or
            "combined" in batch_text or
            "grouped" in batch_text or
            "single message" in batch_text or
            "summary" in batch_text or
            "merge" in batch_text
        )
        # Should NOT produce 3 separate notification entries for e03, e04, e05
        # We check: if all three appear separately as top-level items, that's a fail
        # Count how many separate "dispatch" objects reference exactly one of the events
        def count_separate(ids):
            count = 0
            def walk2(obj, depth=0):
                nonlocal count
                if isinstance(obj, dict):
                    t = json.dumps(obj).lower()
                    matched = [eid for eid in ids if eid.lower() in t]
                    if len(matched) == 1 and depth > 0:
                        count += 1
                        return
                    for v in obj.values():
                        walk2(v, depth+1)
                elif isinstance(obj, list):
                    for item in obj:
                        walk2(item, depth)
            walk2(plan)
            return count
        # If all three are separate → spam (fail)
        # Alpha project mentioned + batching keyword → pass
        has_alpha = "alpha" in batch_text
        passed_batch = mentions_batched and has_alpha
        checks.append(score_check(
            "E03_E04_E05_batched_into_one",
            passed_batch,
            f"Batching check. mentions_batched={mentions_batched}, has_alpha={has_alpha}. Snippet: {batch_text[:400]}"
        ))
    except Exception as ex:
        checks.append(score_check("E03_E04_E05_batched_into_one", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 4: E06 daily summary for Bob at 02:00 Tokyo (quiet hours) → queued to 08:00 Tokyo
    # ══════════════════════════════════════════════════════════════════════════
    try:
        e06_text = plan_text_for(["e06"])
        is_queued = (
            "queue" in e06_text or
            "08:00" in e06_text or
            "8:00" in e06_text or
            "deliver at" in e06_text or
            "morning" in e06_text or
            "quiet hour" in e06_text or
            "held" in e06_text or
            "delay" in e06_text or
            "scheduled" in e06_text
        )
        passed_e06 = is_queued
        checks.append(score_check(
            "E06_quiet_hours_queued",
            passed_e06,
            f"E06 daily summary during Tokyo quiet hours. queued={is_queued}. Snippet: {e06_text[:300]}"
        ))
    except Exception as ex:
        checks.append(score_check("E06_quiet_hours_queued", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 5: E09 system down (level 5) for Carol at 23:30 NY → breaks quiet hours, push + sms
    # ══════════════════════════════════════════════════════════════════════════
    try:
        e09_text = plan_text_for(["e09"])
        has_push = "push" in e09_text
        has_sms = "sms" in e09_text
        is_immediate = "immediate" in e09_text or "now" in e09_text or "24/7" in e09_text or "break" in e09_text
        passed_e09 = has_push and has_sms and is_immediate
        checks.append(score_check(
            "E09_system_down_push_sms_immediate",
            passed_e09,
            f"E09 system down level-5 during quiet hours. push={has_push}, sms={has_sms}, immediate={is_immediate}. Snippet: {e09_text[:400]}"
        ))
    except Exception as ex:
        checks.append(score_check("E09_system_down_push_sms_immediate", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 6: E08 weekly summary for Carol → Email channel, scheduled Monday 09:00
    # ══════════════════════════════════════════════════════════════════════════
    try:
        e08_text = plan_text_for(["e08"])
        has_email = "email" in e08_text
        is_scheduled = "scheduled" in e08_text or "monday" in e08_text or "09:00" in e08_text or "9:00" in e08_text
        passed_e08 = has_email
        checks.append(score_check(
            "E08_weekly_summary_email",
            passed_e08,
            f"E08 weekly summary. email={has_email}, scheduled={is_scheduled}. Snippet: {e08_text[:300]}"
        ))
    except Exception as ex:
        checks.append(score_check("E08_weekly_summary_email", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 7: E02 build failed → Telegram for Alice, immediate, message leads with outcome
    # Content must mention STRIPE_KEY (specific, not generic "error occurred")
    # ══════════════════════════════════════════════════════════════════════════
    try:
        e02_text = plan_text_for(["e02"])
        has_telegram = "telegram" in e02_text
        is_immediate = "immediate" in e02_text or "now" in e02_text
        has_specific_content = "stripe" in e02_text or "stripe_key" in e02_text or "build" in e02_text
        # Must NOT be a generic "error occurred" type message
        is_not_generic = "error occurred" not in e02_text and "task completed" not in e02_text
        passed_e02 = has_telegram and has_specific_content and is_not_generic
        checks.append(score_check(
            "E02_build_fail_specific_message_telegram",
            passed_e02,
            f"E02 build fail. telegram={has_telegram}, specific_content={has_specific_content}, not_generic={is_not_generic}. Snippet: {e02_text[:400]}"
        ))
    except Exception as ex:
        checks.append(score_check("E02_build_fail_specific_message_telegram", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 8: E11 escalation plan → must mention: wait 2h, second attempt, secondary channel after 4h, max 3 attempts
    # ══════════════════════════════════════════════════════════════════════════
    try:
        e11_text = plan_text_for(["e11"])
        has_escalation = "escalat" in e11_text
        mentions_2h = "2 hour" in e11_text or "2h" in e11_text or "two hour" in e11_text
        mentions_max_attempts = "3" in e11_text and ("attempt" in e11_text or "reminder" in e11_text or "time" in e11_text)
        mentions_secondary = "secondary" in e11_text or "another channel" in e11_text or "different channel" in e11_text or "sms" in e11_text or "email" in e11_text
        # Should NOT say "contact others without permission"
        no_contact_others = "contact others" not in e11_text and "notify others" not in e11_text
        passed_e11 = has_escalation and (mentions_2h or mentions_max_attempts) and no_contact_others
        checks.append(score_check(
            "E11_escalation_plan_correct",
            passed_e11,
            f"E11 escalation. has_escalation={has_escalation}, 2h_wait={mentions_2h}, max_attempts={mentions_max_attempts}, secondary={mentions_secondary}, no_contact_others={no_contact_others}. Snippet: {e11_text[:500]}"
        ))
    except Exception as ex:
        checks.append(score_check("E11_escalation_plan_correct", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 9: Confirmation format present (✅ Scheduled / 📅 / 📬 / 🔕)
    # At least one notification must include the required confirmation block format
    # ══════════════════════════════════════════════════════════════════════════
    try:
        has_checkmark = "✅" in raw
        has_calendar = "📅" in raw
        has_mailbox = "📬" in raw
        has_bell = "🔕" in raw
        confirmation_keywords = ("scheduled" in raw_lower or "via:" in raw_lower or "respects quiet" in raw_lower)
        passed_confirm = (has_checkmark and has_calendar) or (has_checkmark and has_mailbox) or confirmation_keywords
        checks.append(score_check(
            "confirmation_format_present",
            passed_confirm,
            f"Confirmation block format. ✅={has_checkmark}, 📅={has_calendar}, 📬={has_mailbox}, 🔕={has_bell}, keywords={confirmation_keywords}"
        ))
    except Exception as ex:
        checks.append(score_check("confirmation_format_present", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 10: SMS or Push size constraints respected (for E09 which hits Carol's sms/push)
    # Any SMS content in the plan must be ≤ 160 chars; push title ≤ 50 chars
    # ══════════════════════════════════════════════════════════════════════════
    try:
        sms_violations = []
        push_violations = []
        def check_sizes(obj, path=""):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if isinstance(v, str):
                        key_lower = k.lower()
                        if "sms" in key_lower and "content" in key_lower or ("sms" in key_lower and "message" in key_lower) or ("sms" in key_lower and "body" in key_lower) or ("sms" in key_lower and "text" in key_lower):
                            if len(v) > 160:
                                sms_violations.append((path+"."+k, len(v)))
                        if "push" in key_lower and "title" in key_lower:
                            if len(v) > 50:
                                push_violations.append((path+"."+k, len(v)))
                        if "push" in key_lower and ("body" in key_lower or "message" in key_lower):
                            if len(v) > 100:
                                push_violations.append((path+"."+k, len(v)))
                    elif isinstance(v, (dict, list)):
                        check_sizes(v, path+"."+k)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_sizes(item, path+f"[{i}]")
        check_sizes(plan)
        passed_sizes = len(sms_violations) == 0 and len(push_violations) == 0
        detail = "No size violations found."
        if sms_violations:
            detail = f"SMS violations (>160 chars): {sms_violations}"
        if push_violations:
            detail += f" Push violations: {push_violations}"
        checks.append(score_check("channel_size_constraints", passed_sizes, detail))
    except Exception as ex:
        checks.append(score_check("channel_size_constraints", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 11: E10 task_completed for Bob during quiet hours (00:30 Tokyo) → queued to 08:00
    # ══════════════════════════════════════════════════════════════════════════
    try:
        e10_text = plan_text_for(["e10"])
        is_queued = (
            "queue" in e10_text or
            "08:00" in e10_text or
            "8:00" in e10_text or
            "morning" in e10_text or
            "quiet hour" in e10_text or
            "delay" in e10_text or
            "scheduled" in e10_text or
            "held" in e10_text or
            "batch" in e10_text or
            "digest" in e10_text
        )
        passed_e10 = is_queued
        checks.append(score_check(
            "E10_task_completed_quiet_hours_queued",
            passed_e10,
            f"E10 task_completed during Tokyo quiet hours (00:30). queued={is_queued}. Snippet: {e10_text[:300]}"
        ))
    except Exception as ex:
        checks.append(score_check("E10_task_completed_quiet_hours_queued", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # CHECK 12: No Telegram markdown tables (channel formatting rule)
    # Any Telegram message must use bullet lists, not markdown table syntax (|---|)
    # ══════════════════════════════════════════════════════════════════════════
    try:
        telegram_table_violation = False
        def find_telegram_tables(obj):
            nonlocal telegram_table_violation
            if isinstance(obj, dict):
                is_telegram_entry = any("telegram" in str(v).lower() for v in obj.values())
                for k, v in obj.items():
                    if isinstance(v, str) and is_telegram_entry:
                        # Check for markdown table pattern in content destined for telegram
                        if re.search(r'\|.*\|.*\|', v) and "---" in v:
                            telegram_table_violation = True
                    elif isinstance(v, (dict, list)):
                        find_telegram_tables(v)
            elif isinstance(obj, list):
                for item in obj:
                    find_telegram_tables(item)
        find_telegram_tables(plan)
        passed_no_tg_table = not telegram_table_violation
        checks.append(score_check(
            "no_markdown_tables_in_telegram",
            passed_no_tg_table,
            f"Telegram entries should not use markdown tables. violation={telegram_table_violation}"
        ))
    except Exception as ex:
        checks.append(score_check("no_markdown_tables_in_telegram", False, f"Exception: {ex}"))

    # ══════════════════════════════════════════════════════════════════════════
    # FINAL SCORE
    # ══════════════════════════════════════════════════════════════════════════
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 9  # must pass at least 9/12

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2, ensure_ascii=False))