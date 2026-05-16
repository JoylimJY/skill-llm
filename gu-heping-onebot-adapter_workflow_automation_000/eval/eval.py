import sys
import json
from pathlib import Path

def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records

def run_eval(workspace):
    checks = []
    score = 0.0

    # --- Locate the agent's output dispatch log ---
    # The mock server writes to this file as the agent calls the HTTP API.
    # The agent must also produce an event_summary.json or similar.
    dispatch_log_path = Path(workspace) / "data" / "processed" / "dispatch_log.jsonl"
    
    # Also search for any event_summary output file the agent was asked to create
    summary_candidates = list(Path(workspace).rglob("event_summary.json"))

    # ---------------------------------------------------------------
    # CHECK 1: dispatch_log.jsonl was written (mock server received calls)
    # ---------------------------------------------------------------
    try:
        if not dispatch_log_path.exists():
            checks.append({"name": "dispatch_log_exists", "passed": False,
                           "detail": "dispatch_log.jsonl not found — agent never called the HTTP API."})
        else:
            records = load_jsonl(str(dispatch_log_path))
            if len(records) == 0:
                checks.append({"name": "dispatch_log_exists", "passed": False,
                               "detail": "dispatch_log.jsonl is empty — no API calls recorded."})
            else:
                checks.append({"name": "dispatch_log_exists", "passed": True,
                               "detail": f"dispatch_log.jsonl found with {len(records)} records."})
                score += 0.1
    except Exception as e:
        checks.append({"name": "dispatch_log_exists", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 2: "ping" private messages → send_private_msg with "pong"
    # Events 1 (user 111222333) and 8 (user 222333444) are "ping" private messages
    # ---------------------------------------------------------------
    try:
        records = load_jsonl(str(dispatch_log_path)) if dispatch_log_path.exists() else []
        ping_replies = [
            r for r in records
            if r.get("action") == "send_private_msg" and r.get("message") == "pong"
        ]
        ping_user_ids = {r.get("user_id") for r in ping_replies}
        expected_ping_users = {111222333, 222333444}
        missing = expected_ping_users - ping_user_ids
        if not missing:
            checks.append({"name": "ping_pong_private_reply", "passed": True,
                           "detail": f"Both ping→pong private replies sent. user_ids: {ping_user_ids}"})
            score += 0.2
        else:
            checks.append({"name": "ping_pong_private_reply", "passed": False,
                           "detail": f"Missing pong replies for user_ids: {missing}. Found: {ping_user_ids}"})
    except Exception as e:
        checks.append({"name": "ping_pong_private_reply", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 3: Group messages with "帮助" → send_group_msg with exact keyword reply
    # Events 2 (group 500600700) and 9 (group 800900100)
    # Exact reply from SKILL.md: "可用命令: /help, /status, /info"
    # ---------------------------------------------------------------
    try:
        records = load_jsonl(str(dispatch_log_path)) if dispatch_log_path.exists() else []
        expected_help_reply = "可用命令: /help, /status, /info"
        help_replies = [
            r for r in records
            if r.get("action") == "send_group_msg" and r.get("message") == expected_help_reply
        ]
        help_group_ids = {r.get("group_id") for r in help_replies}
        expected_groups = {500600700, 800900100}
        missing_groups = expected_groups - help_group_ids
        if not missing_groups:
            checks.append({"name": "help_keyword_group_reply", "passed": True,
                           "detail": f"Both 帮助 group replies sent with correct text. groups: {help_group_ids}"})
            score += 0.2
        else:
            checks.append({"name": "help_keyword_group_reply", "passed": False,
                           "detail": f"Missing 帮助 group replies for groups: {missing_groups}. "
                                     f"Expected message: '{expected_help_reply}'. "
                                     f"Found group IDs with help replies: {help_group_ids}"})
    except Exception as e:
        checks.append({"name": "help_keyword_group_reply", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 4: Private "/" command → send_private_msg with "执行命令: /status"
    # Event 3: user 777888999, message "/status"
    # Exact reply: "执行命令: /status"
    # ---------------------------------------------------------------
    try:
        records = load_jsonl(str(dispatch_log_path)) if dispatch_log_path.exists() else []
        cmd_private = [
            r for r in records
            if r.get("action") == "send_private_msg"
            and r.get("user_id") == 777888999
            and r.get("message") == "执行命令: /status"
        ]
        if cmd_private:
            checks.append({"name": "slash_command_private_reply", "passed": True,
                           "detail": "Private /status command routed correctly with 执行命令: prefix."})
            score += 0.15
        else:
            # Show what was actually sent to this user
            sent_to_user = [r for r in records if r.get("user_id") == 777888999]
            checks.append({"name": "slash_command_private_reply", "passed": False,
                           "detail": f"Expected send_private_msg to 777888999 with '执行命令: /status'. "
                                     f"Found: {sent_to_user}"})
    except Exception as e:
        checks.append({"name": "slash_command_private_reply", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 5: Group "/" command → send_group_msg with "执行命令: /help"
    # Event 4: group 500600700, message "/help"
    # Exact reply: "执行命令: /help"
    # ---------------------------------------------------------------
    try:
        records = load_jsonl(str(dispatch_log_path)) if dispatch_log_path.exists() else []
        cmd_group = [
            r for r in records
            if r.get("action") == "send_group_msg"
            and r.get("group_id") == 500600700
            and r.get("message") == "执行命令: /help"
        ]
        if cmd_group:
            checks.append({"name": "slash_command_group_reply", "passed": True,
                           "detail": "Group /help command routed correctly with 执行命令: prefix to group."})
            score += 0.15
        else:
            sent_to_group = [r for r in records if r.get("group_id") == 500600700]
            checks.append({"name": "slash_command_group_reply", "passed": False,
                           "detail": f"Expected send_group_msg to group 500600700 with '执行命令: /help'. "
                                     f"Found records for that group: {sent_to_group}"})
    except Exception as e:
        checks.append({"name": "slash_command_group_reply", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 6: Plain group text ("晚上吃什么") and notice/meta events → NOT replied to
    # ---------------------------------------------------------------
    try:
        records = load_jsonl(str(dispatch_log_path)) if dispatch_log_path.exists() else []
        spurious = [
            r for r in records
            if (r.get("action") == "send_group_msg" and r.get("group_id") == 500600700
                and r.get("message") not in [
                    "可用命令: /help, /status, /info",
                    "执行命令: /help"
                ])
        ]
        # Also check no spurious send for user 999000111 (plain text sender)
        spurious_private = [
            r for r in records
            if r.get("action") == "send_private_msg" and r.get("user_id") == 999000111
        ]
        if not spurious and not spurious_private:
            checks.append({"name": "no_spurious_replies", "passed": True,
                           "detail": "No spurious replies sent to plain messages or notice events."})
            score += 0.1
        else:
            checks.append({"name": "no_spurious_replies", "passed": False,
                           "detail": f"Spurious group messages: {spurious}. "
                                     f"Spurious private to 999000111: {spurious_private}"})
    except Exception as e:
        checks.append({"name": "no_spurious_replies", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 7: event_summary.json exists and contains notice event classifications
    # ---------------------------------------------------------------
    try:
        if not summary_candidates:
            checks.append({"name": "event_summary_json_exists", "passed": False,
                           "detail": "event_summary.json not found anywhere in workspace."})
        else:
            summary_path = summary_candidates[0]
            with open(summary_path, "r", encoding="utf-8") as f:
                summary = json.load(f)

            # Must be a list or dict with event entries
            if isinstance(summary, list):
                entries = summary
            elif isinstance(summary, dict) and "events" in summary:
                entries = summary["events"]
            else:
                entries = [summary]

            # Check notice events are present
            notice_entries = [
                e for e in entries
                if (e.get("post_type") == "notice" or e.get("type") == "notice"
                    or "notice" in str(e.get("notice_type", "")))
            ]
            
            # Check for group_ban with duration
            ban_entries = [
                e for e in entries
                if ("group_ban" in str(e.get("notice_type", "")) or
                    "group_ban" in str(e.get("type", "")) or
                    e.get("duration") == 3600)
            ]

            if len(notice_entries) >= 2:
                checks.append({"name": "event_summary_json_exists", "passed": True,
                               "detail": f"event_summary.json found at {summary_path} "
                                         f"with {len(entries)} entries including {len(notice_entries)} notice events."})
                score += 0.1
            else:
                checks.append({"name": "event_summary_json_exists", "passed": False,
                               "detail": f"event_summary.json found but missing notice event entries. "
                                         f"Found {len(notice_entries)} notice entries. Entries: {entries[:3]}"})
    except Exception as e:
        checks.append({"name": "event_summary_json_exists", "passed": False, "detail": str(e)})

    # --- Final score ---
    passed = all(c["passed"] for c in checks)
    # Normalize score to max 1.0
    score = min(round(score, 2), 1.0)

    return {"passed": passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))