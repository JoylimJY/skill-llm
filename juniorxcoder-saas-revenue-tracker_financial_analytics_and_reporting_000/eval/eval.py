import sys
import json
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── Locate the report file ──────────────────────────────────────────────
    report_files = list(workspace.rglob("revenue_intelligence_report.json"))
    if not report_files:
        checks.append({"name": "report_file_exists", "passed": False,
                        "detail": "revenue_intelligence_report.json not found anywhere in workspace."})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    report_path = report_files[0]
    checks.append({"name": "report_file_exists", "passed": True,
                    "detail": f"Found at {report_path}"})
    total_score += 0.05

    try:
        with open(report_path) as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "report_valid_json", "passed": False,
                        "detail": f"Failed to parse JSON: {e}"})
        print(json.dumps({"passed": False, "score": total_score, "checks": checks}))
        return

    checks.append({"name": "report_valid_json", "passed": True, "detail": "Valid JSON."})
    total_score += 0.05

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 1: MRR Milestone Assessment
    # Month 1: $820 < $1000 → MISSED
    # Month 3: $2650 < $3000 → MISSED
    # Month 6: $5100 < $7500 → MISSED
    # Month 8: N/A (not a standard checkpoint month for month 12 target)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        milestones = report.get("mrr_milestone_assessment", {})
        
        # Month 1 check
        m1 = milestones.get("month_1", {})
        m1_target = m1.get("target", 0)
        m1_actual = m1.get("actual", 0)
        m1_met = m1.get("met", None)
        m1_correct = (
            abs(m1_target - 1000) <= 1 and
            abs(m1_actual - 820) <= 5 and
            m1_met == False
        )
        checks.append({"name": "milestone_month1_correct",
                        "passed": m1_correct,
                        "detail": f"month_1 target={m1_target}, actual={m1_actual}, met={m1_met}. Expected target=1000, actual=820, met=false."})
        if m1_correct:
            total_score += 0.08

        # Month 3 check
        m3 = milestones.get("month_3", {})
        m3_target = m3.get("target", 0)
        m3_actual = m3.get("actual", 0)
        m3_met = m3.get("met", None)
        m3_correct = (
            abs(m3_target - 3000) <= 1 and
            abs(m3_actual - 2650) <= 5 and
            m3_met == False
        )
        checks.append({"name": "milestone_month3_correct",
                        "passed": m3_correct,
                        "detail": f"month_3 target={m3_target}, actual={m3_actual}, met={m3_met}. Expected target=3000, actual=2650, met=false."})
        if m3_correct:
            total_score += 0.08

        # Month 6 check
        m6 = milestones.get("month_6", {})
        m6_target = m6.get("target", 0)
        m6_actual = m6.get("actual", 0)
        m6_met = m6.get("met", None)
        m6_correct = (
            abs(m6_target - 7500) <= 1 and
            abs(m6_actual - 5100) <= 5 and
            m6_met == False
        )
        checks.append({"name": "milestone_month6_correct",
                        "passed": m6_correct,
                        "detail": f"month_6 target={m6_target}, actual={m6_actual}, met={m6_met}. Expected target=7500, actual=5100, met=false."})
        if m6_correct:
            total_score += 0.08

    except Exception as e:
        checks.append({"name": "milestone_assessment_error", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 2: Business Status Classification
    # Month 7 MRR: $5050, Month 8 MRR: $4890 → declining 2 consecutive months
    # Churn month 7: 7/59 = 11.86% > 10% → High churn
    # Churn month 8: 8/57 = 14.04% > 10% → High churn
    # Status should be "The Ugly" (declining revenue for 2+ months) OR at minimum "The Bad"
    # The skill says "The Ugly": declining revenue for 3+ months → not yet 3
    # "The Bad": high churn (>10% monthly) ✓, flat growth for 2+ months (it's actually declining)
    # Declining for 2 months → "The Ugly" is triggered by 3+ but declining is worse than flat
    # Most conservative reading: "The Bad" minimum, "The Ugly" if agent interprets 2 months declining as entering Ugly territory
    # We'll accept either "The Bad" or "The Ugly" but NOT "The Good"
    # ═══════════════════════════════════════════════════════════════════════
    try:
        business_status = report.get("business_status", {})
        status_category = business_status.get("category", "").strip()
        
        # Must NOT be "The Good" - revenue declining and churn >10%
        not_the_good = "good" not in status_category.lower()
        checks.append({"name": "business_status_not_the_good",
                        "passed": not_the_good,
                        "detail": f"Status category='{status_category}'. Must not be 'The Good' given declining MRR and >10% churn."})
        if not_the_good:
            total_score += 0.05

        is_bad_or_ugly = ("bad" in status_category.lower() or "ugly" in status_category.lower())
        checks.append({"name": "business_status_bad_or_ugly",
                        "passed": is_bad_or_ugly,
                        "detail": f"Status='{status_category}'. Expected 'The Bad' or 'The Ugly'."})
        if is_bad_or_ugly:
            total_score += 0.07

    except Exception as e:
        checks.append({"name": "business_status_error", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 3: Churn Rate Calculation
    # Month 7 churn: 7 churned / 59 (start of month) ≈ 11.86%  → > 10% = "Bad"
    # Month 8 churn: 8 churned / 57 (start of month) ≈ 14.04%  → > 10% = "Bad"
    # Accept churn calculation using active_customers at start of month
    # ═══════════════════════════════════════════════════════════════════════
    try:
        churn_data = report.get("churn_analysis", {})
        
        # Month 7 churn rate check (11-12% acceptable range)
        m7_churn = churn_data.get("month_7_churn_rate", None)
        if m7_churn is None:
            m7_churn = churn_data.get("month_7", {}).get("churn_rate", None)
        
        if m7_churn is not None:
            m7_churn_val = float(m7_churn) if m7_churn > 1 else float(m7_churn) * 100
            m7_churn_correct = 10.0 <= m7_churn_val <= 14.0
            checks.append({"name": "churn_month7_correct",
                            "passed": m7_churn_correct,
                            "detail": f"Month 7 churn rate ≈ {m7_churn_val:.2f}%. Expected ~11.86% (7/59). Got {m7_churn}."})
            if m7_churn_correct:
                total_score += 0.07
        else:
            checks.append({"name": "churn_month7_missing", "passed": False,
                            "detail": "month_7_churn_rate not found in churn_analysis."})

        # Month 8 churn rate check (12-16% acceptable range)
        m8_churn = churn_data.get("month_8_churn_rate", None)
        if m8_churn is None:
            m8_churn = churn_data.get("month_8", {}).get("churn_rate", None)
        
        if m8_churn is not None:
            m8_churn_val = float(m8_churn) if m8_churn > 1 else float(m8_churn) * 100
            m8_churn_correct = 12.0 <= m8_churn_val <= 16.5
            checks.append({"name": "churn_month8_correct",
                            "passed": m8_churn_correct,
                            "detail": f"Month 8 churn rate ≈ {m8_churn_val:.2f}%. Expected ~14.04% (8/57). Got {m8_churn}."})
            if m8_churn_correct:
                total_score += 0.07
        else:
            checks.append({"name": "churn_month8_missing", "passed": False,
                            "detail": "month_8_churn_rate not found in churn_analysis."})

        # Churn trend flag: both months > 10% threshold
        high_churn_flag = churn_data.get("exceeds_bad_threshold", None)
        if high_churn_flag is None:
            high_churn_flag = churn_data.get("above_10_percent_threshold", None)
        churn_flag_correct = high_churn_flag == True
        checks.append({"name": "churn_high_flag_correct",
                        "passed": churn_flag_correct,
                        "detail": f"exceeds_bad_threshold={high_churn_flag}. Expected True (both months >10%)."})
        if churn_flag_correct:
            total_score += 0.04

    except Exception as e:
        checks.append({"name": "churn_analysis_error", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 4: Customer Segmentation (Whale / Core / Trial classification)
    # 57 active customers
    # Top 20% = ~11 customers (11.4 → 11 or 12 acceptable)
    # Whale revenue = $3939 / Total MRR $4890 ≈ 80.6% → Confirms Pareto rule
    # ═══════════════════════════════════════════════════════════════════════
    try:
        segments = report.get("customer_segments", {})
        
        # Whale count: 20% of 57 active customers = 11-12
        whale_count = segments.get("whales", {}).get("count", None)
        if whale_count is None:
            whale_count = segments.get("whale_count", None)
        
        whale_count_correct = whale_count is not None and 10 <= int(whale_count) <= 12
        checks.append({"name": "whale_count_correct",
                        "passed": whale_count_correct,
                        "detail": f"Whale count={whale_count}. Expected 11-12 (20% of 57 active customers)."})
        if whale_count_correct:
            total_score += 0.06

        # Whale revenue percentage: should be ~80%
        whale_revenue_pct = segments.get("whales", {}).get("revenue_percentage", None)
        if whale_revenue_pct is None:
            whale_revenue_pct = segments.get("whale_revenue_percentage", None)
        
        if whale_revenue_pct is not None:
            wpct = float(whale_revenue_pct) if float(whale_revenue_pct) <= 1 else float(whale_revenue_pct) / 100
            whale_pct_correct = 0.72 <= wpct <= 0.88
            checks.append({"name": "whale_revenue_pct_correct",
                            "passed": whale_pct_correct,
                            "detail": f"Whale revenue %={whale_revenue_pct}. Expected ~80% (±8pp)."})
            if whale_pct_correct:
                total_score += 0.05
        else:
            checks.append({"name": "whale_revenue_pct_missing", "passed": False,
                            "detail": "Whale revenue percentage not found."})

    except Exception as e:
        checks.append({"name": "customer_segmentation_error", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 5: Revenue Forecasting (3-scenario model)
    # Latest month growth rate: (4890-5050)/5050 = -3.168%
    # Base Case: MRR * (1 + growth_rate) → 4890 * (1 - 0.03168) = $4735 approx
    # Optimistic: growth_rate * 1.5 acceleration → 4890 * (1 + (-0.03168 * 1.5))
    #            = 4890 * (1 - 0.04752) = $4657 approx
    # Pessimistic: growth_rate * 0.75 deceleration → 4890 * (1 + (-0.03168 * 0.75))
    #            = 4890 * (1 - 0.02376) = $4774 approx
    # NOTE: Some agents may interpret "acceleration" differently for negative growth.
    # We'll check that the 3 scenarios exist and have the right relative ordering.
    # For negative growth: optimistic (less decline) > base > pessimistic (more decline)
    # ═══════════════════════════════════════════════════════════════════════
    try:
        forecast = report.get("revenue_forecast", {})
        
        has_base = "base_case" in forecast or "base" in forecast
        has_optimistic = "optimistic_case" in forecast or "optimistic" in forecast
        has_pessimistic = "pessimistic_case" in forecast or "pessimistic" in forecast
        
        all_scenarios_present = has_base and has_optimistic and has_pessimistic
        checks.append({"name": "forecast_three_scenarios_present",
                        "passed": all_scenarios_present,
                        "detail": f"base={has_base}, optimistic={has_optimistic}, pessimistic={has_pessimistic}. All three required."})
        if all_scenarios_present:
            total_score += 0.06

        # Extract MRR values
        def get_forecast_mrr(fc, key1, key2):
            section = fc.get(key1, fc.get(key2, {}))
            if isinstance(section, dict):
                return section.get("next_month_mrr", section.get("projected_mrr", section.get("mrr", None)))
            return None

        base_mrr = get_forecast_mrr(forecast, "base_case", "base")
        opt_mrr = get_forecast_mrr(forecast, "optimistic_case", "optimistic")
        pess_mrr = get_forecast_mrr(forecast, "pessimistic_case", "pessimistic")

        if base_mrr and opt_mrr and pess_mrr:
            base_mrr = float(base_mrr)
            opt_mrr = float(opt_mrr)
            pess_mrr = float(pess_mrr)

            # Base case: ~$4735 (allow ±$200)
            base_correct = 4450 <= base_mrr <= 5050
            checks.append({"name": "forecast_base_case_value",
                            "passed": base_correct,
                            "detail": f"Base case MRR={base_mrr}. Expected ~$4735 (range $4450-$5050)."})
            if base_correct:
                total_score += 0.06

            # For declining growth: pessimistic < base < optimistic (less decline is optimistic)
            order_correct = pess_mrr <= base_mrr <= opt_mrr or opt_mrr <= base_mrr <= pess_mrr
            # Accept either ordering interpretation, but they must be different
            scenarios_distinct = not (abs(base_mrr - opt_mrr) < 1 and abs(base_mrr - pess_mrr) < 1)
            checks.append({"name": "forecast_scenarios_distinct",
                            "passed": scenarios_distinct,
                            "detail": f"base={base_mrr}, optimistic={opt_mrr}, pessimistic={pess_mrr}. Scenarios must differ."})
            if scenarios_distinct:
                total_score += 0.04

            # Check multipliers: optimistic uses 1.5x growth acceleration, pessimistic 0.75x deceleration
            # Growth rate M7→M8: (4890-5050)/5050 = -0.031683...
            growth_rate = (4890 - 5050) / 5050
            expected_base = 4890 * (1 + growth_rate)  # ~4735
            expected_opt_accel = 4890 * (1 + growth_rate * 1.5)  # more negative = lower OR less negative = higher
            expected_pess_decel = 4890 * (1 + growth_rate * 0.75)  # less decline
            
            # Key check: optimistic multiplier is 1.5, pessimistic is 0.75
            # Optimistic for negative growth = less decline = growth_rate * 0.75 applied → higher MRR
            # Pessimistic for negative growth = more decline = growth_rate * 1.5 applied → lower MRR
            # Some agents may interpret optimistic as 50% acceleration of absolute growth rate
            # Check that the spread uses roughly 1.5 and 0.75 factors
            spread_opt = abs(opt_mrr - expected_base)
            spread_pess = abs(pess_mrr - expected_base)
            
            # Ratio of spreads should be ~2:1 (1.5/0.75 = 2)
            if spread_pess > 0 and spread_opt > 0:
                ratio = max(spread_opt, spread_pess) / min(spread_opt, spread_pess)
                ratio_correct = 1.5 <= ratio <= 2.5
                checks.append({"name": "forecast_multiplier_ratio_correct",
                                "passed": ratio_correct,
                                "detail": f"Spread ratio optimistic/pessimistic ≈ {ratio:.2f}. Expected ~2.0 (1.5x vs 0.75x multipliers)."})
                if ratio_correct:
                    total_score += 0.07

    except Exception as e:
        checks.append({"name": "forecast_error", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 6: LTV:CAC Analysis
    # Must flag whether ratio meets the 3:1 minimum from SKILL.md
    # ═══════════════════════════════════════════════════════════════════════
    try:
        ltv_cac = report.get("ltv_cac_analysis", {})
        
        minimum_ratio = ltv_cac.get("minimum_required_ratio", None)
        # Should be 3 or 3.0
        ratio_correct = minimum_ratio is not None and abs(float(minimum_ratio) - 3.0) < 0.1
        checks.append({"name": "ltv_cac_minimum_ratio_correct",
                        "passed": ratio_correct,
                        "detail": f"minimum_required_ratio={minimum_ratio}. Expected 3.0 (3:1 from SKILL.md)."})
        if ratio_correct:
            total_score += 0.06

        # Average LTV:CAC across customers should be computed
        avg_ratio = ltv_cac.get("average_ratio", ltv_cac.get("avg_ratio", None))
        avg_ratio_present = avg_ratio is not None
        checks.append({"name": "ltv_cac_avg_ratio_present",
                        "passed": avg_ratio_present,
                        "detail": f"average_ratio={avg_ratio}. Must be computed from customer_profiles data."})
        if avg_ratio_present:
            total_score += 0.03

    except Exception as e:
        checks.append({"name": "ltv_cac_error", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 7: Burn Rate and Runway
    # Month 8 expenses: 210+350+2100+6000+260 = $8,920
    # Month 8 MRR: $4,890
    # Monthly burn (net): $8,920 - $4,890 = $4,030
    # ═══════════════════════════════════════════════════════════════════════
    try:
        cash_flow = report.get("cash_flow_analysis", {})
        
        burn_rate = cash_flow.get("monthly_burn_rate", cash_flow.get("burn_rate", None))
        if burn_rate is not None:
            burn_val = float(burn_rate)
            # Gross burn: ~$8920, Net burn: ~$4030
            burn_correct = (3500 <= burn_val <= 9500)
            checks.append({"name": "burn_rate_plausible",
                            "passed": burn_correct,
                            "detail": f"burn_rate={burn_val}. Expected net ~$4,030 or gross ~$8,920."})
            if burn_correct:
                total_score += 0.04
        else:
            checks.append({"name": "burn_rate_missing", "passed": False,
                            "detail": "monthly_burn_rate not found in cash_flow_analysis."})

        # Break-even MRR should equal total monthly expenses (~$8920)
        breakeven = cash_flow.get("breakeven_mrr", cash_flow.get("break_even_mrr", None))
        if breakeven is not None:
            be_val = float(breakeven)
            breakeven_correct = 8000 <= be_val <= 9500
            checks.append({"name": "breakeven_mrr_correct",
                            "passed": breakeven_correct,
                            "detail": f"breakeven_mrr={be_val}. Expected ~$8,920 (month 8 total expenses)."})
            if breakeven_correct:
                total_score += 0.04
        else:
            checks.append({"name": "breakeven_mrr_missing", "passed": False,
                            "detail": "breakeven_mrr not found in cash_flow_analysis."})

    except Exception as e:
        checks.append({"name": "cash_flow_error", "passed": False, "detail": str(e)})

    # ═══════════════════════════════════════════════════════════════════════
    # CHECK 8: Red Flags section present and relevant
    # SKILL.md: Red Flags include "MRR declining for 2+ months" → this triggers here
    # ═══════════════════════════════════════════════════════════════════════
    try:
        red_flags = report.get("red_flags", [])
        if isinstance(red_flags, list):
            has_decline_flag = any(
                "declin" in str(f).lower() or "mrr" in str(f).lower()
                for f in red_flags
            )
            checks.append({"name": "red_flags_mrr_decline",
                            "passed": has_decline_flag,
                            "detail": f"red_flags list has {len(red_flags)} items. Must include MRR decline flag."})
            if has_decline_flag:
                total_score += 0.05
        elif isinstance(red_flags, dict):
            has_decline_flag = any(
                "declin" in str(v).lower() or "mrr" in str(v).lower()
                for v in red_flags.values()
            )
            checks.append({"name": "red_flags_mrr_decline",
                            "passed": has_decline_flag,
                            "detail": f"red_flags dict. Must include MRR decline. Keys: {list(red_flags.keys())}"})
            if has_decline_flag:
                total_score += 0.05
        else:
            checks.append({"name": "red_flags_format",
                            "passed": False,
                            "detail": f"red_flags is neither list nor dict: type={type(red_flags)}"})

    except Exception as e:
        checks.append({"name": "red_flags_error", "passed": False, "detail": str(e)})

    # ── Final determination ─────────────────────────────────────────────────
    # Normalize score to [0, 1]
    total_score = min(total_score, 1.0)

    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)

    # Must pass at minimum: file exists, valid JSON, at least 2 milestone checks,
    # business status not "The Good", churn analysis, and forecasting
    critical_checks = [
        "report_file_exists",
        "report_valid_json",
        "milestone_month1_correct",
        "milestone_month6_correct",
        "business_status_bad_or_ugly",
        "forecast_three_scenarios_present",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )

    overall_passed = critical_passed and total_score >= 0.55

    result = {
        "passed": overall_passed,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "invocation", "passed": False, "detail": "Usage: eval_script.py <workspace_dir>"}
        ]}))
        sys.exit(1)
    evaluate(sys.argv[1])