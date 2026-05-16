import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Find the output file
    target_file = None
    candidates = list(Path(workspace_dir).rglob("资源对接方案*")) + \
                 list(Path(workspace_dir).rglob("*资源对接方案*")) + \
                 list(Path(workspace_dir).rglob("resource_plan*")) + \
                 list(Path(workspace_dir).rglob("*docking_plan*")) + \
                 list(Path(workspace_dir).rglob("*对接方案*"))
    
    # Also check for JSON specifically
    json_candidates = list(Path(workspace_dir).rglob("resource_docking_plan.json")) + \
                      list(Path(workspace_dir).rglob("资源对接方案.json")) + \
                      list(Path(workspace_dir).rglob("docking_plan.json"))
    
    all_candidates = json_candidates + candidates
    
    if not all_candidates:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "No resource docking plan file found in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    target_file = all_candidates[0]
    checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found file: {target_file}"})
    
    # Read the file
    try:
        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "file_readable", "passed": True, "detail": "File read successfully"})
    
    # Try to parse as JSON
    plan_data = None
    is_json = False
    try:
        plan_data = json.loads(content)
        is_json = True
    except:
        plan_data = content  # treat as text
    
    # CHECK 1: Must contain all 5 required sections from SKILL.md
    # 1. 已有资源盘点 2. 待对接资源清单 3. 对接优先级排序 4. 对接行动计划 5. 资源整合策略
    required_sections = [
        ("已有资源盘点", ["已有资源", "现有资源", "current_resources", "existing_resources"]),
        ("待对接资源清单", ["待对接", "需要对接", "pending_resources", "resources_needed", "target_resources"]),
        ("对接优先级排序", ["优先级", "priority", "priorities", "排序"]),
        ("对接行动计划", ["行动计划", "action_plan", "时间表", "timeline", "责任人"]),
        ("资源整合策略", ["整合策略", "integration_strategy", "整合", "策略"]),
    ]
    
    section_score = 0
    for section_name, keywords in required_sections:
        found = False
        if is_json:
            # Check JSON keys
            content_str = json.dumps(plan_data, ensure_ascii=False).lower()
            for kw in keywords + [section_name]:
                if kw.lower() in content_str:
                    found = True
                    break
        else:
            for kw in keywords + [section_name]:
                if kw.lower() in content.lower():
                    found = True
                    break
        checks.append({
            "name": f"section_{section_name}",
            "passed": found,
            "detail": f"Section '{section_name}' {'found' if found else 'NOT FOUND'} in output"
        })
        if found:
            section_score += 1
    
    # CHECK 2: 3-tier ecosystem coverage (大学/平台/社会)
    tier_keywords = {
        "university_tier": ["大学层面", "大学支持", "学校", "university", "校内", "教务处", "人事处", "院系"],
        "platform_tier": ["平台层面", "x-lab", "xlab", "清华", "孵化", "平台", "platform", "驻校企业家", "EiR"],
        "social_tier": ["社会层面", "投资", "产业", "政府", "social", "investor", "government", "补贴"],
    }
    
    tier_score = 0
    for tier_name, keywords in tier_keywords.items():
        found = any(kw.lower() in content.lower() for kw in keywords)
        checks.append({
            "name": f"tier_{tier_name}",
            "passed": found,
            "detail": f"Tier '{tier_name}' {'covered' if found else 'NOT COVERED'}"
        })
        if found:
            tier_score += 1
    
    # CHECK 3: Specific proprietary details from SKILL.md
    
    # 3a: EiR / 驻校企业家 concept from x-lab (very specific to SKILL.md)
    eir_found = any(kw.lower() in content.lower() for kw in ["驻校企业家", "EiR", "eir", "Entrepreneur in Residence"])
    checks.append({
        "name": "proprietary_eir_concept",
        "passed": eir_found,
        "detail": f"EiR/驻校企业家 concept {'found' if eir_found else 'NOT FOUND'} - this is proprietary to x-lab section of SKILL.md"
    })
    
    # 3b: Teacher entrepreneurship policy - 保留教职 (specific policy)
    teacher_policy_found = any(kw.lower() in content.lower() for kw in ["保留教职", "职称评审", "教师创业", "人事处"])
    checks.append({
        "name": "proprietary_teacher_policy",
        "passed": teacher_policy_found,
        "detail": f"Teacher entrepreneurship policy (保留教职/职称评审) {'found' if teacher_policy_found else 'NOT FOUND'}"
    })
    
    # 3c: Student policy - 学分认定 or 保留学籍
    student_policy_found = any(kw.lower() in content.lower() for kw in ["学分认定", "保留学籍", "学籍管理", "学分", "教务处"])
    checks.append({
        "name": "proprietary_student_policy",
        "passed": student_policy_found,
        "detail": f"Student policy (学分认定/保留学籍) {'found' if student_policy_found else 'NOT FOUND'}"
    })
    
    # 3d: 科技成果转化 policy (IP/tech transfer specific to SKILL.md)
    ip_policy_found = any(kw.lower() in content.lower() for kw in ["成果转化", "科技成果", "成果归属", "收益分配", "技术转让"])
    checks.append({
        "name": "proprietary_ip_policy",
        "passed": ip_policy_found,
        "detail": f"Tech transfer/IP policy (成果转化/收益分配) {'found' if ip_policy_found else 'NOT FOUND'}"
    })
    
    # 3e: Investment stage matching - 天使投资人 for 种子期 (from investment table)
    investment_stage_found = any(kw.lower() in content.lower() for kw in ["天使投资", "种子期", "早期VC", "天使轮"])
    checks.append({
        "name": "proprietary_investment_stages",
        "passed": investment_stage_found,
        "detail": f"Investment stage mapping (天使投资/种子期) {'found' if investment_stage_found else 'NOT FOUND'}"
    })
    
    # CHECK 4: Action plan must include timeline/schedule and responsible party
    timeline_found = any(kw.lower() in content.lower() for kw in 
                         ["时间", "timeline", "时间表", "4月", "月", "周", "week", "month", "schedule", "Q1", "Q2"])
    responsibility_found = any(kw.lower() in content.lower() for kw in 
                               ["责任人", "负责人", "responsible", "owner", "张明", "王浩", "李雪", "团队"])
    
    checks.append({
        "name": "action_plan_has_timeline",
        "passed": timeline_found,
        "detail": f"Action plan timeline {'present' if timeline_found else 'MISSING'}"
    })
    checks.append({
        "name": "action_plan_has_responsible_party",
        "passed": responsibility_found,
        "detail": f"Action plan responsible party {'present' if responsibility_found else 'MISSING'}"
    })
    
    # CHECK 5: Industry partner (浙江贝塔医药) is addressed
    pharma_partner_found = any(kw.lower() in content.lower() for kw in 
                               ["浙江贝塔", "beta pharma", "贝塔医药", "产业伙伴", "技术合作", "产业合作"])
    checks.append({
        "name": "pharma_partner_addressed",
        "passed": pharma_partner_found,
        "detail": f"Pharma partner (浙江贝塔医药) or industry partner category {'addressed' if pharma_partner_found else 'NOT ADDRESSED'}"
    })
    
    # CHECK 6: Government subsidies/tax policy mentioned
    gov_support_found = any(kw.lower() in content.lower() for kw in 
                            ["政府", "补贴", "高新", "税收", "人社局", "发改委", "创业补贴", "政策扶持"])
    checks.append({
        "name": "government_support_addressed",
        "passed": gov_support_found,
        "detail": f"Government support/subsidies {'addressed' if gov_support_found else 'NOT ADDRESSED'}"
    })
    
    # CHECK 7: 三创 education framework mentioned (very specific to SKILL.md x-lab section)
    sanchuang_found = any(kw.lower() in content.lower() for kw in ["三创", "创意", "创新", "创业", "证书课程", "创新力提升"])
    checks.append({
        "name": "sanchuang_education_framework",
        "passed": sanchuang_found,
        "detail": f"三创 education framework or x-lab certificate program {'mentioned' if sanchuang_found else 'NOT MENTIONED'}"
    })
    
    # CHECK 8: Priority ordering is present and logical (early stage should prioritize policy/platform)
    priority_found = any(kw.lower() in content.lower() for kw in 
                         ["优先级", "priority", "紧急", "urgent", "首先", "第一", "P1", "高优先", "优先"])
    checks.append({
        "name": "priority_ordering_present",
        "passed": priority_found,
        "detail": f"Priority ordering {'present' if priority_found else 'MISSING'}"
    })
    
    # Calculate score
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks
    
    # Must pass critical checks to pass overall
    critical_checks = [
        "output_file_exists", "file_readable",
        "section_已有资源盘点", "section_待对接资源清单", "section_对接优先级排序",
        "section_对接行动计划", "section_资源整合策略",
        "proprietary_ip_policy",
        "proprietary_teacher_policy",
    ]
    
    critical_passed = all(
        any(c["name"] == cc and c["passed"] for c in checks)
        for cc in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.65
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        workspace_dir = "/workspace"
    else:
        workspace_dir = sys.argv[1]
    
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))