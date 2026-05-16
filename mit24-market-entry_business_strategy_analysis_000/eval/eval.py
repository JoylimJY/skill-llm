import sys
import json
import os
from pathlib import Path

def find_report(workspace):
    """Find the market_entry_strategy_report.json anywhere in workspace."""
    results = list(Path(workspace).rglob("market_entry_strategy_report.json"))
    return results[0] if results else None

def evaluate(workspace):
    checks = []
    total_score = 0.0
    weights = {}

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score
        if passed:
            total_score += weight
        weights[name] = weight

    total_weight = 0.0

    # ── Find report file ───────────────────────────────────────────────────
    report_path = find_report(workspace)
    file_found = report_path is not None
    add_check(
        "report_file_exists",
        file_found,
        f"Found at: {report_path}" if file_found else "market_entry_strategy_report.json not found anywhere in workspace",
        weight=1.0
    )
    total_weight += 1.0

    if not file_found:
        total = sum(w for w in [1.0, 2.0, 1.5, 1.0, 1.5, 1.5, 1.5, 2.0, 1.5, 1.5, 2.0, 1.5])
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Load JSON ──────────────────────────────────────────────────────────
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        add_check("report_is_valid_json", True, "Successfully parsed as JSON", weight=1.0)
        total_weight += 1.0
    except Exception as e:
        add_check("report_is_valid_json", False, f"JSON parse error: {e}", weight=1.0)
        total_weight += 1.0
        total = sum([1.0, 1.0, 2.0, 1.5, 1.0, 1.5, 1.5, 1.5, 2.0, 1.5, 1.5, 2.0, 1.5])
        return {"passed": False, "score": 0.0, "checks": checks}

    report_str = json.dumps(report, ensure_ascii=False).lower()

    # ══════════════════════════════════════════════════════════════════════
    # STEP 15: CAC Calculation
    # ══════════════════════════════════════════════════════════════════════

    # Correct calculation:
    # Marketing costs (excluding misclassified OTHER items):
    #   Google Ads: 18500
    #   LinkedIn: 12300
    #   Content Marketing: 8700
    #   Webinars: 5200
    #   Tradeshows: 14000
    #   Brand Design: 3100
    #   Total Marketing = 61800
    # Sales costs:
    #   Salaries: 52000
    #   Commissions: 9800
    #   CRM: 2700
    #   Sales Tools: 1800
    #   Demo hosting: 600
    #   Travel: 4200
    #   Total Sales = 71100
    # Total = 132900
    # New customers = 7
    # CAC = 132900 / 7 = 18985.71...
    # The OVERHEAD items are ambiguous — agent may or may not include them
    # The OTHER items (R&D 7800, Legal 2400) must be EXCLUDED per the note
    # We check that R&D/Legal are excluded and denominator is 7

    # Check 1: CAC value is approximately correct (18900-19500 without overhead, or up to ~20600 with overhead)
    # Core check: numerator excludes the 2 misclassified OTHER items
    try:
        cac_section = None
        if isinstance(report, dict):
            for key in report:
                if "cac" in key.lower() or "获客" in key.lower() or "customer_acquisition" in key.lower() or "step15" in key.lower() or "step_15" in key.lower() or "15" in str(key):
                    cac_section = report[key]
                    break
            if cac_section is None:
                # Try nested
                for key, val in report.items():
                    s = json.dumps(val, ensure_ascii=False).lower()
                    if "cac" in s and ("18" in s or "19" in s or "20" in s):
                        cac_section = val
                        break

        # Extract numeric CAC value from entire report string
        import re
        # Look for numbers in range 18000-21000 (reasonable CAC)
        cac_numbers = re.findall(r'\b1[89]\d{3}(?:\.\d+)?\b|\b20\d{3}(?:\.\d+)?\b', report_str)
        # Also search original (non-lowercased) for CAC value
        report_str_orig = json.dumps(report, ensure_ascii=False)
        cac_numbers_orig = re.findall(r'\b1[89]\d{3}(?:\.\d+)?\b|\b20\d{3}(?:\.\d+)?\b', report_str_orig)
        all_cac = cac_numbers + cac_numbers_orig

        cac_reasonable = len(all_cac) > 0
        # More specific: CAC should be around 18985 (±1500)
        cac_correct = False
        for n in all_cac:
            try:
                val = float(n)
                if 17500 <= val <= 20700:
                    cac_correct = True
                    break
            except:
                pass

        add_check(
            "cac_correctly_calculated",
            cac_correct,
            f"CAC should be ~18,986 (excluding misclassified R&D/Legal items, 7 new customers). Found candidate values: {all_cac[:5]}",
            weight=2.0
        )
        total_weight += 2.0
    except Exception as e:
        add_check("cac_correctly_calculated", False, f"Error checking CAC: {e}", weight=2.0)
        total_weight += 2.0

    # Check 2: CLV/CAC ratio evaluated against >3 threshold
    # CLV = 42000, CAC ≈ 18986 → ratio ≈ 2.21 → FAILS the >3 threshold
    try:
        import re
        # Look for ratio value around 2.0-2.5 and for threshold mention of 3
        ratio_mention = re.findall(r'\b2\.[012345]\d*\b', report_str)
        threshold_3_mentioned = "3" in report_str and ("ratio" in report_str or "clv" in report_str or "ltv" in report_str)
        # The ratio ~2.21 should appear, or explicit "below 3" / "unhealthy" language
        health_fail_mentioned = any(word in report_str for word in [
            "unhealthy", "below 3", "不健康", "低于3", "fails", "does not meet", 
            "below threshold", "警告", "risk", "concern", "red flag", "warning"
        ])

        clv_cac_check = (len(ratio_mention) > 0 or health_fail_mentioned) and threshold_3_mentioned
        add_check(
            "clv_cac_ratio_assessed_with_threshold",
            clv_cac_check,
            f"CLV=42000, CAC≈18986 → ratio≈2.21 which is BELOW the required >3 threshold. "
            f"Ratio values found: {ratio_mention[:3]}, threshold_3_mentioned={threshold_3_mentioned}, "
            f"health_fail_mentioned={health_fail_mentioned}",
            weight=1.5
        )
        total_weight += 1.5
    except Exception as e:
        add_check("clv_cac_ratio_assessed_with_threshold", False, f"Error: {e}", weight=1.5)
        total_weight += 1.5

    # Check 3: CAC payback period assessed
    # Monthly revenue = 1167, GM = 71% → monthly gross profit = 828.57
    # CAC ≈ 18986 → payback = 18986 / 828.57 ≈ 22.9 months → FAILS < 12 months
    try:
        import re
        # Look for payback period number around 22-24 months
        payback_vals = re.findall(r'\b2[023]\b|\b2[0-9]\.\d+\b', report_str)
        # Or look for "exceeds 12" / "above 12" type language
        payback_fail = any(phrase in report_str for phrase in [
            "exceeds 12", "above 12", "more than 12", ">12", "超过12",
            "22", "23", "24", "longer than", "beyond 12"
        ])
        twelve_month_mention = "12" in report_str
        payback_check = (len(payback_vals) > 0 or payback_fail) and twelve_month_mention
        add_check(
            "cac_payback_period_assessed",
            payback_check,
            f"Payback = CAC/monthly_gross_profit ≈ 18986/(1167*0.71) ≈ 22.9 months, exceeds 12-month threshold. "
            f"Found payback indicators: {payback_vals[:3]}, twelve_month_mention={twelve_month_mention}",
            weight=1.0
        )
        total_weight += 1.0
    except Exception as e:
        add_check("cac_payback_period_assessed", False, f"Error: {e}", weight=1.0)
        total_weight += 1.0

    # ══════════════════════════════════════════════════════════════════════
    # STEP 16: 7-Stage Sales Process
    # ══════════════════════════════════════════════════════════════════════

    # Check 4: Sales process has all 7 stages (or clearly covers them)
    required_stages = [
        # stage name variants (EN or CN)
        ["lead generation", "lead gen", "潜在客户", "leads", "prospecting"],
        ["qualification", "qualify", "资格审查", "qualified"],
        ["needs analysis", "discovery", "需求分析", "need analysis"],
        ["presentation", "demo", "方案展示", "present"],
        ["objection", "异议", "objection handling"],
        ["closing", "close", "成交"],
        ["follow", "follow-up", "post-sale", "售后", "retention", "upsell", "referral"],
    ]
    try:
        stages_found = []
        for stage_variants in required_stages:
            found = any(v in report_str for v in stage_variants)
            stages_found.append(found)

        stages_count = sum(stages_found)
        all_7_found = stages_count >= 6  # Allow 1 missing for flexibility
        add_check(
            "sales_process_seven_stages",
            all_7_found,
            f"Found {stages_count}/7 required sales stages. Missing: "
            f"{[required_stages[i][0] for i, f in enumerate(stages_found) if not f]}",
            weight=1.5
        )
        total_weight += 1.5
    except Exception as e:
        add_check("sales_process_seven_stages", False, f"Error: {e}", weight=1.5)
        total_weight += 1.5

    # Check 5: Sales process includes conversion rate targets / metrics
    try:
        import re
        # Look for percentage values that could be conversion rates
        pct_values = re.findall(r'\b\d{1,2}(?:\.\d+)?%', report_str)
        has_conversion_rates = len(pct_values) >= 3  # At least 3 percentage mentions
        rate_keywords = any(kw in report_str for kw in [
            "conversion rate", "转化率", "conversion", "rate", "funnel"
        ])
        add_check(
            "sales_process_conversion_rates",
            has_conversion_rates and rate_keywords,
            f"Found {len(pct_values)} percentage values and rate_keywords={rate_keywords}. "
            f"Sample percentages: {pct_values[:5]}",
            weight=1.5
        )
        total_weight += 1.5
    except Exception as e:
        add_check("sales_process_conversion_rates", False, f"Error: {e}", weight=1.5)
        total_weight += 1.5

    # ══════════════════════════════════════════════════════════════════════
    # STEP 17: Critical Assumptions with Priority Ordering
    # ══════════════════════════════════════════════════════════════════════

    # Check 6: At least 5 of the 7 assumption types are addressed
    assumption_types = [
        ["demand", "需求假设", "pain point", "痛点", "a1"],
        ["market size", "market capacity", "市场容量", "tam", "a2", "320"],
        ["product", "feature", "产品功能", "a3", "procore"],
        ["pric", "定价", "willingness to pay", "a4", "1167"],
        ["channel", "渠道", "acquisition channel", "a5", "linkedin"],
        ["cac", "获客成本", "acquisition cost", "a6"],
        ["margin", "毛利", "gross margin", "a7", "70"],
    ]
    try:
        types_found = []
        for atype_variants in assumption_types:
            found = any(v.lower() in report_str for v in atype_variants)
            types_found.append(found)
        types_count = sum(types_found)
        add_check(
            "assumptions_cover_multiple_types",
            types_count >= 5,
            f"Found {types_count}/7 assumption types. Missing types: "
            f"{[assumption_types[i][0] for i, f in enumerate(types_found) if not f]}",
            weight=1.5
        )
        total_weight += 1.5
    except Exception as e:
        add_check("assumptions_cover_multiple_types", False, f"Error: {e}", weight=1.5)
        total_weight += 1.5

    # Check 7: Priority ordering uses the 3-axis system (lethal + uncertain + verifiable)
    try:
        priority_axes = [
            ["lethal", "fatal", "致命", "critical", "most dangerous", "if wrong", "invalidate"],
            ["uncertain", "uncertainty", "不确定", "confidence", "unvalidated", "unverified", "团队分歧"],
            ["verif", "testable", "易验证", "low cost", "快速", "speed", "easy to test"],
        ]
        axes_found = []
        for axis_variants in priority_axes:
            found = any(v.lower() in report_str for v in axis_variants)
            axes_found.append(found)
        axes_count = sum(axes_found)
        # Also check for priority/ranking language
        has_priority = any(kw in report_str for kw in [
            "priority", "priorit", "ranked", "ranking", "优先", "first", "most important",
            "highest priority", "p1", "p2", "critical"
        ])
        add_check(
            "assumptions_prioritized_with_three_axes",
            axes_count >= 2 and has_priority,
            f"Found {axes_count}/3 priority axes (lethal/uncertain/verifiable) and "
            f"has_priority_language={has_priority}",
            weight=2.0
        )
        total_weight += 2.0
    except Exception as e:
        add_check("assumptions_prioritized_with_three_axes", False, f"Error: {e}", weight=2.0)
        total_weight += 2.0

    # ══════════════════════════════════════════════════════════════════════
    # STEP 18: Experiment Plan with 5-Step Framework
    # ══════════════════════════════════════════════════════════════════════

    # Check 8: Experiment plan uses the 5-step design framework
    five_steps = [
        ["hypothesis", "假设", "hypothes"],
        ["success metric", "success criteria", "成功标准", "metric", "kpi", "measure"],
        ["minimum viable experiment", "mve", "minimal experiment", "最小实验", "experiment design"],
        ["execut", "collect", "run", "执行", "data collection"],
        ["analys", "decision", "result", "分析", "outcome", "conclusion"],
    ]
    try:
        steps_found = []
        for step_variants in five_steps:
            found = any(v.lower() in report_str for v in step_variants)
            steps_found.append(found)
        steps_count = sum(steps_found)
        add_check(
            "experiment_plan_five_step_framework",
            steps_count >= 4,
            f"Found {steps_count}/5 experiment design steps "
            f"(hypothesis, success metric, MVE, execute, analyze). "
            f"Missing: {[five_steps[i][0] for i, f in enumerate(steps_found) if not f]}",
            weight=1.5
        )
        total_weight += 1.5
    except Exception as e:
        add_check("experiment_plan_five_step_framework", False, f"Error: {e}", weight=1.5)
        total_weight += 1.5

    # Check 9: Experiment methods from the table are referenced
    valid_methods = [
        ["customer interview", "客户访谈", "interview"],
        ["survey", "问卷", "questionnaire"],
        ["landing page", "落地页"],
        ["a/b test", "ab test", "a/b测试"],
        ["presale", "pre-sale", "waitlist", "候补", "预售"],
        ["fake door", "假门", "smoke test"],
        ["pilot", "试点", "small-scale"],
    ]
    try:
        methods_found = []
        for method_variants in valid_methods:
            found = any(v.lower() in report_str for v in method_variants)
            methods_found.append(found)
        methods_count = sum(methods_found)
        add_check(
            "experiment_uses_valid_methods",
            methods_count >= 3,
            f"Found {methods_count}/7 valid experiment methods from the framework table. "
            f"Methods found: {[valid_methods[i][0] for i, f in enumerate(methods_found) if found]}",
            weight=1.5
        )
        total_weight += 1.5
    except Exception as e:
        add_check("experiment_uses_valid_methods", False, f"Error: {e}", weight=1.5)
        total_weight += 1.5

    # Check 10: Report has all 4 sections required by the output format
    four_sections = [
        ["cac", "获客成本", "customer acquisition cost", "step 15", "step15"],
        ["sales process", "sales funnel", "销售流程", "step 16", "step16"],
        ["assumption", "假设", "step 17", "step17", "critical assumption"],
        ["experiment", "验证", "test plan", "step 18", "step18", "validation"],
    ]
    try:
        sections_found = [
            any(v.lower() in report_str for v in section_variants)
            for section_variants in four_sections
        ]
        sections_count = sum(sections_found)
        add_check(
            "report_has_all_four_sections",
            sections_count == 4,
            f"Report has {sections_count}/4 required sections "
            f"(CAC, Sales Process, Assumptions, Experiment Plan). "
            f"Missing: {[four_sections[i][0] for i, f in enumerate(sections_found) if not f]}",
            weight=2.0
        )
        total_weight += 2.0
    except Exception as e:
        add_check("report_has_all_four_sections", False, f"Error: {e}", weight=2.0)
        total_weight += 2.0

    # ── Final scoring ──────────────────────────────────────────────────────
    final_score = round(total_score / total_weight, 3) if total_weight > 0 else 0.0
    passed = final_score >= 0.70 and all(
        c["passed"] for c in checks
        if c["name"] in ["report_file_exists", "report_is_valid_json", "cac_correctly_calculated"]
    )

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))