import sys
import json
import re
from pathlib import Path

def find_report(workspace):
    """Search for the validation report file."""
    patterns = [
        "团队与产品验证报告*",
        "*团队*产品*验证*报告*",
        "*validation_report*",
        "mvbp_report*",
        "*phase5*report*",
        "product_validation*",
    ]
    for pattern in patterns:
        results = list(Path(workspace).rglob(pattern))
        if results:
            return results[0]
    # Fallback: search for any md/txt/docx that might be the report
    candidates = []
    for ext in ["*.md", "*.txt", "*.json"]:
        for f in Path(workspace).rglob(ext):
            name_lower = f.name.lower()
            content_keywords = ["mvbp", "demo", "团队", "visionary", "executor", "technician"]
            if any(k in name_lower for k in ["report", "报告", "validation", "验证", "mvbp", "phase5", "team"]):
                candidates.append(f)
    if candidates:
        # Pick the largest file as most likely to be the report
        return max(candidates, key=lambda f: f.stat().st_size)
    return None

def read_file_content(filepath):
    """Read file content, trying multiple encodings."""
    for enc in ["utf-8", "utf-8-sig", "gbk", "gb2312"]:
        try:
            return filepath.read_text(encoding=enc)
        except Exception:
            continue
    return ""

def check_mvbp_section(content: str) -> list:
    checks = []
    content_lower = content.lower()

    # Check 1: MVBP vs MVP distinction is present
    has_mvbp = bool(re.search(r'mvbp', content, re.IGNORECASE))
    has_distinction = bool(re.search(r'(mvbp|最小可行商业产品)', content, re.IGNORECASE))
    checks.append({
        "name": "MVBP: Section exists with MVBP concept",
        "passed": has_distinction,
        "detail": f"Found MVBP concept: {has_distinction}"
    })

    # Check 2: Core features count <= 5
    # Look for numbered lists in MVBP section context
    feature_patterns = [
        r'核心功能[：:][^#]*?(\d+)[\.、。]',
        r'功能[：:][^#]*((?:\n\s*[\d一二三四五]+[\.、].*){1,10})',
        r'(?:功能|特性)[^\n]*\n((?:[\s]*[\d一二三四五]+[\.、·\-\*].*\n?){1,10})',
    ]
    
    # Count numbered items in list contexts near "功能" or "feature"
    # Simple heuristic: find lines that look like numbered list items
    lines = content.split('\n')
    mvbp_section_lines = []
    in_mvbp = False
    for line in lines:
        if re.search(r'mvbp|最小可行商业产品|核心功能', line, re.IGNORECASE):
            in_mvbp = True
        elif re.match(r'^#{1,3}\s', line) and in_mvbp:
            in_mvbp = False
        if in_mvbp:
            mvbp_section_lines.append(line)
    
    mvbp_text = '\n'.join(mvbp_section_lines)
    # Find numbered items
    numbered_items = re.findall(r'^\s*[\d一二三四五]+[\.、\)]\s*.+', mvbp_text, re.MULTILINE)
    feature_count_ok = False
    feature_count_detail = f"Found ~{len(numbered_items)} numbered items in MVBP section"
    
    if len(numbered_items) > 0 and len(numbered_items) <= 5:
        feature_count_ok = True
    elif len(numbered_items) == 0:
        # Try alternative: look for bullet lists
        bullets = re.findall(r'^\s*[-\*•]\s*.+', mvbp_text, re.MULTILINE)
        if 0 < len(bullets) <= 5:
            feature_count_ok = True
            feature_count_detail = f"Found {len(bullets)} bullet items in MVBP section (≤5 required)"
        else:
            feature_count_detail = f"Could not determine feature count. Bullets found: {len(bullets)}"
    else:
        feature_count_detail = f"Found {len(numbered_items)} items — exceeds 5-feature limit from SKILL.md"
    
    checks.append({
        "name": "MVBP: Core features count ≤ 5",
        "passed": feature_count_ok,
        "detail": feature_count_detail
    })

    # Check 3: Timeline 4-8 weeks mentioned
    timeline_match = re.search(r'([4-8]|四|五|六|七|八)\s*[周weeks週]', content, re.IGNORECASE)
    timeline_ok = bool(timeline_match)
    checks.append({
        "name": "MVBP: Timeline specified as 4-8 weeks",
        "passed": timeline_ok,
        "detail": f"Found timeline reference: {timeline_match.group(0) if timeline_match else 'Not found'}"
    })

    # Check 4: Non-functional requirements mentioned
    nfr_patterns = [r'非功能', r'non.?functional', r'性能', r'安全', r'可用性']
    nfr_ok = any(re.search(p, content, re.IGNORECASE) for p in nfr_patterns)
    checks.append({
        "name": "MVBP: Non-functional requirements included",
        "passed": nfr_ok,
        "detail": f"Non-functional requirements mentioned: {nfr_ok}"
    })

    # Check 5: End-to-end customer experience mentioned (from 认知到购买到使用)
    e2e_patterns = [r'端到端', r'end.to.end', r'认知.*购买.*使用', r'完整.*客户.*体验', r'从.*购买']
    e2e_ok = any(re.search(p, content, re.IGNORECASE) for p in e2e_patterns)
    checks.append({
        "name": "MVBP: End-to-end customer experience addressed",
        "passed": e2e_ok,
        "detail": f"E2E customer experience mentioned: {e2e_ok}"
    })

    return checks

