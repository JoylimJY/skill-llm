import sys
import json
import re
from pathlib import Path

def load_report(workspace: str):
    """Find cpa_guardrails_report.md anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("cpa_guardrails_report.md"))
    if not candidates:
        return None, "File cpa_guardrails_report.md not found anywhere in workspace"
    return candidates[0], None

def parse_number(text: str, label: str):
    """Extract the first float/int following a label (case-insensitive)."""
    pattern = rf"{re.escape(label)}[^\d\-]*([0-9]+(?:\.[0-9]+)?)"
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        return float(m.group(1))
    return None

def check_value_approx(actual, expected, tol=0.05, label=""):
    """Return (passed, detail)."""
    if actual is None:
        return False, f"{label}: value not found in report"
    if abs(actual - expected) / max(abs(expected), 1e-9) <= tol:
        return True, f"{label}: {actual:.2f} ≈ {expected:.2f} (within {tol*100:.0f}%)"
    return False, f"{label}: got {actual:.2f}, expected ≈ {expected:.2f}"

def expected_cpa(list_price, cogs, shipping, pick_pack, discount_pct, refund_pct, ltv):
    """
    Per references/output-template.md:
      effective_price = list_price * (1 - discount_pct/100)
      gross_margin_pct = (effective_price - cogs) / effective_price   [implicit from COGS]
      fulfillment = shipping + pick_pack
      refund_loss = effective_price * (refund_pct/100)
      net_profit = effective_price - cogs - fulfillment - refund_loss + ltv
      break_even_cpa = net_profit
    Note: gross margin % = (effective_price - cogs) / effective_price
    So effective_price * gross_margin_pct = effective_price - cogs
    net_profit = effective_price * gross_margin_pct - fulfillment - refund_loss + ltv
    Both formulations are equivalent; we use the direct one.
    """
    effective_price = list_price * (1 - discount_pct / 100)
    fulfillment = shipping + pick_pack
    refund_loss = effective_price * (refund_pct / 100)
    net_profit = effective_price - cogs - fulfillment - refund_loss + ltv
    return net_profit

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── 1. File existence ────────────────────────────────────────────────────
    report_path, err = load_report(workspace)
    file_found = report_path is not None
    checks.append({
        "name": "report_file_exists",
        "passed": file_found,
        "detail": str(report_path) if file_found else err
    })
    if not file_found:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    try:
        content = report_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    content_lower = content.lower()

    # ── 2. All three SKUs present ────────────────────────────────────────────
    for sku_name in ["starter pack", "subscription bundle", "premium bundle"]:
        present = sku_name in content_lower
        checks.append({
            "name": f"sku_present_{sku_name.replace(' ','_')}",
            "passed": present,
            "detail": f"'{sku_name}' {'found' if present else 'NOT found'} in report"
        })

    # ── 3. Four mandatory sections present ──────────────────────────────────
    section_keywords = [
        ("assumptions_table", ["假设", "assumption"]),
        ("break_even_cpa_section", ["break-even cpa", "break_even", "breakeven"]),
        ("allowable_cpa_section", ["allowable cpa", "allowable", "安全系数", "conservative", "moderate", "aggressive", "保守", "稳健", "激进"]),
        ("recommended_actions_section", ["建议", "recommended action", "action", "优化"]),
    ]
    for sec_name, keywords in section_keywords:
        found = any(k in content_lower for k in keywords)
        checks.append({
            "name": f"section_{sec_name}",
            "passed": found,
            "detail": f"Section '{sec_name}' {'found' if found else 'NOT found'} (looked for: {keywords})"
        })

    # ── 4. Break-even CPA values (per SKU) ──────────────────────────────────
    # SKU-001 Starter Pack
    be_001 = expected_cpa(
        list_price=49.00, cogs=12.50, shipping=4.80, pick_pack=1.20,
        discount_pct=10, refund_pct=8, ltv=0.00
    )
    # SKU-002 Subscription Bundle
    be_002 = expected_cpa(
        list_price=119.00, cogs=28.00, shipping=6.50, pick_pack=2.10,
        discount_pct=15, refund_pct=5, ltv=22.00
    )
    # SKU-003 Premium Bundle
    be_003 = expected_cpa(
        list_price=198.00, cogs=55.00, shipping=8.20, pick_pack=3.00,
        discount_pct=5, refund_pct=12, ltv=45.00
    )

    # Extract break-even CPAs from report using various patterns
    def find_be_cpa_near_sku(text, sku_hint, expected_val):
        """
        Look for a dollar/numeric value near the SKU mention that approximates expected_val.
        We scan for all floats in the document and check if any is within 10% of expected.
        Additionally we check for values near the sku section.
        """
        # Find all numeric values in the document
        all_nums = [float(x) for x in re.findall(r'\b(\d{1,4}(?:\.\d{1,2})?)\b', text)]
        close = [v for v in all_nums if abs(v - expected_val) / max(abs(expected_val), 1e-9) <= 0.10]
        return len(close) > 0, close

    for sku_label, be_val in [("SKU-001/Starter", be_001), ("SKU-002/Subscription", be_002), ("SKU-003/Premium", be_003)]:
        found, close_vals = find_be_cpa_near_sku(content, sku_label, be_val)
        checks.append({
            "name": f"break_even_cpa_{sku_label.replace('/', '_')}",
            "passed": found,
            "detail": f"Break-even CPA for {sku_label}: expected ≈ {be_val:.2f}, found values within 10%: {close_vals[:3]}"
        })

    # ── 5. Allowable CPA range: conservative = BE × 0.5, moderate = BE × 0.7, aggressive = BE × 0.9 ──
    # Check that all three tiers exist numerically in the report for at least two SKUs
    def check_allowable_tiers(text, be_vals):
        tier_factors = [0.5, 0.7, 0.9]
        all_nums = [float(x) for x in re.findall(r'\b(\d{1,4}(?:\.\d{1,2})?)\b', text)]
        matched_tiers = 0
        details = []
        for be_val in be_vals:
            for factor in tier_factors:
                target = be_val * factor
                close = [v for v in all_nums if abs(v - target) / max(abs(target), 1e-9) <= 0.12]
                if close:
                    matched_tiers += 1
                    details.append(f"BE×{factor}={target:.2f} found: {close[:2]}")
        return matched_tiers, details

    matched, tier_details = check_allowable_tiers(content, [be_001, be_002, be_003])
    # Expect at least 6 of 9 possible tier values to be present (2 SKUs × 3 tiers)
    tiers_ok = matched >= 6
    checks.append({
        "name": "allowable_cpa_three_tiers",
        "passed": tiers_ok,
        "detail": f"Found {matched}/9 allowable CPA tier values. Details: {tier_details[:6]}"
    })

    # ── 6. Refund impact not ignored ────────────────────────────────────────
    refund_mentioned = any(k in content_lower for k in ["refund", "return rate", "退款", "return"])
    checks.append({
        "name": "refund_impact_addressed",
        "passed": refund_mentioned,
        "detail": "Refund/return rate {'mentioned' if refund_mentioned else 'NOT mentioned'} in report"
    })

    # ── 7. Break-even vs Allowable CPA explicitly differentiated ────────────
    diff_keywords = ["break-even", "allowable", "safety", "安全系数", "conservative", "保守"]
    diff_count = sum(1 for k in diff_keywords if k in content_lower)
    differentiated = diff_count >= 3
    checks.append({
        "name": "be_vs_allowable_differentiated",
        "passed": differentiated,
        "detail": f"Differentiation keywords found: {diff_count}/6 required ≥ 3"
    })

    # ── 8. Specific recommended actions present ──────────────────────────────
    action_keywords = ["pricing", "discount", "conversion", "refund", "bid", "提价", "转化", "折扣", "出价", "退款率"]
    action_count = sum(1 for k in action_keywords if k in content_lower)
    actions_ok = action_count >= 3
    checks.append({
        "name": "specific_recommended_actions",
        "passed": actions_ok,
        "detail": f"Action keywords found: {action_count}/10, required ≥ 3"
    })

    # ── 9. Fulfillment cost included in calculation ──────────────────────────
    fulfillment_mentioned = any(k in content_lower for k in ["fulfillment", "shipping", "履约", "pick", "pack"])
    checks.append({
        "name": "fulfillment_cost_included",
        "passed": fulfillment_mentioned,
        "detail": f"Fulfillment cost {'mentioned' if fulfillment_mentioned else 'NOT mentioned'}"
    })

    # ── 10. LTV / repeat purchase contribution included ──────────────────────
    ltv_mentioned = any(k in content_lower for k in ["ltv", "repeat", "复购", "contribution", "lifetime"])
    checks.append({
        "name": "ltv_repeat_contribution_included",
        "passed": ltv_mentioned,
        "detail": f"LTV/repeat contribution {'mentioned' if ltv_mentioned else 'NOT mentioned'}"
    })

    # ── Final scoring ────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)

    # Hard requirement: file exists + all 3 SKUs + break-even CPAs numerically correct + 4 sections
    hard_checks = [
        "report_file_exists",
        "sku_present_starter_pack",
        "sku_present_subscription_bundle",
        "sku_present_premium_bundle",
        "break_even_cpa_SKU-001_Starter",
        "break_even_cpa_SKU-002_Subscription",
        "break_even_cpa_SKU-003_Premium",
        "allowable_cpa_three_tiers",
        "section_assumptions_table",
        "section_break_even_cpa_section",
        "section_allowable_cpa_section",
        "section_recommended_actions_section",
    ]
    check_map = {c["name"]: c["passed"] for c in checks}
    hard_passed = all(check_map.get(h, False) for h in hard_checks)

    overall_passed = hard_passed and score >= 0.75

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()