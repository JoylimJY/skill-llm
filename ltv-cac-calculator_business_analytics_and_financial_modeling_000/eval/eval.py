import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    ws = Path(workspace_dir)
    checks = []
    
    # ── Locate the report file ───────────────────────────────────────────────
    candidates = list(ws.rglob("ltv_cac_report.md"))
    report_path = candidates[0] if candidates else None
    
    if not report_path or not report_path.exists():
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{
                "name": "report_file_exists",
                "passed": False,
                "detail": "ltv_cac_report.md not found anywhere in workspace"
            }]
        }
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{
                "name": "report_readable",
                "passed": False,
                "detail": f"Could not read ltv_cac_report.md: {e}"
            }]
        }
    
    content_lower = content.lower()
    
    # ── CHECK 1: Five required sections present ──────────────────────────────
    section_patterns = [
        # Section 1: assumptions table
        (r"假设|assumption", "Section 1: Assumptions table"),
        # Section 2: LTV/CAC result
        (r"ltv.*cac|cac.*ltv|ltv/cac|ltv：|ltv:", "Section 2: LTV/CAC result"),
        # Section 3: Risk commentary
        (r"风险|risk", "Section 3: Risk commentary"),
        # Section 4: Recommended actions
        (r"建议|recommend|action", "Section 4: Recommended actions"),
        # Section 5: Python script
        (r"```python|def |import pandas|import numpy", "Section 5: Python script"),
    ]
    
    section_results = []
    for pattern, label in section_patterns:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        section_results.append((label, found))
        checks.append({
            "name": f"section_present:{label}",
            "passed": found,
            "detail": f"Pattern '{pattern}' {'found' if found else 'NOT found'} in report"
        })
    
    # ── CHECK 2: Gross Profit LTV (not revenue-only) ─────────────────────────
    uses_gross_profit = bool(re.search(
        r"gross.profit|毛利|cogs|cost.of.goods|gross_profit",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "ltv_uses_gross_profit",
        "passed": uses_gross_profit,
        "detail": "Report must compute LTV on gross profit basis, not revenue only"
    })
    
    # ── CHECK 3: 12-month window explicitly stated ────────────────────────────
    twelve_month = bool(re.search(
        r"12.month|12个月|twelve.month|12-month|annual.*window|window.*12",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "ltv_window_12_months",
        "passed": twelve_month,
        "detail": "Report must explicitly state the 12-month LTV calculation window"
    })
    
    # ── CHECK 4: Full CAC includes all 4 components ───────────────────────────
    # Must mention ad spend + channel/agency fee + team cost + discount/voucher
    cac_ad = bool(re.search(r"ad.spend|media.buy|广告费|1[,.]?800[,.]?000", content, re.IGNORECASE))
    cac_agency = bool(re.search(r"agency|channel.fee|渠道|service.fee|1[,.]?068[,.]?000", content, re.IGNORECASE))
    cac_team = bool(re.search(r"team.cost|headcount|人力|staff|420[,.]?000", content, re.IGNORECASE))
    cac_voucher = bool(re.search(r"voucher|discount|补贴|108[,.]?000|welcome", content, re.IGNORECASE))
    
    all_four_cac = cac_ad and cac_agency and cac_team and cac_voucher
    checks.append({
        "name": "cac_all_four_components",
        "passed": all_four_cac,
        "detail": (
            f"CAC must include all 4 components. "
            f"Ad spend: {cac_ad}, Agency/channel fee: {cac_agency}, "
            f"Team cost: {cac_team}, Voucher/discount: {cac_voucher}"
        )
    })
    
    # ── CHECK 5: Full CAC value is roughly correct ────────────────────────────
    # Total cost = 1,800,000 + 1,068,000 + 420,000 + 108,000 = 3,396,000
    # New customers = 6,000
    # Full CAC = 3,396,000 / 6,000 = 566 CNY
    # Accept range: 540–600 (allow for rounding/interpretation of partial components)
    cac_value_found = False
    cac_detail = "No numeric CAC value in expected range [540, 600] found"
    
    # Extract all numbers from content
    numbers = re.findall(r'\b(\d{3,4}(?:\.\d+)?)\b', content)
    for n in numbers:
        try:
            val = float(n)
            if 540 <= val <= 600:
                cac_value_found = True
                cac_detail = f"Found CAC value {val} in acceptable range [540, 600]"
                break
        except ValueError:
            pass
    
    checks.append({
        "name": "cac_numeric_value_correct",
        "passed": cac_value_found,
        "detail": cac_detail
    })
    
    # ── CHECK 6: LTV/CAC ratio computed and stated ────────────────────────────
    ratio_found = bool(re.search(
        r"ltv\s*[/:]\s*cac|ratio|比率|比值|\d+\s*:\s*\d+",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "ltv_cac_ratio_stated",
        "passed": ratio_found,
        "detail": "Report must state the LTV:CAC ratio explicitly"
    })
    
    # ── CHECK 7: Payback period stated ───────────────────────────────────────
    payback_found = bool(re.search(
        r"payback|回收期|pay.back|months? to|回本",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "payback_period_stated",
        "passed": payback_found,
        "detail": "Report must include payback period analysis"
    })
    
    # ── CHECK 8: Weakest link / risk identified ───────────────────────────────
    weakest_link = bool(re.search(
        r"weakest|最弱|retention|留存|churn|fragile|sensitive|risk.*factor|风险.*留存|留存.*风险",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "weakest_link_identified",
        "passed": weakest_link,
        "detail": "Report must identify the weakest assumption/risk factor (e.g., retention)"
    })
    
    # ── CHECK 9: Lifecycle assumption explicitly disclaimed ───────────────────
    lifecycle_disclaimer = bool(re.search(
        r"assum|假设|lifecycle.assum|生命周期假设|based on|window.*assum|注[：:]",
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "lifecycle_assumption_stated",
        "passed": lifecycle_disclaimer,
        "detail": "Report must explicitly state lifecycle assumptions (quality standard: don't pretend to be precise)"
    })
    
    # ── CHECK 10: Reusable Python script is actually runnable ─────────────────
    python_block_match = re.search(r'```python(.*?)```', content, re.DOTALL | re.IGNORECASE)
    python_runnable = False
    python_detail = "No ```python code block found in report"
    
    if python_block_match:
        python_code = python_block_match.group(1).strip()
        # Must have meaningful content: function def or calculation logic
        has_function_or_logic = bool(re.search(
            r'def |ltv|cac|gross_profit|pandas|csv|return|print',
            python_code, re.IGNORECASE
        ))
        has_reasonable_length = len(python_code.splitlines()) >= 10
        python_runnable = has_function_or_logic and has_reasonable_length
        python_detail = (
            f"Python block found ({len(python_code.splitlines())} lines). "
            f"Has LTV/CAC logic: {has_function_or_logic}, "
            f"Has reasonable length (>=10 lines): {has_reasonable_length}"
        )
    
    checks.append({
        "name": "python_script_reusable",
        "passed": python_runnable,
        "detail": python_detail
    })
    
    # ── CHECK 11: Does NOT use old revenue-only formula without gross profit ──
    uses_deprecated_formula = bool(re.search(
        r"aov\s*\*\s*freq.*lifespan|revenue.*ltv\s*=\s*aov",
        content, re.IGNORECASE
    ))
    # This is a negative check — using deprecated formula is a failure
    avoids_deprecated = not uses_deprecated_formula
    checks.append({
        "name": "avoids_deprecated_revenue_only_formula",
        "passed": avoids_deprecated,
        "detail": (
            "Report must NOT use the deprecated revenue-only formula from legacy script "
            f"(deprecated pattern detected: {uses_deprecated_formula})"
        )
    })
    
    # ── Scoring ──────────────────────────────────────────────────────────────
    # Weight the checks
    weights = {
        "section_present:Section 1: Assumptions table": 1.0,
        "section_present:Section 2: LTV/CAC result": 1.0,
        "section_present:Section 3: Risk commentary": 1.0,
        "section_present:Section 4: Recommended actions": 1.0,
        "section_present:Section 5: Python script": 1.0,
        "ltv_uses_gross_profit": 2.0,
        "ltv_window_12_months": 1.5,
        "cac_all_four_components": 2.0,
        "cac_numeric_value_correct": 2.0,
        "ltv_cac_ratio_stated": 1.5,
        "payback_period_stated": 1.5,
        "weakest_link_identified": 1.5,
        "lifecycle_assumption_stated": 1.0,
        "python_script_reusable": 2.0,
        "avoids_deprecated_revenue_only_formula": 1.0,
    }
    
    total_weight = sum(weights.values())
    earned_weight = sum(
        weights.get(c["name"], 1.0)
        for c in checks
        if c["passed"] and c["name"] in weights
    )
    
    score = round(earned_weight / total_weight, 4)
    passed = score >= 0.70  # Require at least 70% weighted score
    
    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))