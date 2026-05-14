import sys
import json
import math
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0
    max_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        nonlocal total_score, max_score
        max_score += weight
        if passed:
            total_score += weight

    # =========================================================
    # CHECK 1: Report file exists
    # =========================================================
    report_files = list(workspace.rglob("tax_deduction_report.json"))
    if not report_files:
        add_check("report_file_exists", False, "tax_deduction_report.json not found anywhere in workspace.", weight=2.0)
        # Cannot continue without the file
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result, indent=2))
        return
    
    report_path = report_files[0]
    add_check("report_file_exists", True, f"Found at {report_path}", weight=2.0)

    try:
        report = json.loads(report_path.read_text())
    except Exception as e:
        add_check("report_json_valid", False, f"Could not parse JSON: {e}", weight=2.0)
        result = {
            "passed": False,
            "score": round(total_score / max_score, 3),
            "checks": checks
        }
        print(json.dumps(result, indent=2))
        return

    add_check("report_json_valid", True, "JSON parses successfully.", weight=2.0)

    # =========================================================
    # CHECK 2: Summary section exists with required fields
    # =========================================================
    summary = report.get("summary", report.get("impact_summary", report.get("estimate", {})))
    has_summary = isinstance(summary, dict) and len(summary) > 0
    add_check("summary_section_exists", has_summary, 
              f"Summary section found: {has_summary}. Keys: {list(summary.keys()) if has_summary else 'N/A'}", 
              weight=1.0)

    # =========================================================
    # CHECK 3: Transactions reviewed count (should be 20)
    # =========================================================
    reviewed = None
    for key in ["transactions_reviewed", "total_transactions", "transactions_analyzed"]:
        if key in summary:
            reviewed = summary[key]
            break
    # Also check top-level
    if reviewed is None:
        for key in ["transactions_reviewed", "total_transactions", "transactions_analyzed"]:
            if key in report:
                reviewed = report[key]
                break

    reviewed_correct = reviewed is not None and int(reviewed) == 20
    add_check("transactions_reviewed_count", reviewed_correct,
              f"Expected 20 transactions reviewed, got: {reviewed}", weight=1.0)

    # =========================================================
    # CHECK 4: Missed deductions found
    # The agent should flag at minimum these transactions as deductions:
    # txn_001 (internet), txn_002 (Adobe), txn_004 (travel meal), txn_005 (monitor/keyboard GWG),
    # txn_007 (insurance), txn_008 (domain), txn_010 (course), txn_011 (client gift <=35),
    # txn_013 (hosting), txn_014 (bank fees), txn_015 (transport), txn_017 (Slack),
    # txn_018 (conference), txn_019 (hotel)
    # txn_006 should be flagged but with depreciation note (over 800 EUR net => pool/depreciate)
    # txn_012 should be flagged as partially deductible (over 35 EUR limit)
    # Minimum acceptable: 10 deductions flagged
    # =========================================================
    deductions = report.get("missed_deductions", report.get("potential_deductions", report.get("deductions", [])))
    if not isinstance(deductions, list):
        # Try nested
        for key in report:
            if isinstance(report[key], list) and len(report[key]) > 0:
                first = report[key][0]
                if isinstance(first, dict) and any(k in first for k in ["transaction_id", "id", "txn_id", "description"]):
                    deductions = report[key]
                    break

    num_deductions = len(deductions) if isinstance(deductions, list) else 0
    deductions_sufficient = num_deductions >= 10
    add_check("min_deductions_flagged", deductions_sufficient,
              f"Expected at least 10 potential deductions, found: {num_deductions}", weight=2.0)

    # =========================================================
    # CHECK 5: SKR04 categories used
    # SKR04 codes for common deductions:
    # 4730: Miete (rent), 4741: Strom/Heizung, 4780: Internet
    # 4822: Software/SaaS, 4930: Steuerberatung, 4660: Reisekosten
    # 4670: Verpflegung/Bewirtung, 4783: Büroausstattung/GWG
    # 4350: Versicherungen, 4970: Bankgebühren, 4830: Werbung/Marketing
    # 4900: Fortbildung, 4940: Fachliteratur, 6800: Geschäftsreisen
    # =========================================================
    skr04_pattern_keys = ["skr04", "category", "suggested_category", "new_category", "skr_category"]
    skr04_found = set()
    
    if isinstance(deductions, list):
        for d in deductions:
            if isinstance(d, dict):
                for key in skr04_pattern_keys:
                    val = d.get(key, "")
                    if isinstance(val, str) and val.strip().isdigit() and len(val.strip()) == 4:
                        skr04_found.add(val.strip())
                    elif isinstance(val, (int, float)) and 4000 <= int(val) <= 7000:
                        skr04_found.add(str(int(val)))

    skr04_used = len(skr04_found) >= 3
    add_check("skr04_categories_used", skr04_used,
              f"SKR04 codes found: {sorted(skr04_found)}. Need at least 3 distinct codes.", weight=2.0)

    # =========================================================
    # CHECK 6: GWG threshold correctly applied
    # txn_005: amount=999.60 EUR gross, net=999.60/1.19=840.00 EUR => under 1000 EUR net => GWG fully deductible
    # txn_006: amount=952.00 EUR gross, net=952/1.19=800.00 EUR => at 800 EUR boundary 
    # The agent must note that GWG threshold uses NET amounts
    # =========================================================
    gwg_mentioned = False
    gwg_net_correct = False
    report_text = json.dumps(report).lower()
    
    if "gwg" in report_text or "geringwertige" in report_text or "1000" in report_text:
        gwg_mentioned = True
    if "net" in report_text or "netto" in report_text or "excl" in report_text or "ohne mwst" in report_text or "840" in report_text:
        gwg_net_correct = True

    add_check("gwg_threshold_mentioned", gwg_mentioned,
              f"GWG/1000 EUR threshold referenced in report: {gwg_mentioned}", weight=1.5)
    add_check("gwg_net_amount_used", gwg_net_correct,
              f"Net amount consideration for GWG found in report: {gwg_net_correct}", weight=1.5)

    # =========================================================
    # CHECK 7: Verpflegungspauschale rates mentioned
    # Must reference 14 EUR (partial day) and/or 28 EUR (full day)
    # =========================================================
    verpflegung_mentioned = (
        "verpflegungspauschale" in report_text or
        "verpflegungs" in report_text or
        "per diem" in report_text.replace("-", "")
    )
    correct_rates = "14" in report_text and "28" in report_text
    
    add_check("verpflegungspauschale_referenced", verpflegung_mentioned,
              f"Verpflegungspauschale mentioned: {verpflegung_mentioned}", weight=1.0)
    add_check("correct_per_diem_rates", correct_rates,
              f"Both 14 EUR and 28 EUR rates present in report: {correct_rates}", weight=1.5)

    # =========================================================
    # CHECK 8: Client gift cap (35 EUR per person) correctly applied
    # txn_011 (29.90 EUR) should be deductible
    # txn_012 (42.00 EUR) should be flagged as over limit / non-deductible or only partial
    # =========================================================
    client_gift_35 = "35" in report_text
    txn_012_flagged_as_problematic = False
    
    if isinstance(deductions, list):
        for d in deductions:
            if isinstance(d, dict):
                txt = json.dumps(d).lower()
                if "42" in txt or "txn_012" in txt or "anna" in txt or "schmidt" in txt:
                    if any(w in txt for w in ["exceed", "über", "limit", "non-deductible", "nicht", "partial", "35", "over"]):
                        txn_012_flagged_as_problematic = True

    # Also check at report level
    if not txn_012_flagged_as_problematic:
        if "42" in report_text and "35" in report_text:
            txn_012_flagged_as_problematic = True

    add_check("client_gift_35eur_cap_applied", client_gift_35,
              f"35 EUR client gift cap referenced in report: {client_gift_35}", weight=1.5)
    add_check("over_limit_gift_flagged", txn_012_flagged_as_problematic,
              f"42 EUR client gift (txn_012/Anna Schmidt) flagged as exceeding limit: {txn_012_flagged_as_problematic}", weight=1.5)

    # =========================================================
    # CHECK 9: Tax savings estimate using 30-42% range
    # =========================================================
    tax_savings_present = False
    uses_correct_rate_range = False
    
    for key in ["estimated_tax_savings", "tax_savings", "approximate_savings", "steuerersparnis"]:
        if key in summary:
            tax_savings_present = True
            val = summary[key]
            break
    if not tax_savings_present and "savings" in report_text and "eur" in report_text:
        tax_savings_present = True

    # Check for rate range 30-42%
    if ("30" in report_text and "42" in report_text) or ("0.30" in report_text and "0.42" in report_text):
        uses_correct_rate_range = True
    elif "30%" in report_text and "42%" in report_text:
        uses_correct_rate_range = True

    add_check("tax_savings_estimated", tax_savings_present,
              f"Tax savings estimate present in report: {tax_savings_present}", weight=1.5)
    add_check("correct_marginal_rate_range", uses_correct_rate_range,
              f"30-42% marginal rate range used: {uses_correct_rate_range}", weight=1.5)

    # =========================================================
    # CHECK 10: categorize_transaction API was called
    # Check the categorized log written by mock server
    # =========================================================
    cat_log_path = workspace / "tools" / "config" / "categorized_log.json"
    categorization_called = False
    min_categorizations = False
    
    try:
        if cat_log_path.exists():
            cat_log = json.loads(cat_log_path.read_text())
            if isinstance(cat_log, list) and len(cat_log) > 0:
                categorization_called = True
                min_categorizations = len(cat_log) >= 3
        add_check("categorize_transaction_called", categorization_called,
                  f"categorize_transaction API called: {categorization_called}. Total calls: {len(cat_log) if categorization_called else 0}", weight=2.0)
        add_check("min_categorizations_applied", min_categorizations,
                  f"At least 3 transactions recategorized: {min_categorizations}", weight=1.5)
    except Exception as e:
        add_check("categorize_transaction_called", False,
                  f"Error reading categorization log: {e}", weight=2.0)
        add_check("min_categorizations_applied", False,
                  f"Could not verify categorizations: {e}", weight=1.5)

    # =========================================================
    # CHECK 11: Soli + Einkommensteuer mentioned
    # =========================================================
    soli_mentioned = "soli" in report_text or "solidaritätszuschlag" in report_text or "solidarity" in report_text
    einkommensteuer_mentioned = "einkommensteuer" in report_text or "income tax" in report_text
    
    add_check("soli_mentioned", soli_mentioned,
              f"Solidaritätszuschlag/Soli referenced: {soli_mentioned}", weight=0.5)
    add_check("einkommensteuer_mentioned", einkommensteuer_mentioned,
              f"Einkommensteuer referenced: {einkommensteuer_mentioned}", weight=0.5)

    # =========================================================
    # CHECK 12: Non-deductible items correctly excluded
    # txn_009 (groceries), txn_016 (revenue), txn_020 (jacket) should NOT be in deductions
    # =========================================================
    false_positives = 0
    if isinstance(deductions, list):
        for d in deductions:
            if isinstance(d, dict):
                txt = json.dumps(d).lower()
                if any(fp in txt for fp in ["rewe", "supermarket", "groceries", "winter jacket", "lebensmittel"]):
                    false_positives += 1
                if "revenue" in txt and "deduct" in txt:
                    false_positives += 1

    no_false_positives = false_positives == 0
    add_check("no_false_positive_deductions", no_false_positives,
              f"False positive deductions (groceries/personal items): {false_positives}", weight=1.5)

    # =========================================================
    # FINAL SCORING
    # =========================================================
    final_score = round(total_score / max_score, 3) if max_score > 0 else 0.0
    all_critical_passed = (
        checks[0]["passed"] and   # file exists
        checks[1]["passed"] and   # valid JSON
        deductions_sufficient and  # enough deductions flagged
        skr04_used                 # SKR04 codes used
    )
    
    result = {
        "passed": final_score >= 0.70 and all_critical_passed,
        "score": final_score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "args", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    run_eval(sys.argv[1])