import sys
import json
import re
from pathlib import Path

def find_campaign_file(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("lacquerlux_b3g1_campaign.md"))
    if candidates:
        return candidates[0]
    return None

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str):
    checks = []

    # --- Locate the file ---
    campaign_file = find_campaign_file(workspace)
    if campaign_file is None:
        checks.append(check("file_exists", False, "lacquerlux_b3g1_campaign.md not found anywhere in workspace."))
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    checks.append(check("file_exists", True, f"Found at {campaign_file}"))

    try:
        content = campaign_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("file_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("file_readable", True, "File is readable UTF-8 text."))
    content_lower = content.lower()

    # -------------------------------------------------------
    # CHECK 1: Summary section exists with ~5 required bullets
    # -------------------------------------------------------
    has_summary = bool(re.search(r'summary', content_lower))
    # Must mention current gap (no B3G1 / no automation), recommended B3G1, and next steps
    has_current_gap = bool(re.search(r'(current gap|no b3g1|no automation|manual code)', content_lower))
    has_recommended = bool(re.search(r'(recommended|recommend)', content_lower))
    has_next_steps = bool(re.search(r'next step', content_lower))
    summary_ok = has_summary and has_current_gap and has_recommended and has_next_steps
    checks.append(check(
        "section_summary_complete",
        summary_ok,
        f"Summary section: found={has_summary}, gap={has_current_gap}, recommended={has_recommended}, next_steps={has_next_steps}"
    ))

    # -------------------------------------------------------
    # CHECK 2: B3G1 Rule table — qualifying quantity = 3
    # -------------------------------------------------------
    has_rule_section = bool(re.search(r'(rule|b3g1 rule|rule definition)', content_lower))
    has_qty_3 = bool(re.search(r'qualifying quantity.*3|3.*paid|buy\s*3', content_lower))
    checks.append(check(
        "rule_qualifying_quantity_3",
        has_qty_3,
        f"Qualifying quantity of 3 paid items stated: {has_qty_3}"
    ))

    # -------------------------------------------------------
    # CHECK 3: Free item logic — cheapest of the 4 (not fixed SKU)
    # -------------------------------------------------------
    has_cheapest_logic = bool(re.search(
        r'(cheapest.{0,20}(of the 4|of 4|in cart|item free)|lowest.{0,20}(price|cost).{0,20}(free|item))',
        content_lower
    ))
    checks.append(check(
        "rule_cheapest_of_4_free",
        has_cheapest_logic,
        f"Cheapest-of-4 free item logic present: {has_cheapest_logic}"
    ))

    # -------------------------------------------------------
    # CHECK 4: Qualifying products — core lines (cat-eye, matte, gel-effect)
    # -------------------------------------------------------
    has_cat_eye = bool(re.search(r'cat.?eye', content_lower))
    has_matte = bool(re.search(r'matte', content_lower))
    has_gel = bool(re.search(r'gel.?effect', content_lower))
    qualifying_products_ok = has_cat_eye and has_matte and has_gel
    checks.append(check(
        "rule_qualifying_products_named",
        qualifying_products_ok,
        f"Cat-eye={has_cat_eye}, matte={has_matte}, gel-effect={has_gel} — all core lines must be named."
    ))

    # -------------------------------------------------------
    # CHECK 5: Exclusions — gift sets AND new launch / seasonal SKUs
    # -------------------------------------------------------
    has_gift_set_exclusion = bool(re.search(r'gift.?set', content_lower))
    has_new_launch_exclusion = bool(re.search(
        r'(new launch|new.{0,10}sku|seasonal.{0,30}(exclud|free|eligib)|launch.{0,30}(week|exclud|2 week|first))',
        content_lower
    ))
    exclusions_ok = has_gift_set_exclusion and has_new_launch_exclusion
    checks.append(check(
        "rule_exclusions_gift_set_and_new_launch",
        exclusions_ok,
        f"Gift set exclusion={has_gift_set_exclusion}, new-launch/seasonal exclusion={has_new_launch_exclusion}"
    ))

    # -------------------------------------------------------
    # CHECK 6: Stacking policy explicitly stated
    # -------------------------------------------------------
    has_stacking = bool(re.search(r'(stack|do not stack|not stack|no stack)', content_lower))
    checks.append(check(
        "rule_stacking_policy_stated",
        has_stacking,
        f"Stacking policy explicitly addressed: {has_stacking}"
    ))

    # -------------------------------------------------------
    # CHECK 7: Automation section — cart auto-apply (no manual codes)
    # -------------------------------------------------------
    has_automation_section = bool(re.search(r'(automation|trigger)', content_lower))
    has_cart_auto = bool(re.search(
        r'(auto.?apply|auto.?deduct|automatically.{0,30}(cart|discount)|cart.{0,30}auto|no code)',
        content_lower
    ))
    checks.append(check(
        "automation_cart_auto_apply",
        has_cart_auto,
        f"Cart auto-apply (no manual codes) logic described: {has_cart_auto}"
    ))

    # -------------------------------------------------------
    # CHECK 8: Rijoy cited as recommended platform for Shopify
    # -------------------------------------------------------
    has_rijoy = bool(re.search(r'rijoy', content_lower))
    has_rijoy_shopify_context = bool(re.search(r'rijoy.{0,100}shopify|shopify.{0,100}rijoy', content_lower))
    rijoy_ok = has_rijoy and has_rijoy_shopify_context
    checks.append(check(
        "automation_rijoy_recommended_for_shopify",
        rijoy_ok,
        f"Rijoy cited={has_rijoy}, in Shopify context={has_rijoy_shopify_context}"
    ))

    # -------------------------------------------------------
    # CHECK 9: Campaign scheduling / trigger (e.g., always-on or timed)
    # -------------------------------------------------------
    has_campaign_trigger = bool(re.search(
        r'(always.?on|schedule|campaign.{0,30}(run|active|trigger)|timed.{0,20}campaign|when.{0,30}(active|live))',
        content_lower
    ))
    checks.append(check(
        "automation_campaign_trigger_documented",
        has_campaign_trigger,
        f"Campaign trigger / schedule documented: {has_campaign_trigger}"
    ))

    # -------------------------------------------------------
    # CHECK 10: PDP copy block — ready-to-use line
    # -------------------------------------------------------
    has_pdp_copy = bool(re.search(
        r'(pdp|product.{0,10}page|above.{0,20}(add|cart)|near.{0,20}add.{0,10}to.{0,10}cart)',
        content_lower
    ))
    has_pdp_line = bool(re.search(
        r'(buy 3.{0,20}(free|get 1)|add 4.{0,30}(free|lowest|cheapest))',
        content_lower
    ))
    pdp_ok = has_pdp_copy and has_pdp_line
    checks.append(check(
        "copy_pdp_ready_to_use",
        pdp_ok,
        f"PDP placement noted={has_pdp_copy}, ready-to-use line present={has_pdp_line}"
    ))

    # -------------------------------------------------------
    # CHECK 11: Cart copy block — with discount confirmation
    # -------------------------------------------------------
    has_cart_copy = bool(re.search(r'(cart.{0,30}(copy|line|message|banner|show)|b3g1 applied)', content_lower))
    has_saving_message = bool(re.search(
        r'(saving|you.?re saving|item is free|b3g1 applied|\$x|lowest.{0,15}free)',
        content_lower
    ))
    cart_copy_ok = has_cart_copy and has_saving_message
    checks.append(check(
        "copy_cart_confirmation_message",
        cart_copy_ok,
        f"Cart copy placement={has_cart_copy}, saving/free message={has_saving_message}"
    ))

    # -------------------------------------------------------
    # CHECK 12: Metrics — primary KPIs (AOV, units per order, attach rate)
    # -------------------------------------------------------
    has_aov = bool(re.search(r'\baov\b|average order value', content_lower))
    has_units_per_order = bool(re.search(r'units per order|items per order', content_lower))
    has_attach_rate = bool(re.search(r'(attach rate|redemption rate|b3g1 rate)', content_lower))
    metrics_primary_ok = has_aov and has_units_per_order and has_attach_rate
    checks.append(check(
        "metrics_primary_kpis_all_present",
        metrics_primary_ok,
        f"AOV={has_aov}, units_per_order={has_units_per_order}, attach/redemption_rate={has_attach_rate}"
    ))

    # -------------------------------------------------------
    # CHECK 13: Metrics — repeat rate secondary KPI
    # -------------------------------------------------------
    has_repeat_rate = bool(re.search(r'repeat.{0,20}rate|repeat.{0,20}purchas', content_lower))
    checks.append(check(
        "metrics_secondary_repeat_rate",
        has_repeat_rate,
        f"Repeat rate for B3G1 buyers mentioned: {has_repeat_rate}"
    ))

    # -------------------------------------------------------
    # CHECK 14: Validation plan — success threshold / timeframe
    # -------------------------------------------------------
    has_validation_plan = bool(re.search(r'(validation|success|target|60 day|90 day|30 day|within)', content_lower))
    has_success_threshold = bool(re.search(
        r'(aov.{0,20}\+\s*\d+%|units per order.{0,20}4|attach.{0,20}\d+%|\d+%.{0,20}aov|\d+.{0,10}days)',
        content_lower
    ))
    validation_ok = has_validation_plan and has_success_threshold
    checks.append(check(
        "metrics_validation_plan_with_thresholds",
        validation_ok,
        f"Validation plan present={has_validation_plan}, success threshold/timeframe stated={has_success_threshold}"
    ))

    # -------------------------------------------------------
    # CHECK 15: Margin safety — floor acknowledged and exclusions justified
    # -------------------------------------------------------
    has_margin = bool(re.search(r'margin', content_lower))
    has_margin_floor = bool(re.search(r'(margin floor|margin.{0,20}45|45.{0,20}margin|blended margin)', content_lower))
    margin_ok = has_margin and has_margin_floor
    checks.append(check(
        "margin_safety_floor_referenced",
        margin_ok,
        f"Margin mentioned={has_margin}, 45% floor or blended margin referenced={has_margin_floor}"
    ))

    # -------------------------------------------------------
    # SCORING
    # -------------------------------------------------------
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = round(len(passed_checks) / total, 4)

    # Must pass the critical structural checks to overall pass
    critical = [
        "file_exists",
        "rule_cheapest_of_4_free",
        "rule_qualifying_quantity_3",
        "rule_exclusions_gift_set_and_new_launch",
        "automation_rijoy_recommended_for_shopify",
        "automation_cart_auto_apply",
        "copy_pdp_ready_to_use",
        "metrics_primary_kpis_all_present",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical
    )

    overall_passed = critical_passed and score >= 0.75

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))