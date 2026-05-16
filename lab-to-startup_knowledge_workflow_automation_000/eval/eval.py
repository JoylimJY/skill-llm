import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    
    # Find the advisory report
    report_path = None
    candidates = list(Path(workspace_dir).rglob("advisory_report.json"))
    if candidates:
        report_path = candidates[0]

    if not report_path or not report_path.exists():
        checks.append({
            "name": "file_exists",
            "passed": False,
            "detail": "advisory_report.json not found anywhere in workspace"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "file_exists",
        "passed": True,
        "detail": f"Found advisory_report.json at {report_path}"
    })

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
    except Exception as e:
        checks.append({
            "name": "json_valid",
            "passed": False,
            "detail": f"File is not valid JSON: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({
        "name": "json_valid",
        "passed": True,
        "detail": "File is valid JSON"
    })

    report_str = json.dumps(report, ensure_ascii=False).lower()

    # ==========================================================================
    # CHECK 1: Correct Team Type Classification
    # The scenario maps to 师生共同主导型 (Co-leadership):
    # - Long-cycle industry (pharmaceutical, 3-5 years to product)
    # - Clear application scenario (drug toxicity testing / organ-on-chip)
    # - Mutual trust between teacher and student (4 years together)
    # - Both Prof Chen and Zhao want central roles (not advisor-only)
    # The SKILL.md decision matrix: "长周期 + 明确应用场景 + 师生互信" => 师生共同主导型
    # ==========================================================================
    
    co_lead_keywords = [
        "师生共同主导", "共同主导", "co-lead", "co-leadership", "joint leadership",
        "共同领导", "合伙人", "partnership", "共创型", "师生共创主导",
        "type 3", "类型三", "第三种", "three", "third type"
    ]
    
    # Must NOT say teacher-led or student-led as primary recommendation
    wrong_teacher_led = ["老师主导型", "teacher-led", "teacher led", "教师主导型", "类型一", "type 1", "type one"]
    wrong_student_led_only = ["学生主导型", "student-led", "student led", "类型二", "type 2", "type two"]
    
    correct_type_found = any(kw in report_str for kw in co_lead_keywords)
    
    # Check if wrongly classified (unless they mention it as comparison, which is ok)
    # We'll be generous - just check if the PRIMARY recommendation is correct
    teacher_led_primary = any(kw in report_str for kw in wrong_teacher_led)
    student_led_primary = any(kw in report_str for kw in wrong_student_led_only)
    
    check1_passed = correct_type_found
    checks.append({
        "name": "correct_team_type_classification",
        "passed": check1_passed,
        "detail": (
            f"Team type correctly identified as 师生共同主导型 (Co-leadership): {correct_type_found}. "
            f"This is required because: long pharmaceutical development cycle (3-5 years), "
            f"clear application scenario (drug testing), mutual trust between Prof. Chen and Zhao (4 years). "
            f"SKILL.md decision matrix: '长周期 + 明确应用场景 + 师生互信 => 师生共同主导型'."
        )
    })
    if check1_passed:
        total_score += 0.20

    # ==========================================================================
    # CHECK 2: Correct Role Division for 师生共同主导型
    # SKILL.md specifies for this type:
    # - 老师: 技术研发、学术合作、长期规划 (tech R&D, academic collaboration, long-term planning)
    # - 学生: 商业运营、市场拓展、团队管理 (business ops, market expansion, team management)
    # Liu Yanran (MBA, non-lab): should be placed in business/commercial role
    # ==========================================================================
    
    teacher_role_keywords = ["技术研发", "学术合作", "长期规划", "tech", "technical", "research", "r&d", "academic", "technology direction", "技术方向"]
    student_role_keywords = ["商业运营", "市场拓展", "团队管理", "business", "commercial", "market", "operations", "ceo", "运营"]
    
    teacher_role_correct = any(kw in report_str for kw in teacher_role_keywords)
    student_role_correct = any(kw in report_str for kw in student_role_keywords)
    
    # Check Liu Yanran's role (business/commercial since she's MBA, non-lab)
    liu_business_role = any(kw in report_str for kw in ["liu", "刘艳然", "liu yanran", "mba", "business development", "商业", "market"])
    
    check2_passed = teacher_role_correct and student_role_correct
    checks.append({
        "name": "correct_role_division",
        "passed": check2_passed,
        "detail": (
            f"Role division for 师生共同主导型 - Teacher roles (tech/academic/planning): {teacher_role_correct}, "
            f"Student roles (business/market/operations): {student_role_correct}. "
            f"Liu Yanran placed in business context: {liu_business_role}. "
            f"Per SKILL.md: teacher handles 技术研发+学术合作+长期规划; student handles 商业运营+市场拓展+团队管理."
        )
    })
    if check2_passed:
        total_score += 0.15

    # ==========================================================================
    # CHECK 3: Problem A (Leadership Conflict) - Must reference specific mechanisms
    # SKILL.md specifies for "谁来主导" problem:
    # - 明确角色分工表 (clear role responsibility matrix)
    # - 建立定期沟通机制 (regular communication mechanism)
    # - 制定决策权限规则 (decision authority rules)
    # - 建立冲突解决机制 (conflict resolution mechanism)
    # ==========================================================================
    
    problem_a_keywords = [
        "角色分工", "决策权限", "沟通机制", "冲突解决",
        "role division", "decision authority", "communication mechanism", "conflict resolution",
        "decision rights", "authority", "分工", "权限", "机制", "沟通"
    ]
    
    problem_a_hits = sum(1 for kw in problem_a_keywords if kw in report_str)
    check3_passed = problem_a_hits >= 2
    checks.append({
        "name": "problem_a_leadership_conflict_solution",
        "passed": check3_passed,
        "detail": (
            f"Problem A (leadership conflict) addressed with {problem_a_hits} relevant mechanism keywords. "
            f"SKILL.md requires: role matrix, communication mechanism, decision authority rules, conflict resolution. "
            f"Minimum 2 of these must appear. Found: {problem_a_hits}."
        )
    })
    if check3_passed:
        total_score += 0.15

    # ==========================================================================
    # CHECK 4: Problem B (Technology Grounding) - Must mention TRL
    # SKILL.md specifies for "技术落地难" problem:
    # - 进行技术成熟度评估 (TRL) - THIS IS THE KEY PROPRIETARY TERM
    # - 制定渐进式产品化路径
    # - 早期引入用户参与设计
    # - 平衡技术先进性和成本
    # TRL is a specific jargon from the skill that generic agents won't naturally use for this problem
    # ==========================================================================
    
    trl_keywords = ["trl", "技术成熟度", "technology readiness level", "技术成熟度评估", "maturity level", "readiness"]
    product_path_keywords = ["产品化路径", "渐进式", "productization", "incremental", "phased", "分阶段", "路线图", "roadmap"]
    user_involvement_keywords = ["早期用户", "用户参与", "early user", "user participation", "共同开发", "co-development", "试用", "pilot"]
    
    trl_mentioned = any(kw in report_str for kw in trl_keywords)
    product_path_mentioned = any(kw in report_str for kw in product_path_keywords)
    user_involvement_mentioned = any(kw in report_str for kw in user_involvement_keywords)
    
    check4_passed = trl_mentioned  # TRL is the key proprietary check
    checks.append({
        "name": "problem_b_tech_grounding_trl",
        "passed": check4_passed,
        "detail": (
            f"Problem B (tech grounding) must include TRL assessment: {trl_mentioned}. "
            f"Product path mentioned: {product_path_mentioned}. User involvement: {user_involvement_mentioned}. "
            f"TRL (技术成熟度评估) is the specific proprietary framework term from SKILL.md for this problem. "
            f"A generic agent would not naturally use TRL here without reading the skill documentation."
        )
    })
    if check4_passed:
        total_score += 0.15

    # ==========================================================================
    # CHECK 5: Problem C (Tech-Market Matching) - Must identify correct approach
    # SKILL.md: 技术导向型 vs 市场导向型 distinction, plus 5-step transition process
    # The scenario is currently tech-driven but should move to market-driven
    # Key steps: 深入调研潜在应用场景, 识别客户痛点, 评估基础设施, 计算客户替代成本, 调整技术战略定位
    # ==========================================================================
    
    tech_oriented_keywords = ["技术导向", "technology-driven", "tech-driven", "technology oriented"]
    market_oriented_keywords = ["市场导向", "market-driven", "market oriented", "用户需求", "customer needs", "痛点", "pain point"]
    transition_keywords = [
        "应用场景", "客户痛点", "替代成本", "基础设施", 
        "application scenario", "customer pain", "switching cost", "infrastructure",
        "转型", "transition", "调研", "场景"
    ]
    
    identifies_both_types = (
        any(kw in report_str for kw in tech_oriented_keywords) or 
        any(kw in report_str for kw in market_oriented_keywords)
    )
    transition_hits = sum(1 for kw in transition_keywords if kw in report_str)
    
    check5_passed = identifies_both_types and transition_hits >= 2
    checks.append({
        "name": "problem_c_tech_market_matching",
        "passed": check5_passed,
        "detail": (
            f"Problem C (tech-market matching): identifies tech/market orientation distinction: {identifies_both_types}, "
            f"transition process keywords found: {transition_hits}/required 2. "
            f"SKILL.md requires identifying tech-oriented vs market-oriented approaches and providing 5-step transition guidance."
        )
    })
    if check5_passed:
        total_score += 0.10

    # ==========================================================================
    # CHECK 6: Implementation Roadmap - Must follow 3-phase structure
    # SKILL.md specifies exact 3 phases: 启动阶段, 验证阶段, 成长阶段
    # Each with specific sub-items
    # ==========================================================================
    
    phase1_keywords = ["启动", "startup phase", "launch", "initiation", "识别可转化", "组建核心团队", "商业计划"]
    phase2_keywords = ["验证", "validation", "verify", "技术验证", "市场验证", "mvp", "prototype", "原型"]
    phase3_keywords = ["成长", "growth", "scale", "产品化", "市场拓展", "组织建设", "scaling"]
    
    phase1_found = any(kw in report_str for kw in phase1_keywords)
    phase2_found = any(kw in report_str for kw in phase2_keywords)
    phase3_found = any(kw in report_str for kw in phase3_keywords)
    
    phases_count = sum([phase1_found, phase2_found, phase3_found])
    check6_passed = phases_count >= 2
    checks.append({
        "name": "implementation_roadmap_three_phases",
        "passed": check6_passed,
        "detail": (
            f"Implementation roadmap phases - 启动 (launch): {phase1_found}, "
            f"验证 (validation): {phase2_found}, 成长 (growth): {phase3_found}. "
            f"Found {phases_count}/3 phases. Need at least 2. "
            f"SKILL.md defines exactly 3 implementation phases: 启动阶段, 验证阶段, 成长阶段."
        )
    })
    if check6_passed:
        total_score += 0.10

    # ==========================================================================
    # CHECK 7: Success Factor Checklist - Must cover all 3 SKILL.md dimensions
    # SKILL.md defines exactly 3 dimensions: 团队层面, 资源层面, 战略层面
    # ==========================================================================
    
    team_dimension_keywords = ["团队", "team", "能力结构", "愿景", "价值观", "沟通", "分工", "complementary"]
    resource_dimension_keywords = ["资源", "resource", "政策支持", "实验室", "投资", "产业合作", "policy", "funding", "investor"]
    strategy_dimension_keywords = ["战略", "strategy", "技术定位", "市场策略", "知识产权", "ip", "intellectual property", "long-term"]
    
    team_dim = any(kw in report_str for kw in team_dimension_keywords)
    resource_dim = any(kw in report_str for kw in resource_dimension_keywords)
    strategy_dim = any(kw in report_str for kw in strategy_dimension_keywords)
    
    dims_count = sum([team_dim, resource_dim, strategy_dim])
    check7_passed = dims_count >= 2
    checks.append({
        "name": "success_factor_checklist_three_dimensions",
        "passed": check7_passed,
        "detail": (
            f"Success factor checklist dimensions - 团队 (team): {team_dim}, "
            f"资源 (resources): {resource_dim}, 战略 (strategy): {strategy_dim}. "
            f"Found {dims_count}/3 dimensions. Need at least 2. "
            f"SKILL.md defines exactly 3 checklist dimensions with specific items under each."
        )
    })
    if check7_passed:
        total_score += 0.10

    # ==========================================================================
    # CHECK 8: Structural Quality - Report must be structured JSON (not just text dump)
    # Must have meaningful keys/structure, not just a single "content" string
    # ==========================================================================
    
    is_dict = isinstance(report, dict)
    has_multiple_keys = isinstance(report, dict) and len(report.keys()) >= 3
    
    # Check for meaningful nested structure
    has_nested = False
    if isinstance(report, dict):
        for v in report.values():
            if isinstance(v, (dict, list)):
                has_nested = True
                break
    
    check8_passed = is_dict and has_multiple_keys and has_nested
    checks.append({
        "name": "structured_json_quality",
        "passed": check8_passed,
        "detail": (
            f"JSON is a dict: {is_dict}, has >= 3 keys: {has_multiple_keys} "
            f"(found {len(report.keys()) if is_dict else 0}), has nested structure: {has_nested}. "
            f"Report must be properly structured with multiple sections, not a flat text dump."
        )
    })
    if check8_passed:
        total_score += 0.05

    # Determine overall pass: must pass at least 5 of 8 checks including the critical classification check
    critical_checks_passed = check1_passed  # Must correctly identify team type
    total_checks_passed = sum(1 for c in checks[1:] if c["passed"])  # exclude file_exists
    
    overall_passed = (
        critical_checks_passed and 
        total_checks_passed >= 4 and
        total_score >= 0.50
    )

    return {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))