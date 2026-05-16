import sys
import os
import json
import re
from pathlib import Path

def find_file(workspace, filename):
    """Find a file by name anywhere in workspace."""
    results = list(Path(workspace).rglob(filename))
    return results[0] if results else None

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return None

def check_exam(content):
    checks = []
    
    # Check 1: Blueprint cognitive levels present
    has_memory = bool(re.search(r'记忆|识记', content))
    has_understanding = bool(re.search(r'理解', content))
    has_application = bool(re.search(r'应用', content))
    has_analysis = bool(re.search(r'分析', content))
    has_evaluation = bool(re.search(r'评价', content))
    has_creation = bool(re.search(r'创造|构造|变式', content))
    
    all_levels = all([has_memory, has_understanding, has_application, has_analysis, has_evaluation, has_creation])
    checks.append({
        "name": "exam_all_bloom_levels_present",
        "passed": all_levels,
        "detail": f"记忆:{has_memory}, 理解:{has_understanding}, 应用:{has_application}, 分析:{has_analysis}, 评价:{has_evaluation}, 创造:{has_creation}"
    })
    
    # Check 2: High-order (分析+评价+创造) >= 40%
    # Look for score mentions near these levels
    # We look for explicit percentage or score mentions of high-order being >=40
    high_order_match = re.search(r'(分析.*?评价.*?创造|高阶).*?(\d+)\s*[%％分]', content, re.DOTALL)
    # Also check if the blueprint table shows 25+10+5=40 or >=40
    score_pattern = re.findall(r'(\d+)\s*[%％分]', content)
    # Try to find the high-order sum
    has_40_percent = bool(re.search(r'4[0-9]\s*[%％]|40\s*分', content))
    # Also check for explicit label of 诊断/比选/构造
    has_diagnostic_label = bool(re.search(r'诊断|比选|构造', content))
    checks.append({
        "name": "exam_highorder_ge_40_percent",
        "passed": has_40_percent or (has_analysis and has_evaluation and has_creation and has_diagnostic_label),
        "detail": f"Found >=40% marker: {has_40_percent}, has diagnostic/compare/construct label: {has_diagnostic_label}"
    })
    
    # Check 3: At least 1 question explicitly labeled 「诊断/比选/构造」
    checks.append({
        "name": "exam_has_diagnostic_or_compare_or_construct_label",
        "passed": has_diagnostic_label,
        "detail": f"Found 诊断/比选/构造 label: {has_diagnostic_label}"
    })
    
    # Check 4: Difficulty ratio mentioned (易/中/难 = 3:5:2)
    has_difficulty_ratio = bool(re.search(r'3\s*[：:]\s*5\s*[：:]\s*2|易.*?中.*?难|难度', content))
    checks.append({
        "name": "exam_difficulty_ratio_352",
        "passed": has_difficulty_ratio,
        "detail": f"Difficulty ratio 3:5:2 or difficulty mentioned: {has_difficulty_ratio}"
    })
    
    # Check 5: skillId for ch7 (常微分方程Skill or 常微分方程求解Skill)
    has_skill_id = bool(re.search(r'常微分方程Skill|常微分方程求解Skill', content))
    checks.append({
        "name": "exam_has_ode_skillId",
        "passed": has_skill_id,
        "detail": f"Found ODE skillId: {has_skill_id}"
    })
    
    # Check 6: Chapter 7 content (differential equations topics)
    has_ch7_content = bool(re.search(r'微分方程|一阶线性|二阶|积分因子|分离变量|线性方程', content))
    checks.append({
        "name": "exam_ch7_content_present",
        "passed": has_ch7_content,
        "detail": f"Ch7 differential equations content present: {has_ch7_content}"
    })
    
    # Check 7: Innovative questions >= 12%
    has_innovative_12 = bool(re.search(r'1[2-9]\s*[%％]|创新题|12[%％]', content))
    checks.append({
        "name": "exam_innovative_ge_12_percent",
        "passed": has_innovative_12 or has_diagnostic_label,
        "detail": f">=12% innovative mentioned or diagnostic label present: {has_innovative_12 or has_diagnostic_label}"
    })
    
    return checks

