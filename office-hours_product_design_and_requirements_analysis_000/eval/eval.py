import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)
    
    # Find the design doc
    candidates = list(workspace.rglob("design_doc.md"))
    if not candidates:
        # Also search for any file named design_doc with .md
        candidates = list(workspace.rglob("design_doc.md"))
    
    if not candidates:
        checks.append(check("file_exists", False, "design_doc.md not found anywhere in workspace"))
        return checks, 0.0

    # Use the first found
    doc_path = candidates[0]
    checks.append(check("file_exists", True, f"Found at {doc_path}"))
    
    try:
        content = doc_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        return checks, 0.0
    
    checks.append(check("file_readable", True, f"File size: {len(content)} chars"))

    # --- Check 1: Startup mode template used (not Builder) ---
    # Must have "模式：Startup" or "模式: Startup"
    startup_mode = bool(re.search(r'模式[:：]\s*Startup', content))
    checks.append(check(
        "startup_mode_declared",
        startup_mode,
        "Document must declare '模式：Startup'" if not startup_mode else "Found Startup mode declaration"
    ))

    # --- Check 2: All required Startup template sections present ---
    required_sections = [
        "问题陈述",
        "需求证据",
        "现状替代方案",
        "目标用户与最窄切入口",
        "约束条件",
        "前提假设",
        "方案对比",
        "推荐方案",
        "待解决问题",
        "成功标准",
        "下一步行动",
        "我注意到的你的思维方式",
    ]
    missing_sections = []
    for section in required_sections:
        if section not in content:
            missing_sections.append(section)
    
    sections_ok = len(missing_sections) == 0
    checks.append(check(
        "all_required_sections_present",
        sections_ok,
        f"Missing sections: {missing_sections}" if missing_sections else "All 12 required sections found"
    ))

    # --- Check 3: Phase 3 前提假设 in correct format [陈述] — 同意/不同意？ ---
    # Must have at least 2 entries in the format: numbered or bulleted item ending with 同意/不同意？
    premise_pattern = re.findall(r'[同意|不同意]？', content)
    premise_format_ok = len(premise_pattern) >= 2
    checks.append(check(
        "premise_format_correct",
        premise_format_ok,
        f"Found {len(premise_pattern)} '同意/不同意？' markers. Need at least 2." 
        if not premise_format_ok else f"Found {len(premise_pattern)} premise challenge items with correct format"
    ))

    # --- Check 4: Phase 4 方案 schema — must have at least 方案 A and 方案 B ---
    plan_a = bool(re.search(r'方案\s*[Aa一]', content))
    plan_b = bool(re.search(r'方案\s*[Bb二]', content))
    plans_ok = plan_a and plan_b
    checks.append(check(
        "multiple_plans_generated",
        plans_ok,
        f"plan_A={plan_a}, plan_B={plan_b}. Both required." if not plans_ok else "Found 方案A and 方案B"
    ))

    # --- Check 5: 方案 schema fields — 工作量, 风险, 优势, 劣势 must appear (for at least one plan) ---
    schema_fields = ["工作量", "风险", "优势", "劣势"]
    missing_fields = [f for f in schema_fields if f not in content]
    schema_ok = len(missing_fields) == 0
    checks.append(check(
        "plan_schema_fields_present",
        schema_ok,
        f"Missing schema fields: {missing_fields}" if not schema_ok else "All required plan schema fields present (工作量/风险/优势/劣势)"
    ))

    # --- Check 6: 工作量 values must be S/M/L/XL ---
    workload_values = re.findall(r'工作量[:：]\s*([^\n,，。\s]+)', content)
    valid_workloads = {"S", "M", "L", "XL", "s", "m", "l", "xl"}
    workload_ok = any(v.strip() in valid_workloads for v in workload_values) if workload_values else False
    checks.append(check(
        "workload_uses_smlxl_scale",
        workload_ok,
        f"Found workload values: {workload_values}. Must use S/M/L/XL scale." 
        if not workload_ok else f"Workload values correct: {workload_values}"
    ))

    # --- Check 7: 风险 values must be 低/中/高 ---
    risk_values = re.findall(r'风险[:：]\s*([^\n,，。\s]+)', content)
    valid_risks = {"低", "中", "高"}
    risk_ok = any(v.strip() in valid_risks for v in risk_values) if risk_values else False
    checks.append(check(
        "risk_uses_low_mid_high_scale",
        risk_ok,
        f"Found risk values: {risk_values}. Must use 低/中/高 scale."
        if not risk_ok else f"Risk values correct: {risk_values}"
    ))

    # --- Check 8: 观察反射 contains direct quotes from the transcript (verbatim quotes) ---
    # Key quotes from the transcript that must appear in 观察反射
    key_quotes = [
        "张律师",          # "上海浦东的张律师" — specific person named
        "实习生",           # observation about unexpected usage pattern  
        "民事借贷",        # specific narrow entry point named
        "本周",            # "本周就能让人付钱" — specific timing
    ]
    # At least 2 of these verbatim fragments must appear in the 观察反射 section
    # Find 观察反射 section
    reflection_match = re.search(r'我注意到的你的思维方式(.+?)(?=##|$)', content, re.DOTALL)
    if reflection_match:
        reflection_text = reflection_match.group(1)
        found_quotes = [q for q in key_quotes if q in reflection_text]
        reflection_ok = len(found_quotes) >= 2
        checks.append(check(
            "reflection_contains_verbatim_quotes",
            reflection_ok,
            f"Found {len(found_quotes)}/4 key quotes in 观察反射: {found_quotes}. Need at least 2 verbatim quotes from transcript."
            if not reflection_ok else f"观察反射 contains {len(found_quotes)} direct quotes from transcript: {found_quotes}"
        ))
    else:
        checks.append(check(
            "reflection_contains_verbatim_quotes",
            False,
            "Could not locate '我注意到的你的思维方式' section content"
        ))

    # --- Check 9: No code blocks in the document ---
    # Must NOT contain code fences with actual code (triple backtick + language identifier + code)
    code_blocks = re.findall(r'```(?:python|javascript|java|sql|bash|sh|typescript|go|rust|cpp|c\+\+)[^\n]*\n(.+?)```', content, re.DOTALL)
    no_code_ok = len(code_blocks) == 0
    checks.append(check(
        "no_code_written",
        no_code_ok,
        f"Found {len(code_blocks)} code block(s) with programming language identifiers. This skill NEVER writes code."
        if not no_code_ok else "No code blocks found — design-only document"
    ))

    # --- Check 10: 最小可行版 concept present (one plan must be minimum viable) ---
    min_viable_keywords = ["最小", "最小可行", "MVP", "minimal", "轻量"]
    mvp_present = any(kw in content for kw in min_viable_keywords)
    checks.append(check(
        "minimum_viable_plan_included",
        mvp_present,
        "Must include a minimum viable plan option among the solutions"
        if not mvp_present else "Minimum viable plan concept found"
    ))

    # --- Check 11: 下一步行动 is specific (not generic like "开始做") ---
    next_step_match = re.search(r'下一步行动[（(]?具体的一件事[）)]?\s*\n(.+?)(?=\n##|\n#|$)', content, re.DOTALL)
    if next_step_match:
        next_step_text = next_step_match.group(1).strip()
        # Should be non-empty and reasonably specific (>10 chars)
        specific_ok = len(next_step_text) > 10
        checks.append(check(
            "next_step_is_specific",
            specific_ok,
            f"下一步行动 text too short or vague: '{next_step_text[:100]}'"
            if not specific_ok else f"下一步行动 is specific: '{next_step_text[:100]}'"
        ))
    else:
        # Try looser match
        next_step_loose = re.search(r'下一步行动(.{0,30})\n(.{10,})', content)
        if next_step_loose:
            checks.append(check("next_step_is_specific", True, "下一步行动 section found with content"))
        else:
            checks.append(check("next_step_is_specific", False, "下一步行动 section not found or empty"))

    # --- Check 12: Correct stage-based question focus ---
    # The transcript shows "有用户无付费" → Q2, Q4, Q5 should be dominant
    # Q1 (需求真实性 from scratch) should NOT be the main focus; instead Q4 (最窄切入口) and Q5 (观察意外) should appear
    # Check that the doc addresses the unexpected user observation (Q5: 实习生/助理 using it, not main lawyers)
    q5_addressed = "实习生" in content or "助理" in content
    q4_addressed = "民事借贷" in content or "最窄" in content or "起诉状" in content
    q2_addressed = "Word模板" in content or "无讼" in content or "2-3小时" in content or "现状" in content
    
    stage_focus_ok = q2_addressed and q4_addressed and q5_addressed
    checks.append(check(
        "correct_stage_question_focus",
        stage_focus_ok,
        f"For '已有用户' stage, must address Q2(现状替代方案)={q2_addressed}, Q4(最窄切入口)={q4_addressed}, Q5(观察意外)={q5_addressed}"
        if not stage_focus_ok else "Correctly focused on Q2/Q4/Q5 appropriate for 已有用户 stage"
    ))

    # Compute score
    total = len(checks) - 2  # exclude file_exists and file_readable from scoring
    passed_count = sum(1 for c in checks[2:] if c["passed"])
    score = round(passed_count / total, 3) if total > 0 else 0.0
    overall_passed = score >= 0.75

    return checks, score, overall_passed


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace dir provided"}]}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    
    try:
        checks, score, overall_passed = run_eval(workspace_dir)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": f"Evaluator crashed: {e}"}]
        }
        print(json.dumps(result, ensure_ascii=False))
        sys.exit(1)
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()