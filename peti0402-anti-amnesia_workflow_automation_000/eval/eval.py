import sys
import json
import os
from pathlib import Path
from datetime import datetime

def run_eval(workspace: str):
    workspace = Path(workspace)
    home = Path.home()
    today = datetime.now().strftime("%Y-%m-%d")
    checks = []
    
    def check(name, condition, detail):
        checks.append({"name": name, "passed": bool(condition), "detail": detail})
        return bool(condition)

    # ── CHECK 1: ~/.openclaw/openclaw.json has correct hooks structure ──
    openclaw_path = home / ".openclaw" / "openclaw.json"
    hook_ok = False
    hook_detail = ""
    try:
        with open(openclaw_path) as f:
            cfg = json.load(f)
        hooks = cfg.get("hooks", {})
        sm = hooks.get("session-memory", {})
        enabled = sm.get("enabled") is True
        messages_val = sm.get("messages")
        messages_ok = messages_val == 9999
        path_ok = sm.get("path") == "memory/"
        hook_ok = enabled and messages_ok and path_ok
        hook_detail = (
            f"enabled={sm.get('enabled')}, messages={messages_val} (expected 9999), "
            f"path='{sm.get('path')}' (expected 'memory/')"
        )
    except FileNotFoundError:
        hook_detail = f"File not found: {openclaw_path}"
    except json.JSONDecodeError as e:
        hook_detail = f"JSON parse error: {e}"
    except Exception as e:
        hook_detail = f"Unexpected error: {e}"
    check("openclaw.json has correct session-memory hook", hook_ok, hook_detail)

    # ── CHECK 2: hook key is 'session-memory' (hyphenated, not underscore) ──
    key_ok = False
    key_detail = ""
    try:
        with open(openclaw_path) as f:
            cfg = json.load(f)
        hooks = cfg.get("hooks", {})
        has_hyphen = "session-memory" in hooks
        has_underscore = "session_memory" in hooks
        key_ok = has_hyphen and not has_underscore
        key_detail = f"'session-memory' present: {has_hyphen}, 'session_memory' (wrong) present: {has_underscore}"
    except Exception as e:
        key_detail = f"Error reading config: {e}"
    check("Hook key is 'session-memory' (hyphenated)", key_ok, key_detail)

    # ── CHECK 3: STATE.md exists in workspace root ──
    state_path = workspace / "STATE.md"
    state_exists = state_path.exists()
    state_detail = f"File exists: {state_exists}"
    check("STATE.md exists in workspace root", state_exists, state_detail)

    # ── CHECK 4: STATE.md has required sections (copied from template, not empty) ──
    state_content_ok = False
    state_content_detail = ""
    try:
        content = state_path.read_text()
        has_active = "Active Projects" in content
        has_decisions = "Iron Decisions" in content
        has_issues = "Open Issues" in content
        has_cron = "Cron Health" in content or "consecutiveErrors" in content
        state_content_ok = has_active and has_decisions and has_issues and has_cron
        state_content_detail = (
            f"Active Projects: {has_active}, Iron Decisions: {has_decisions}, "
            f"Open Issues: {has_issues}, Cron Health section: {has_cron}"
        )
    except Exception as e:
        state_content_detail = f"Error reading STATE.md: {e}"
    check("STATE.md contains required sections from template", state_content_ok, state_content_detail)

    # ── CHECK 5: HEARTBEAT.md exists in workspace root ──
    hb_path = workspace / "HEARTBEAT.md"
    hb_exists = hb_path.exists()
    hb_detail = f"File exists: {hb_exists}"
    check("HEARTBEAT.md exists in workspace root", hb_exists, hb_detail)

    # ── CHECK 6: HEARTBEAT.md has wake-up checklist content ──
    hb_content_ok = False
    hb_content_detail = ""
    try:
        content = hb_path.read_text()
        has_read_state = "STATE.md" in content
        has_cron_check = "consecutiveErrors" in content
        has_process_check = "critical processes" in content.lower() or "Critical Processes" in content
        has_memory_write = "memory/" in content or "today.md" in content
        hb_content_ok = has_read_state and has_cron_check and (has_process_check or has_memory_write)
        hb_content_detail = (
            f"References STATE.md: {has_read_state}, consecutiveErrors check: {has_cron_check}, "
            f"process check: {has_process_check}, memory write: {has_memory_write}"
        )
    except Exception as e:
        hb_content_detail = f"Error reading HEARTBEAT.md: {e}"
    check("HEARTBEAT.md contains wake-up protocol content", hb_content_ok, hb_content_detail)

    # ── CHECK 7: memory/ directory exists ──
    memory_dir = workspace / "memory"
    memory_exists = memory_dir.is_dir()
    check("memory/ directory exists", memory_exists, f"Directory exists: {memory_exists}")

    # ── CHECK 8: Today's daily journal exists: memory/YYYY-MM-DD.md ──
    journal_path = memory_dir / f"{today}.md"
    journal_exists = journal_path.exists()
    journal_detail = f"Expected: {journal_path}, exists: {journal_exists}"
    check(f"Today's journal exists at memory/{today}.md", journal_exists, journal_detail)

    # ── CHECK 9: Today's journal has meaningful content (not empty) ──
    journal_content_ok = False
    journal_content_detail = ""
    try:
        content = journal_path.read_text().strip()
        # Must have at least a header and some content — more than 10 chars
        journal_content_ok = len(content) > 10 and (
            "#" in content or today in content or "session" in content.lower()
        )
        journal_content_detail = f"Content length: {len(content)}, has header or date reference: {journal_content_ok}"
    except Exception as e:
        journal_content_detail = f"Error reading journal: {e}"
    check("Today's journal has meaningful content", journal_content_ok, journal_content_detail)

    # ── CHECK 10: AGENTS.md contains the mandatory session start protocol ──
    agents_path = workspace / "AGENTS.md"
    agents_protocol_ok = False
    agents_detail = ""
    try:
        content = agents_path.read_text()
        # Must contain references to reading STATE.md, today's journal (memory/), and MEMORY.md
        has_state_read = "STATE.md" in content
        has_memory_read = "MEMORY.md" in content
        has_journal_ref = "memory/" in content or "YYYY-MM-DD" in content or "today" in content.lower()
        # Must be a numbered/structured protocol — look for "Every Session" or similar
        has_protocol_header = (
            "Every Session" in content
            or "session start" in content.lower()
            or "Mandatory" in content
            or "Session Start" in content
        )
        agents_protocol_ok = has_state_read and has_memory_read and has_journal_ref and has_protocol_header
        agents_detail = (
            f"Reads STATE.md: {has_state_read}, Reads MEMORY.md: {has_memory_read}, "
            f"References journal/memory dir: {has_journal_ref}, Has protocol header: {has_protocol_header}"
        )
    except Exception as e:
        agents_detail = f"Error reading AGENTS.md: {e}"
    check("AGENTS.md contains mandatory session start protocol (all 3 steps)", agents_protocol_ok, agents_detail)

    # ── CHECK 11: MEMORY.md exists ──
    memory_md_path = workspace / "MEMORY.md"
    memory_md_exists = memory_md_path.exists()
    check("MEMORY.md exists in workspace root", memory_md_exists, f"File exists: {memory_md_exists}")

    # ── CHECK 12: MEMORY.md has at least one decision or long-term memory entry ──
    memory_md_content_ok = False
    memory_md_detail = ""
    try:
        content = memory_md_path.read_text().strip()
        has_decision = (
            "Decision" in content or "decision" in content
            or "decided" in content.lower()
            or "##" in content
        )
        has_content = len(content) > 20
        memory_md_content_ok = has_content and has_decision
        memory_md_detail = f"Content length: {len(content)}, has decision/entry: {has_decision}"
    except Exception as e:
        memory_md_detail = f"Error reading MEMORY.md: {e}"
    check("MEMORY.md has meaningful long-term memory content", memory_md_content_ok, memory_md_detail)

    # ── CHECK 13: messages value is EXACTLY 9999 (not 9998, 10000, 100, etc.) ──
    messages_exact_ok = False
    messages_exact_detail = ""
    try:
        with open(openclaw_path) as f:
            cfg = json.load(f)
        val = cfg.get("hooks", {}).get("session-memory", {}).get("messages")
        messages_exact_ok = val == 9999
        messages_exact_detail = f"messages = {val!r} (must be integer 9999 exactly)"
    except Exception as e:
        messages_exact_detail = f"Error: {e}"
    check("session-memory messages is exactly 9999", messages_exact_ok, messages_exact_detail)

    # ── Compute final score ──
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    overall_passed = passed_count == total

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument check", "passed": False, "detail": "No workspace path provided"}
        ]}))
        sys.exit(1)
    run_eval(sys.argv[1])