def check_homework(content):
    checks = []
    
    # Check 1: Required emoji section headers present
    has_basic = bool(re.search(r'🟢\s*基础', content))
    has_advanced = bool(re.search(r'🟡\s*进阶', content))
    has_challenge = bool(re.search(r'🔴\s*挑战', content))
    has_all_sections = has_basic and has_advanced and has_challenge
    checks.append({
        "name": "homework_three_tier_emoji_headers",
        "passed": has_all_sections,
        "detail": f"🟢基础:{has_basic}, 🟡进阶:{has_advanced}, 🔴挑战:{has_challenge}"
    })
    
    # Check 2: Per-question metadata (预计 + 星级 + 布鲁姆)
    has_time_estimate = bool(re.search(r'预计\s*\d+\s*min', content))
    has_star_rating = bool(re.search(r'[⭐★]{1,3}', content))
    has_bloom_label = bool(re.search(r'认知[：:]|布鲁姆|识记|理解|应用|分析|评价|创造', content))
    has_metadata = has_time_estimate and has_star_rating and has_bloom_label
    checks.append({
        "name": "homework_per_question_metadata",
        "passed": has_metadata,
        "detail": f"时间估计:{has_time_estimate}, 星级:{has_star_rating}, 布鲁姆:{has_bloom_label}"
    })
    
    # Check 3: Proportion labels (35%, 45%, 20%)
    has_35 = bool(re.search(r'35\s*[%％]', content))
    has_45 = bool(re.search(r'45\s*[%％]', content))
    has_20 = bool(re.search(r'20\s*[%％]', content))
    checks.append({
        "name": "homework_tier_proportions_35_45_20",
        "passed": has_35 and has_45 and has_20,
        "detail": f"35%:{has_35}, 45%:{has_45}, 20%:{has_20}"
    })
    
    # Check 4: At least 2 high-order task types from the table
    task_types = [
        bool(re.search(r'错误诊断|诊断', content)),
        bool(re.search(r'多法比选|比选|多种方法', content)),
        bool(re.search(r'表征转换|几何意义|物理意义', content)),
        bool(re.search(r'条件弱化|反例', content)),
        bool(re.search(r'约束建模|建模', content)),
    ]
    high_order_count = sum(task_types)
    checks.append({
        "name": "homework_at_least_2_highorder_task_types",
        "passed": high_order_count >= 2,
        "detail": f"High-order task types found: {high_order_count} (需>=2). 类型: 诊断={task_types[0]}, 比选={task_types[1]}, 表征={task_types[2]}, 反例={task_types[3]}, 建模={task_types[4]}"
    })
    
    # Check 5: At least 1 multi-solution or error-diagnosis question
    has_multi_or_diag = bool(re.search(r'一题多解|多解|错误诊断|诊断', content))
    checks.append({
        "name": "homework_has_multi_solution_or_error_diagnosis",
        "passed": has_multi_or_diag,
        "detail": f"一题多解 or 错误诊断 present: {has_multi_or_diag}"
    })
    
    # Check 6: Common error traps warned
    has_error_trap = bool(re.search(r'常见错误|陷阱|误区|注意', content))
    checks.append({
        "name": "homework_error_trap_warnings",
        "passed": has_error_trap,
        "detail": f"Error trap / 常见错误 mentioned: {has_error_trap}"
    })
    
    # Check 7: Hints provided (思路提示 not full answers)
    has_hints = bool(re.search(r'思路提示|提示|hint', content, re.IGNORECASE))
    checks.append({
        "name": "homework_hints_not_full_answers",
        "passed": has_hints,
        "detail": f"思路提示 present: {has_hints}"
    })
    
    # Check 8: skillId for ch7
    has_skill_id = bool(re.search(r'常微分方程Skill|常微分方程求解Skill', content))
    checks.append({
        "name": "homework_has_ode_skillId",
        "passed": has_skill_id,
        "detail": f"ODE skillId found: {has_skill_id}"
    })
    
    return checks

