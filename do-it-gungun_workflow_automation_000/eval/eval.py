import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Find the output file
    output_file = None
    possible_names = ["decision_report.md", "case_002_output.md", "gungun_decision.md", 
                      "do_it_report.md", "career_decision_report.md"]
    
    # Search for any .md file that looks like the output
    for f in Path(workspace_dir).rglob("*.md"):
        try:
            content = f.read_text(encoding="utf-8")
            if "滚滚的判断" in content and "do it" in content.lower():
                output_file = f
                break
        except Exception:
            continue
    
    if output_file is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_found", "passed": False, 
                        "detail": "No output markdown file found containing '滚滚的判断'"}]
        }
    
    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_readable", "passed": False, 
                        "detail": f"Could not read output file: {e}"}]
        }
    
    # Check 1: Correct title/header
    check1_passed = bool(re.search(r'#\s*🌪️\s*do it\s*-\s*滚滚的判断', content))
    checks.append({
        "name": "correct_title_header",
        "passed": check1_passed,
        "detail": f"Output must start with '# 🌪️ do it - 滚滚的判断'. Found: {'YES' if check1_passed else 'NO'}"
    })
    
    # Check 2: Problem restatement section
    check2_passed = bool(re.search(r'##\s*你的问题', content))
    checks.append({
        "name": "problem_restatement_section",
        "passed": check2_passed,
        "detail": f"'## 你的问题' section present: {'YES' if check2_passed else 'NO'}"
    })
    
    # Check 3: All 4 analyst agents present (1-4号滚滚)
    analyst_checks = []
    for i in range(1, 5):
        analyst_present = bool(re.search(rf'{i}\s*号滚滚', content))
        analyst_checks.append(analyst_present)
    
    # Verify roles
    check3a = analyst_checks[0] and bool(re.search(r'首席判断官', content))
    check3b = analyst_checks[1] and bool(re.search(r'业务分析师', content))
    check3c = analyst_checks[2] and bool(re.search(r'数据分析师', content))
    check3d = analyst_checks[3] and bool(re.search(r'情报分析师', content))
    check3_passed = all([check3a, check3b, check3c, check3d])
    checks.append({
        "name": "all_four_analysts_with_roles",
        "passed": check3_passed,
        "detail": f"1号(首席判断官):{check3a}, 2号(业务分析师):{check3b}, 3号(数据分析师):{check3c}, 4号(情报分析师):{check3d}"
    })
    
    # Check 4: Debate section with 5号 and 6号
    check4_debate_header = bool(re.search(r'##\s*💬\s*辩论环节', content))
    check4_5hao = bool(re.search(r'5\s*号滚滚', content)) and bool(re.search(r'乐观研究员', content))
    check4_6hao = bool(re.search(r'6\s*号滚滚', content)) and bool(re.search(r'保守研究员', content))
    check4_bull = bool(re.search(r'🐂', content))
    check4_bear = bool(re.search(r'🐻', content))
    check4_passed = all([check4_debate_header, check4_5hao, check4_6hao, check4_bull, check4_bear])
    checks.append({
        "name": "debate_section_with_5_and_6",
        "passed": check4_passed,
        "detail": f"辩论环节:{check4_debate_header}, 5号乐观🐂:{check4_5hao and check4_bull}, 6号保守🐻:{check4_6hao and check4_bear}"
    })
    
    # Check 5: 5号 has at least 3 numbered support points
    five_section_match = re.search(r'5\s*号滚滚.*?(?=6\s*号滚滚|##)', content, re.DOTALL)
    if five_section_match:
        five_content = five_section_match.group()
        five_points = re.findall(r'^\s*[123456789]\d*[\.\)]\s*.+', five_content, re.MULTILINE)
        check5_passed = len(five_points) >= 3
        check5_detail = f"5号提出了 {len(five_points)} 个论点 (需要至少3个)"
    else:
        check5_passed = False
        check5_detail = "Could not find 5号 section to count arguments"
    checks.append({
        "name": "five_has_three_plus_arguments",
        "passed": check5_passed,
        "detail": check5_detail
    })
    
    # Check 6: 6号 has at least 3 numbered risk points
    six_section_match = re.search(r'6\s*号滚滚.*?(?=###\s*辩论总结|##\s*🎯)', content, re.DOTALL)
    if six_section_match:
        six_content = six_section_match.group()
        six_points = re.findall(r'^\s*[123456789]\d*[\.\)]\s*.+', six_content, re.MULTILINE)
        check6_passed = len(six_points) >= 3
        check6_detail = f"6号提出了 {len(six_points)} 个风险点 (需要至少3个)"
    else:
        check6_passed = False
        check6_detail = "Could not find 6号 section to count risk points"
    checks.append({
        "name": "six_has_three_plus_risk_points",
        "passed": check6_passed,
        "detail": check6_detail
    })
    
    # Check 7: Debate summary with 共识点 AND 分歧点
    check7_consensus = bool(re.search(r'共识点', content))
    check7_divergence = bool(re.search(r'分歧点', content))
    check7_passed = check7_consensus and check7_divergence
    checks.append({
        "name": "debate_summary_consensus_and_divergence",
        "passed": check7_passed,
        "detail": f"共识点:{check7_consensus}, 分歧点:{check7_divergence}"
    })
    
    # Check 8: Decision section with 7, 8, 9号
    check8_7 = bool(re.search(r'7\s*号滚滚', content)) and bool(re.search(r'首席决策官', content))
    check8_8 = bool(re.search(r'8\s*号滚滚', content)) and bool(re.search(r'策略规划师', content))
    check8_9 = bool(re.search(r'9\s*号滚滚', content)) and bool(re.search(r'风险评估师', content))
    # Also accept decision section even if 7/8/9 are referenced in the decision section
    check8_decision = bool(re.search(r'##\s*🎯\s*滚滚的决策', content))
    check8_recommend = bool(re.search(r'✅\s*推荐选择', content))
    check8_core_logic = bool(re.search(r'核心逻辑', content))
    check8_passed = check8_decision and check8_recommend and check8_core_logic
    checks.append({
        "name": "decision_section_structure",
        "passed": check8_passed,
        "detail": f"决策section:{check8_decision}, 推荐选择:{check8_recommend}, 核心逻辑:{check8_core_logic}"
    })
    
    # Check 9: Execution plan with checkbox format in 3 time horizons
    check9_plan = bool(re.search(r'##\s*📋\s*执行计划', content))
    check9_week = bool(re.search(r'第一步.*本周', content, re.DOTALL)) or bool(re.search(r'本周', content))
    check9_month = bool(re.search(r'本月', content))
    check9_3months = bool(re.search(r'3\s*个月', content))
    # Check for checkbox format
    checkboxes = re.findall(r'- \[ \]', content)
    check9_checkbox = len(checkboxes) >= 3
    check9_passed = check9_plan and check9_week and check9_month and check9_3months and check9_checkbox
    checks.append({
        "name": "execution_plan_with_checkboxes_and_three_horizons",
        "passed": check9_passed,
        "detail": f"执行计划:{check9_plan}, 本周:{check9_week}, 本月:{check9_month}, 3个月:{check9_3months}, checkboxes(≥3):{check9_checkbox}({len(checkboxes)}个)"
    })
    
    # Check 10: Risk assessment section
    check10_risk = bool(re.search(r'##\s*⚠️\s*风险评估', content))
    check10_problem = bool(re.search(r'可能遇到的问题', content))
    check10_solution = bool(re.search(r'应对方案', content))
    check10_passed = check10_risk and check10_problem and check10_solution
    checks.append({
        "name": "risk_assessment_section",
        "passed": check10_passed,
        "detail": f"风险评估:{check10_risk}, 可能遇到的问题:{check10_problem}, 应对方案:{check10_solution}"
    })
    
    # Check 11: Emotional support section
    check11_passed = bool(re.search(r'##\s*💚\s*滚滚的话', content))
    checks.append({
        "name": "emotional_support_section",
        "passed": check11_passed,
        "detail": f"'## 💚 滚滚的话' section present: {'YES' if check11_passed else 'NO'}"
    })
    
    # Check 12: 参与滚滚 roster section with all 4 teams
    check12_section = bool(re.search(r'##\s*📊\s*参与滚滚', content))
    check12_analysts = bool(re.search(r'分析师.*1\s*号.*2\s*号.*3\s*号.*4\s*号', content, re.DOTALL)) or \
                       bool(re.search(r'分析师：1 号、2 号、3 号、4 号', content))
    check12_researchers = bool(re.search(r'研究员.*5\s*号.*6\s*号', content, re.DOTALL)) or \
                          bool(re.search(r'研究员：5 号、6 号', content))
    check12_decision = bool(re.search(r'决策.*7\s*号.*8\s*号.*9\s*号', content, re.DOTALL)) or \
                       bool(re.search(r'决策者：7 号、8 号、9 号', content))
    check12_qc = bool(re.search(r'质控.*10\s*号.*11\s*号', content, re.DOTALL)) or \
                 bool(re.search(r'质控：10 号、11 号', content))
    check12_passed = check12_section and check12_analysts and check12_researchers and check12_decision and check12_qc
    checks.append({
        "name": "participation_roster_all_four_teams",
        "passed": check12_passed,
        "detail": f"参与滚滚 section:{check12_section}, 分析师(1-4):{check12_analysts}, 研究员(5-6):{check12_researchers}, 决策者(7-9):{check12_decision}, 质控(10-11):{check12_qc}"
    })
    
    # Check 13: The case is actually about the right topic (字节跳动 / AI startup / career)
    check13_bytedance = bool(re.search(r'字节跳动|ByteDance', content, re.IGNORECASE))
    check13_startup = bool(re.search(r'创业|明日 AI|AI.*公司|startup', content, re.IGNORECASE))
    check13_passed = check13_bytedance or check13_startup
    checks.append({
        "name": "content_addresses_correct_case",
        "passed": check13_passed,
        "detail": f"Report addresses the correct case (字节跳动/AI startup). Found: 字节跳动={check13_bytedance}, 创业/AI={check13_startup}"
    })
    
    # Calculate score
    passed_count = sum(1 for c in checks if c["passed"])
    total_count = len(checks)
    score = passed_count / total_count
    
    # Overall pass: must pass at least 10 out of 13 checks, and specifically must pass checks 3, 4, 8, 9, 12
    critical_checks = ["all_four_analysts_with_roles", "debate_section_with_5_and_6", 
                       "decision_section_structure", "execution_plan_with_checkboxes_and_three_horizons",
                       "participation_roster_all_four_teams"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and passed_count >= 10
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    workspace_dir = sys.argv[1]
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))