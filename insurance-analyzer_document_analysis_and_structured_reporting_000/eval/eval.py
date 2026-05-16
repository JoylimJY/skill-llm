import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    # Find the output report file
    report_files = list(workspace.rglob("analysis_report.md"))
    
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_file_exists", "passed": False, "detail": "analysis_report.md not found anywhere in workspace"}]
        }
    
    report_path = report_files[0]
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "report_readable", "passed": False, "detail": f"Could not read file: {e}"}]
        }

    # ---- CHECK 1: Policy Summary Table (3.1 保单梳理表) exists with required fields ----
    required_table_fields = ["保险公司", "保障类型", "保额", "保费", "缴费期限", "保障期限", "等待期", "保障范围"]
    table_found = all(field in content for field in required_table_fields)
    checks.append({
        "name": "policy_summary_table_fields",
        "passed": table_found,
        "detail": f"保单梳理表 must contain all required fields: {required_table_fields}. Found: {table_found}"
    })

    # ---- CHECK 2: 综合评估 section with EXACT four dimensions from SKILL.md 3.2 ----
    required_eval_dimensions = ["覆盖全面性", "保额充足性", "费用合理性", "家庭适配度"]
    eval_dims_found = all(dim in content for dim in required_eval_dimensions)
    checks.append({
        "name": "comprehensive_evaluation_four_dimensions",
        "passed": eval_dims_found,
        "detail": f"综合评估 must contain exactly these 4 dimensions: {required_eval_dimensions}. Found: {eval_dims_found}"
    })

    # ---- CHECK 3: Star ratings present in 综合评估 (⭐ characters) ----
    star_pattern = re.search(r'⭐', content)
    checks.append({
        "name": "star_ratings_present",
        "passed": star_pattern is not None,
        "detail": "综合评估 must use ⭐ star ratings for each dimension per SKILL.md 3.2 template"
    })

    # ---- CHECK 4: 问题诊断 section with bracketed problem tags ----
    # Must have bracketed tags like 【保额不足】 or 【缺失保障】 or 【等待期风险】
    bracket_tag_pattern = re.findall(r'【[^】]+】', content)
    problem_tags = [t for t in bracket_tag_pattern if any(kw in t for kw in ["保额", "缺失", "等待期", "不足", "风险", "缺口", "偏低"])]
    has_problem_tags = len(problem_tags) >= 1
    checks.append({
        "name": "problem_diagnosis_bracket_tags",
        "passed": has_problem_tags,
        "detail": f"问题诊断 (3.3) must use 【】 bracketed problem tags. Found tags: {problem_tags}"
    })

    # ---- CHECK 5: 优化建议 with 【优先级：高/中/低】 structure ----
    priority_high = "优先级：高" in content or "优先级:高" in content
    priority_mid = "优先级：中" in content or "优先级:中" in content
    priority_low = "优先级：低" in content or "优先级:低" in content
    has_priority_structure = priority_high and (priority_mid or priority_low)
    checks.append({
        "name": "optimization_priority_structure",
        "passed": has_priority_structure,
        "detail": f"优化建议 (3.4) must contain 【优先级：高】/【优先级：中】/【优先级：低】 structure. High: {priority_high}, Mid: {priority_mid}, Low: {priority_low}"
    })

    # ---- CHECK 6: Client's actual policy data extracted correctly ----
    # Must mention the 重疾险 with 30万 保额 and correctly identify it as insufficient
    critical_illness_found = "30万" in content and ("重疾" in content)
    checks.append({
        "name": "critical_illness_30wan_extracted",
        "passed": critical_illness_found,
        "detail": f"Must extract client's 重疾险 with 30万 保额 from raw notes. Found: {critical_illness_found}"
    })

    # ---- CHECK 7: Medical insurance (医疗险) details extracted ----
    # 300万保额, 680元/年, 10000免赔额
    medical_extracted = "300万" in content and ("680" in content or "免赔" in content)
    checks.append({
        "name": "medical_insurance_extracted",
        "passed": medical_extracted,
        "detail": f"Must extract 医疗险 with 300万 保额 and 680元 保费. Found: {medical_extracted}"
    })

    # ---- CHECK 8: Term life insurance (定期寿险) details present ----
    term_life_found = ("100万" in content and "寿险" in content) or ("定期" in content and "1500" in content)
    checks.append({
        "name": "term_life_insurance_extracted",
        "passed": term_life_found,
        "detail": f"Must extract 定期寿险 100万保额/1500元保费. Found: {term_life_found}"
    })

    # ---- CHECK 9: Compliance - NO specific product recommendations ----
    # Should NOT recommend specific product names from the product database
    banned_product_names = ["超越保2024", "达尔文6号", "康惠保旗舰版", "好医保", "尊享e生"]
    product_recommendation_found = any(name in content for name in banned_product_names)
    no_product_recommendation = not product_recommendation_found
    checks.append({
        "name": "no_specific_product_recommendation",
        "passed": no_product_recommendation,
        "detail": f"Per SKILL.md Section 4, must NOT recommend specific products. Found banned product names: {[n for n in banned_product_names if n in content]}"
    })

    # ---- CHECK 10: Compliance - Response to "换个好点的公司" query handled appropriately ----
    # Must redirect to professional consultation, not directly answer "which company is better"
    professional_redirect_keywords = ["保险经纪人", "专业人士", "专业顾问", "专业咨询", "以保单合同为准", "咨询专业", "持证"]
    has_professional_redirect = any(kw in content for kw in professional_redirect_keywords)
    checks.append({
        "name": "professional_redirect_compliance",
        "passed": has_professional_redirect,
        "detail": f"Per SKILL.md Section 4, must redirect specific product questions to professionals. Found redirect: {has_professional_redirect}"
    })

    # ---- CHECK 11: Client's 重疾险 inadequacy correctly flagged ----
    # 重疾险 30万 is clearly insufficient for IT engineer with 42万 annual income
    inadequacy_flagged = any(kw in content for kw in ["不足", "偏低", "建议提升", "建议提高", "不够"]) and "重疾" in content
    checks.append({
        "name": "critical_illness_inadequacy_flagged",
        "passed": inadequacy_flagged,
        "detail": f"Must flag 重疾险 30万保额 as insufficient for client's income level. Found: {inadequacy_flagged}"
    })

    # ---- CHECK 12: User info section present (1.1 framework applied) ----
    user_info_keywords = ["35岁", "IT", "年收入", "房贷", "已婚", "子女"]
    user_info_present = sum(1 for kw in user_info_keywords if kw in content) >= 3
    checks.append({
        "name": "user_profile_extracted",
        "passed": user_info_present,
        "detail": f"Must extract user profile info (age, profession, income, family). Found {sum(1 for kw in user_info_keywords if kw in content)}/6 keywords"
    })

    # ---- Scoring ----
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = round(passed_checks / total_checks, 3)
    
    # Must pass critical checks to be considered overall passing
    critical_checks = [
        "policy_summary_table_fields",
        "comprehensive_evaluation_four_dimensions",
        "optimization_priority_structure",
        "no_specific_product_recommendation",
        "problem_diagnosis_bracket_tags"
    ]
    critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))