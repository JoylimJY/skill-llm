import sys
import json
import math
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight

    # Find the output file
    report_path = None
    candidates = list(Path(workspace_dir).rglob("monetization_report.json"))
    if candidates:
        report_path = candidates[0]

    add_check(
        "output_file_exists",
        report_path is not None,
        f"Found monetization_report.json at {report_path}" if report_path else "monetization_report.json not found anywhere in workspace",
        weight=1.0
    )

    if report_path is None:
        final_score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": False, "score": final_score, "checks": checks}

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        add_check("report_parseable", False, f"Could not parse JSON: {e}", weight=2.0)
        final_score = total_score / max_score if max_score > 0 else 0.0
        return {"passed": False, "score": final_score, "checks": checks}

    add_check("report_parseable", True, "Report is valid JSON", weight=1.0)

    # ============================================================
    # CHECK 1: Content Value Score Calculation
    # The rubric specifies exact max scores per sub-dimension.
    # raw_scores are given on /10 scale for all dims; agent must
    # apply them against rubric maximums:
    #
    # Content Quality (25pts):
    #   professionalism: raw=8, max=10  => 8
    #   practicality:    raw=9, max=10  => 9
    #   uniqueness:      raw=6, max=10, BUT rubric max=5 => must scale: min(6,10)/10*5 = 3.0
    #     (OR interpret as: score = min(raw, max_rubric) = min(6,5) = ... ambiguous)
    #     The most natural reading: uniqueness raw score out of 10 → scale to rubric max of 5: (6/10)*5=3
    #
    # Audience Value (25pts):
    #   demand_intensity:    raw=9, max=10  => 9
    #   payment_willingness: raw=8, max=10  => 8
    #   market_size:         raw=4, max=10, rubric max=5 => (4/10)*5=2
    #
    # Competitive Advantage (25pts):
    #   scarcity:    raw=8, max=10  => 8
    #   brand_power: raw=6, max=10  => 6
    #   trust:       raw=3, max=10, rubric max=5 => (3/10)*5=1.5
    #
    # Monetization Potential (25pts):
    #   multi_channel: raw=9, max=10  => 9
    #   repurchase:    raw=8, max=10  => 8
    #   virality:      raw=4, max=10, rubric max=5 => (4/10)*5=2
    #
    # Total = (8+9+3) + (9+8+2) + (8+6+1.5) + (9+8+2) = 20 + 19 + 15.5 + 19 = 73.5
    # => 4-star rating (60-79)
    # ============================================================

    expected_content_quality = 8 + 9 + (6/10)*5       # 20.0
    expected_audience_value  = 9 + 8 + (4/10)*5       # 19.0
    expected_comp_advantage  = 8 + 6 + (3/10)*5       # 15.5
    expected_monetize_pot    = 9 + 8 + (4/10)*5       # 19.0
    expected_total_score     = expected_content_quality + expected_audience_value + expected_comp_advantage + expected_monetize_pot
    # = 20 + 19 + 15.5 + 19 = 73.5

    # Accept range ±2 for score (in case of minor rounding)
    SCORE_TOLERANCE = 3.0

    try:
        # Look for total score in various common key names
        reported_score = None
        for key in ["total_score", "score", "overall_score", "content_value_score", "评分", "总分", "总评分"]:
            if key in report:
                reported_score = float(report[key])
                break
        # Also check nested
        if reported_score is None:
            for section_key in ["content_evaluation", "value_assessment", "evaluation", "内容价值评估"]:
                if section_key in report and isinstance(report[section_key], dict):
                    for key in ["total_score", "score", "overall_score", "总分"]:
                        if key in report[section_key]:
                            reported_score = float(report[section_key][key])
                            break

        score_ok = reported_score is not None and abs(reported_score - expected_total_score) <= SCORE_TOLERANCE
        add_check(
            "content_value_score_correct",
            score_ok,
            f"Expected total score ~{expected_total_score} (±{SCORE_TOLERANCE}), got {reported_score}",
            weight=2.0
        )
    except Exception as e:
        add_check("content_value_score_correct", False, f"Error checking score: {e}", weight=2.0)

    # CHECK 2: Star rating must be 4-star (60-79 range)
    try:
        star_rating = None
        report_str = json.dumps(report, ensure_ascii=False)
        # Check for 4-star indicators
        star_indicators_4 = ["⭐⭐⭐⭐", "4星", "四星", "4-star", "four star", "4 stars", "4⭐"]
        star_indicators_5 = ["⭐⭐⭐⭐⭐", "5星", "五星", "5-star"]
        
        # 73.5 is in range 60-79 => 4 stars (not 5)
        has_4_star = any(ind in report_str for ind in star_indicators_4)
        # Make sure it's not incorrectly 5 stars
        # ⭐⭐⭐⭐⭐ would also contain ⭐⭐⭐⭐, so check order
        has_5_star_explicit = "⭐⭐⭐⭐⭐" in report_str or "5星" in report_str or "五星" in report_str

        # More precise: look for exact 4-star (not 5-star superset)
        # Count occurrences
        import re
        star_pattern = re.findall(r'⭐+', report_str)
        four_star_found = any(len(s) == 4 for s in star_pattern)
        five_star_found = any(len(s) == 5 for s in star_pattern)

        rating_correct = (has_4_star or four_star_found or "4" in report_str) and not (five_star_found and not four_star_found)
        
        # Also check for numeric star rating
        for key in ["star_rating", "stars", "等级", "星级", "rating_stars"]:
            if key in report:
                val = report[key]
                if isinstance(val, (int, float)) and abs(float(val) - 4) < 0.5:
                    rating_correct = True
                    break
            
        add_check(
            "star_rating_4_stars",
            rating_correct,
            f"Score 73.5 should yield 4-star rating (60-79 range). Found 4-star: {four_star_found}, found 5-star only: {five_star_found and not four_star_found}",
            weight=1.5
        )
    except Exception as e:
        add_check("star_rating_4_stars", False, f"Error checking star rating: {e}", weight=1.5)

    # CHECK 3: Value Pricing Formula
    # user_value = 4000 CNY/month * 12 months = 48000 CNY
    # price = 48000 * 10% = 4800 CNY => recommended ~4799 or 4999 or similar
    expected_value_price = 4000 * 12 * 0.10  # = 4800
    PRICE_TOLERANCE = 500  # allow some rounding

    try:
        report_str = json.dumps(report, ensure_ascii=False)
        # Look for price near 4800
        import re
        numbers = re.findall(r'\b(\d{3,5})\b', report_str)
        numeric_vals = [int(n) for n in numbers]
        price_found = any(abs(v - expected_value_price) <= PRICE_TOLERANCE for v in numeric_vals)
        
        add_check(
            "value_pricing_formula_applied",
            price_found,
            f"Value pricing = 4000*12*10% = {expected_value_price} CNY. Found price near this value: {price_found}. Numbers found near range: {[v for v in numeric_vals if abs(v - expected_value_price) <= 1000]}",
            weight=2.0
        )
    except Exception as e:
        add_check("value_pricing_formula_applied", False, f"Error: {e}", weight=2.0)

    # CHECK 4: Revenue prediction formula: 月收入 = 流量 × 转化率 × 客单价
    # = 15000 * 0.025 * 399 = 149625 CNY
    expected_monthly_revenue = 15000 * 0.025 * 399  # = 149625
    REVENUE_TOLERANCE = 5000

    try:
        report_str = json.dumps(report, ensure_ascii=False)
        import re
        # Look for the monthly revenue value
        numbers = re.findall(r'\b(\d{4,7})\b', report_str)
        numeric_vals = [int(n) for n in numbers]
        revenue_found = any(abs(v - expected_monthly_revenue) <= REVENUE_TOLERANCE for v in numeric_vals)
        
        add_check(
            "revenue_prediction_formula_correct",
            revenue_found,
            f"月收入 = 15000 × 2.5% × 399 = {expected_monthly_revenue}. Found value near this: {revenue_found}. Nearby values: {[v for v in numeric_vals if abs(v - expected_monthly_revenue) <= 10000]}",
            weight=2.0
        )
    except Exception as e:
        add_check("revenue_prediction_formula_correct", False, f"Error: {e}", weight=2.0)

    # CHECK 5: Growth projection must have 4 time periods (1/3/6/12 months)
    try:
        report_str = json.dumps(report, ensure_ascii=False)
        has_month1  = "1" in report_str and ("第1个月" in report_str or "month_1" in report_str or "1个月" in report_str or "month1" in report_str.lower() or '"1"' in report_str)
        has_month3  = "第3个月" in report_str or "month_3" in report_str or "3个月" in report_str or "month3" in report_str.lower()
        has_month6  = "第6个月" in report_str or "month_6" in report_str or "6个月" in report_str or "month6" in report_str.lower()
        has_month12 = "第12个月" in report_str or "month_12" in report_str or "12个月" in report_str or "month12" in report_str.lower()
        
        # More flexible: look for any growth projection section with 4 entries
        growth_ok = (has_month3 and has_month6 and has_month12) or \
                    ("growth" in report_str.lower() and ("12" in report_str)) or \
                    ("增长" in report_str and "12" in report_str)
        
        add_check(
            "growth_projection_4_periods",
            growth_ok,
            f"Growth projection should cover months 1,3,6,12. Found month3:{has_month3}, month6:{has_month6}, month12:{has_month12}",
            weight=1.5
        )
    except Exception as e:
        add_check("growth_projection_4_periods", False, f"Error: {e}", weight=1.5)

    # CHECK 6: Channel recommendations must include knowledge payment channel (知识付费)
    try:
        report_str = json.dumps(report, ensure_ascii=False)
        has_knowledge_channel = any(kw in report_str for kw in [
            "知识付费", "录播课", "在线课程", "小鹅通", "千聊", "得到", "知乎Live",
            "online course", "knowledge", "训练营"
        ])
        add_check(
            "channel_recommendation_present",
            has_knowledge_channel,
            f"Report should recommend knowledge payment channel for professional content. Found: {has_knowledge_channel}",
            weight=1.0
        )
    except Exception as e:
        add_check("channel_recommendation_present", False, f"Error: {e}", weight=1.0)

    # CHECK 7: Tiered pricing structure (基础版/标准版/高级版)
    try:
        report_str = json.dumps(report, ensure_ascii=False)
        has_basic   = any(kw in report_str for kw in ["基础版", "基础", "basic", "Basic", "starter"])
        has_standard = any(kw in report_str for kw in ["标准版", "标准", "standard", "Standard"])
        has_premium = any(kw in report_str for kw in ["高级版", "高级", "premium", "Premium", "advanced", "Advanced"])
        tiered_ok = has_basic and has_standard and has_premium
        add_check(
            "tiered_pricing_structure",
            tiered_ok,
            f"Tiered pricing (基础/标准/高级) required. Found basic:{has_basic}, standard:{has_standard}, premium:{has_premium}",
            weight=1.5
        )
    except Exception as e:
        add_check("tiered_pricing_structure", False, f"Error: {e}", weight=1.5)

    # CHECK 8: Execution checklist present (at least reference to phases)
    try:
        report_str = json.dumps(report, ensure_ascii=False)
        has_checklist = any(kw in report_str for kw in [
            "执行清单", "checklist", "第1周", "准备期", "启动期", "稳定期", "增长期",
            "week", "phase", "阶段"
        ])
        add_check(
            "execution_checklist_present",
            has_checklist,
            f"Report should include an execution checklist/phases. Found: {has_checklist}",
            weight=1.0
        )
    except Exception as e:
        add_check("execution_checklist_present", False, f"Error: {e}", weight=1.0)

    # Final scoring
    final_score = total_score / max_score if max_score > 0 else 0.0
    passed = final_score >= 0.65 and checks[0]["passed"]  # Must have output file and pass majority

    return {
        "passed": passed,
        "score": round(final_score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))