import sys
import json
import os
import re
import subprocess
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
    
    # Find the output file
    output_file = None
    for candidate in ["session_output.json", "dispatch_results.json", "output.json", "results.json"]:
        p = Path(workspace) / candidate
        if p.exists():
            output_file = p
            break
    
    if output_file is None:
        # Try recursive search
        found = list(Path(workspace).rglob("session_output.json"))
        if not found:
            found = list(Path(workspace).rglob("dispatch_results.json"))
        if found:
            output_file = found[0]
    
    if output_file is None:
        add_check("output_file_exists", False, "No session_output.json or dispatch_results.json found in workspace")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("output_file_exists", True, f"Found output file: {output_file}")
    
    try:
        with open(output_file) as f:
            results = json.load(f)
    except Exception as e:
        add_check("output_file_parseable", False, f"Could not parse JSON: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("output_file_parseable", True, "Output JSON is valid")
    
    # Normalize: results can be a list or dict with a 'results' key
    if isinstance(results, dict) and "results" in results:
        results = results["results"]
    
    if not isinstance(results, list):
        add_check("output_is_list", False, f"Expected list of results, got {type(results)}")
        return {"passed": False, "score": 0.0, "checks": checks}
    
    add_check("output_is_list", True, f"Output contains {len(results)} entries")
    
    # Helper to find result by id or index
    def get_result(id_val):
        for r in results:
            if isinstance(r, dict):
                if r.get("id") == id_val or r.get("step") == id_val:
                    return r
        # fallback: by index
        idx = id_val - 1
        if 0 <= idx < len(results):
            return results[idx]
        return None
    
    def get_text(r):
        """Extract response text from a result entry"""
        if not r:
            return ""
        for key in ["response", "output", "text", "reply", "result", "message"]:
            if key in r:
                return str(r[key])
        return str(r)
    
    def get_command(r):
        """Extract shell command from a result entry"""
        if not r:
            return ""
        for key in ["command", "shell_command", "cmd", "script_call", "invocation"]:
            if key in r:
                return str(r[key])
        return ""
    
    # ================================================================
    # CHECK 1: Step 1 - /cc (no args) triggers SETUP_NEEDED flow
    # Must call scripts/cc.sh projects, detect exit 100, ask about project root
    # ================================================================
    r1 = get_result(1)
    text1 = get_text(r1).lower()
    cmd1 = get_command(r1).lower()
    
    setup_needed_detected = (
        "setup" in text1 or 
        "project" in text1 and ("root" in text1 or "where" in text1 or "path" in text1 or "director" in text1) or
        "setup_needed" in text1
    )
    projects_called = "projects" in cmd1 or (r1 and "projects" in str(r1).lower() and "cc.sh" in str(r1).lower())
    
    add_check(
        "step1_setup_needed_detection",
        setup_needed_detected,
        f"Step 1 (/cc): Should detect SETUP_NEEDED and ask for project root. Got response snippet: '{text1[:200]}'"
    )
    
    # ================================================================
    # CHECK 2: Step 2 - User provides ~/projects path → config root called
    # Must call: scripts/cc.sh config root ~/projects
    # ================================================================
    r2 = get_result(2)
    cmd2 = get_command(r2).lower()
    text2 = get_text(r2).lower()
    
    config_root_called = (
        ("config" in cmd2 and "root" in cmd2) or
        ("config" in text2 and "root" in text2 and "project" in text2)
    )
    path_in_cmd = "~/projects" in get_command(r2) or "~/projects" in get_text(r2)
    
    add_check(
        "step2_config_root_called",
        config_root_called and path_in_cmd,
        f"Step 2 (user gives path): Must call 'scripts/cc.sh config root ~/projects'. cmd='{cmd2[:150]}' text='{text2[:150]}'"
    )
    
    # ================================================================
    # CHECK 3: Step 3 - /cc on webapp → correct start message
    # ================================================================
    r3 = get_result(3)
    text3 = get_text(r3)
    cmd3 = get_command(r3).lower()
    
    on_called = "on" in cmd3 and "webapp" in cmd3
    success_reported = (
        "✅" in text3 or 
        "started" in text3.lower() or 
        "claude code session" in text3.lower()
    )
    relay_announced = (
        "relay" in text3.lower() or 
        "/cc off" in text3 or 
        "forwarded" in text3.lower() or
        "directly" in text3.lower()
    )
    
    add_check(
        "step3_session_started_message",
        on_called and success_reported,
        f"Step 3 (/cc on webapp): Must call cc.sh on webapp and report success. cmd='{cmd3[:100]}' resp='{text3[:150]}'"
    )
    add_check(
        "step3_relay_mode_announced",
        relay_announced,
        f"Step 3: Must announce relay mode to user (mention /cc off or forwarding). resp='{text3[:150]}'"
    )
    
    # ================================================================
    # CHECK 4: Step 4 - User message in relay mode → forwarded to Claude Code
    # Must call: scripts/cc.sh webapp "<message>"
    # Must show ⏳ immediate acknowledgment
    # ================================================================
    r4 = get_result(4)
    text4 = get_text(r4)
    cmd4 = get_command(r4)
    
    message_forwarded = (
        "webapp" in cmd4.lower() and 
        ("refactor" in cmd4.lower() or "authentication" in cmd4.lower() or "jwt" in cmd4.lower())
    ) or (
        "webapp" in str(r4).lower() and 
        ("refactor" in str(r4).lower() or "authentication" in str(r4).lower())
    )
    
    instant_ack = "⏳" in text4 or "⏳" in str(r4)
    
    add_check(
        "step4_message_forwarded",
        message_forwarded,
        f"Step 4 (relay msg): Must call cc.sh webapp with the user's message. cmd='{cmd4[:150]}'"
    )
    add_check(
        "step4_instant_acknowledgment",
        instant_ack,
        f"Step 4: Must immediately reply with ⏳ before forwarding. Got: '{text4[:100]}'"
    )
    
    # ================================================================
    # CHECK 5: Step 5 - /cc ? in relay mode → NOT forwarded, calls check
    # CRITICAL: Must call 'scripts/cc.sh check webapp' (NOT 'status webapp')
    # ================================================================
    r5 = get_result(5)
    cmd5 = get_command(r5).lower()
    text5 = get_text(r5)
    all5 = str(r5).lower()
    
    check_called_not_status = (
        ("check" in cmd5 and "webapp" in cmd5) or
        ("check" in all5 and "webapp" in all5 and "cc.sh" in all5)
    )
    status_misused = (
        "status" in cmd5 and "webapp" in cmd5 and "check" not in cmd5
    )
    
    # Status for webapp is RUNNING → should show 🟢
    running_status = "🟢" in text5 or "running" in text5.lower()
    
    add_check(
        "step5_uses_check_not_status",
        check_called_not_status and not status_misused,
        f"Step 5 (/cc ?): CRITICAL - must call 'cc.sh check webapp', NOT 'cc.sh status'. cmd='{cmd5[:150]}'"
    )
    add_check(
        "step5_running_emoji",
        running_status,
        f"Step 5: webapp is RUNNING → must show 🟢 emoji. Got: '{text5[:150]}'"
    )
    
    # ================================================================
    # CHECK 6: Step 6 - /cc tail webapp → NOT forwarded, calls tail
    # Output is >4000 chars → must use summary format with "Full output: send /cc tail"
    # ================================================================
    r6 = get_result(6)
    text6 = get_text(r6)
    cmd6 = get_command(r6).lower()
    all6 = str(r6).lower()
    
    tail_called = (
        ("tail" in cmd6 and "webapp" in cmd6) or
        ("tail" in all6 and "webapp" in all6 and "cc.sh" in all6)
    )
    
    # Large output → summary format required (NOT the full output in a code block)
    # Must contain the "Full output: send /cc tail" indicator
    has_tail_hint = (
        "/cc tail" in text6 or 
        "full output" in text6.lower() or
        "send /cc tail" in text6.lower() or
        "tail" in text6.lower() and "more" in text6.lower()
    )
    
    # Must NOT be a single massive code block of the full output (4000+ chars)
    is_summarized = len(text6) < 4000 or has_tail_hint
    
    add_check(
        "step6_tail_not_forwarded",
        tail_called,
        f"Step 6 (/cc tail): Must call cc.sh tail, not forward to Claude. cmd='{cmd6[:100]}'"
    )
    add_check(
        "step6_large_output_summarized",
        has_tail_hint and is_summarized,
        f"Step 6: Output >4000 chars must be summarized with '/cc tail' hint. has_hint={has_tail_hint}, len={len(text6)}"
    )
    
    # ================================================================
    # CHECK 7: Step 7 - Another relay message → forwarded (⏳ + forward)
    # ================================================================
    r7 = get_result(7)
    text7 = get_text(r7)
    cmd7 = get_command(r7)
    
    msg7_forwarded = (
        "webapp" in cmd7.lower() and 
        ("test" in cmd7.lower() or "unit" in cmd7.lower() or "auth" in cmd7.lower())
    ) or (
        "webapp" in str(r7).lower() and "cc.sh" in str(r7).lower()
    )
    ack7 = "⏳" in text7 or "⏳" in str(r7)
    
    add_check(
        "step7_second_relay_message_forwarded",
        msg7_forwarded,
        f"Step 7 (relay msg): Must forward to cc.sh webapp. cmd='{cmd7[:100]}'"
    )
    add_check(
        "step7_acknowledgment",
        ack7,
        f"Step 7: Must show ⏳ acknowledgment. Got: '{text7[:80]}'"
    )
    
    # ================================================================
    # CHECK 8: Step 8 - /cc off → ends relay mode, correct message
    # ================================================================
    r8 = get_result(8)
    text8 = get_text(r8)
    cmd8 = get_command(r8).lower()
    
    off_called = (
        ("off" in cmd8 and "webapp" in cmd8) or
        ("off" in str(r8).lower() and "webapp" in str(r8).lower() and "cc.sh" in str(r8).lower())
    )
    session_ended_msg = (
        "session ended" in text8.lower() or
        "ended" in text8.lower() or
        "normal chat" in text8.lower() or
        "back to" in text8.lower()
    )
    
    add_check(
        "step8_off_command_processed",
        off_called,
        f"Step 8 (/cc off): Must call cc.sh off webapp. cmd='{cmd8[:100]}'"
    )
    add_check(
        "step8_relay_ended_message",
        session_ended_msg,
        f"Step 8: Must report session ended / back to normal. Got: '{text8[:150]}'"
    )
    
    # ================================================================
    # CHECK 9: Step 9 - /cc status (not in relay) → call cc.sh status
    # ================================================================
    r9 = get_result(9)
    cmd9 = get_command(r9).lower()
    
    status_called = (
        "status" in cmd9 and "cc.sh" in cmd9
    ) or (
        "status" in str(r9).lower() and "cc.sh" in str(r9).lower()
    )
    
    add_check(
        "step9_status_command",
        status_called,
        f"Step 9 (/cc status): Must call cc.sh status. cmd='{cmd9[:100]}'"
    )
    
    # ================================================================
    # CHECK 10: Step 10 - /cc on api-service → start session
    # ================================================================
    r10 = get_result(10)
    cmd10 = get_command(r10).lower()
    text10 = get_text(r10)
    
    on_api_called = (
        "on" in cmd10 and "api-service" in cmd10
    ) or (
        "api-service" in str(r10).lower() and ("on" in str(r10).lower() or "start" in str(r10).lower())
    )
    
    add_check(
        "step10_on_api_service",
        on_api_called,
        f"Step 10 (/cc on api-service): Must call cc.sh on api-service. cmd='{cmd10[:100]}'"
    )
    
    # ================================================================
    # CHECK 11: Step 11 - /cc ? for api-service → check, status is PROCESSING
    # Must show 🔄 emoji
    # ================================================================
    r11 = get_result(11)
    cmd11 = get_command(r11).lower()
    text11 = get_text(r11)
    all11 = str(r11)
    
    check11_called = (
        "check" in cmd11 and "api-service" in cmd11
    ) or (
        "check" in all11.lower() and "api-service" in all11.lower()
    )
    
    processing_emoji = "🔄" in text11 or "🔄" in all11 or "processing" in text11.lower()
    
    add_check(
        "step11_check_api_service",
        check11_called,
        f"Step 11 (/cc ? for api-service): Must call cc.sh check api-service. cmd='{cmd11[:100]}'"
    )
    add_check(
        "step11_processing_emoji",
        processing_emoji,
        f"Step 11: api-service is PROCESSING → must show 🔄. Got: '{text11[:100]}'"
    )
    
    # ================================================================
    # CHECK 12: Step 12 - /cc projects in relay mode → NOT forwarded, lists projects
    # ================================================================
    r12 = get_result(12)
    cmd12 = get_command(r12).lower()
    text12 = get_text(r12)
    
    projects_not_forwarded = (
        "projects" in cmd12 and "api-service" not in cmd12.replace("api-service", "")
    ) or (
        "projects" in str(r12).lower() and ("webapp" in str(r12).lower() or "ml-pipeline" in str(r12).lower())
    )
    
    # Should NOT contain the user's message text (it should NOT have been forwarded)
    not_sent_as_relay = "/cc projects" not in cmd12
    
    add_check(
        "step12_projects_not_forwarded",
        projects_not_forwarded,
        f"Step 12 (/cc projects in relay): Must call cc.sh projects, not forward message. cmd='{cmd12[:100]}'"
    )
    
    # ================================================================
    # SCORING
    # ================================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)
    overall_passed = score >= 0.75  # Must pass 75% of checks
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))