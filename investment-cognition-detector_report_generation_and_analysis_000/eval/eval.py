import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the report file ---
    report_files = list(workspace.rglob("investment_diagnosis_report.md"))
    
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_exists", "passed": False, "detail": "Could not find 'investment_diagnosis_report.md' anywhere in the workspace."}]
        }
    
    report_path = report_files[0]
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_readable", "passed": False, "detail": f"Could not read report file: {e}"}]
        }

    content_lower = content.lower()

    # -------------------------------------------------------
    # CHECK 1: File is Markdown with substantial content
    # -------------------------------------------------------
    check1_passed = len(content) >= 800 and content.count('#') >= 3
    checks.append({
        "name": "report_is_substantial_markdown",
        "passed": check1_passed,
        "detail": f"Report length: {len(content)} chars, heading count: {content.count('#')}. Expected >= 800 chars and >= 3 headings."
    })

    # -------------------------------------------------------
    # CHECK 2: Must reference the correct company (鸿利佳)
    # -------------------------------------------------------
    has_company = "鸿利佳" in content
    checks.append({
        "name": "references_correct_company",
        "passed": has_company,
        "detail": "Report must reference 鸿利佳食品 (the company from the transcript)." if not has_company else "Company name found."
    })

    # -------------------------------------------------------
    # CHECK 3: Contains 总体评分 section (Overall Score section)
    # -------------------------------------------------------
    has_overall_score = bool(re.search(r'总体评分|总体得分|整体评分|整体得分', content))
    checks.append({
        "name": "has_overall_score_section",
        "passed": has_overall_score,
        "detail": "Must contain a 总体评分 (overall score) section as specified in SKILL.md."
    })

    # -------------------------------------------------------
    # CHECK 4: Overall grade must be 🟡 初步懂 (40-70% range)
    # The answers score approximately: Q1~65, Q2~50, Q3~30, Q4~60 → avg ~51% → 🟡 初步懂
    # We check for the yellow circle emoji + 初步懂 label
    # -------------------------------------------------------
    has_correct_tier_label = "初步懂" in content
    has_yellow_indicator = "🟡" in content or "初步懂" in content
    correct_overall_grade = has_correct_tier_label and has_yellow_indicator
    checks.append({
        "name": "correct_overall_grade_chu_bu_dong",
        "passed": correct_overall_grade,
        "detail": f"Overall grade must be '🟡 初步懂' (40-70% range). Found '初步懂': {has_correct_tier_label}, Found '🟡': {'🟡' in content}."
    })

    # -------------------------------------------------------
    # CHECK 5: Must NOT assign 基本懂 or 完全懂 as primary grade
    # (those would indicate wrong scoring)
    # -------------------------------------------------------
    # Check that the report doesn't give a top grade
    has_wrong_top_grade_primary = bool(re.search(r'✅\s*完全懂|完全懂.*90|90.*完全懂', content))
    # It's okay if 基本懂/完全懂 appears as part of the rubric explanation, 
    # but the OVERALL assessment should say 初步懂
    checks.append({
        "name": "does_not_assign_top_grade_incorrectly",
        "passed": not has_wrong_top_grade_primary,
        "detail": "Report should not claim the investor has '✅ 完全懂' overall — that would indicate wrong scoring."
    })

    # -------------------------------------------------------
    # CHECK 6: Contains 四问得分 section (Four-question scores)
    # -------------------------------------------------------
    has_four_q_scores = bool(re.search(r'四问得分|四问评分|四问分析|Q1|Q2|Q3|Q4|问题一|问题二|问题三|问题四', content))
    checks.append({
        "name": "has_four_question_scores_section",
        "passed": has_four_q_scores,
        "detail": "Must contain scores or evaluations for all four questions (Q1-Q4 / 问题一-问题四)."
    })

    # -------------------------------------------------------
    # CHECK 7: Q3 (Growth) must be identified as the weakest question
    # The investor explicitly said "我也不是很清楚" for the second growth curve
    # -------------------------------------------------------
    # Check that Q3/问题三/成长性 is flagged as weak/lowest score
    q3_patterns = [
        r'问题三.*?(弱|不足|最低|最差|薄弱|盲点|不清楚|模糊)',
        r'(Q3|成长性|第二增长曲线).*?(弱|不足|最低|最差|薄弱|盲点)',
        r'(弱|最低|最差|薄弱).*?(Q3|问题三|成长|增长曲线)',
        r'增长.*?(弱|不足|薄弱|不清楚)',
    ]
    q3_weak = any(re.search(p, content, re.DOTALL | re.IGNORECASE) for p in q3_patterns)
    # Also accept if Q3 has the lowest numeric score
    q3_score_match = re.search(r'(?:问题三|Q3)[^\d]*(\d{1,3})\s*%', content)
    if q3_score_match:
        q3_score_val = int(q3_score_match.group(1))
        q3_weak = q3_weak or (q3_score_val < 50)
    
    checks.append({
        "name": "q3_growth_identified_as_weakest",
        "passed": q3_weak,
        "detail": "Q3 (成长性/growth) must be identified as the weakest area. Investor said '我也不是很清楚' about second growth curve."
    })

    # -------------------------------------------------------
    # CHECK 8: Contains 认知盲点 section (Cognitive Blind Spots)
    # -------------------------------------------------------
    has_blind_spots = bool(re.search(r'认知盲点|盲点', content))
    checks.append({
        "name": "has_cognitive_blind_spots_section",
        "passed": has_blind_spots,
        "detail": "Must contain a '认知盲点' (cognitive blind spots) section as required by SKILL.md."
    })

    # -------------------------------------------------------
    # CHECK 9: Must quote user's original words (用户原话)
    # Check for at least one direct quote from the transcript
    # -------------------------------------------------------
    user_phrases = [
        "应该还是酱油",
        "我也不是很清楚",
        "感觉管理层应该有规划",
        "反正有分就行",
        "这个我没算过",
        "人总要吃饭",
        "40%",
        "说不太清楚",
    ]
    found_quotes = [phrase for phrase in user_phrases if phrase in content]
    has_user_quotes = len(found_quotes) >= 2
    checks.append({
        "name": "quotes_user_original_words",
        "passed": has_user_quotes,
        "detail": f"Must quote user's original words as evidence. Found {len(found_quotes)} matching phrases: {found_quotes[:3]}."
    })

    # -------------------------------------------------------
    # CHECK 10: Contains 学习建议 section (Learning Recommendations)
    # -------------------------------------------------------
    has_learning_advice = bool(re.search(r'学习建议|研究建议|研究方向|改进建议', content))
    checks.append({
        "name": "has_learning_recommendations_section",
        "passed": has_learning_advice,
        "detail": "Must contain a '学习建议' (learning recommendations) section as required by SKILL.md."
    })

    # -------------------------------------------------------
    # CHECK 11: Report uses all four emoji tier indicators somewhere
    # (showing the agent knows the full rubric and applies it contextually)
    # The report should at minimum reference the scoring tiers
    # -------------------------------------------------------
    tier_references = sum([
        "🔴" in content or "不懂" in content,
        "🟡" in content or "初步懂" in content,
        "🟢" in content or "基本懂" in content,
        "✅" in content or "完全懂" in content,
    ])
    has_tier_rubric = tier_references >= 2
    checks.append({
        "name": "references_scoring_tier_system",
        "passed": has_tier_rubric,
        "detail": f"Report should reference the 4-tier scoring system (🔴🟡🟢✅). Found {tier_references}/4 tiers referenced."
    })

    # -------------------------------------------------------
    # CHECK 12: Contains 核心追问 section (Key Follow-up Questions)
    # -------------------------------------------------------
    has_followup = bool(re.search(r'核心追问|关键追问|核心问题|追问', content))
    checks.append({
        "name": "has_key_followup_questions_section",
        "passed": has_followup,
        "detail": "Must contain a '核心追问' (key follow-up questions) section as required by SKILL.md."
    })

    # -------------------------------------------------------
    # Final scoring
    # -------------------------------------------------------
    passed_count = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_count / total_checks

    # Must pass at minimum: file exists, correct company, correct grade, has blind spots, has user quotes
    critical_checks = ["report_is_substantial_markdown", "references_correct_company",
                       "correct_overall_grade_chu_bu_dong", "has_cognitive_blind_spots_section",
                       "quotes_user_original_words", "q3_growth_identified_as_weakest"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))