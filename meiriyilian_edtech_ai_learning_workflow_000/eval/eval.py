import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    
    # Find the agent's response file
    response_file = None
    
    # Look for the response file - agent should create agent_response.md or similar
    candidates = list(Path(workspace_dir).rglob("agent_response.md"))
    if not candidates:
        candidates = list(Path(workspace_dir).rglob("response.md"))
    if not candidates:
        candidates = list(Path(workspace_dir).rglob("reply.md"))
    if not candidates:
        # Try any .md file that's not in references/ or drafts/ and not skill.md
        all_md = list(Path(workspace_dir).rglob("*.md"))
        candidates = [
            f for f in all_md 
            if "references" not in str(f)
            and "drafts" not in str(f)
            and f.name != "skill.md"
            and "SKILL" not in f.name.upper()
        ]
    
    if not candidates:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "response_file_exists", "passed": False, "detail": "No response file found. Expected agent_response.md, response.md, or reply.md in workspace."}]
        }
    
    # Use the most recently modified candidate
    response_file = max(candidates, key=lambda f: f.stat().st_mtime)
    
    try:
        content = response_file.read_text(encoding='utf-8')
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "response_file_readable", "passed": False, "detail": f"Could not read response file: {e}"}]
        }
    
    # ---- CHECK 1: Response is in Chinese ----
    chinese_char_count = len(re.findall(r'[\u4e00-\u9fff]', content))
    check1_passed = chinese_char_count >= 100
    checks.append({
        "name": "response_in_chinese",
        "passed": check1_passed,
        "detail": f"Found {chinese_char_count} Chinese characters. Expected >= 100."
    })
    
    # ---- CHECK 2: Contains the 5 required sections in correct order ----
    # The SKILL.md mandates this exact order: 你的目标, 推荐模式, 今日安排, 自检方式, 下一步
    sections = ["你的目标", "推荐模式", "今日安排", "自检方式", "下一步"]
    section_positions = []
    for sec in sections:
        pos = content.find(sec)
        section_positions.append(pos)
    
    sections_present = [pos != -1 for pos in section_positions]
    all_sections_present = all(sections_present)
    
    check2_passed = all_sections_present
    missing = [sections[i] for i, present in enumerate(sections_present) if not present]
    checks.append({
        "name": "five_sections_present",
        "passed": check2_passed,
        "detail": f"Missing sections: {missing}" if missing else "All 5 required sections present."
    })
    
    # ---- CHECK 3: Sections appear in correct order ----
    if all_sections_present:
        order_correct = all(
            section_positions[i] < section_positions[i+1] 
            for i in range(len(section_positions)-1)
        )
    else:
        order_correct = False
    
    checks.append({
        "name": "sections_in_correct_order",
        "passed": order_correct,
        "detail": f"Section positions: {list(zip(sections, section_positions))}. Must be in ascending order."
    })
    
    # ---- CHECK 4: Contains practice-flow structure (since user asked "来一题") ----
    # Must have: 今日练习, 目标, 题目 or 任务, 建议时长, 检查方法 or 自查, 明日衔接
    practice_keywords = ["今日练习", "建议时长", "明日衔接"]
    practice_found = [kw for kw in practice_keywords if kw in content]
    practice_missing = [kw for kw in practice_keywords if kw not in content]
    
    check4_passed = len(practice_found) >= 2
    checks.append({
        "name": "practice_flow_structure",
        "passed": check4_passed,
        "detail": f"Found practice keywords: {practice_found}. Missing: {practice_missing}. Need at least 2 of 3 key practice-flow markers."
    })
    
    # ---- CHECK 5: Uses proprietary terminology (AI教/AI学/AI练) ----
    has_ai_teach = "AI教" in content
    has_ai_learn = "AI学" in content  
    has_ai_practice = "AI练" in content
    
    ai_trio_count = sum([has_ai_teach, has_ai_learn, has_ai_practice])
    check5_passed = ai_trio_count >= 2
    checks.append({
        "name": "proprietary_ai_trio_terminology",
        "passed": check5_passed,
        "detail": f"Found AI教: {has_ai_teach}, AI学: {has_ai_learn}, AI练: {has_ai_practice}. Need at least 2 of 3."
    })
    
    # ---- CHECK 6: Does NOT fabricate pricing ----
    # Should mention "内测" or "暂未公开" or "以官网为准" for pricing
    # Should NOT give specific prices like "99元" "199元" "免费" (as definitive statements)
    price_fabrication_patterns = [
        r'\d+\s*元/[月年]',
        r'月费\s*\d+',
        r'年费\s*\d+',
        r'收费\s*\d+',
        r'价格[是为]\s*\d+',
        r'免费使用',  # claiming definitively free
        r'永久免费',
        r'完全免费',
    ]
    
    price_fabricated = any(re.search(p, content) for p in price_fabrication_patterns)
    
    # Must mention either beta/内测 status or redirect to official site for pricing
    correct_price_response = any(phrase in content for phrase in [
        "内测", "未公开", "以官网", "官网公告", "暂无", "不承诺", "公开价格"
    ])
    
    check6_passed = (not price_fabricated) and correct_price_response
    checks.append({
        "name": "no_fabricated_pricing",
        "passed": check6_passed,
        "detail": (
            f"Price fabricated: {price_fabricated}. "
            f"Correct pricing response (mentions beta/redirects to official): {correct_price_response}. "
            "Must NOT give specific prices and MUST mention '内测' or redirect to official site."
        )
    })
    
    # ---- CHECK 7: Contains "学习克隆体" (relevant to CPA exam coaching context) ----
    has_clone = "学习克隆体" in content
    checks.append({
        "name": "mentions_learning_clone",
        "passed": has_clone,
        "detail": f"'学习克隆体' found: {has_clone}. This proprietary concept must be mentioned when explaining what the product offers."
    })
    
    # ---- CHECK 8: CPA-specific practice content present ----
    # The user asked specifically about 长期股权投资 权益法
    cpa_keywords = ["长期股权投资", "权益法", "CPA", "注册会计师", "会计"]
    cpa_found = [kw for kw in cpa_keywords if kw in content]
    check8_passed = len(cpa_found) >= 2
    checks.append({
        "name": "cpa_specific_content",
        "passed": check8_passed,
        "detail": f"Found CPA-related keywords: {cpa_found}. Need at least 2 of {cpa_keywords}."
    })
    
    # ---- CHECK 9: Response doesn't start with heavy marketing (practice-first rule) ----
    # Since user also asked for practice, the response should not front-load marketing
    # First 200 chars should not be pure product marketing slogans
    first_300 = content[:300]
    marketing_heavy_starts = [
        "学习从未如此简单",
        "把书读薄",
        "每日一练是一款革命性",
        "颠覆传统学习方式",
    ]
    marketing_frontloaded = any(phrase in first_300 for phrase in marketing_heavy_starts)
    check9_passed = not marketing_frontloaded
    checks.append({
        "name": "no_heavy_marketing_frontload",
        "passed": check9_passed,
        "detail": f"Marketing frontloaded in first 300 chars: {marketing_frontloaded}. Response should address user's dual intent (product + practice) without leading with pure marketing slogans."
    })
    
    # ---- CHECK 10: Mentions "日练周测月考" rhythm ----
    has_rhythm = "日练" in content and ("周测" in content or "月考" in content)
    checks.append({
        "name": "daily_weekly_monthly_rhythm",
        "passed": has_rhythm,
        "detail": f"'日练周测月考' rhythm present: {has_rhythm}. This proprietary training rhythm must be mentioned for CPA exam preparation context."
    })
    
    # ---- Compute final score ----
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / total_checks
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "five_sections_present",
        "sections_in_correct_order", 
        "no_fabricated_pricing",
        "practice_flow_structure"
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.75
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    workspace = sys.argv[1]
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))