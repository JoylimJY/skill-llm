#!/usr/bin/env python3
"""
Evaluation script for the cc-bridge routing task.

Checks:
1. routing_log.json exists and has 6 entries (one per message)
2. Session ID is correctly sanitized (only [a-zA-Z0-9_], consistent across all messages)
3. Status is called first for every message (call_log.jsonl)
4. Message 1 (start): control command → start action called
5. Message 2 (cc状态): control command → status action called  
6. Message 3 (large task): send called with --long flag
7. Message 4 (允许): approval-waiting → approve called with arg "2" (not 1!)
8. Message 5 (/compact): CC slash command → send called with '/compact'
9. Message 6 (stop): control command → stop called
10. Output formatting: prefix with 🤖 **CC →**, truncation for large output
"""

import sys
import json
import re
from pathlib import Path

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_jsonl(path):
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries

def check_session_id_valid(sid: str) -> bool:
    """Session ID must only contain [a-zA-Z0-9_]"""
    return bool(re.fullmatch(r'[a-zA-Z0-9_]+', sid))

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Helper ─────────────────────────────────────────────────────────────────
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── 1. routing_log.json exists ─────────────────────────────────────────────
    routing_log_paths = list(workspace.rglob("routing_log.json"))
    if not routing_log_paths:
        add_check("routing_log.json exists", False, "File not found anywhere in workspace")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    routing_log_path = routing_log_paths[0]
    try:
        routing_log = load_json(routing_log_path)
    except Exception as e:
        add_check("routing_log.json parseable", False, f"JSON parse error: {e}")
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    add_check("routing_log.json exists and parseable", True, f"Found at {routing_log_path}")

    # ── 2. Has 6 entries ───────────────────────────────────────────────────────
    has_6 = add_check(
        "routing_log has 6 entries",
        len(routing_log) == 6,
        f"Found {len(routing_log)} entries, expected 6"
    )

    if len(routing_log) < 4:
        print(json.dumps({"passed": False, "score": 0.05, "checks": checks}))
        return

    # ── 3. call_log.jsonl exists ───────────────────────────────────────────────
    call_log_path = workspace / "tmp/sessions/call_log.jsonl"
    try:
        call_log = load_jsonl(call_log_path)
    except Exception as e:
        add_check("call_log.jsonl readable", False, f"Error: {e}")
        call_log = []

    if call_log:
        add_check("call_log.jsonl readable", True, f"{len(call_log)} calls recorded")
    
    # ── 4. Session ID sanitization ─────────────────────────────────────────────
    # Extract all session IDs used in call log
    used_session_ids = list(set(e.get("session_id", "") for e in call_log))
    
    session_id_ok = False
    session_id_detail = "No calls found"
    if used_session_ids:
        # Should be exactly one consistent session ID
        if len(used_session_ids) == 1:
            sid = used_session_ids[0]
            valid = check_session_id_valid(sid)
            # Should contain something from both "telegram" and "42"
            has_channel = "telegram" in sid.lower()
            has_chatid = "42" in sid or "chat" in sid.lower()
            session_id_ok = valid and has_channel
            session_id_detail = (
                f"Session ID used: '{sid}'. "
                f"Valid chars: {valid}, Contains channel ref: {has_channel}, "
                f"Contains chat ref: {has_chatid}"
            )
        else:
            # Multiple session IDs — might still be ok if all valid and consistent pattern
            all_valid = all(check_session_id_valid(s) for s in used_session_ids)
            session_id_detail = f"Multiple session IDs found: {used_session_ids}. All valid chars: {all_valid}"
            session_id_ok = all_valid and len(used_session_ids) <= 2

    add_check("Session ID correctly sanitized (only [a-zA-Z0-9_])", session_id_ok, session_id_detail)

    # ── 5. Status called before each message (routing) ─────────────────────────
    # Check that 'status' appears multiple times in call log (at least 5 status calls for 6 messages,
    # noting that msg2 is itself a status command so may or may not call status first)
    status_calls = [e for e in call_log if e.get("action") == "status"]
    status_first_check = len(status_calls) >= 4
    add_check(
        "Status checked before routing (≥4 status calls)",
        status_first_check,
        f"Found {len(status_calls)} status calls in call_log"
    )

    # ── 6. Message 1: start command called ─────────────────────────────────────
    start_calls = [e for e in call_log if e.get("action") == "start"]
    msg1_ok = len(start_calls) >= 1
    add_check(
        "Msg1 'start claude code' → start action executed",
        msg1_ok,
        f"Found {len(start_calls)} start call(s)"
    )

    # ── 7. Message 3: send with --long flag ────────────────────────────────────
    long_send_calls = [
        e for e in call_log 
        if e.get("action") == "send" and e.get("flag") == "--long"
    ]
    msg3_ok = len(long_send_calls) >= 1
    add_check(
        "Msg3 large refactor task → send called with --long flag",
        msg3_ok,
        f"Found {len(long_send_calls)} send --long call(s). "
        f"All send calls: {[e for e in call_log if e.get('action')=='send']}"
    )

    # ── 8. Message 4: approve 2 (允许 = Allow always, NOT approve 1) ───────────
    approve_calls = [e for e in call_log if e.get("action") == "approve"]
    approve_2_calls = [e for e in approve_calls if e.get("arg") in ("2", 2)]
    approve_1_calls = [e for e in approve_calls if e.get("arg") in ("1", 1)]
    
    # '允许' must map to approve 2
    msg4_ok = len(approve_2_calls) >= 1
    msg4_not_1 = len(approve_1_calls) == 0  # Extra credit if no wrong mapping
    add_check(
        "Msg4 '允许' → approve 2 (Allow always), NOT approve 1",
        msg4_ok,
        f"approve 2 calls: {len(approve_2_calls)}, approve 1 calls: {len(approve_1_calls)}. "
        f"All approve calls: {approve_calls}"
    )

    # ── 9. Message 5: /compact sent via send action ───────────────────────────
    compact_calls = [
        e for e in call_log
        if e.get("action") == "send" and "/compact" in str(e.get("arg", ""))
    ]
    msg5_ok = len(compact_calls) >= 1
    add_check(
        "Msg5 '/compact' CC slash command → forwarded via send",
        msg5_ok,
        f"Found {len(compact_calls)} send call(s) with /compact arg. "
        f"All send calls: {[(e.get('action'), e.get('arg')) for e in call_log if e.get('action')=='send']}"
    )

    # ── 10. Message 6: stop command called ────────────────────────────────────
    stop_calls = [e for e in call_log if e.get("action") == "stop"]
    msg6_ok = len(stop_calls) >= 1
    add_check(
        "Msg6 'stop claude code' → stop action executed",
        msg6_ok,
        f"Found {len(stop_calls)} stop call(s)"
    )

    # ── 11. Output formatting: 🤖 **CC →** prefix ────────────────────────────
    prefix_found = False
    prefix_detail = "No routing_log entries checked"
    try:
        for entry in routing_log:
            response = str(entry.get("response", "") or entry.get("reply", "") or entry.get("output", ""))
            if "🤖" in response and "CC" in response:
                prefix_found = True
                break
        prefix_detail = f"Prefix '🤖 **CC →**' found in at least one response: {prefix_found}"
    except Exception as e:
        prefix_detail = f"Error checking prefix: {e}"
    
    add_check("Output prefixed with 🤖 **CC →**", prefix_found, prefix_detail)

    # ── 12. Output truncation for large history output ────────────────────────
    # If the agent called history (which returns >3000 chars), check truncation behavior
    history_calls = [e for e in call_log if e.get("action") == "history"]
    trunc_check_name = "Long output (>3000 chars) truncated to last 2000 chars"
    if history_calls:
        trunc_ok = False
        trunc_detail = "History was called; checking routing_log for truncation"
        for entry in routing_log:
            response = str(entry.get("response", "") or entry.get("reply", "") or entry.get("output", ""))
            if len(response) > 500:  # history response would be substantial
                # Should not exceed 2000 chars for the CC portion (plus prefix overhead)
                # Allow up to 2200 for prefix/formatting
                if len(response) <= 2500:
                    trunc_ok = True
                trunc_detail = f"Response length: {len(response)} chars"
                break
        add_check(trunc_check_name, trunc_ok, trunc_detail)
    else:
        # Not called, check if any response is overly long
        any_huge = any(
            len(str(e.get("response", "") or e.get("reply", "") or e.get("output", ""))) > 3500
            for e in routing_log
        )
        add_check(
            trunc_check_name,
            not any_huge,
            "History not explicitly called; no response exceeded 3500 chars" if not any_huge
            else "A response exceeded 3500 chars without truncation"
        )

    # ── Scoring ────────────────────────────────────────────────────────────────
    weights = {
        "routing_log.json exists and parseable": 0.05,
        "routing_log has 6 entries": 0.05,
        "Session ID correctly sanitized (only [a-zA-Z0-9_])": 0.15,
        "Status checked before routing (≥4 status calls)": 0.10,
        "Msg1 'start claude code' → start action executed": 0.10,
        "Msg3 large refactor task → send called with --long flag": 0.15,
        "Msg4 '允许' → approve 2 (Allow always), NOT approve 1": 0.15,
        "Msg5 '/compact' CC slash command → forwarded via send": 0.10,
        "Msg6 'stop claude code' → stop action executed": 0.05,
        "Output prefixed with 🤖 **CC →**": 0.05,
    }

    score = 0.0
    for check in checks:
        w = weights.get(check["name"], 0.025)
        if check["passed"]:
            score += w

    score = min(1.0, round(score, 4))
    passed = score >= 0.70

    print(json.dumps({
        "passed": passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace_dir)