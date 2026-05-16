import sys
import os
import re
import json
from pathlib import Path

def find_review_report(workspace: str):
    """Find the review report file in the workspace."""
    # Look for any markdown file that could be the review report
    candidates = list(Path(workspace).rglob("*.md")) + list(Path(workspace).rglob("*.txt"))
    # Exclude known distractor docs
    candidates = [
        p for p in candidates
        if "api_spec" not in p.name and "README" not in p.name
        and ".github" not in str(p)
    ]
    # Prefer files with "review" or "report" in name, or that contain the expected sections
    for p in candidates:
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            if "代码评审报告" in content or ("评审结论" in content and "代码评分" in content):
                return p, content
        except Exception:
            pass
    # Fallback: any file containing the key Chinese section headers
    for p in candidates:
        try:
            content = p.read_text(encoding="utf-8", errors="ignore")
            if "修改方案性价比" in content or "最佳实践建议" in content:
                return p, content
        except Exception:
            pass
    return None, None


def eval_report(workspace: str):
    checks = []

    report_path, content = find_review_report(workspace)

    # CHECK 0: Report file exists
    if report_path is None or content is None:
        checks.append({
            "name": "report_file_exists",
            "passed": False,
            "detail": "No review report file found. Expected a .md or .txt file containing '代码评审报告' or the 5 required section headers."
        })
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}
    else:
        checks.append({
            "name": "report_file_exists",
            "passed": True,
            "detail": f"Found report at: {report_path}"
        })

    # CHECK 1: Five required sections present
    required_sections = [
        ("section_overview", ["改动概览", "一、改动概览", "变更类型", "涉及文件"]),
        ("section_review_dimensions", ["评审结论", "二、评审结论", "正确性", "可读性"]),
        ("section_best_practices", ["最佳实践建议", "三、最佳实践建议"]),
        ("section_cost_benefit", ["修改方案性价比", "四、修改方案性价比", "性价比"]),
        ("section_score", ["代码评分", "五、代码评分"]),
    ]

    for section_id, keywords in required_sections:
        found = any(kw in content for kw in keywords)
        checks.append({
            "name": section_id,
            "passed": found,
            "detail": f"Section '{section_id}' {'found' if found else 'NOT found'} (looked for: {keywords[:2]})"
        })

    # CHECK 2: All 6 review dimensions present
    dimensions = ["正确性", "可读性", "可维护性", "性能", "安全", "测试"]
    dimensions_found = [d for d in dimensions if d in content]
    all_dims_present = len(dimensions_found) == 6
    checks.append({
        "name": "all_six_dimensions",
        "passed": all_dims_present,
        "detail": f"Found dimensions: {dimensions_found} ({len(dimensions_found)}/6)"
    })

    # CHECK 3: Three-tier recommendation labels
    must_fix = bool(re.search(r'\[必须改\]|必须改', content))
    suggest_fix = bool(re.search(r'\[建议改\]|建议改', content))
    optional = bool(re.search(r'\[可选优化\]|可选优化', content))
    three_tier = must_fix and suggest_fix and optional
    checks.append({
        "name": "three_tier_recommendation_labels",
        "passed": three_tier,
        "detail": f"[必须改]={must_fix}, [建议改]={suggest_fix}, [可选优化]={optional}"
    })

    # CHECK 4: Score in range 0-100 with numeric value present
    score_match = re.search(r'(\d{1,3})\s*/\s*100', content)
    score_present = False
    score_value = None
    if score_match:
        score_value = int(score_match.group(1))
        score_present = (0 <= score_value <= 100)
    checks.append({
        "name": "numeric_score_present",
        "passed": score_present,
        "detail": f"Score found: {score_value}/100" if score_present else "No valid XX/100 score pattern found"
    })

    # CHECK 5: Grade letter present (A/B/C/D/E) with 等级
    grade_match = re.search(r'等级[：:]\s*([A-E])', content) or re.search(r'([A-E])\s*(优秀|良好|合格|需改进|不达标)', content)
    grade_present = grade_match is not None
    checks.append({
        "name": "grade_letter_present",
        "passed": grade_present,
        "detail": f"Grade found: {grade_match.group(0) if grade_match else 'None'}"
    })

    # CHECK 6: Score is in the appropriate range given the issues
    # The diff has: SQL injection (critical), eval() usage (critical), deleted tests, no input validation
    # Expected score should be D (40-59) or lower, definitely not A or B
    score_appropriately_low = False
    if score_value is not None:
        # Should not be in A (90-100) or B (75-89) range given critical security issues
        score_appropriately_low = score_value < 75
    checks.append({
        "name": "score_appropriately_reflects_severity",
        "passed": score_appropriately_low,
        "detail": f"Score {score_value} should be < 75 given critical security bugs (SQL injection, eval()). Got: {score_value}"
    })

    # CHECK 7: Security issues identified (SQL injection and eval())
    sql_injection_mentioned = bool(re.search(r'SQL\s*注入|sql\s*injection|SQL injection|注入攻击|字符串拼接.*SQL|SQL.*拼接', content, re.IGNORECASE))
    eval_mentioned = bool(re.search(r'eval\(\)|eval\s+函数|eval 风险|危险.*eval|eval.*危险|任意代码|代码注入', content, re.IGNORECASE))
    security_issues_found = sql_injection_mentioned and eval_mentioned
    checks.append({
        "name": "security_issues_identified",
        "passed": security_issues_found,
        "detail": f"SQL injection mentioned: {sql_injection_mentioned}, eval() risk mentioned: {eval_mentioned}"
    })

    # CHECK 8: Missing input validation / test deletion noted
    missing_validation = bool(re.search(r'输入校验|参数校验|缺少校验|input validation|缺少验证|amount.*None|None.*amount', content, re.IGNORECASE))
    test_deletion = bool(re.search(r'测试.*删除|删除.*测试|test_charge.*删|unit test|单元测试.*缺失|缺少.*测试|测试覆盖', content, re.IGNORECASE))
    checks.append({
        "name": "correctness_and_test_issues_noted",
        "passed": missing_validation or test_deletion,
        "detail": f"Missing validation noted: {missing_validation}, Test deletion noted: {test_deletion}"
    })

    # CHECK 9: Cost-benefit section has 高/中/低性价比 conclusion
    cost_benefit_conclusion = bool(re.search(r'高性价比|中性价比|低性价比|高.*性价比|性价比.*高|性价比.*低|性价比.*中', content))
    checks.append({
        "name": "cost_benefit_has_conclusion",
        "passed": cost_benefit_conclusion,
        "detail": f"Cost-benefit conclusion (高/中/低性价比) {'found' if cost_benefit_conclusion else 'NOT found'}"
    })

    # CHECK 10: One-sentence summary present
    one_liner = bool(re.search(r'一句话总结|一句话|总结：|总结:|Summary:', content, re.IGNORECASE))
    checks.append({
        "name": "one_sentence_summary",
        "passed": one_liner,
        "detail": f"One-sentence summary {'found' if one_liner else 'NOT found'}"
    })

    # --- Compute final score ---
    # Weight the checks
    weights = {
        "report_file_exists": 3,
        "section_overview": 1,
        "section_review_dimensions": 1,
        "section_best_practices": 1,
        "section_cost_benefit": 1,
        "section_score": 1,
        "all_six_dimensions": 2,
        "three_tier_recommendation_labels": 2,
        "numeric_score_present": 1,
        "grade_letter_present": 1,
        "score_appropriately_reflects_severity": 2,
        "security_issues_identified": 3,
        "correctness_and_test_issues_noted": 2,
        "cost_benefit_has_conclusion": 2,
        "one_sentence_summary": 1,
    }

    total_weight = sum(weights.values())
    earned_weight = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    final_score = round(earned_weight / total_weight, 4)

    # Must pass: report exists + security identified + score present
    critical_checks = ["report_file_exists", "security_issues_identified", "numeric_score_present"]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)

    return {
        "passed": critical_passed and final_score >= 0.65,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    try:
        result = eval_report(workspace)
    except Exception as e:
        result = {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }
    print(json.dumps(result, ensure_ascii=False, indent=2))