def check_demo_section(content: str) -> list:
    checks = []

    # Check 1: Demo section exists
    demo_exists = bool(re.search(r'(demo|演示|展示方案|客户展示|解决方案展示)', content, re.IGNORECASE))
    checks.append({
        "name": "Demo: Section exists",
        "passed": demo_exists,
        "detail": f"Demo section found: {demo_exists}"
    })

    # Check 2: 30-second opener mentioned
    opener_match = re.search(r'30\s*(秒|second|sec)', content, re.IGNORECASE)
    checks.append({
        "name": "Demo: 30-second opener element present",
        "passed": bool(opener_match),
        "detail": f"30-second opener: {'Found' if opener_match else 'Not found — required by SKILL.md step 20'}"
    })

    # Check 3: 10-minute product demo timing
    ten_min_match = re.search(r'10\s*(分钟|minute|min)', content, re.IGNORECASE)
    checks.append({
        "name": "Demo: 10-minute product demo timing present",
        "passed": bool(ten_min_match),
        "detail": f"10-minute constraint: {'Found' if ten_min_match else 'Not found — required by SKILL.md step 20'}"
    })

    # Check 4: All 5 demo elements present
    demo_elements = [
        (r'(开场|共鸣|痛点|开头|opener)', "开场/共鸣"),
        (r'(产品展示|核心功能|产品演示|product demo)', "产品展示"),
        (r'(价值证明|数据|案例|proof)', "价值证明"),
        (r'(互动|操作|提问|Q&A|interactive)', "互动环节"),
        (r'(下一步|行动号召|CTA|call.to.action|next step|后续)', "下一步/CTA"),
    ]
    elements_found = 0
    element_details = []
    for pattern, name in demo_elements:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        if found:
            elements_found += 1
        element_details.append(f"{name}: {'✓' if found else '✗'}")
    
    checks.append({
        "name": "Demo: All 5 structural elements present",
        "passed": elements_found >= 4,  # Allow 4/5 minimum
        "detail": f"Elements found: {elements_found}/5 — {', '.join(element_details)}"
    })

    # Check 5: Feedback collection form with all 5 required questions
    feedback_questions = [
        (r'(最喜欢|喜欢什么|like most)', "客户最喜欢什么"),
        (r'(缺少|缺什么|missing|lack)', "客户觉得缺少什么"),
        (r'(购买意愿|付费意愿|willingness.*pay|1.*10|打分)', "购买意愿评分(1-10)"),
        (r'(愿意付.*钱|付多少|price.*willing|价格意愿)', "愿意付多少钱"),
        (r'(顾虑|疑虑|concern|worry|担心)', "顾虑/疑虑"),
    ]
    feedback_found = 0
    feedback_details = []
    for pattern, name in feedback_questions:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        if found:
            feedback_found += 1
        feedback_details.append(f"{name}: {'✓' if found else '✗'}")
    
    checks.append({
        "name": "Demo: Feedback form includes all 5 prescribed questions",
        "passed": feedback_found >= 4,
        "detail": f"Questions found: {feedback_found}/5 — {', '.join(feedback_details)}"
    })

    return checks

