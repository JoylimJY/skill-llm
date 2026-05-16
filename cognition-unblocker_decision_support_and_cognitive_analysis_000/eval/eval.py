import sys
import json
import re
from pathlib import Path

def normalize(text):
    """Lowercase and strip for fuzzy matching."""
    return text.lower().strip()

def search(text, patterns, threshold=1):
    """Return True if at least `threshold` patterns are found in text."""
    found = sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
    return found >= threshold

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    
    # --- Locate the output file ---
    candidates = list(workspace.rglob("decision_analysis.md"))
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "decision_analysis.md not found anywhere in workspace."}]
        }
    
    output_file = candidates[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {output_file}"})
    
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "output_file_readable", "passed": False, "detail": str(e)}]
        }
    
    checks.append({"name": "output_file_readable", "passed": True, "detail": f"File size: {len(content)} chars"})
    
    # --- CHECK 1: Minimum content length (not a stub) ---
    min_length = 1500
    length_ok = len(content) >= min_length
    checks.append({
        "name": "minimum_content_length",
        "passed": length_ok,
        "detail": f"Content length: {len(content)} chars (minimum: {min_length})"
    })
    
    # --- CHECK 2: Step 2 - Three-Layer Problem Decomposition ---
    # Must contain all three layers: 表层问题, 深层原因, 核心矛盾
    surface_patterns = [r'表层问题', r'surface.{0,20}problem', r'表层']
    deep_patterns = [r'深层原因', r'deep.{0,20}cause', r'深层']
    core_patterns = [r'核心矛盾', r'core.{0,20}conflict', r'核心.{0,10}矛盾', r'根本.{0,10}矛盾']
    
    has_surface = search(content, surface_patterns)
    has_deep = search(content, deep_patterns)
    has_core = search(content, core_patterns)
    
    layer_decomp_ok = has_surface and has_deep and has_core
    checks.append({
        "name": "step2_three_layer_decomposition",
        "passed": layer_decomp_ok,
        "detail": f"表层问题: {has_surface}, 深层原因: {has_deep}, 核心矛盾: {has_core}"
    })
    
    # --- CHECK 3: Step 3 - Multiple Perspectives (≥3) ---
    perspective_keywords = [
        r'成本.{0,10}视角|cost.{0,10}perspective',
        r'收益.{0,10}视角|长期.{0,10}视角|long.term.{0,10}perspective|benefit.{0,10}perspective',
        r'人性.{0,10}视角|心理.{0,10}视角|psychology|human.{0,10}perspective',
        r'系统.{0,10}视角|环境.{0,10}视角|system.{0,10}perspective|market.{0,10}perspective',
        r'视角|perspective|angle',
    ]
    # More lenient: just count sections with "视角" or clear perspective headers
    perspective_count_pattern = re.findall(r'(?:视角|perspective|角度|维度)', content, re.IGNORECASE)
    has_multiple_perspectives = len(perspective_count_pattern) >= 3
    
    # Also check for at least 3 distinct perspective headings
    perspective_heading_pattern = re.findall(
        r'(?:成本|收益|长期|人性|心理|系统|环境|风险|机会|cost|benefit|psychological|system|market|personal).{0,15}(?:视角|perspective|角度)',
        content, re.IGNORECASE
    )
    has_perspective_headings = len(perspective_heading_pattern) >= 3
    
    perspective_ok = has_multiple_perspectives or has_perspective_headings
    checks.append({
        "name": "step3_minimum_3_perspectives",
        "passed": perspective_ok,
        "detail": f"Perspective keyword count: {len(perspective_count_pattern)}, Perspective headings: {len(perspective_heading_pattern)}"
    })
    
    # --- CHECK 4: Step 4 - Plan Enumeration (3-6 plans) ---
    # Count plan/option sections - look for numbered plans or plan headers
    plan_patterns = re.findall(
        r'(?:方案\s*[一二三四五六1-6]|方案\s*\d|Plan\s*[A-F1-6]|选项\s*\d|Option\s*[A-F1-6]|##.{0,5}方案|###.{0,5}方案)',
        content, re.IGNORECASE
    )
    plan_count = len(plan_patterns)
    
    # Alternative: count bold plan headers
    if plan_count < 3:
        alt_plan_patterns = re.findall(
            r'\*\*方案[^*]+\*\*|\*\*选项[^*]+\*\*|\*\*Plan\s*[A-F1-6][^*]*\*\*',
            content, re.IGNORECASE
        )
        plan_count = max(plan_count, len(alt_plan_patterns))
    
    plans_count_ok = 3 <= plan_count <= 6
    checks.append({
        "name": "step4_plan_count_3_to_6",
        "passed": plans_count_ok,
        "detail": f"Detected plan count: {plan_count} (required: 3-6)"
    })
    
    # --- CHECK 5: Step 4 - All 5 required fields per plan ---
    # Must have: 方案描述, 成本, 风险, 成功率, 适配场景
    desc_pattern = search(content, [r'方案描述|plan.{0,10}description|做法'])
    cost_pattern = search(content, [r'成本', r'cost', r'付出', r'失去'])
    risk_pattern = search(content, [r'风险', r'risk', r'坏情况', r'worst'])
    success_rate_pattern = search(content, [r'成功率', r'success.{0,10}rate', r'高/中/低|高／中／低', r'\d{1,3}%', r'高\b.*中\b.*低|低\b.*中\b.*高'])
    fit_pattern = search(content, [r'适配场景', r'适合.{0,10}场景', r'适合.{0,10}人', r'fit.{0,20}scenario', r'suitable.{0,20}for'])
    
    all_five_fields = desc_pattern and cost_pattern and risk_pattern and success_rate_pattern and fit_pattern
    checks.append({
        "name": "step4_all_five_plan_fields",
        "passed": all_five_fields,
        "detail": f"方案描述:{desc_pattern}, 成本:{cost_pattern}, 风险:{risk_pattern}, 成功率:{success_rate_pattern}, 适配场景:{fit_pattern}"
    })
    
    # --- CHECK 6: Step 4 - All three plan types covered ---
    has_direct = search(content, [r'直接.{0,10}型|立刻.{0,10}做|立即.{0,10}辞职|直接辞|全职', r'direct.{0,10}type|quit.{0,5}immediately'])
    has_compromise = search(content, [r'折中|兼职|小步|试点|part.time|hybrid|side.{0,5}by.{0,5}side|过渡', r'compromise|phased|试错'])
    has_wait = search(content, [r'暂缓|观望|等待|先积累|先验证|wait|hold.off|先稳', r'defer|delay'])
    
    all_plan_types = has_direct and has_compromise and has_wait
    checks.append({
        "name": "step4_all_three_plan_types",
        "passed": all_plan_types,
        "detail": f"直接型:{has_direct}, 折中型:{has_compromise}, 暂缓观望型:{has_wait}"
    })
    
    # --- CHECK 7: Step 5 - Execution Path Structure ---
    # Must have: 分阶段步骤, 注意事项, 风险与止损
    has_stages = search(content, [r'第[一二三1-3]阶段|阶段\s*[一二三1-3]|Phase\s*[1-3]|Week|第.{0,3}周|第.{0,3}个月'])
    has_notes = search(content, [r'注意事项|注意|caution|注意点|注意：|⚠'])
    has_stoploss = search(content, [r'止损|stop.loss|风险控制|if.{0,10}fail|如果.{0,10}结果.{0,10}差|及早.{0,5}调整|撤退|退出'])
    
    execution_path_ok = has_stages and has_notes and has_stoploss
    checks.append({
        "name": "step5_execution_path_structure",
        "passed": execution_path_ok,
        "detail": f"分阶段:{has_stages}, 注意事项:{has_notes}, 风险止损:{has_stoploss}"
    })
    
    # --- CHECK 8: Step 5 - User agency respected (choice invitation) ---
    has_user_choice = search(content, [
        r'选择权在你|你来选|你决定|选择权|你更倾向|你倾向|you.{0,10}choose|choice.{0,10}yours|final.{0,10}decision',
        r'你会更倾向|最想要|哪.*方案|which.{0,10}option'
    ])
    checks.append({
        "name": "step5_user_choice_respected",
        "passed": has_user_choice,
        "detail": f"User agency/choice invitation present: {has_user_choice}"
    })
    
    # --- CHECK 9: Step 6 - Wrap-up / Follow-up section ---
    has_followup = search(content, [
        r'如果.{0,20}新的卡壳|遇到新|随时.{0,10}来|后续|兜底|follow.?up|卡壳点',
        r'如果你.{0,30}问题|有没有.{0,20}不现实|仍然.{0,10}担心|any.{0,10}concern'
    ])
    checks.append({
        "name": "step6_followup_section",
        "passed": has_followup,
        "detail": f"Step 6 wrap-up/follow-up present: {has_followup}"
    })
    
    # --- CHECK 10: Scenario relevance - mentions Li Wei's specific context ---
    has_context_refs = search(content, [
        r'李伟|Li Wei|中兴|telecom|400,?000|6,?000|MRR|12.?18\s*个?月|mortgage|房贷|12,?000'
    ], threshold=1)
    checks.append({
        "name": "scenario_specific_content",
        "passed": has_context_refs,
        "detail": f"Contains scenario-specific references (Li Wei/中兴/salary/MRR etc.): {has_context_refs}"
    })
    
    # --- Final scoring ---
    critical_checks = [
        "step2_three_layer_decomposition",
        "step4_all_five_plan_fields",
        "step4_plan_count_3_to_6",
        "step5_execution_path_structure",
    ]
    
    all_check_names = {c["name"]: c["passed"] for c in checks}
    
    # All critical checks must pass
    critical_passed = all(all_check_names.get(name, False) for name in critical_checks)
    
    # Count total passed
    total_passed = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = total_passed / total_checks
    
    # Must pass all critical checks AND have score >= 0.75 to overall pass
    overall_passed = critical_passed and score >= 0.75
    
    # Adjust score down if critical checks fail
    if not critical_passed:
        score = min(score, 0.49)
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))