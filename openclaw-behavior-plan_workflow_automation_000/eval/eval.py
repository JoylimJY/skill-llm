import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def evaluate(workspace_dir):
    ws = Path(workspace_dir)
    checks = []

    # Find the plan file
    candidates = list(ws.rglob("incident_response_plan.md"))
    if not candidates:
        checks.append(check("file_exists", False, "incident_response_plan.md not found anywhere in workspace"))
        return {"passed": False, "score": 0.0, "checks": checks}
    
    plan_path = candidates[0]
    try:
        content = plan_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_exists", True, f"Found at {plan_path}"))

    # --- CHECK 1: Trigger phrase ---
    trigger_ok = "正在触发 openclaw-behavior-plan skill" in content
    checks.append(check(
        "trigger_phrase",
        trigger_ok,
        "Must contain '正在触发 openclaw-behavior-plan skill'" if not trigger_ok else "Trigger phrase found"
    ))

    # --- CHECK 2: Top-level title ---
    title_ok = bool(re.search(r"^#\s+行为计划[：:].+", content, re.MULTILINE))
    checks.append(check(
        "plan_title",
        title_ok,
        "Must have '# 行为计划：...' as the top-level heading"
    ))

    # --- CHECK 3: Required section headers (Chinese, exact) ---
    required_sections = ["## 目标", "## 前置条件", "## 执行步骤", "## 异常与回退", "## 完成标准"]
    for section in required_sections:
        found = section in content
        checks.append(check(
            f"section_{section.strip('# ')}",
            found,
            f"Required section '{section}' {'found' if found else 'MISSING'}"
        ))

    # --- CHECK 4: Step headers with ### 步骤 N ---
    step_headers = re.findall(r"^###\s+步骤\s+\d+", content, re.MULTILINE)
    step_count_ok = len(step_headers) >= 4
    checks.append(check(
        "step_count",
        step_count_ok,
        f"Found {len(step_headers)} step(s) (### 步骤 N). Need at least 4 for this workflow."
    ))

    # --- CHECK 5: Each step has all 4 required bullet fields ---
    required_fields = ["**目的**", "**工具/技能**", "**输入**", "**预期输出**"]
    # Split into step blocks
    step_blocks = re.split(r"(?=^###\s+步骤\s+\d+)", content, flags=re.MULTILINE)
    step_blocks = [b for b in step_blocks if re.match(r"###\s+步骤\s+\d+", b.strip())]
    
    fields_ok = True
    missing_info = []
    for i, block in enumerate(step_blocks):
        for field in required_fields:
            if field not in block:
                fields_ok = False
                missing_info.append(f"Step {i+1} missing {field}")
    checks.append(check(
        "step_fields",
        fields_ok,
        "All steps have 目的/工具技能/输入/预期输出" if fields_ok else f"Missing fields: {'; '.join(missing_info[:5])}"
    ))

    # --- CHECK 6: Tool names from approved list ---
    approved_tools = ["execute_shell", "search_web", "read_file", "write_file"]
    tools_used = [t for t in approved_tools if t in content]
    tools_ok = len(tools_used) >= 2
    checks.append(check(
        "approved_tools_used",
        tools_ok,
        f"Tools from approved list found: {tools_used}. Need at least 2."
    ))

    # Specifically check: read_file for scanning logs, write_file for report
    read_file_ok = "read_file" in content or "execute_shell" in content
    write_file_ok = "write_file" in content
    checks.append(check(
        "read_tool_present",
        read_file_ok,
        "read_file or execute_shell must appear (for log scanning step)"
    ))
    checks.append(check(
        "write_file_present",
        write_file_ok,
        "write_file must appear for the remediation report writing step"
    ))

    # --- CHECK 7: Dependency notation ("依赖步骤 N") ---
    dependency_ok = bool(re.search(r"依赖步骤\s*\d+", content))
    checks.append(check(
        "dependency_notation",
        dependency_ok,
        "Must use '依赖步骤 N' notation to express inter-step dependencies"
    ))

    # --- CHECK 8: Preconditions use checkbox format ---
    precond_section = ""
    pre_match = re.search(r"## 前置条件(.+?)(?=^##|\Z)", content, re.DOTALL | re.MULTILINE)
    if pre_match:
        precond_section = pre_match.group(1)
    checkbox_pre_ok = bool(re.search(r"- \[[ x]\]", precond_section))
    checks.append(check(
        "preconditions_checkboxes",
        checkbox_pre_ok,
        "前置条件 section must use '- [ ]' checkbox format"
    ))

    # --- CHECK 9: 异常与回退 uses "若...→..." pattern ---
    fallback_section = ""
    fb_match = re.search(r"## 异常与回退(.+?)(?=^##|\Z)", content, re.DOTALL | re.MULTILINE)
    if fb_match:
        fallback_section = fb_match.group(1)
    fallback_pattern_ok = bool(re.search(r"若.+[→>].+", fallback_section))
    checks.append(check(
        "fallback_conditional_pattern",
        fallback_pattern_ok,
        "异常与回退 section must use '若 [condition] → [action]' conditional pattern"
    ))

    # --- CHECK 10: 完成标准 uses checkbox format ---
    completion_section = ""
    comp_match = re.search(r"## 完成标准(.+?)(?=^##|\Z)", content, re.DOTALL | re.MULTILINE)
    if comp_match:
        completion_section = comp_match.group(1)
    checkbox_comp_ok = bool(re.search(r"- \[[ x]\]", completion_section))
    checks.append(check(
        "completion_criteria_checkboxes",
        checkbox_comp_ok,
        "完成标准 section must use '- [ ]' checkbox format"
    ))

    # --- CHECK 11: Task-specific content (log scanning, remediation report, slack) ---
    has_log_content = bool(re.search(r"log|日志|ERROR|错误.*日志|log.*scan", content, re.IGNORECASE))
    has_report_content = bool(re.search(r"remediation.*report|remediation_report\.md|修复报告|整改报告", content, re.IGNORECASE))
    has_slack_content = bool(re.search(r"slack|Slack", content))

    checks.append(check("covers_log_scanning", has_log_content, "Plan must address log scanning for ERROR entries"))
    checks.append(check("covers_report_writing", has_report_content, "Plan must reference remediation_report.md or equivalent"))
    checks.append(check("covers_slack_notification", has_slack_content, "Plan must address posting Slack notification to #sre-alerts"))

    # --- Scoring ---
    passed_checks = [c for c in checks if c["passed"]]
    critical_checks = [
        "trigger_phrase", "plan_title",
        "section_目标", "section_前置条件", "section_执行步骤", "section_异常与回退", "section_完成标准",
        "step_fields", "dependency_notation", "fallback_conditional_pattern",
        "preconditions_checkboxes", "completion_criteria_checkboxes"
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    
    score = len(passed_checks) / len(checks)
    overall_passed = critical_passed and score >= 0.80

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))