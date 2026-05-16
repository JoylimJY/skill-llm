import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 8.0

    # ---- FIND TARGET FILES ----
    # 1. The three-step formatted response file
    response_files = list(workspace.rglob("INC-2024-0887_response.md")) + \
                     list(workspace.rglob("incident_response.md")) + \
                     list(workspace.rglob("response.md"))
    
    # Also accept .txt variants
    if not response_files:
        response_files = list(workspace.rglob("INC-2024-0887_response.txt")) + \
                         list(workspace.rglob("incident_response.txt"))

    # 2. The memory palace extraction file
    memory_files = list(workspace.rglob("memory_palace.md")) + \
                   list(workspace.rglob("memory_palace.txt")) + \
                   list(workspace.rglob("memory_palace.json")) + \
                   list(workspace.rglob("memory_extraction.md")) + \
                   list(workspace.rglob("memory_extraction.txt")) + \
                   list(workspace.rglob("memory_extraction.json"))

    # ---- CHECK 1: Response file exists ----
    if not response_files:
        checks.append(check("response_file_exists", False, "No response file found (expected INC-2024-0887_response.md or similar)"))
    else:
        checks.append(check("response_file_exists", True, f"Found: {response_files[0]}"))
    
    response_content = ""
    if response_files:
        try:
            response_content = response_files[0].read_text(encoding="utf-8")
        except Exception as e:
            checks.append(check("response_file_readable", False, f"Could not read response file: {e}"))
            response_content = ""

    # ---- CHECK 2: 思考 section present ----
    has_thinking = bool(re.search(r'[思]考|Thinking|1\.\s*思考', response_content, re.IGNORECASE))
    checks.append(check("section_thinking_present", has_thinking,
        "Section '思考' (Thinking) found" if has_thinking else "Missing '思考' section"))
    if has_thinking:
        total_score += 0.75

    # ---- CHECK 3: 思考 section has required sub-elements ----
    thinking_has_goal = bool(re.search(r'目标|goal|achieve|what.*trying', response_content, re.IGNORECASE))
    thinking_has_options = bool(re.search(r'方案|option|alternative|可选', response_content, re.IGNORECASE))
    thinking_has_rationale = bool(re.search(r'选择|rationale|why|reason|因为', response_content, re.IGNORECASE))
    thinking_complete = thinking_has_goal and thinking_has_options and thinking_has_rationale
    checks.append(check("thinking_section_complete",
        thinking_complete,
        f"Goal:{thinking_has_goal} Options:{thinking_has_options} Rationale:{thinking_has_rationale}"))
    if thinking_complete:
        total_score += 0.75

    # ---- CHECK 4: 执行 section present ----
    has_execution = bool(re.search(r'执行|Execution|2\.\s*执行', response_content, re.IGNORECASE))
    checks.append(check("section_execution_present", has_execution,
        "Section '执行' (Execution) found" if has_execution else "Missing '执行' section"))
    if has_execution:
        total_score += 0.75

    # ---- CHECK 5: 执行 section has command + result sub-elements ----
    exec_has_command = bool(re.search(r'命令|command|cmd|步骤|step', response_content, re.IGNORECASE))
    exec_has_result = bool(re.search(r'结果|result|output|执行结果|产出', response_content, re.IGNORECASE))
    execution_complete = exec_has_command and exec_has_result
    checks.append(check("execution_section_complete",
        execution_complete,
        f"Command:{exec_has_command} Result:{exec_has_result}"))
    if execution_complete:
        total_score += 0.75

    # ---- CHECK 6: 复盘 section present ----
    has_reflection = bool(re.search(r'复盘|Reflection|3\.\s*复盘', response_content, re.IGNORECASE))
    checks.append(check("section_reflection_present", has_reflection,
        "Section '复盘' (Reflection) found" if has_reflection else "Missing '复盘' section"))
    if has_reflection:
        total_score += 0.75

    # ---- CHECK 7: 复盘 section has required sub-elements ----
    reflect_has_highlight = bool(re.search(r'亮点|went well|worked|好的', response_content, re.IGNORECASE))
    reflect_has_improve = bool(re.search(r'优化|improve|better|改进', response_content, re.IGNORECASE))
    reflect_has_learned = bool(re.search(r'学到|learned|insight|new.*know|收获', response_content, re.IGNORECASE))
    reflection_complete = reflect_has_highlight and reflect_has_improve and reflect_has_learned
    checks.append(check("reflection_section_complete",
        reflection_complete,
        f"Highlight:{reflect_has_highlight} Improve:{reflect_has_improve} Learned:{reflect_has_learned}"))
    if reflection_complete:
        total_score += 0.75

    # ---- CHECK 8: Self-check checklist present ----
    has_selfcheck = bool(re.search(r'自检|self.?check|checklist|思考.*✅|执行.*✅|复盘.*✅', response_content, re.IGNORECASE | re.DOTALL))
    # Also accept explicit listing of all three sections as confirmed
    has_all_confirmed = (
        bool(re.search(r'思考.*[✅✓√]', response_content)) and
        bool(re.search(r'执行.*[✅✓√]', response_content)) and
        bool(re.search(r'复盘.*[✅✓√]', response_content))
    )
    selfcheck_passed = has_selfcheck or has_all_confirmed
    checks.append(check("self_check_checklist_present", selfcheck_passed,
        "Self-check checklist present" if selfcheck_passed else "Missing self-check checklist (should show all 3 modules verified)"))
    if selfcheck_passed:
        total_score += 0.5

    # ---- CHECK 9: Correct section ORDER (思考 → 执行 → 复盘) ----
    order_correct = False
    if has_thinking and has_execution and has_reflection:
        pos_thinking = re.search(r'[思]考|Thinking', response_content, re.IGNORECASE)
        pos_execution = re.search(r'[执]行|Execution', response_content, re.IGNORECASE)
        pos_reflection = re.search(r'[复]盘|Reflection', response_content, re.IGNORECASE)
        if pos_thinking and pos_execution and pos_reflection:
            order_correct = (pos_thinking.start() < pos_execution.start() < pos_reflection.start())
    checks.append(check("section_order_correct", order_correct,
        "Sections in correct order: 思考 → 执行 → 复盘" if order_correct else "Sections not in correct order"))
    if order_correct:
        total_score += 0.5

    # ---- CHECK 10: Memory palace file exists ----
    if not memory_files:
        checks.append(check("memory_palace_file_exists", False,
            "No memory palace extraction file found (expected memory_palace.md or memory_extraction.md)"))
    else:
        checks.append(check("memory_palace_file_exists", True, f"Found: {memory_files[0]}"))

    memory_content = ""
    if memory_files:
        try:
            memory_content = memory_files[0].read_text(encoding="utf-8")
        except Exception as e:
            checks.append(check("memory_palace_file_readable", False, f"Could not read memory file: {e}"))
            memory_content = ""

    # ---- CHECK 11: Memory palace has 热/原则 section with decision rationale ----
    has_hot_principle = bool(re.search(r'热/原则|热.*原则|hot.*principle|principles?\s*section|原则', memory_content, re.IGNORECASE))
    checks.append(check("memory_palace_hot_principle", has_hot_principle,
        "热/原则 (principles) section present" if has_hot_principle else "Missing 热/原则 section in memory palace"))
    if has_hot_principle:
        total_score += 0.5

    # ---- CHECK 12: Memory palace has 温/done section with execution results ----
    has_warm_done = bool(re.search(r'温/done|温.*done|warm.*done|completed|done\s*section|done:', memory_content, re.IGNORECASE))
    checks.append(check("memory_palace_warm_done", has_warm_done,
        "温/done (completed work) section present" if has_warm_done else "Missing 温/done section in memory palace"))
    if has_warm_done:
        total_score += 0.5

    # ---- CHECK 13: Memory palace has 热/领悟 section with reflections ----
    has_hot_insight = bool(re.search(r'热/领悟|热.*领悟|hot.*insight|insight\s*section|领悟', memory_content, re.IGNORECASE))
    checks.append(check("memory_palace_hot_insight", has_hot_insight,
        "热/领悟 (insights) section present" if has_hot_insight else "Missing 热/领悟 section in memory palace"))
    if has_hot_insight:
        total_score += 0.5

    # ---- CHECK 14: Memory palace content is grounded in the incident ----
    incident_keywords = ['pgbouncer', 'connection pool', 'analytics', 'replica', 'INC-2024', 'postgres', 'batch']
    incident_grounded = any(kw.lower() in memory_content.lower() for kw in incident_keywords)
    checks.append(check("memory_palace_incident_grounded", incident_grounded,
        "Memory palace content references incident details" if incident_grounded else
        "Memory palace content does not reference the actual incident"))
    if incident_grounded:
        total_score += 0.5

    # ---- Final scoring ----
    final_score = min(1.0, total_score / max_score)
    
    # Must pass at minimum: all 3 sections present, correct order, AND at least 2 memory palace sections
    core_passed = (
        has_thinking and has_execution and has_reflection and
        order_correct and
        bool(memory_files) and
        (has_hot_principle or has_warm_done or has_hot_insight)
    )

    result = {
        "passed": core_passed and final_score >= 0.65,
        "score": round(final_score, 3),
        "checks": checks
    }
    return result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))