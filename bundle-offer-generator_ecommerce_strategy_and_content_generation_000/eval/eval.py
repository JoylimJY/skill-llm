import sys
import json
import re
from pathlib import Path

def find_output_file(workspace):
    """Find the bundle_offer_plan.md file anywhere in the workspace."""
    matches = list(Path(workspace).rglob("bundle_offer_plan.md"))
    return matches[0] if matches else None

def load_file(path):
    try:
        return Path(path).read_text(encoding="utf-8")
    except Exception as e:
        return None

def run_checks(workspace):
    checks = []
    score = 0.0

    # --- Find the output file ---
    output_path = find_output_file(workspace)
    file_found = output_path is not None
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found at {output_path}" if file_found else "bundle_offer_plan.md not found anywhere in workspace"
    })
    if not file_found:
        return checks, 0.0

    content = load_file(output_path)
    if content is None:
        checks.append({"name": "file_readable", "passed": False, "detail": "Could not read file"})
        return checks, 0.0

    content_lower = content.lower()

    # -------------------------------------------------------------------------
    # CHECK 1: All four mandatory sections present
    # -------------------------------------------------------------------------
    section1_present = bool(re.search(r'bundle\s*(方案列表|方案\s*列表|list)', content, re.IGNORECASE))
    section2_present = bool(re.search(r'(定价逻辑|pricing\s*logic|price\s*rationale)', content, re.IGNORECASE))
    section3_present = bool(re.search(r'(margin\s*风险|margin\s*risk|利润.*风险|风险.*提示)', content, re.IGNORECASE))
    section4_present = bool(re.search(r'(建议.*使用场景|使用场景|recommended.*scenario|use\s*case)', content, re.IGNORECASE))

    all_sections = section1_present and section2_present and section3_present and section4_present
    checks.append({
        "name": "all_four_sections_present",
        "passed": all_sections,
        "detail": (
            f"Section1(Bundle方案列表):{section1_present}, "
            f"Section2(定价逻辑):{section2_present}, "
            f"Section3(Margin风险提示):{section3_present}, "
            f"Section4(建议使用场景):{section4_present}"
        )
    })
    if all_sections:
        score += 0.20

    # -------------------------------------------------------------------------
    # CHECK 2: Three tiers present (基础款 / 进阶款 / 高价值款)
    # -------------------------------------------------------------------------
    tier_basic = bool(re.search(r'(基础款|basic\s*tier|starter\s*kit|entry[\s\-]level)', content, re.IGNORECASE))
    tier_advanced = bool(re.search(r'(进阶款|advanced\s*tier|upgrade|mid[\s\-]tier)', content, re.IGNORECASE))
    tier_premium = bool(re.search(r'(高价值款|premium|high[\s\-]value|pro\s*kit)', content, re.IGNORECASE))

    all_tiers = tier_basic and tier_advanced and tier_premium
    checks.append({
        "name": "three_tiers_present",
        "passed": all_tiers,
        "detail": (
            f"基础款:{tier_basic}, 进阶款:{tier_advanced}, 高价值款:{tier_premium}"
        )
    })
    if all_tiers:
        score += 0.20

    # -------------------------------------------------------------------------
    # CHECK 3: Margin risk section has actual content (not empty / placeholder)
    # -------------------------------------------------------------------------
    # Extract text after the margin risk section header
    margin_section_match = re.search(
        r'(margin\s*风险|margin\s*risk|利润.*风险|风险.*提示)(.*?)(?=##|\Z)',
        content, re.IGNORECASE | re.DOTALL
    )
    margin_content = margin_section_match.group(2).strip() if margin_section_match else ""
    margin_has_substance = (
        len(margin_content) > 80 and
        bool(re.search(r'(margin|利润|%|blended|风险|risk|protect|floor|ceiling)', margin_content, re.IGNORECASE))
    )
    checks.append({
        "name": "margin_risk_section_has_substance",
        "passed": margin_has_substance,
        "detail": f"Margin section length={len(margin_content)}, contains margin keywords={bool(re.search(r'margin|利润|%', margin_content, re.IGNORECASE))}"
    })
    if margin_has_substance:
        score += 0.15

    # -------------------------------------------------------------------------
    # CHECK 4: Purchase reasoning ("why buy together") not just price savings
    # -------------------------------------------------------------------------
    # Must contain reasoning beyond discount — scenario/use-case language
    has_purchase_reasoning = bool(re.search(
        r'(why|because|together|完整|场景|trip|night|trail|safety|experience|系统|搭配|理由|need|purpose|完成|complement)',
        content, re.IGNORECASE
    ))
    # Must NOT be only about discounts
    heavy_discount_only = (
        len(re.findall(r'(save|discount|cheaper|off|优惠|折扣|省)', content, re.IGNORECASE)) > 10
        and not has_purchase_reasoning
    )
    purchase_reasoning_passes = has_purchase_reasoning and not heavy_discount_only
    checks.append({
        "name": "purchase_reasoning_beyond_price",
        "passed": purchase_reasoning_passes,
        "detail": f"Has scenario/use reasoning: {has_purchase_reasoning}, Discount-only text overload: {heavy_discount_only}"
    })
    if purchase_reasoning_passes:
        score += 0.15

    # -------------------------------------------------------------------------
    # CHECK 5: Pricing logic section has concrete numbers (prices or %)
    # -------------------------------------------------------------------------
    pricing_section_match = re.search(
        r'(定价逻辑|pricing\s*logic|price\s*rationale)(.*?)(?=##|\Z)',
        content, re.IGNORECASE | re.DOTALL
    )
    pricing_content = pricing_section_match.group(2).strip() if pricing_section_match else ""
    has_numbers = bool(re.search(r'(\$\d+|\d+\.?\d*\s*%|\d+\s*USD)', pricing_content))
    checks.append({
        "name": "pricing_logic_has_numbers",
        "passed": has_numbers and len(pricing_content) > 60,
        "detail": f"Pricing section length={len(pricing_content)}, contains numbers={has_numbers}"
    })
    if has_numbers and len(pricing_content) > 60:
        score += 0.10

    # -------------------------------------------------------------------------
    # CHECK 6: Uses actual products from the catalog (at least 6 distinct SKUs mentioned)
    # -------------------------------------------------------------------------
    product_keywords = [
        'tent', 'sleeping bag', 'sleeping pad', 'headlamp', 'camp kitchen',
        'trekking poles', 'water filter', 'first aid', 'stuff sack', 'rain jacket',
        'solar charger', 'bear canister',
        'TP-001', 'TP-002', 'TP-003', 'TP-004', 'TP-005', 'TP-006',
        'TP-007', 'TP-008', 'TP-009', 'TP-010', 'TP-011', 'TP-012',
        'trailpeak', 'ultralight', 'headlamp pro'
    ]
    found_products = [kw for kw in product_keywords if kw.lower() in content_lower]
    distinct_products = len(set(found_products))
    product_check_passed = distinct_products >= 6
    checks.append({
        "name": "uses_catalog_products",
        "passed": product_check_passed,
        "detail": f"Distinct product references found: {distinct_products} (need >=6). Found: {list(set(found_products))[:10]}"
    })
    if product_check_passed:
        score += 0.10

    # -------------------------------------------------------------------------
    # CHECK 7: Respects discount ceiling (no bundle claims >15% discount)
    # -------------------------------------------------------------------------
    discount_mentions = re.findall(r'(\d+(?:\.\d+)?)\s*%\s*(?:off|discount|折扣|优惠)', content, re.IGNORECASE)
    egregious_discounts = [float(d) for d in discount_mentions if float(d) > 20]
    discount_ceiling_ok = len(egregious_discounts) == 0
    checks.append({
        "name": "discount_ceiling_respected",
        "passed": discount_ceiling_ok,
        "detail": f"Discounts mentioned >20%: {egregious_discounts} (policy ceiling is 12-15%)"
    })
    if discount_ceiling_ok:
        score += 0.05

    # -------------------------------------------------------------------------
    # CHECK 8: Customer segment targeting — mentions at least one segment
    # -------------------------------------------------------------------------
    segment_mentioned = bool(re.search(
        r'(first[\s\-]time\s*camp|weekend\s*warrior|thru[\s\-]hiker|multi[\s\-]day|beginner|初次|新手|进阶用户|资深)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "customer_segment_targeted",
        "passed": segment_mentioned,
        "detail": f"Mentions a specific customer segment: {segment_mentioned}"
    })
    if segment_mentioned:
        score += 0.05

    # -------------------------------------------------------------------------
    # CHECK 9: File length sanity — not a stub
    # -------------------------------------------------------------------------
    word_count = len(content.split())
    length_ok = word_count >= 300
    checks.append({
        "name": "output_has_sufficient_depth",
        "passed": length_ok,
        "detail": f"Word count: {word_count} (minimum 300 required)"
    })
    if length_ok:
        score += 0.0  # bonus not scored separately; already captured by other checks

    final_score = round(min(score, 1.0), 3)
    return checks, final_score


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    workspace = sys.argv[1]
    try:
        checks, score = run_checks(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "eval_crash", "passed": False, "detail": str(e)}]
        }))
        sys.exit(1)

    passed = score >= 0.65
    print(json.dumps({"passed": passed, "score": score, "checks": checks}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()