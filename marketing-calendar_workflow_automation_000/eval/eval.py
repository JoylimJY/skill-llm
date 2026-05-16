import sys
import json
import re
from pathlib import Path

def find_html_report(workspace):
    candidates = list(Path(workspace).rglob("marketing_calendar_report.html"))
    return candidates[0] if candidates else None

def evaluate(workspace):
    checks = []
    total_score = 0.0

    # ── Check 1: HTML file exists ─────────────────────────────────────────────
    html_path = find_html_report(workspace)
    if html_path is None:
        checks.append({"name": "HTML report exists", "passed": False, "detail": "marketing_calendar_report.html not found anywhere in workspace."})
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({"name": "HTML report exists", "passed": True, "detail": f"Found at {html_path}"})
    total_score += 10

    try:
        content = html_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "HTML readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": total_score, "checks": checks}
    
    checks.append({"name": "HTML readable", "passed": True, "detail": f"File size: {len(content)} chars"})

    # ── Check 2: Brand name present ───────────────────────────────────────────
    brand_present = "辣聚火锅" in content or "辣聚" in content
    checks.append({
        "name": "Brand name in report",
        "passed": brand_present,
        "detail": "Brand '辣聚火锅' or '辣聚' found in HTML." if brand_present else "Brand name missing from HTML."
    })
    if brand_present:
        total_score += 5

    # ── Check 3: Target months covered (2, 5, 7, 10) ─────────────────────────
    # Check that at least 3 of the 4 target months are referenced
    month_keywords = {
        "2": ["2月", "情人节", "February", "二月"],
        "5": ["5月", "劳动节", "五月", "May"],
        "7": ["7月", "七月", "暑", "July"],
        "10": ["10月", "国庆", "十月", "October"],
    }
    months_found = []
    for month, keywords in month_keywords.items():
        if any(kw in content for kw in keywords):
            months_found.append(month)
    
    month_check_passed = len(months_found) >= 3
    checks.append({
        "name": "Target months covered (≥3 of 2,5,7,10)",
        "passed": month_check_passed,
        "detail": f"Found months: {months_found}. Need at least 3 of [2,5,7,10]."
    })
    if month_check_passed:
        total_score += 10

    # ── Check 4: Five elements present in activities ──────────────────────────
    five_elements = ["文化母体", "品牌契合", "活动命名", "促销指令", "超级符号"]
    elements_found = [el for el in five_elements if el in content]
    five_elements_passed = len(elements_found) >= 4
    checks.append({
        "name": "Five elements framework applied",
        "passed": five_elements_passed,
        "detail": f"Found elements: {elements_found}. Need ≥4 of 5."
    })
    if five_elements_passed:
        total_score += 15

    # ── Check 5: Scoring format present ───────────────────────────────────────
    # Look for score patterns like "= 92" or "总分" or "评分"
    score_patterns = [
        r'总分[：:]\s*\d+',
        r'=\s*\d{2,3}',
        r'评分[：:]',
        r'\d+\s*分',
    ]
    score_found = any(re.search(p, content) for p in score_patterns)
    checks.append({
        "name": "Scoring information present",
        "passed": score_found,
        "detail": "Score/评分 found in HTML." if score_found else "No scoring information found in HTML."
    })
    if score_found:
        total_score += 10

    # ── Check 6: Sub-dimension scores present (format: X+X+X+X+X = total) ───
    subdim_pattern = re.search(r'\d+\s*\+\s*\d+\s*\+\s*\d+\s*\+\s*\d+\s*\+\s*\d+\s*[=＝]\s*(\d+)', content)
    subdim_passed = subdim_pattern is not None
    checks.append({
        "name": "Five-dimension score breakdown present",
        "passed": subdim_passed,
        "detail": f"Found breakdown: '{subdim_pattern.group(0)}'" if subdim_passed else "No '5-part + sum' score pattern found. Each activity must show individual dimension scores."
    })
    if subdim_passed:
        total_score += 10

    # ── Check 7: No sub-80 activities should appear ───────────────────────────
    # Find all total scores in the document
    all_totals = re.findall(r'[=＝]\s*(\d+)', content)
    sub80_violations = [s for s in all_totals if int(s) < 80]
    no_sub80 = len(sub80_violations) == 0
    checks.append({
        "name": "No sub-80 activities included",
        "passed": no_sub80,
        "detail": f"No scores below 80 found." if no_sub80 else f"Found scores below 80: {sub80_violations}. These must be excluded per SKILL.md rules."
    })
    if no_sub80:
        total_score += 15

    # ── Check 8: Gold color for ≥90 activities ────────────────────────────────
    gold_indicators = ["gold", "#FFD700", "#ffd700", "金色", "爆款潜力", "golden"]
    gold_present = any(ind in content for ind in gold_indicators)
    checks.append({
        "name": "Gold styling for ≥90 'blockbuster' activities",
        "passed": gold_present,
        "detail": "Gold color indicator found for ≥90 score activities." if gold_present else "No gold styling found. ≥90 activities must have gold border/label."
    })
    if gold_present:
        total_score += 10

    # ── Check 9: Blue color for 80-89 activities ──────────────────────────────
    blue_indicators = ["blue", "#0000FF", "#1E90FF", "#4169E1", "蓝色", "#007BFF", "#2196F3", "#1976D2", "steelblue", "royalblue"]
    blue_present = any(ind.lower() in content.lower() for ind in blue_indicators)
    checks.append({
        "name": "Blue styling for 80-89 quality activities",
        "passed": blue_present,
        "detail": "Blue color indicator found for 80-89 score activities." if blue_present else "No blue styling found. 80-89 activities must have blue border."
    })
    if blue_present:
        total_score += 10

    # ── Check 10: Activity naming convention [品牌名]+[节日名] ────────────────
    # Look for activity names that combine brand and festival
    naming_patterns = [
        r'辣聚[^\s，。！]{2,10}节',
        r'辣聚[^\s，。！]{2,10}日',
        r'辣聚[^\s，。！]{2,8}宴',
        r'辣聚[^\s，。！]{2,8}活动',
        r'辣聚[^\s，。！]{2,8}季',
    ]
    naming_found = any(re.search(p, content) for p in naming_patterns)
    checks.append({
        "name": "Activity naming follows [品牌名]+[节日名] convention",
        "passed": naming_found,
        "detail": "Found activity names combining '辣聚' + festival name." if naming_found else "No activity names following '[品牌名]+[节日名]' pattern found."
    })
    if naming_found:
        total_score += 10

    # ── Check 11: 促销指令 has action→benefit structure ──────────────────────
    # Look for "做X→得Y" or similar explicit action+reward patterns
    promo_patterns = [
        r'[做参带分享拍邀][^\n，。]{2,20}[→得赢获赠免送享]',
        r'[A-Za-z\u4e00-\u9fff]+[→>]\s*[A-Za-z\u4e00-\u9fff]',
        r'凭[^\n，。]{2,15}[免减赠送享]',
        r'每[^\n，。]{2,15}[赠送享得]',
        r'[买点到][^\n，。]{2,15}[送减免赠]',
    ]
    promo_found = any(re.search(p, content) for p in promo_patterns)
    checks.append({
        "name": "促销指令 has explicit action→benefit structure",
        "passed": promo_found,
        "detail": "Found action→benefit pattern in 促销指令." if promo_found else "No clear 'do X → get Y' structure found in 促销指令."
    })
    if promo_found:
        total_score += 5

    # ── Check 12: Brand asset summary section ────────────────────────────────
    asset_indicators = ["品牌资产", "超级符号", "沸腾红锅", "热辣沸腾"]
    asset_summary_found = sum(1 for ind in asset_indicators if ind in content) >= 2
    checks.append({
        "name": "Brand asset summary section in HTML",
        "passed": asset_summary_found,
        "detail": "Brand asset summary with key brand elements found." if asset_summary_found else "Brand asset summary section missing or incomplete."
    })
    if asset_summary_found:
        total_score += 5

    # ── Final verdict ─────────────────────────────────────────────────────────
    # Must-pass checks (critical)
    critical_passed = (
        html_path is not None and
        brand_present and
        five_elements_passed and
        no_sub80
    )

    # Normalize score to 0-100
    max_possible = 10 + 5 + 10 + 15 + 10 + 10 + 15 + 10 + 10 + 10 + 5 + 5  # = 115, normalize
    normalized_score = round((total_score / 115) * 100, 1)

    overall_passed = critical_passed and normalized_score >= 55.0

    return {
        "passed": overall_passed,
        "score": normalized_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))