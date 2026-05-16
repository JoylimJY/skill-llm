import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    checks = []
    score = 0.0
    total_weight = 0.0

    # --- Find the output file ---
    target_files = list(Path(workspace_dir).rglob("brand_naming_report.md"))
    
    if not target_files:
        checks.append({"name": "file_exists", "passed": False, "detail": "brand_naming_report.md not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = target_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at: {report_path}"})
    score += 5.0
    total_weight += 5.0

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "file_readable", "passed": True, "detail": "File is readable UTF-8."})

    # --- Check 1: Top-level header ---
    has_main_header = bool(re.search(r'^#\s+品牌命名方案', content, re.MULTILINE))
    checks.append({
        "name": "main_header_correct",
        "passed": has_main_header,
        "detail": "Must have '# 品牌命名方案' as a top-level heading." if not has_main_header else "Found correct main header."
    })
    if has_main_header:
        score += 5.0
    total_weight += 5.0

    # --- Check 2: 备选名称 section ---
    has_beixin = bool(re.search(r'##\s+备选名称', content, re.MULTILINE))
    checks.append({
        "name": "section_beixin_exists",
        "passed": has_beixin,
        "detail": "Must have '## 备选名称' section." if not has_beixin else "Found 备选名称 section."
    })
    if has_beixin:
        score += 5.0
    total_weight += 5.0

    # --- Check 3: At least 3 proposals with ### 方案N headers ---
    proposals = re.findall(r'###\s+方案\d+[：:]?\s*\S+', content)
    has_three_proposals = len(proposals) >= 3
    checks.append({
        "name": "at_least_3_proposals",
        "passed": has_three_proposals,
        "detail": f"Found {len(proposals)} proposal(s). Need at least 3 with '### 方案N' headers." if not has_three_proposals else f"Found {len(proposals)} proposals."
    })
    if has_three_proposals:
        score += 10.0
    total_weight += 10.0

    # --- Check 4: Each proposal has all 7 required fields ---
    required_fields = ["读音", "含义", "联想", "优点", "缺点", "域名", "商标"]
    # Split content into proposal blocks
    proposal_blocks = re.split(r'###\s+方案\d+', content)
    # Skip the first element (before any proposal)
    proposal_blocks = proposal_blocks[1:] if len(proposal_blocks) > 1 else []
    
    # Trim to first 3 or however many we found
    evaluated_blocks = proposal_blocks[:max(3, len(proposals))]
    
    all_fields_present = True
    missing_fields_detail = []
    for i, block in enumerate(evaluated_blocks[:3]):
        for field in required_fields:
            if field not in block:
                all_fields_present = False
                missing_fields_detail.append(f"方案{i+1} missing: {field}")
    
    checks.append({
        "name": "all_7_fields_in_proposals",
        "passed": all_fields_present,
        "detail": "; ".join(missing_fields_detail) if missing_fields_detail else "All 7 required fields (读音/含义/联想/优点/缺点/域名/商标) present in first 3 proposals."
    })
    if all_fields_present:
        score += 15.0
    total_weight += 15.0

    # --- Check 5: Domain check format - must have .com, .cn, .com.cn ---
    has_dot_com = bool(re.search(r'\.com\b', content))
    has_dot_cn = bool(re.search(r'\.cn\b', content))
    has_dot_com_cn = bool(re.search(r'\.com\.cn', content))
    domain_checks_complete = has_dot_com and has_dot_cn and has_dot_com_cn
    checks.append({
        "name": "domain_checks_com_cn_comcn",
        "passed": domain_checks_complete,
        "detail": f".com:{has_dot_com}, .cn:{has_dot_cn}, .com.cn:{has_dot_com_cn}. All three domain extensions must be checked per SKILL.md." if not domain_checks_complete else "All three domain extensions (.com, .cn, .com.cn) mentioned."
    })
    if domain_checks_complete:
        score += 10.0
    total_weight += 10.0

    # --- Check 6: Domain availability symbols ✓ or ✗ ---
    has_check_symbol = bool(re.search(r'[✓✗]', content))
    checks.append({
        "name": "domain_availability_symbols",
        "passed": has_check_symbol,
        "detail": "Must use ✓ or ✗ symbols for domain availability per template." if not has_check_symbol else "Found domain availability symbols (✓/✗)."
    })
    if has_check_symbol:
        score += 8.0
    total_weight += 8.0

    # --- Check 7: Trademark notation □可注册 □有风险 ---
    has_trademark_notation = bool(re.search(r'□可注册|□有风险', content))
    checks.append({
        "name": "trademark_notation_correct",
        "passed": has_trademark_notation,
        "detail": "Must use □可注册 / □有风险 notation for trademark status per template." if not has_trademark_notation else "Found correct trademark notation."
    })
    if has_trademark_notation:
        score += 8.0
    total_weight += 8.0

    # --- Check 8: Evaluation table with ★ symbols ---
    has_star_rating = bool(re.search(r'★', content))
    checks.append({
        "name": "star_ratings_present",
        "passed": has_star_rating,
        "detail": "Evaluation table must use ★ symbols for ratings." if not has_star_rating else "Found ★ star rating symbols."
    })
    if has_star_rating:
        score += 8.0
    total_weight += 8.0

    # --- Check 9: Evaluation table has required dimension rows ---
    eval_dimensions = ["好记程度", "行业相关性", "国际化", "可注册性", "总体评分"]
    found_dims = [d for d in eval_dimensions if d in content]
    eval_table_complete = len(found_dims) >= 4
    checks.append({
        "name": "evaluation_table_dimensions",
        "passed": eval_table_complete,
        "detail": f"Found {len(found_dims)}/5 required evaluation dimensions: {found_dims}. Need at least 4." if not eval_table_complete else f"Found all evaluation dimensions: {found_dims}."
    })
    if eval_table_complete:
        score += 10.0
    total_weight += 10.0

    # --- Check 10: 名称评估 section header ---
    has_eval_section = bool(re.search(r'##\s+名称评估', content, re.MULTILINE))
    checks.append({
        "name": "section_pinggu_exists",
        "passed": has_eval_section,
        "detail": "Must have '## 名称评估' section." if not has_eval_section else "Found 名称评估 section."
    })
    if has_eval_section:
        score += 5.0
    total_weight += 5.0

    # --- Check 11: 推荐方案 section with bold recommendation ---
    has_recommend_section = bool(re.search(r'##\s+推荐方案', content, re.MULTILINE))
    has_bold_recommendation = bool(re.search(r'\*\*[^\*]+\*\*', content))
    recommend_complete = has_recommend_section and has_bold_recommendation
    checks.append({
        "name": "recommendation_section_complete",
        "passed": recommend_complete,
        "detail": f"推荐方案 section: {has_recommend_section}, Bold name: {has_bold_recommendation}. Both required." if not recommend_complete else "Found 推荐方案 section with bold recommended name."
    })
    if recommend_complete:
        score += 10.0
    total_weight += 10.0

    # --- Check 12: Electric motor industry relevance (uses 电机-related naming vocabulary) ---
    motor_keywords = ["电", "磁", "驱", "控", "劲", "恒", "速", "稳", "威", "盾", "锐", "锋", "安", "信", "诺"]
    found_motor_terms = [k for k in motor_keywords if k in content]
    is_motor_relevant = len(found_motor_terms) >= 3
    checks.append({
        "name": "motor_industry_relevance",
        "passed": is_motor_relevant,
        "detail": f"Found {len(found_motor_terms)} motor-industry naming terms: {found_motor_terms}. Need at least 3." if not is_motor_relevant else f"Good motor industry relevance. Terms found: {found_motor_terms}."
    })
    if is_motor_relevant:
        score += 7.0
    total_weight += 7.0

    # --- Check 13: Avoids naming forbidden zones (no 生僻字 or known clones) ---
    forbidden_patterns = ["特拉斯", "长安（长胖）", "覔", "龘"]
    found_forbidden = [fp for fp in forbidden_patterns if fp in content]
    avoids_forbidden = len(found_forbidden) == 0
    checks.append({
        "name": "avoids_naming_forbidden_zones",
        "passed": avoids_forbidden,
        "detail": f"Found forbidden naming patterns: {found_forbidden}" if not avoids_forbidden else "No forbidden naming patterns detected."
    })
    if avoids_forbidden:
        score += 4.0
    total_weight += 4.0

    # --- Check 14: Numeric total scores present ---
    numeric_scores = re.findall(r'\b([0-9]+\.?[0-9]*)\b', content)
    # Filter for plausible 0-10 scores
    valid_scores = [float(s) for s in numeric_scores if 5.0 <= float(s) <= 10.0]
    has_numeric_scores = len(valid_scores) >= 3
    checks.append({
        "name": "numeric_scores_present",
        "passed": has_numeric_scores,
        "detail": f"Found {len(valid_scores)} numeric scores in 5-10 range. Need at least 3 for proposals." if not has_numeric_scores else f"Found numeric scores: {valid_scores[:6]}."
    })
    if has_numeric_scores:
        score += 5.0
    total_weight += 5.0

    # --- Final scoring ---
    final_score = round((score / total_weight) * 100, 2) if total_weight > 0 else 0.0
    
    # Determine pass: must have file, main header, 3 proposals, all fields, eval table, recommendation
    critical_checks = [
        "file_exists", "main_header_correct", "at_least_3_proposals",
        "all_7_fields_in_proposals", "evaluation_table_dimensions", "recommendation_section_complete"
    ]
    critical_results = {c["name"]: c["passed"] for c in checks}
    passed = all(critical_results.get(cn, False) for cn in critical_checks)

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided."}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))