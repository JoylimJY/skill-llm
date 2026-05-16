import sys
import json
import os
from pathlib import Path

def load_jsonl(path):
    entries = []
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except Exception:
        pass
    return entries

def find_result_file(workspace):
    """Find coordination_result.json anywhere in workspace."""
    candidates = list(Path(workspace).rglob("coordination_result.json"))
    if candidates:
        return candidates[0]
    return None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    
    # -----------------------------------------------------------------------
    # Load server-side call logs (ground truth from mock server)
    # -----------------------------------------------------------------------
    log_dir = Path(workspace) / "mock_server_logs"
    
    sessions_list_log = load_jsonl(log_dir / "sessions_list.jsonl")
    sessions_send_log = load_jsonl(log_dir / "sessions_send.jsonl")
    sessions_spawn_log = load_jsonl(log_dir / "sessions_spawn.jsonl")

    # -----------------------------------------------------------------------
    # CHECK 1: sessions_list was called (no hardcoded keys allowed)
    # -----------------------------------------------------------------------
    c1_passed = len(sessions_list_log) >= 1
    checks.append({
        "name": "sessions_list_called",
        "passed": c1_passed,
        "detail": f"sessions_list called {len(sessions_list_log)} time(s). Must be >= 1 to get live session keys (hardcoded keys forbidden)."
    })

    # -----------------------------------------------------------------------
    # CHECK 2: sessions_list was called BEFORE any sessions_send or sessions_spawn
    # -----------------------------------------------------------------------
    c2_passed = False
    c2_detail = "Cannot verify ordering (sessions_list or other calls missing)."
    if sessions_list_log and (sessions_send_log or sessions_spawn_log):
        list_ts = min(e["timestamp"] for e in sessions_list_log)
        other_ts_list = [e["timestamp"] for e in sessions_send_log + sessions_spawn_log]
        if other_ts_list:
            first_other_ts = min(other_ts_list)
            c2_passed = list_ts <= first_other_ts
            c2_detail = (
                f"sessions_list first call at t={list_ts:.3f}, "
                f"first send/spawn at t={first_other_ts:.3f}. "
                f"{'Correct ordering.' if c2_passed else 'VIOLATION: sessions_list must precede all sends/spawns.'}"
            )
    elif sessions_list_log and not (sessions_send_log or sessions_spawn_log):
        c2_detail = "sessions_list called but no send/spawn calls found."
    checks.append({
        "name": "sessions_list_called_before_send_spawn",
        "passed": c2_passed,
        "detail": c2_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 3: Blocking query to MarketDataAgent via sessions_send (timeout=120)
    # -----------------------------------------------------------------------
    blocking_send = None
    for entry in sessions_send_log:
        p = entry.get("payload", {})
        msg = p.get("message", "")
        timeout = p.get("timeoutSeconds", p.get("timeout", None))
        session_key = p.get("sessionKey", "")
        # Must target MarketDataAgent (check sessionKey or message content)
        targets_market = (
            "sk-live-MARKET-f8c2e1a9" in session_key or
            "MarketDataAgent" in msg or
            "market" in msg.lower() or
            "AAPL" in msg or "MSFT" in msg or "closing" in msg.lower()
        )
        if targets_market and timeout == 120:
            blocking_send = entry
            break

    c3_passed = blocking_send is not None
    c3_detail = (
        f"Found blocking sessions_send to MarketDataAgent with timeoutSeconds=120." 
        if c3_passed 
        else "No sessions_send found targeting MarketDataAgent with timeoutSeconds=120. Check: correct sessionKey from sessions_list, timeout must be exactly 120."
    )
    checks.append({
        "name": "blocking_send_to_market_data_agent",
        "passed": c3_passed,
        "detail": c3_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 4: Blocking send message follows the required template format
    # -----------------------------------------------------------------------
    c4_passed = False
    c4_detail = "No valid blocking send found to check message format."
    if blocking_send:
        msg = blocking_send.get("payload", {}).get("message", "")
        required_fields = [
            "【Agent 间通信】",
            "发件方:",
            "收件方:",
            "source sessionKey:",
            "通信目的:",
            "期望响应:",
            "timeout:",
            "用户需求:",
            "上下文摘要:",
        ]
        missing = [f for f in required_fields if f not in msg]
        c4_passed = len(missing) == 0
        c4_detail = (
            f"Message template complete. All required fields present."
            if c4_passed
            else f"Message template INCOMPLETE. Missing fields: {missing}"
        )
    checks.append({
        "name": "blocking_send_message_template_correct",
        "passed": c4_passed,
        "detail": c4_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 5: Fire-and-forget notification to AuditLoggerAgent (timeout=0)
    # -----------------------------------------------------------------------
    fire_forget_send = None
    for entry in sessions_send_log:
        p = entry.get("payload", {})
        msg = p.get("message", "")
        timeout = p.get("timeoutSeconds", p.get("timeout", None))
        session_key = p.get("sessionKey", "")
        targets_audit = (
            "sk-live-AUDIT-3d7f902b" in session_key or
            "AuditLogger" in msg or
            "audit" in msg.lower() or
            "notif" in msg.lower() or
            "log" in msg.lower()
        )
        if targets_audit and timeout == 0:
            fire_forget_send = entry
            break

    c5_passed = fire_forget_send is not None
    c5_detail = (
        "Found fire-and-forget sessions_send to AuditLoggerAgent with timeoutSeconds=0."
        if c5_passed
        else "No sessions_send found targeting AuditLoggerAgent with timeoutSeconds=0. For notifications, timeout MUST be 0 (fire-and-forget)."
    )
    checks.append({
        "name": "fire_and_forget_send_to_audit_agent",
        "passed": c5_passed,
        "detail": c5_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 6: Fire-and-forget message also uses the template format
    # -----------------------------------------------------------------------
    c6_passed = False
    c6_detail = "No valid fire-and-forget send found to check message format."
    if fire_forget_send:
        msg = fire_forget_send.get("payload", {}).get("message", "")
        required_fields = [
            "【Agent 间通信】",
            "发件方:",
            "收件方:",
            "source sessionKey:",
            "通信目的:",
            "期望响应:",
            "timeout:",
        ]
        missing = [f for f in required_fields if f not in msg]
        c6_passed = len(missing) == 0
        c6_detail = (
            "Fire-and-forget message template complete."
            if c6_passed
            else f"Fire-and-forget message template INCOMPLETE. Missing fields: {missing}"
        )
    checks.append({
        "name": "fire_and_forget_message_template_correct",
        "passed": c6_passed,
        "detail": c6_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 7: Background task delegated to ReportWriterAgent via sessions_spawn
    # -----------------------------------------------------------------------
    spawn_call = None
    for entry in sessions_spawn_log:
        p = entry.get("payload", {})
        task = p.get("task", "")
        agent_id = p.get("agentId", "")
        label = p.get("label", "")
        targets_report = (
            "rwa-live-4e1d" in agent_id or
            "ReportWriter" in task or
            "report" in task.lower() or
            "ReportWriter" in label or
            "report" in label.lower() or
            "summary" in task.lower()
        )
        if targets_report:
            spawn_call = entry
            break

    c7_passed = spawn_call is not None
    c7_detail = (
        "Found sessions_spawn targeting ReportWriterAgent for background report generation."
        if c7_passed
        else "No sessions_spawn found targeting ReportWriterAgent. Background tasks MUST use sessions_spawn (not sessions_send)."
    )
    checks.append({
        "name": "sessions_spawn_for_report_writer",
        "passed": c7_passed,
        "detail": c7_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 8: sessions_spawn includes a 'task' field with market data context
    # -----------------------------------------------------------------------
    c8_passed = False
    c8_detail = "No spawn call found to verify task field."
    if spawn_call:
        p = spawn_call.get("payload", {})
        task_content = p.get("task", "")
        has_task = len(task_content.strip()) > 20
        # The task should reference the market data retrieved (context passing)
        has_market_context = any(kw in task_content for kw in [
            "AAPL", "MSFT", "GOOGL", "market", "closing", "189", "415", "173",
            "MarketData", "market data", "financial"
        ])
        c8_passed = has_task and has_market_context
        c8_detail = (
            f"spawn 'task' field present and contains market data context."
            if c8_passed
            else f"spawn 'task' field missing or lacks market data context. task='{task_content[:120]}...'"
        )
    checks.append({
        "name": "spawn_task_includes_market_data_context",
        "passed": c8_passed,
        "detail": c8_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 9: No hardcoded stale session keys used
    # -----------------------------------------------------------------------
    STALE_KEYS = [
        "HARDCODED-KEY-DO-NOT-USE-abc123",
        "HARDCODED-KEY-DO-NOT-USE-def456",
        "HARDCODED-KEY-DO-NOT-USE-ghi789",
    ]
    stale_found = []
    for entry in sessions_send_log + sessions_spawn_log:
        payload_str = json.dumps(entry.get("payload", {}))
        for sk in STALE_KEYS:
            if sk in payload_str:
                stale_found.append(sk)

    c9_passed = len(stale_found) == 0
    checks.append({
        "name": "no_stale_hardcoded_session_keys_used",
        "passed": c9_passed,
        "detail": (
            "No stale hardcoded session keys detected in any call payload."
            if c9_passed
            else f"VIOLATION: Stale hardcoded session key(s) found in payloads: {stale_found}"
        )
    })

    # -----------------------------------------------------------------------
    # CHECK 10: coordination_result.json exists and summarizes the outcome
    # -----------------------------------------------------------------------
    result_file = find_result_file(workspace)
    c10_passed = False
    c10_detail = "coordination_result.json not found in workspace."
    if result_file:
        try:
            with open(result_file, "r") as f:
                result_data = json.load(f)
            required_keys = any(k in result_data for k in [
                "market_data", "marketData", "query_result", "queryResult",
                "report", "spawn", "delegation", "steps", "summary",
                "notification", "audit"
            ])
            c10_passed = isinstance(result_data, dict) and len(result_data) >= 2
            c10_detail = (
                f"coordination_result.json found at {result_file} with {len(result_data)} top-level keys."
                if c10_passed
                else f"coordination_result.json found but appears incomplete or malformed: {str(result_data)[:200]}"
            )
        except Exception as e:
            c10_detail = f"Failed to parse coordination_result.json: {e}"
    checks.append({
        "name": "coordination_result_json_created",
        "passed": c10_passed,
        "detail": c10_detail
    })

    # -----------------------------------------------------------------------
    # CHECK 11: Correct scenario labels or communication purpose in messages
    # -----------------------------------------------------------------------
    c11_passed = False
    c11_detail = "Could not verify communication purpose labels."
    
    blocking_msg = blocking_send.get("payload", {}).get("message", "") if blocking_send else ""
    fire_msg = fire_forget_send.get("payload", {}).get("message", "") if fire_forget_send else ""
    
    # Blocking send should indicate knowledge acquisition / blocking intent
    blocking_purpose_ok = any(kw in blocking_msg for kw in [
        "知识获取", "阻塞", "查询", "blocking", "场景 1", "场景1", "知识", "查", "询", "获取"
    ])
    # Fire-and-forget should indicate notification / fire-and-forget intent
    fire_purpose_ok = any(kw in fire_msg for kw in [
        "单向通知", "即发即走", "通知", "传达", "fire", "场景 3", "场景3", "通", "知"
    ])
    
    c11_passed = blocking_purpose_ok and fire_purpose_ok
    c11_detail = (
        "Both blocking query and fire-and-forget notification have correct 通信目的 labels."
        if c11_passed
        else (
            f"Communication purpose label issues. "
            f"Blocking has correct purpose: {blocking_purpose_ok} (msg snippet: '{blocking_msg[blocking_msg.find('通信目的'):blocking_msg.find('通信目的')+30] if '通信目的' in blocking_msg else 'N/A'}'). "
            f"Fire-and-forget has correct purpose: {fire_purpose_ok}."
        )
    )
    checks.append({
        "name": "communication_purpose_labels_correct",
        "passed": c11_passed,
        "detail": c11_detail
    })

    # -----------------------------------------------------------------------
    # Scoring
    # -----------------------------------------------------------------------
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = passed_count >= 9  # Must pass at least 9/11

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()