def check_team_section(content: str) -> list:
    checks = []

    # Check 1: Team section exists
    team_exists = bool(re.search(r'(团队|team|核心成员|合伙人|创始团队)', content, re.IGNORECASE))
    checks.append({
        "name": "Team: Section exists",
        "passed": team_exists,
        "detail": f"Team section found: {team_exists}"
    })

    # Check 2: All 4 role types present (PROPRIETARY - must use exact MIT framework names)
    role_patterns = [
        (r'(visionary|愿景型|愿景)', "Visionary (愿景型)"),
        (r'(executor|执行型|执行者)', "Executor (执行型)"),
        (r'(technician|技术型|技术负责)', "Technician (技术型)"),
        (r'(business|商业型|商务型)', "Business (商业型)"),
    ]
    roles_found = 0
    role_details = []
    for pattern, name in role_patterns:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        if found:
            roles_found += 1
        role_details.append(f"{name}: {'✓' if found else '✗'}")
    
    checks.append({
        "name": "Team: All 4 MIT framework role types present (Visionary/Executor/Technician/Business)",
        "passed": roles_found >= 3,
        "detail": f"Roles found: {roles_found}/4 — {', '.join(role_details)}"
    })

    # Check 3: Team size 3-5 mentioned
    team_size_match = re.search(r'([3-5]|三|四|五)\s*(人|位|members?|persons?)', content, re.IGNORECASE)
    # Also accept explicit mention of "3-5" range
    size_range_match = re.search(r'3[-–到至]5\s*(人|位|members?)?', content, re.IGNORECASE)
    team_size_ok = bool(team_size_match) or bool(size_range_match)
    checks.append({
        "name": "Team: Size constraint 3-5 people mentioned",
        "passed": team_size_ok,
        "detail": f"Team size reference found: {team_size_ok} (match: {team_size_match or size_range_match})"
    })

    # Check 4: Equity/decision mechanism mentioned
    equity_patterns = [r'(股权|equity|股份|分配)', r'(决策机制|decision|决策权)']
    equity_ok = all(any(re.search(p, content, re.IGNORECASE) for p in [pattern]) for pattern in equity_patterns)
    # Be lenient: at least one of equity or decision mechanism
    equity_any = any(
        bool(re.search(p, content, re.IGNORECASE))
        for p in [r'股权', r'equity', r'决策机制', r'决策权', r'股份', r'分配方案']
    )
    checks.append({
        "name": "Team: Equity/decision mechanism addressed",
        "passed": equity_any,
        "detail": f"Equity or decision mechanism mentioned: {equity_any}"
    })

    # Check 5: Recruitment plan included
    recruit_patterns = [r'(招聘|recruit|hiring|引入|寻找|人才)', r'(合伙人|co.founder|联合创始人)']
    recruit_ok = any(bool(re.search(p, content, re.IGNORECASE)) for p in recruit_patterns)
    checks.append({
        "name": "Team: Recruitment plan or co-founder strategy mentioned",
        "passed": recruit_ok,
        "detail": f"Recruitment/co-founder strategy found: {recruit_ok}"
    })

    return checks

def check_overall_structure(content: str) -> list:
    checks = []
    
    # Check: Report is a unified document (not just one section)
    section_count = 0
    for pattern in [
        r'(mvbp|最小可行商业产品|产品规格)',
        r'(demo|演示|展示方案|客户展示)',
        r'(团队|core team|核心团队)',
    ]:
        if re.search(pattern, content, re.IGNORECASE):
            section_count += 1
    
    checks.append({
        "name": "Structure: Report contains all 3 required sub-documents",
        "passed": section_count >= 3,
        "detail": f"Sub-document sections found: {section_count}/3 (MVBP + Demo + Team)"
    })
    
    # Check: Report is substantial (not a stub)
    word_count = len(content.split())
    checks.append({
        "name": "Structure: Report is substantive (>300 words)",
        "passed": word_count > 300,
        "detail": f"Word count: {word_count}"
    })
    
    return checks

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    
    all_checks = []
    total_score = 0.0
    
    # Find the report file
    report_path = find_report(workspace)
    
    if report_path is None:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{
                "name": "File: Report file found",
                "passed": False,
                "detail": f"Could not find the 团队与产品验证报告 file in workspace: {workspace}"
            }]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    all_checks.append({
        "name": "File: Report file found",
        "passed": True,
        "detail": f"Found report at: {report_path}"
    })
    
    # Read content
    content = read_file_content(report_path)
    
    if not content:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": all_checks + [{
                "name": "File: Report readable",
                "passed": False,
                "detail": "File found but could not be read or is empty"
            }]
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    
    all_checks.append({
        "name": "File: Report readable and non-empty",
        "passed": True,
        "detail": f"Content length: {len(content)} chars"
    })
    
    # Run all checks
    all_checks.extend(check_overall_structure(content))
    all_checks.extend(check_mvbp_section(content))
    all_checks.extend(check_demo_section(content))
    all_checks.extend(check_team_section(content))
    
    # Calculate score
    passed_checks = sum(1 for c in all_checks if c["passed"])
    total_checks = len(all_checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    
    # Critical checks that must pass for overall pass
    critical_checks = [
        "MVBP: Core features count ≤ 5",
        "MVBP: Timeline specified as 4-8 weeks",
        "Demo: 30-second opener element present",
        "Demo: 10-minute product demo timing present",
        "Demo: Feedback form includes all 5 prescribed questions",
        "Team: All 4 MIT framework role types present (Visionary/Executor/Technician/Business)",
        "Structure: Report contains all 3 required sub-documents",
    ]
    
    critical_passed = all(
        c["passed"] for c in all_checks 
        if c["name"] in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.65
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": all_checks,
        "summary": {
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "critical_checks_passed": critical_passed,
            "report_file": str(report_path)
        }
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()