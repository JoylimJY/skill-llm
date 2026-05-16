import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    total_score = 0.0
    
    workspace = Path(workspace_dir)
    
    # ── Locate the output file ──────────────────────────────────────────────
    # Look for the report file - agent should create it in workspace
    report_files = list(workspace.rglob("帝王会议*.md")) + \
                   list(workspace.rglob("帝王会议*.txt")) + \
                   list(workspace.rglob("imperial_council*.md")) + \
                   list(workspace.rglob("strategic_analysis*.md")) + \
                   list(workspace.rglob("strategic_report*.md")) + \
                   list(workspace.rglob("analysis_report*.md")) + \
                   list(workspace.rglob("council_report*.md")) + \
                   list(workspace.rglob("战略分析*.md")) + \
                   list(workspace.rglob("战略分析*.txt")) + \
                   list(workspace.rglob("会议报告*.md")) + \
                   list(workspace.rglob("会议报告*.txt"))

    # Also check for any .md file that is NOT the SKILL.md and NOT a distractor
    distractor_names = {
        "quarterly_goals.txt", "annual_review.md", "vacation_policy.txt",
        "job_postings.md", "2025_budget.csv", "2025_roadmap.md",
        "global_launch.txt", "nda_template.txt", "board_meeting_jan.md",
        "strategy_session.md", "global_market_2025.txt", "competitor_matrix.csv",
        "strategic_report_old.md", "planning_framework.txt", "2023_strategy.txt",
        "SKILL.md", "strategic_brief.txt"
    }
    
    if not report_files:
        # Broader search: any new .md or .txt that's not a distractor
        all_md = list(workspace.rglob("*.md")) + list(workspace.rglob("*.txt"))
        report_files = [f for f in all_md if f.name not in distractor_names]
    
    # Check 1: File exists
    file_found = len(report_files) > 0
    file_path = report_files[0] if file_found else None
    
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found report file: {file_path}" if file_found else "No output report file found in workspace"
    })
    
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Read content
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        try:
            content = file_path.read_text(encoding="gbk")
        except Exception as e2:
            checks.append({
                "name": "file_readable",
                "passed": False,
                "detail": f"Cannot read file: {e2}"
            })
            return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "file_readable",
        "passed": True,
        "detail": f"File read successfully, length: {len(content)} chars"
    })
    
    # Check 2: 会议主题 section present
    has_meeting_topic = bool(re.search(r'会议主题', content))
    checks.append({
        "name": "section_meeting_topic",
        "passed": has_meeting_topic,
        "detail": "Contains '会议主题' section" if has_meeting_topic else "Missing '会议主题' section"
    })
    
    # Check 3: 主要矛盾分析 section with Mao's perspective
    has_contradiction_analysis = bool(re.search(r'主要矛盾', content))
    has_mao_section = bool(re.search(r'毛主席|毛泽东', content))
    passed_contradiction = has_contradiction_analysis and has_mao_section
    checks.append({
        "name": "section_main_contradiction_analysis",
        "passed": passed_contradiction,
        "detail": f"Has '主要矛盾': {has_contradiction_analysis}, Has Mao reference: {has_mao_section}"
    })
    
    # Check 4: All 4 emperors present with their sections
    emperor_checks = {
        "秦始皇": ["制度", "法", "书同文", "车同轨", "令行禁止", "标准", "法度"],
        "汉武帝": ["战略", "出击", "主动", "扩张", "布局", "强汉", "寇可往"],
        "唐太宗": ["纳谏", "用人", "兼听", "水能载舟", "干部", "以人为镜", "德才"],
        "朱元璋": ["布衣", "民间", "群众", "贪", "民心", "咱", "一线"],
    }
    
    emperor_presence_results = {}
    for emperor, keywords in emperor_checks.items():
        has_emperor = emperor in content
        has_keywords = any(kw in content for kw in keywords)
        emperor_presence_results[emperor] = has_emperor and has_keywords
    
    all_emperors_present = all(emperor_presence_results.values())
    checks.append({
        "name": "all_four_emperors_present",
        "passed": all_emperors_present,
        "detail": f"Emperor presence: {emperor_presence_results}"
    })
    
    # Check 5: Each emperor uses their domain framing
    # 秦始皇 must address 制度建设/中央集权/标准化
    qin_domain = bool(re.search(r'秦始皇', content)) and any(kw in content for kw in ["制度", "标准", "法度", "规范", "机制建设"])
    checks.append({
        "name": "qin_shihuang_domain_content",
        "passed": qin_domain,
        "detail": "秦始皇 addresses 制度建设 domain" if qin_domain else "秦始皇 missing domain-specific 制度建设 content"
    })
    
    # 汉武帝 must address 对外战略/扩张
    han_domain = bool(re.search(r'汉武帝', content)) and any(kw in content for kw in ["战略", "主动", "出击", "扩张", "布局", "进攻", "主动权"])
    checks.append({
        "name": "han_wudi_domain_content",
        "passed": han_domain,
        "detail": "汉武帝 addresses 对外战略 domain" if han_domain else "汉武帝 missing domain-specific 对外战略 content"
    })
    
    # 唐太宗 must address 用人/团队建设
    tang_domain = bool(re.search(r'唐太宗', content)) and any(kw in content for kw in ["用人", "纳谏", "人才", "团队", "干部", "兼听"])
    checks.append({
        "name": "tang_taizong_domain_content",
        "passed": tang_domain,
        "detail": "唐太宗 addresses 用人纳谏 domain" if tang_domain else "唐太宗 missing domain-specific 用人纳谏 content"
    })
    
    # 朱元璋 must address 群众/基层
    zhu_domain = bool(re.search(r'朱元璋', content)) and any(kw in content for kw in ["群众", "民间", "基层", "民心", "一线", "布衣", "动员"])
    checks.append({
        "name": "zhu_yuanzhang_domain_content",
        "passed": zhu_domain,
        "detail": "朱元璋 addresses 群众动员 domain" if zhu_domain else "朱元璋 missing domain-specific 群众动员 content"
    })
    
    # Check 6: 统一决策 section exists and assigns tasks to named emperors
    has_unified_decision = bool(re.search(r'统一决策', content))
    # Must assign responsibility to at least 2 named emperors
    assignment_pattern = re.findall(r'(秦始皇|汉武帝|唐太宗|朱元璋).{0,20}(负责|主导|承担|执行|牵头)', content)
    has_emperor_assignments = len(assignment_pattern) >= 2
    
    # Alternative: emperors mentioned in context of execution
    if not has_emperor_assignments:
        # Check if emperor names appear near action words
        action_context = re.findall(r'(秦始皇|汉武帝|唐太宗|朱元璋).{0,50}(方案|建议|计划|措施)', content)
        has_emperor_assignments = len(action_context) >= 2
    
    unified_decision_ok = has_unified_decision and has_emperor_assignments
    checks.append({
        "name": "unified_decision_section",
        "passed": unified_decision_ok,
        "detail": f"Has '统一决策': {has_unified_decision}, Emperor assignments found: {len(assignment_pattern)}"
    })
    
    # Check 7: 执行计划 section with phases
    has_execution_plan = bool(re.search(r'执行计划', content))
    # Must have phased approach (阶段 or phases)
    has_phases = bool(re.search(r'阶段\s*[1一1-9]|第[一二三四1-9]阶段|Phase\s*[1-9]', content))
    if not has_phases:
        # Check for month-based phases
        has_phases = bool(re.search(r'第[1-9一二三]个?月|[1-9]-[0-9]+月|月[份]?[:：]', content))
    execution_ok = has_execution_plan and has_phases
    checks.append({
        "name": "execution_plan_with_phases",
        "passed": execution_ok,
        "detail": f"Has '执行计划': {has_execution_plan}, Has phased approach: {has_phases}"
    })
    
    # Check 8: 实践检验标准 section with quantitative metrics
    has_practice_standard = bool(re.search(r'实践检验|检验标准|衡量标准|验收标准', content))
    # Must have quantitative metrics (% or numbers)
    has_quantitative = bool(re.search(r'\d+\s*[%％]|\d+\s*(个|家|人|倍|万|亿|点)', content))
    
    # Also check if content contains numeric targets even without % symbol
    if not has_quantitative:
        has_quantitative = bool(re.search(r'提升\s*\d+|达到\s*\d+|增长\s*\d+|超过\s*\d+', content))
    
    practice_standard_ok = has_practice_standard and has_quantitative
    checks.append({
        "name": "practice_verification_standard_with_metrics",
        "passed": practice_standard_ok,
        "detail": f"Has '实践检验标准': {has_practice_standard}, Has quantitative metrics: {has_quantitative}"
    })
    
    # Check 9: Content addresses the specific problem (international expansion)
    addresses_problem = any(kw in content for kw in ["国际", "出海", "海外", "东南亚", "欧美", "扩张", "全球"])
    checks.append({
        "name": "addresses_internationalization_problem",
        "passed": addresses_problem,
        "detail": "Content addresses the international expansion problem" if addresses_problem else "Content does not address the specific internationalization problem"
    })
    
    # Check 10: Main contradiction correctly identified (primary vs secondary)
    has_primary_contradiction = bool(re.search(r'主要矛盾.{0,100}(产品|市场|时机|速度|资源)', content)) or \
                                 bool(re.search(r'(产品|市场|时机|速度|资源).{0,100}主要矛盾', content))
    has_secondary_contradiction = bool(re.search(r'次要矛盾', content))
    contradiction_depth_ok = has_primary_contradiction
    checks.append({
        "name": "contradiction_analysis_depth",
        "passed": contradiction_depth_ok,
        "detail": f"Has specific primary contradiction: {has_primary_contradiction}, Has secondary contradiction: {has_secondary_contradiction}"
    })
    
    # Check 11: Chinese language dominance (must be primarily in Chinese)
    # Count Chinese characters vs total
    chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
    is_chinese = chinese_chars > 200  # At least 200 Chinese chars
    checks.append({
        "name": "chinese_language_requirement",
        "passed": is_chinese,
        "detail": f"Chinese character count: {chinese_chars} (need >200)"
    })
    
    # ── Scoring ──────────────────────────────────────────────────────────────
    critical_checks = [
        "output_file_exists",
        "all_four_emperors_present",
        "section_main_contradiction_analysis",
        "unified_decision_section",
        "execution_plan_with_phases",
        "practice_verification_standard_with_metrics",
    ]
    
    standard_checks = [
        "section_meeting_topic",
        "qin_shihuang_domain_content",
        "han_wudi_domain_content",
        "tang_taizong_domain_content",
        "zhu_yuanzhang_domain_content",
        "addresses_internationalization_problem",
        "contradiction_analysis_depth",
        "chinese_language_requirement",
    ]
    
    critical_weight = 0.7
    standard_weight = 0.3
    
    check_map = {c["name"]: c["passed"] for c in checks}
    
    critical_passed = sum(1 for c in critical_checks if check_map.get(c, False))
    standard_passed = sum(1 for c in standard_checks if check_map.get(c, False))
    
    critical_score = (critical_passed / len(critical_checks)) * critical_weight
    standard_score = (standard_passed / len(standard_checks)) * standard_weight
    
    total_score = round(critical_score + standard_score, 3)
    
    # Must pass ALL critical checks to pass overall
    all_critical_passed = all(check_map.get(c, False) for c in critical_checks)
    overall_passed = all_critical_passed and total_score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))