import sys
import json
import re
from pathlib import Path

def find_output_file(workspace):
    """Find the solution document."""
    candidates = list(Path(workspace).rglob("师生共创挑战应对方案*"))
    if not candidates:
        # Try common variations
        candidates = list(Path(workspace).rglob("challenge_solution*"))
    if not candidates:
        candidates = list(Path(workspace).rglob("solution_report*"))
    return candidates[0] if candidates else None

def read_file(path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        try:
            return path.read_text(encoding="gbk")
        except Exception:
            return ""

def check_five_sections(content):
    """Check that the document contains all 5 required sections."""
    required = [
        (r"(核心挑战诊断|挑战诊断|现状诊断)", "Section 1: 挑战诊断"),
        (r"(挑战优先级|优先级排序|优先级)", "Section 2: 优先级排序"),
        (r"(解决方案|针对性解决|应对方案)", "Section 3: 解决方案"),
        (r"(实施时间线|时间线|里程碑)", "Section 4: 时间线与里程碑"),
        (r"(风险预案|风险应对|风险)", "Section 5: 风险预案"),
    ]
    results = []
    for pattern, name in required:
        found = bool(re.search(pattern, content))
        results.append((name, found))
    return results

def check_three_challenges_identified(content):
    """Check all three core challenges are identified."""
    checks = [
        (r"(主导权|角色分工|决策权|谁来主导)", "挑战一：主导权冲突"),
        (r"(技术落地|产品化|TRL|技术成熟|死亡之谷|量产)", "挑战二：技术落地"),
        (r"(市场匹配|供需错配|市场教育|应用场景|找不到客户)", "挑战三：技术市场匹配"),
    ]
    results = []
    for pattern, name in checks:
        found = bool(re.search(pattern, content))
        results.append((name, found))
    return results

def check_trl_assessment(content):
    """
    Check TRL assessment is applied correctly.
    Based on raw notes: system prototype + field validation in small hospital environment = TRL 6-7.
    The document should reference TRL 6 or 7 (现场验证/系统原型).
    CRITICAL: Since TRL < 7 threshold is ambiguous, we check that TRL is mentioned in context of productization.
    """
    trl_mentioned = bool(re.search(r"TRL\s*[0-9]", content))
    # Should NOT say "TRL 8-9" since yield is only 40% and no paid customers
    trl_89_premature = bool(re.search(r"TRL\s*[89]", content))
    # Should reference TRL 6 or 7 based on the evidence
    trl_67 = bool(re.search(r"TRL\s*[67]", content))
    return trl_mentioned, trl_67, trl_89_premature

def check_leadership_stage(content):
    """
    Check leadership/主导权 recommendations align with SKILL.md dynamic adjustment rules.
    - Team is 15 months old → in 12-24 month range = 学生主导 (growth/productization stage)
    - BUT: TRL not yet at 7+ clearly, no paid customers yet
    - The skill says: 成长期(12-24个月) → 学生主导
    - Trigger signals: TRL 7+, paid customers, team >20 people
    - Team is 15 months in → transition toward 学生主导 or already there
    The document should recommend student-led / 赵晨 taking more operational control.
    """
    student_lead = bool(re.search(r"(学生主导|赵晨.*主导|运营.*学生|学生.*运营决策|CEO.*决策|赵晨.*决策权)", content))
    dynamic_adjust = bool(re.search(r"(动态调整|阶段.*主导|成长期|12.*24|15个月)", content))
    return student_lead, dynamic_adjust

def check_communication_mechanism(content):
    """
    Check that a communication mechanism is proposed with at least weekly meetings.
    The SKILL.md specifies: 日常/周例会/战略对齐/冲突调解 — four levels.
    """
    weekly = bool(re.search(r"(周例会|每周.*会|weekly)", content, re.IGNORECASE))
    monthly = bool(re.search(r"(战略对齐|月.*会|每月.*会|monthly)", content, re.IGNORECASE))
    daily = bool(re.search(r"(日常沟通|每日|即时)", content))
    return weekly, monthly, daily

def check_mvp_cost_philosophy(content):
    """
    Check that the solution addresses the cost problem with the SKILL.md philosophy:
    80% performance + 50% cost > 100% performance + 100% cost
    Or at minimum, addresses the iterative productization approach (MVP first).
    """
    mvp = bool(re.search(r"(MVP|最小可行|先做能用|渐进|逐步迭代)", content))
    cost_perf_balance = bool(re.search(r"(成本.*性能|性能.*成本|80%|平衡.*技术|技术.*平衡)", content))
    return mvp, cost_perf_balance

def check_market_education(content):
    """
    Check market education strategy is included.
    Should mention 认知建立/信任建立/需求激发 or similar 3-stage approach.
    """
    stage1 = bool(re.search(r"(认知建立|让.*知道|行业会议|媒体报道)", content))
    stage2 = bool(re.search(r"(信任建立|标杆案例|试用|让.*相信)", content))
    stage3 = bool(re.search(r"(需求激发|ROI|购买意愿|让.*产生)", content))
    return stage1, stage2, stage3

def check_priority_ordering(content):
    """
    The document should prioritize challenges. Given the situation:
    - Decision conflict is IMMEDIATELY blocking (lost 2 clients, 3 delays in 6 months)
    - Technology productization is critical (cost 2.4x target, 40% yield)
    - Market matching is important but secondary
    The ordering should reflect urgency. Check that 主导权 is mentioned first or as highest priority.
    """
    # Look for numbered priority or explicit priority-1 mention of leadership
    priority_leadership = bool(re.search(r"(优先.*主导|主导.*优先|第一.*挑战|挑战一.*首要|最紧迫.*主导|主导.*最紧迫|1.*主导权|主导权.*1)", content))
    has_ordering = bool(re.search(r"(优先级|排序|第[一二三]|首要|其次|最后)", content))
    return priority_leadership, has_ordering

def check_paid_customer_urgency(content):
    """
    Investment requires paid customer before Pre-A (3-4 months).
    Document should address this urgency — linking to the checklist item about willingness to pay.
    """
    return bool(re.search(r"(付费客户|Pre-A|融资.*客户|客户.*付费|3.*4.*个月|投资.*条件)", content))

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    checks = []
    total_score = 0.0
    
    # Find output file
    output_file = find_output_file(workspace)
    
    file_found = output_file is not None
    checks.append({
        "name": "输出文件存在 (《师生共创挑战应对方案》)",
        "passed": file_found,
        "detail": f"Found: {output_file}" if file_found else "No matching file found. Expected filename containing '师生共创挑战应对方案'"
    })
    
    if not file_found:
        # Try any .txt or .md files that might be the answer
        all_txt = list(Path(workspace).rglob("*.txt")) + list(Path(workspace).rglob("*.md"))
        non_distractor = [f for f in all_txt if f.name not in [
            "budget_draft.txt", "meeting_log.txt", "annual_summary.txt", "ip_register.txt",
            "headcount.txt", "cashflow.txt", "trl_notes.txt", "concept.txt", 
            "spec_v0.1.txt", "random_links.txt", "old_plan.txt", "raw_interview_notes.txt"
        ]]
        if non_distractor:
            output_file = non_distractor[0]
            checks[-1]["passed"] = False
            checks[-1]["detail"] = f"No correctly named file, but found possible output at: {output_file}"
    
    if output_file is None:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result, ensure_ascii=False))
        return
    
    content = read_file(output_file)
    
    if len(content) < 200:
        checks.append({
            "name": "文档内容充实",
            "passed": False,
            "detail": f"Document too short: {len(content)} chars"
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return
    
    checks.append({
        "name": "文档内容充实",
        "passed": True,
        "detail": f"Document length: {len(content)} chars"
    })
    total_score += 0.5
    
    # Check 1: Five required sections
    section_results = check_five_sections(content)
    sections_passed = sum(1 for _, p in section_results if p)
    all_sections = sections_passed == 5
    checks.append({
        "name": "包含五大必要章节",
        "passed": all_sections,
        "detail": f"{sections_passed}/5 sections found: " + ", ".join(f"{n}={'✓' if p else '✗'}" for n, p in section_results)
    })
    if all_sections:
        total_score += 1.5
    elif sections_passed >= 4:
        total_score += 0.75
    elif sections_passed >= 3:
        total_score += 0.4
    
    # Check 2: Three challenges identified
    challenge_results = check_three_challenges_identified(content)
    challenges_passed = sum(1 for _, p in challenge_results if p)
    all_challenges = challenges_passed == 3
    checks.append({
        "name": "识别三大核心挑战",
        "passed": all_challenges,
        "detail": f"{challenges_passed}/3 challenges identified: " + ", ".join(f"{n}={'✓' if p else '✗'}" for n, p in challenge_results)
    })
    if all_challenges:
        total_score += 1.5
    elif challenges_passed >= 2:
        total_score += 0.75
    
    # Check 3: TRL Assessment applied correctly
    trl_mentioned, trl_67, trl_89_premature = check_trl_assessment(content)
    trl_correct = trl_mentioned and trl_67 and not trl_89_premature
    checks.append({
        "name": "正确应用TRL评估（TRL 6-7，非TRL 8-9）",
        "passed": trl_correct,
        "detail": f"TRL mentioned: {trl_mentioned}, TRL 6-7 referenced: {trl_67}, Premature TRL 8-9: {trl_89_premature}"
    })
    if trl_correct:
        total_score += 1.0
    elif trl_mentioned and not trl_89_premature:
        total_score += 0.3
    
    # Check 4: Leadership dynamic adjustment
    student_lead, dynamic_adjust = check_leadership_stage(content)
    leadership_correct = student_lead or dynamic_adjust
    checks.append({
        "name": "动态主导权调整（15个月→成长期→学生/CEO主导运营）",
        "passed": leadership_correct,
        "detail": f"Student/CEO lead recommended: {student_lead}, Dynamic adjustment mentioned: {dynamic_adjust}"
    })
    if leadership_correct:
        total_score += 1.0
    
    # Check 5: Communication mechanism with all 4 levels
    weekly, monthly, daily = check_communication_mechanism(content)
    comm_complete = weekly and monthly
    comm_partial = weekly or monthly
    checks.append({
        "name": "建立沟通机制（至少包含周例会+战略对齐会）",
        "passed": comm_complete,
        "detail": f"Daily comm: {daily}, Weekly meeting: {weekly}, Monthly strategic: {monthly}"
    })
    if comm_complete:
        total_score += 0.8
    elif comm_partial:
        total_score += 0.3
    
    # Check 6: MVP / Cost-performance philosophy
    mvp, cost_perf = check_mvp_cost_philosophy(content)
    productization_addressed = mvp or cost_perf
    checks.append({
        "name": "渐进式产品化策略（MVP优先/成本性能平衡）",
        "passed": productization_addressed,
        "detail": f"MVP approach: {mvp}, Cost-performance balance: {cost_perf}"
    })
    if mvp and cost_perf:
        total_score += 0.8
    elif productization_addressed:
        total_score += 0.4
    
    # Check 7: Market education strategy
    stage1, stage2, stage3 = check_market_education(content)
    market_edu_complete = stage1 and stage2 and stage3
    market_edu_partial = sum([stage1, stage2, stage3]) >= 2
    checks.append({
        "name": "市场教育三步走（认知建立→信任建立→需求激发）",
        "passed": market_edu_complete,
        "detail": f"Stage1认知建立: {stage1}, Stage2信任建立: {stage2}, Stage3需求激发: {stage3}"
    })
    if market_edu_complete:
        total_score += 0.8
    elif market_edu_partial:
        total_score += 0.4
    
    # Check 8: Priority ordering (leadership conflict first)
    priority_leadership, has_ordering = check_priority_ordering(content)
    checks.append({
        "name": "优先级排序（主导权冲突为首要挑战）",
        "passed": priority_leadership and has_ordering,
        "detail": f"Has priority ordering: {has_ordering}, Leadership listed as top priority: {priority_leadership}"
    })
    if priority_leadership and has_ordering:
        total_score += 0.8
    elif has_ordering:
        total_score += 0.3
    
    # Check 9: Urgency of paid customer for Pre-A
    paid_customer = check_paid_customer_urgency(content)
    checks.append({
        "name": "回应Pre-A融资条件（3-4个月内获得付费客户）",
        "passed": paid_customer,
        "detail": f"Pre-A / paid customer urgency addressed: {paid_customer}"
    })
    if paid_customer:
        total_score += 0.8
    
    # Normalize score to 0-10
    max_possible = 0.5 + 1.5 + 1.5 + 1.0 + 1.0 + 0.8 + 0.8 + 0.8 + 0.8 + 0.8
    normalized_score = min(10.0, round((total_score / max_possible) * 10, 2))
    
    all_critical = (
        file_found and
        all_sections and
        all_challenges and
        trl_correct and
        leadership_correct and
        comm_complete
    )
    
    result = {
        "passed": normalized_score >= 6.0,
        "score": normalized_score,
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()