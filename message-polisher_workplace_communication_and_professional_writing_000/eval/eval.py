import sys
import json
import re
from pathlib import Path

def run_checks(workspace: str):
    checks = []
    score = 0.0

    # Find the output file
    output_file = None
    candidates = list(Path(workspace).rglob("polished_communication.md"))
    if candidates:
        output_file = candidates[0]

    # Check 0: File exists
    file_exists = output_file is not None and output_file.exists()
    checks.append({
        "name": "output_file_exists",
        "passed": file_exists,
        "detail": f"Found polished_communication.md at {output_file}" if file_exists else "polished_communication.md not found anywhere in workspace"
    })
    if not file_exists:
        return checks, 0.0

    try:
        content = output_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": str(e)})
        return checks, 0.0

    checks.append({"name": "file_readable", "passed": True, "detail": f"File size: {len(content)} chars"})

    # Check 1: Section 1 present - 核心诉求与风险诊断
    section1_present = bool(re.search(r'核心诉求.*风险诊断|1\s*[.．。].*🔍|🔍.*核心诉求', content))
    checks.append({
        "name": "section1_diagnosis_present",
        "passed": section1_present,
        "detail": "Section 1 (核心诉求与风险诊断) found" if section1_present else "Section 1 header missing"
    })
    if section1_present:
        score += 0.5

    # Check 2: All 4 plans present with correct headers
    plan_a = bool(re.search(r'方案\s*A|Plan\s*A', content, re.IGNORECASE))
    plan_b = bool(re.search(r'方案\s*B|Plan\s*B', content, re.IGNORECASE))
    plan_c = bool(re.search(r'方案\s*C|Plan\s*C', content, re.IGNORECASE))
    plan_d = bool(re.search(r'方案\s*D|Plan\s*D', content, re.IGNORECASE))
    all_plans = plan_a and plan_b and plan_c and plan_d

    checks.append({
        "name": "all_four_plans_present",
        "passed": all_plans,
        "detail": f"Plan A:{plan_a}, Plan B:{plan_b}, Plan C:{plan_c}, Plan D:{plan_d}"
    })
    if all_plans:
        score += 1.0

    # Check 3: Plan A has "Yes, and" style (温和协作) - cooperative framing
    plan_a_section = ""
    plan_a_match = re.search(r'方案\s*A.*?(?=方案\s*B|Plan\s*B|$)', content, re.DOTALL | re.IGNORECASE)
    if plan_a_match:
        plan_a_section = plan_a_match.group(0)
    
    # Plan A should be gentle/collaborative - check for cooperative keywords
    plan_a_cooperative = bool(re.search(
        r'共同|一起|我们|协作|理解|支持|沟通|团队|合作|共创|帮助|期待', 
        plan_a_section
    ))
    checks.append({
        "name": "plan_a_cooperative_tone",
        "passed": plan_a_cooperative,
        "detail": "Plan A contains cooperative/gentle framing keywords" if plan_a_cooperative else "Plan A lacks cooperative tone markers"
    })
    if plan_a_cooperative:
        score += 0.5

    # Check 4: Plan B has SBI model elements and deadline/paper trail (留痕意识)
    plan_b_section = ""
    plan_b_match = re.search(r'方案\s*B.*?(?=方案\s*C|Plan\s*C|$)', content, re.DOTALL | re.IGNORECASE)
    if plan_b_match:
        plan_b_section = plan_b_match.group(0)

    # SBI: Situation/Behavior/Impact or equivalent factual+impact structure
    has_sbi_elements = bool(re.search(
        r'SBI|背景|情况|行为|影响|风险|截止|[Dd]eadline|日期|节点|确认|责任|追溯|留存|记录', 
        plan_b_section
    ))
    # Must reference specific deadline or ask for explicit commitment
    has_deadline_commitment = bool(re.search(
        r'[0-9月日]+.*上线|上线.*[0-9月日]+|截止|[Dd]eadline|明确.*时间|时间.*明确|给出.*日期|日期.*确认|承诺|confirm', 
        plan_b_section,
        re.IGNORECASE
    ))
    plan_b_passed = has_sbi_elements and has_deadline_commitment
    checks.append({
        "name": "plan_b_sbi_and_paper_trail",
        "passed": plan_b_passed,
        "detail": f"SBI/factual elements: {has_sbi_elements}, Deadline/commitment ask: {has_deadline_commitment}"
    })
    if plan_b_passed:
        score += 1.0

    # Check 5: Plan C has conclusion-first (金字塔) AND provides 2-3 options with pros/cons
    plan_c_section = ""
    plan_c_match = re.search(r'方案\s*C.*?(?=方案\s*D|Plan\s*D|$)', content, re.DOTALL | re.IGNORECASE)
    if plan_c_match:
        plan_c_section = plan_c_match.group(0)

    # Must have 2-3 distinct options
    option_count = len(re.findall(
        r'选项\s*[一二三1-3①②③]|方案\s*[一二三1-3①②③]|Option\s*[1-3]|[①②③]|建议\s*[一二三]',
        plan_c_section
    ))
    has_multiple_options = option_count >= 2
    
    # Pros/cons or advantages/disadvantages language
    has_pros_cons = bool(re.search(
        r'优点|缺点|风险|代价|好处|劣势|pros|cons|优劣|利弊|影响.*为|为.*影响',
        plan_c_section,
        re.IGNORECASE
    ))
    
    # Conclusion first - should start with the main ask/situation
    has_conclusion_first = bool(re.search(
        r'^.{0,200}(需要您|请您|目前|当前|汇报|风险|决策)',
        plan_c_section,
        re.DOTALL
    ))

    plan_c_passed = has_multiple_options and has_pros_cons
    checks.append({
        "name": "plan_c_pyramid_with_options",
        "passed": plan_c_passed,
        "detail": f"Option count found: {option_count} (need >=2), Has pros/cons: {has_pros_cons}, Conclusion-first structure: {has_conclusion_first}"
    })
    if plan_c_passed:
        score += 1.5

    # Check 6: Plan D is client-facing and does NOT expose internal conflicts
    plan_d_section = ""
    plan_d_match = re.search(r'方案\s*D.*?(?=##\s*3|第三部分|高情商|Why it works|$)', content, re.DOTALL | re.IGNORECASE)
    if plan_d_match:
        plan_d_section = plan_d_match.group(0)

    # Should be professional/empathetic toward client
    has_client_empathy = bool(re.search(
        r'理解|感谢|抱歉|遗憾|重视|承诺|进展|更新|及时|处理|跟进|安心|放心',
        plan_d_section
    ))
    # Must NOT expose internal blame
    exposes_internal = bool(re.search(
        r'李明|后端团队不|开发团队失|工程师.*拖|技术团队.*没有|内部.*争议|同事.*问题',
        plan_d_section
    ))
    # Should have timeline/progress indication for client
    has_timeline_for_client = bool(re.search(
        r'[0-9]+.*[日天内]|本周|近期|尽快|预计|时间|进展|确认.*后|后.*告知',
        plan_d_section
    ))

    plan_d_passed = has_client_empathy and not exposes_internal and has_timeline_for_client
    checks.append({
        "name": "plan_d_client_safe_no_leak",
        "passed": plan_d_passed,
        "detail": f"Client empathy: {has_client_empathy}, Exposes internal (MUST BE FALSE): {exposes_internal}, Has timeline: {has_timeline_for_client}"
    })
    if plan_d_passed:
        score += 1.0

    # Check 7: Section 3 present - 高情商解析
    section3_present = bool(re.search(r'高情商.*解析|Why it works|沟通技巧.*拆解|后续.*Action|3\s*[.．。].*💡|💡', content))
    checks.append({
        "name": "section3_analysis_present",
        "passed": section3_present,
        "detail": "Section 3 (高情商解析) found" if section3_present else "Section 3 (Why it works) missing"
    })
    if section3_present:
        score += 0.5

    # Check 8: Placeholder brackets [ ] are used correctly for fill-in fields
    placeholder_pattern = re.findall(r'\[([^\]]{1,30})\]', content)
    # Filter out markdown checkboxes like [ ] and pure numbers
    real_placeholders = [p for p in placeholder_pattern if p.strip() and not re.match(r'^[xX\s]$', p)]
    has_placeholders = len(real_placeholders) >= 3
    checks.append({
        "name": "placeholder_brackets_used",
        "passed": has_placeholders,
        "detail": f"Found {len(real_placeholders)} placeholders: {real_placeholders[:5]}"
    })
    if has_placeholders:
        score += 0.5

    # Check 9: Uses "我们" more than "你" in rewritten drafts (去情绪化)
    # Count in the plan sections only (not analysis)
    plans_section = ""
    plans_match = re.search(r'方案\s*A.*?(?=##\s*3|高情商解析|Why it works|$)', content, re.DOTALL | re.IGNORECASE)
    if plans_match:
        plans_section = plans_match.group(0)
    
    women_count = len(re.findall(r'我们', plans_section))
    ni_count = len(re.findall(r'(?<![你我他她它])你(?![们的])', plans_section))
    de_emotionalized = women_count >= 2 and women_count >= ni_count
    checks.append({
        "name": "de_emotionalized_language",
        "passed": de_emotionalized,
        "detail": f"'我们' count: {women_count}, '你' (singular accusatory) count: {ni_count}. Need 我们>=2 and 我们>=你"
    })
    if de_emotionalized:
        score += 0.5

    # Normalize score to max 7.0 points -> scale to 1.0
    max_raw_score = 7.0
    final_score = min(round(score / max_raw_score, 4), 1.0)

    return checks, final_score


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_runtime_error", "passed": False, "detail": str(e)}]
        }))
        sys.exit(1)

    # Must pass critical checks to be considered passing overall
    critical_checks = ["output_file_exists", "all_four_plans_present", "plan_b_sbi_and_paper_trail", "plan_c_pyramid_with_options"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and score >= 0.55

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()