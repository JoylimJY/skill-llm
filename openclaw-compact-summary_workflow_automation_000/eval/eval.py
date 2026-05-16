import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    workspace_path = Path(workspace)

    # ── Locate MEMORY.md ──────────────────────────────────────────────────
    memory_file = workspace_path / "MEMORY.md"
    if not memory_file.exists():
        # Also try rglob in case agent put it elsewhere
        candidates = list(workspace_path.rglob("MEMORY.md"))
        if candidates:
            memory_file = candidates[0]

    if not memory_file.exists():
        checks.append({"name": "file_exists", "passed": False, "detail": "MEMORY.md not found anywhere in workspace"})
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {memory_file}"})

    try:
        content = memory_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": f"File size: {len(content)} chars"})

    # ── Check 1: H1 header with date ─────────────────────────────────────
    h1_pattern = re.compile(r'^#\s+2026-07-15\s+Memory Summary', re.MULTILINE)
    h1_match = bool(h1_pattern.search(content))
    checks.append({
        "name": "h1_header_with_date",
        "passed": h1_match,
        "detail": "H1 header '# 2026-07-15 Memory Summary' found" if h1_match else "Missing or malformed H1 date header"
    })

    # ── Check 2: Conversation Scope section with correct counts ──────────
    # Expected: user=3, assistant=4, tool=5 (tool includes tool_result as separate entries)
    # Let's count from the raw session:
    # Messages: user(1), assistant(2), tool(3), tool_result(4), tool(5), tool_result(6),
    #           assistant(7), user(8), tool(9), tool_result(10), assistant(11), user(12), assistant(13), tool(14), tool_result(15)
    # user=3, assistant=4, tool=3 (pure tool calls), tool_result=5... 
    # SKILL.md groups: user, assistant, tool. tool_result may count under tool or separately.
    # Looking at SKILL.md example: "user=4, assistant=5, tool=3" — tool_results are counted separately as tool.
    # Raw session has 15 messages total.
    # Roles: user=3, assistant=4, tool=3, tool_result=5  → total=15
    # SKILL.md format shows user/assistant/tool in scope. tool_result likely counted with tool.
    # So: user=3, assistant=4, tool=8 (3 tool calls + 5 tool_results) OR tool=3 only.
    # The example in SKILL.md: 12 messages, user=4, assistant=5, tool=3 (no tool_result counted separately in scope)
    # So tool_result lines are NOT counted in "tool" in Conversation Scope — only actual tool calls.
    # user=3, assistant=4, tool=3 → total=10? But total messages is 15.
    # Actually SKILL.md says "Original message count: 12 (user=4, assistant=5, tool=3)" — 4+5+3=12. 
    # So tool_result entries are either folded into tool or not shown. Let's check: 4+5+3=12. 
    # In our case: 3+4+3=10, but total is 15 (including 5 tool_results). 
    # Reasonable interpretation: tool_result messages count as "tool" role too → 3+5=8 tool messages
    # Then 3+4+8=15. OR tool_result is a separate role not in scope formula.
    # Most natural reading: the scope counts all messages = 15, broken down by role.
    # tool messages (role=tool) = 3, tool_result messages (role=tool_result) = 5.
    # Likely agent groups tool+tool_result = 8 under "tool", or keeps only tool=3.
    # We'll accept either: total=15 with user=3, assistant=4, and tool showing 3 or 8.
    # Primary check: total count = 15.

    scope_section = re.search(r'##\s+Conversation Scope(.*?)(?=\n##|\Z)', content, re.DOTALL)
    scope_passed = False
    scope_detail = "Conversation Scope section not found"
    if scope_section:
        scope_text = scope_section.group(1)
        # Check total count = 15
        total_match = re.search(r'Original message count:\s*(\d+)', scope_text)
        user_match = re.search(r'user=(\d+)', scope_text)
        assistant_match = re.search(r'assistant=(\d+)', scope_text)
        tool_match = re.search(r'tool=(\d+)', scope_text)
        date_match = re.search(r'2026-07-15', scope_text)

        total_ok = total_match and int(total_match.group(1)) == 15
        user_ok = user_match and int(user_match.group(1)) == 3
        assistant_ok = assistant_match and int(assistant_match.group(1)) == 4
        # tool can be 3 (just tool calls) or 8 (tool+tool_result)
        tool_ok = tool_match and int(tool_match.group(1)) in (3, 5, 8)
        date_ok = bool(date_match)

        scope_passed = total_ok and user_ok and assistant_ok and tool_ok and date_ok
        scope_detail = (
            f"total={total_match.group(1) if total_match else 'missing'}, "
            f"user={user_match.group(1) if user_match else 'missing'}, "
            f"assistant={assistant_match.group(1) if assistant_match else 'missing'}, "
            f"tool={tool_match.group(1) if tool_match else 'missing'}, "
            f"date_in_scope={date_ok}"
        )

    checks.append({"name": "conversation_scope_counts", "passed": scope_passed, "detail": scope_detail})

    # ── Check 3: Tools Used section ───────────────────────────────────────
    tools_section = re.search(r'##\s+Tools Used(.*?)(?=\n##|\Z)', content, re.DOTALL)
    tools_passed = False
    tools_detail = "Tools Used section not found"
    if tools_section:
        tools_text = tools_section.group(1)
        has_exec = bool(re.search(r'exec', tools_text, re.IGNORECASE))
        has_read_file = bool(re.search(r'read_file', tools_text, re.IGNORECASE))
        has_grep = bool(re.search(r'grep_search', tools_text, re.IGNORECASE))
        tools_passed = has_exec and has_read_file and has_grep
        tools_detail = f"exec={has_exec}, read_file={has_read_file}, grep_search={has_grep}"
    checks.append({"name": "tools_used_all_three", "passed": tools_passed, "detail": tools_detail})

    # ── Check 4: User Requests section ───────────────────────────────────
    requests_section = re.search(r'##\s+User Requests(.*?)(?=\n##|\Z)', content, re.DOTALL)
    requests_passed = False
    requests_detail = "User Requests section not found"
    if requests_section:
        req_text = requests_section.group(1)
        # Should mention: memory flush / bottlenecks, tools library, todo/P0
        has_flush = bool(re.search(r'flush|bottleneck|pipeline|memory', req_text, re.IGNORECASE))
        has_tools = bool(re.search(r'tool|library|lib', req_text, re.IGNORECASE))
        has_todo = bool(re.search(r'todo|p0|fix|draft', req_text, re.IGNORECASE))
        requests_passed = has_flush and has_tools and has_todo
        requests_detail = f"flush/pipeline={has_flush}, tools_check={has_tools}, todo/p0={has_todo}"
    checks.append({"name": "user_requests_content", "passed": requests_passed, "detail": requests_detail})

    # ── Check 5: Todo Items with checkbox syntax ──────────────────────────
    todo_section = re.search(r'##\s+Todo Items(.*?)(?=\n##|\Z)', content, re.DOTALL)
    todo_passed = False
    todo_detail = "Todo Items section not found"
    if todo_section:
        todo_text = todo_section.group(1)
        # Must use "- [ ]" checkbox syntax (not just "- ")
        checkbox_items = re.findall(r'- \[ \]', todo_text)
        has_async_guard = bool(re.search(r'async|flush guard|exec', todo_text, re.IGNORECASE))
        has_serialization = bool(re.search(r'serial|compact|overhead', todo_text, re.IGNORECASE))
        has_tests = bool(re.search(r'test|regression', todo_text, re.IGNORECASE))
        todo_passed = len(checkbox_items) >= 2 and (has_async_guard or has_serialization or has_tests)
        todo_detail = (
            f"checkbox_count={len(checkbox_items)}, "
            f"async_guard={has_async_guard}, serial={has_serialization}, tests={has_tests}"
        )
    checks.append({"name": "todo_items_checkbox_syntax", "passed": todo_passed, "detail": todo_detail})

    # ── Check 6: Key Files with $WORKSPACE prefix ─────────────────────────
    files_section = re.search(r'##\s+Key Files(.*?)(?=\n##|\Z)', content, re.DOTALL)
    files_passed = False
    files_detail = "Key Files section not found"
    if files_section:
        files_text = files_section.group(1)
        workspace_refs = re.findall(r'\$WORKSPACE/', files_text)
        has_compact = bool(re.search(r'compact\.rs', files_text))
        has_lib = bool(re.search(r'lib\.rs', files_text))
        has_settings = bool(re.search(r'settings\.toml', files_text))
        files_passed = len(workspace_refs) >= 2 and (has_compact or has_lib or has_settings)
        files_detail = (
            f"$WORKSPACE_refs={len(workspace_refs)}, "
            f"compact.rs={has_compact}, lib.rs={has_lib}, settings.toml={has_settings}"
        )
    checks.append({"name": "key_files_workspace_prefix", "passed": files_passed, "detail": files_detail})

    # ── Check 7: Current Work section ────────────────────────────────────
    current_section = re.search(r'##\s+Current Work(.*?)(?=\n##|\Z)', content, re.DOTALL)
    current_passed = False
    current_detail = "Current Work section not found"
    if current_section:
        current_text = current_section.group(1).strip()
        has_content = len(current_text) > 10
        has_p0_or_async = bool(re.search(r'async|flush guard|P0|exec|implement', current_text, re.IGNORECASE))
        current_passed = has_content and has_p0_or_async
        current_detail = f"has_content={has_content}, relevant_keywords={has_p0_or_async}, text_preview={current_text[:80]!r}"
    checks.append({"name": "current_work_content", "passed": current_passed, "detail": current_detail})

    # ── Check 8: Timeline section with role: content format ───────────────
    timeline_section = re.search(r'##\s+Timeline(.*?)(?=\n##|\Z)', content, re.DOTALL)
    timeline_passed = False
    timeline_detail = "Timeline section not found"
    if timeline_section:
        tl_text = timeline_section.group(1)
        # Must have entries like "- user: ...", "- assistant: ...", "- tool: ...", "- tool_result: ..."
        user_entries = re.findall(r'-\s+user:', tl_text)
        assistant_entries = re.findall(r'-\s+assistant:', tl_text)
        tool_entries = re.findall(r'-\s+tool:', tl_text)
        tool_result_entries = re.findall(r'-\s+tool_result:', tl_text)
        timeline_passed = (
            len(user_entries) >= 2 and
            len(assistant_entries) >= 2 and
            len(tool_entries) >= 2
        )
        timeline_detail = (
            f"user_entries={len(user_entries)}, assistant_entries={len(assistant_entries)}, "
            f"tool_entries={len(tool_entries)}, tool_result_entries={len(tool_result_entries)}"
        )
    checks.append({"name": "timeline_role_format", "passed": timeline_passed, "detail": timeline_detail})

    # ── Check 9: Resume Instruction section ──────────────────────────────
    resume_section = re.search(r'##\s+Resume Instruction(.*?)(?=\n##|\Z)', content, re.DOTALL)
    resume_passed = False
    resume_detail = "Resume Instruction section not found"
    if resume_section:
        resume_text = resume_section.group(1)
        has_no_acknowledge = bool(re.search(r'do not acknowledge', resume_text, re.IGNORECASE))
        has_no_recap = bool(re.search(r'do not recap|not recap', resume_text, re.IGNORECASE))
        has_no_preface = bool(re.search(r'do not preface|not preface', resume_text, re.IGNORECASE))
        has_continue_directly = bool(re.search(r'continue directly|continue', resume_text, re.IGNORECASE))
        resume_passed = has_no_acknowledge and has_no_recap and has_no_preface and has_continue_directly
        resume_detail = (
            f"no_acknowledge={has_no_acknowledge}, no_recap={has_no_recap}, "
            f"no_preface={has_no_preface}, continue_directly={has_continue_directly}"
        )
    checks.append({"name": "resume_instruction_verbatim", "passed": resume_passed, "detail": resume_detail})

    # ── Check 10: All required sections present ───────────────────────────
    required_sections = [
        "Conversation Scope", "Tools Used", "User Requests",
        "Todo Items", "Key Files", "Current Work", "Timeline", "Resume Instruction"
    ]
    missing_sections = []
    for sec in required_sections:
        if not re.search(r'##\s+' + re.escape(sec), content):
            missing_sections.append(sec)
    all_sections_present = len(missing_sections) == 0
    checks.append({
        "name": "all_required_sections_present",
        "passed": all_sections_present,
        "detail": f"Missing sections: {missing_sections}" if missing_sections else "All 8 sections present"
    })

    # ── Final scoring ─────────────────────────────────────────────────────
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)

    # Must pass at minimum: file_exists, scope, todos (checkbox), key_files ($WORKSPACE), resume_instruction
    critical = ["file_exists", "conversation_scope_counts", "todo_items_checkbox_syntax",
                "key_files_workspace_prefix", "resume_instruction_verbatim", "all_required_sections_present"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))