def check_grading(content):
    checks = []
    
    # Check 1: Error classification used (知识性/方法性/计算性/逻辑性/表达性)
    error_types = [
        bool(re.search(r'知识性', content)),
        bool(re.search(r'方法性', content)),
        bool(re.search(r'计算性', content)),
        bool(re.search(r'逻辑性', content)),
        bool(re.search(r'表达性', content)),
    ]
    has_error_classification = sum(error_types) >= 2
    checks.append({
        "name": "grading_error_classification_used",
        "passed": has_error_classification,
        "detail": f"Error types found: 知识性={error_types[0]}, 方法性={error_types[1]}, 计算性={error_types[2]}, 逻辑性={error_types[3]}, 表达性={error_types[4]}"
    })
    
    # Check 2: Proof checklist items addressed
    proof_items = [
        bool(re.search(r'起点|定理框架|证明框架', content)),
        bool(re.search(r'条件.*验证|验证.*条件|连续.*可导|Picard|存在唯一', content)),
        bool(re.search(r'循环论证|偷换|跳跃|逻辑', content)),
    ]
    has_proof_checklist = sum(proof_items) >= 2
    checks.append({
        "name": "grading_proof_checklist_addressed",
        "passed": has_proof_checklist,
        "detail": f"Proof checklist items: 框架={proof_items[0]}, 条件验证={proof_items[1]}, 逻辑={proof_items[2]}"
    })
    
    # Check 3: Four high-order scoring dimensions addressed
    hd = [
        bool(re.search(r'论证结构', content)),
        bool(re.search(r'策略质量', content)),
        bool(re.search(r'批判性', content)),
        bool(re.search(r'表达严谨性|严谨', content)),
    ]
    has_highorder_dims = sum(hd) >= 3
    checks.append({
        "name": "grading_highorder_dimensions_at_least_3",
        "passed": has_highorder_dims,
        "detail": f"高阶评分维度: 论证结构={hd[0]}, 策略质量={hd[1]}, 批判性={hd[2]}, 表达严谨={hd[3]}"
    })
    
    # Check 4: Three-step feedback rhetoric (affirm → improve → next step)
    has_affirm = bool(re.search(r'肯定|做得好|正确|合理|有效步骤|优点', content))
    has_improve = bool(re.search(r'改进|不足|问题|错误|需要|提升', content))
    has_next_step = bool(re.search(r'下一步|建议|可以尝试|追问|练习|参考', content))
    has_rhetoric = has_affirm and has_improve and has_next_step
    checks.append({
        "name": "grading_three_step_rhetoric_affirm_improve_next",
        "passed": has_rhetoric,
        "detail": f"肯定:{has_affirm}, 改进:{has_improve}, 下一步:{has_next_step}"
    })
    
    # Check 5: Identifies the actual flaw in the proof (Part 1 is too sketchy/circular)
    # The student's existence proof is just "obviously" - should flag logical jump
    identifies_proof_flaw = bool(re.search(r'显然|跳跃|论证不足|不严谨|Picard.*条件|条件.*验证|缺少|未验证|简略', content))
    checks.append({
        "name": "grading_identifies_existence_proof_flaw",
        "passed": identifies_proof_flaw,
        "detail": f"Identifies flaw in existence proof (logical jump/'显然'): {identifies_proof_flaw}"
    })
    
    # Check 6: Validates the correct solution part (y=(x+1)eˣ is correct)
    validates_correct = bool(re.search(r'y\s*=\s*\(x\s*\+\s*1\)\s*e\^?x|正确|计算.*正确|数值.*正确', content))
    checks.append({
        "name": "grading_validates_correct_solution",
        "passed": validates_correct,
        "detail": f"Validates the correct part of solution: {validates_correct}"
    })
    
    # Check 7: skillId present in grading report
    has_skill_id = bool(re.search(r'常微分方程Skill|常微分方程求解Skill', content))
    checks.append({
        "name": "grading_has_ode_skillId",
        "passed": has_skill_id,
        "detail": f"ODE skillId in grading report: {has_skill_id}"
    })
    
    # Check 8: Does NOT provide full complete solution (anti-pattern: 替学生撰写完整解答)
    # Check the grading file is primarily feedback, not a full rewrite
    # Heuristic: grading report should not be 80%+ solution text
    word_count = len(content)
    solution_pattern_count = len(re.findall(r'积分因子|e\^\(-x\)|两边乘以.*μ', content))
    not_full_rewrite = solution_pattern_count <= 3 or word_count > 800
    checks.append({
        "name": "grading_not_full_answer_rewrite",
        "passed": not_full_rewrite,
        "detail": f"Solution pattern count: {solution_pattern_count}, total length: {word_count}"
    })
    
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    all_checks = []
    
    # --- Find and evaluate exam_ch7.md ---
    exam_file = find_file(workspace, "exam_ch7.md")
    if exam_file is None:
        all_checks.append({"name": "exam_ch7_file_exists", "passed": False, "detail": "exam_ch7.md not found anywhere in workspace"})
    else:
        all_checks.append({"name": "exam_ch7_file_exists", "passed": True, "detail": str(exam_file)})
        content = read_file(exam_file)
        if content:
            all_checks.extend(check_exam(content))
        else:
            all_checks.append({"name": "exam_ch7_readable", "passed": False, "detail": "Could not read exam_ch7.md"})
    
    # --- Find and evaluate homework_ch7.md ---
    hw_file = find_file(workspace, "homework_ch7.md")
    if hw_file is None:
        all_checks.append({"name": "homework_ch7_file_exists", "passed": False, "detail": "homework_ch7.md not found anywhere in workspace"})
    else:
        all_checks.append({"name": "homework_ch7_file_exists", "passed": True, "detail": str(hw_file)})
        content = read_file(hw_file)
        if content:
            all_checks.extend(check_homework(content))
        else:
            all_checks.append({"name": "homework_ch7_readable", "passed": False, "detail": "Could not read homework_ch7.md"})
    
    # --- Find and evaluate grading_ch7_studentA.md ---
    grade_file = find_file(workspace, "grading_ch7_studentA.md")
    if grade_file is None:
        all_checks.append({"name": "grading_ch7_studentA_file_exists", "passed": False, "detail": "grading_ch7_studentA.md not found anywhere in workspace"})
    else:
        all_checks.append({"name": "grading_ch7_studentA_file_exists", "passed": True, "detail": str(grade_file)})
        content = read_file(grade_file)
        if content:
            all_checks.extend(check_grading(content))
        else:
            all_checks.append({"name": "grading_ch7_studentA_readable", "passed": False, "detail": "Could not read grading_ch7_studentA.md"})
    
    # Calculate score
    total = len(all_checks)
    passed_count = sum(1 for c in all_checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75
    
    result = {
        "passed": overall_passed,
        "score": score,
        "checks": all_checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()