import json
import sys
import math
from pathlib import Path

def run_eval(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # Find the output file
    output_files = list(workspace.rglob("deduction_analysis.json"))
    if not output_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_exists", "passed": False, "detail": "deduction_analysis.json not found anywhere in workspace"}]
        }

    output_path = output_files[0]
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "output_file_parseable", "passed": False, "detail": f"Failed to parse JSON: {e}"}]
        }

    checks.append({"name": "output_file_exists_and_parseable", "passed": True, "detail": f"Found at {output_path}"})

    # Helper: find deductions list
    deductions = data.get("missed_deductions") or data.get("deductions") or data.get("potential_deductions") or []
    summary = data.get("summary") or data.get("impact_summary") or data.get("estimate") or {}

    def find_txn(txn_id):
        for d in deductions:
            tid = d.get("transaction_id") or d.get("id") or d.get("txn_id") or ""
            if tid == txn_id:
                return d
        return None

    def get_skr(entry):
        if not entry:
            return ""
        return str(entry.get("suggested_skr04") or entry.get("skr04") or entry.get("category_code") or entry.get("suggested_category_code") or "")

    def get_any_str(entry, *keys):
        if not entry:
            return ""
        for k in keys:
            v = entry.get(k)
            if v:
                return str(v)
        return ""

    # =========================================================
    # CHECK 1: Private items NOT flagged as deductions
    # TXN-013 (REWE groceries), TXN-019 (Valentines dinner) must NOT appear in deductions
    # =========================================================
    private_incorrectly_included = []
    for d in deductions:
        tid = d.get("transaction_id") or d.get("id") or d.get("txn_id") or ""
        if tid in ("TXN-013", "TXN-019"):
            private_incorrectly_included.append(tid)

    chk1_passed = len(private_incorrectly_included) == 0
    checks.append({
        "name": "private_transactions_not_flagged",
        "passed": chk1_passed,
        "detail": f"Private items incorrectly included as deductions: {private_incorrectly_included}" if not chk1_passed else "Correctly excluded TXN-013 and TXN-019"
    })
    if chk1_passed:
        total_score += 0.10

    # =========================================================
    # CHECK 2: GWG threshold correctness
    # TXN-003: gross=1190.00, net=1190/1.19=1000.00 EUR exactly => NOT GWG, must be depreciated (AfA)
    # TXN-004: gross=595.00, net=595/1.19=500.00 EUR => GWG, fully deductible
    # =========================================================
    txn003 = find_txn("TXN-003")
    txn004 = find_txn("TXN-004")

    # TXN-003 should be mentioned but flagged for depreciation (AfA), not immediate full deduction
    txn003_correctly_afa = False
    if txn003:
        explanation = (get_any_str(txn003, "explanation", "reason", "note", "comment", "details") or "").lower()
        deductible_type = (get_any_str(txn003, "deduction_type", "type", "treatment") or "").lower()
        # Should mention depreciation/AfA/abschreibung, NOT GWG
        is_afa = any(kw in explanation or kw in deductible_type for kw in ["afa", "depreciat", "abschreibung", "useful life", "nutzungsdauer"])
        is_gwg = any(kw in explanation or kw in deductible_type for kw in ["gwg", "geringwertig", "sofort", "immediately deductible"])
        # Edge: net is exactly 1000 => NOT under 1000, so NOT GWG
        txn003_correctly_afa = is_afa and not is_gwg
    else:
        # Not flagging TXN-003 at all is also acceptable - it might be "already categorized"
        # but it's currently in "Office Supplies" with wrong treatment implied
        # Let's be lenient: if not present, partial credit; strict check below
        txn003_correctly_afa = None  # absent

    # TXN-004 should be GWG / fully deductible
    txn004_gwg = False
    if txn004:
        explanation = (get_any_str(txn004, "explanation", "reason", "note", "comment", "details") or "").lower()
        deductible_type = (get_any_str(txn004, "deduction_type", "type", "treatment") or "").lower()
        txn004_gwg = any(kw in explanation or kw in deductible_type for kw in ["gwg", "geringwertig", "fully deductible", "sofort", "immediately", "full deduction", "voll abziehbar"])

    chk2a_passed = txn003_correctly_afa is True
    chk2b_passed = txn004_gwg and txn004 is not None
    checks.append({
        "name": "gwg_threshold_net_1000_eur_exactly_not_gwg",
        "passed": chk2a_passed,
        "detail": "TXN-003 net=1000 EUR exactly should be depreciated (AfA), NOT GWG. " + (
            "Correctly identified as AfA." if chk2a_passed else
            "Missing or incorrectly classified as GWG (trap: threshold is UNDER 1000 EUR net, not at 1000)."
        )
    })
    checks.append({
        "name": "gwg_monitor_500_eur_net_fully_deductible",
        "passed": chk2b_passed,
        "detail": "TXN-004 net=500 EUR should be GWG. " + (
            "Correctly identified as GWG/fully deductible." if chk2b_passed else "Not correctly identified as GWG immediate deduction."
        )
    })
    if chk2a_passed:
        total_score += 0.12
    if chk2b_passed:
        total_score += 0.08

    # TXN-017: gross=2100, net=2100/1.19=1764.71 => above GWG, must be AfA
    txn017 = find_txn("TXN-017")
    txn017_afa = False
    if txn017:
        explanation = (get_any_str(txn017, "explanation", "reason", "note", "comment", "details") or "").lower()
        deductible_type = (get_any_str(txn017, "deduction_type", "type", "treatment") or "").lower()
        txn017_afa = any(kw in explanation or kw in deductible_type for kw in ["afa", "depreciat", "abschreibung", "useful life"])
    checks.append({
        "name": "mac_studio_above_gwg_afa",
        "passed": txn017_afa,
        "detail": "TXN-017 Mac Studio net=1764.71 EUR must be depreciated (AfA). " + (
            "Correctly identified." if txn017_afa else "Not identified or incorrectly treated."
        )
    })
    if txn017_afa:
        total_score += 0.07

    # =========================================================
    # CHECK 3: Verpflegungspauschale rates
    # TXN-005 (day trip Munich, no overnight) => 14 EUR standard rate
    # TXN-016 (overnight stay Hamburg) => 28 EUR rate
    # =========================================================
    txn005 = find_txn("TXN-005")
    txn016 = find_txn("TXN-016")

    txn005_14eur = False
    if txn005:
        explanation = (get_any_str(txn005, "explanation", "reason", "note", "comment", "details", "verpflegungspauschale") or "").lower()
        # Should mention 14 EUR for day trip
        txn005_14eur = "14" in explanation and any(kw in explanation for kw in ["verpflegung", "pauschale", "meal allowance", "tagegeld"])

    txn016_28eur = False
    if txn016:
        explanation = (get_any_str(txn016, "explanation", "reason", "note", "comment", "details", "verpflegungspauschale") or "").lower()
        # Should mention 28 EUR for overnight
        txn016_28eur = "28" in explanation and any(kw in explanation for kw in ["verpflegung", "pauschale", "meal allowance", "tagegeld", "overnight", "nacht"])

    checks.append({
        "name": "verpflegungspauschale_14eur_day_trip",
        "passed": txn005_14eur,
        "detail": "TXN-005 day trip should mention Verpflegungspauschale of 14 EUR. " + (
            "Correctly noted." if txn005_14eur else "Missing 14 EUR Verpflegungspauschale mention."
        )
    })
    checks.append({
        "name": "verpflegungspauschale_28eur_overnight",
        "passed": txn016_28eur,
        "detail": "TXN-016 overnight trip should mention Verpflegungspauschale of 28 EUR. " + (
            "Correctly noted." if txn016_28eur else "Missing 28 EUR overnight Verpflegungspauschale mention."
        )
    })
    if txn005_14eur:
        total_score += 0.07
    if txn016_28eur:
        total_score += 0.07

    # =========================================================
    # CHECK 4: Client gift 35 EUR per-person-per-year cap
    # TXN-009: 28 EUR gift to Herr Schmidt
    # TXN-010: 15 EUR gift to SAME Herr Schmidt
    # Cumulative: 43 EUR > 35 EUR cap
    # Only 35 EUR total deductible; excess (8 EUR) not deductible
    # =========================================================
    txn009 = find_txn("TXN-009")
    txn010 = find_txn("TXN-010")

    gift_cap_correct = False
    # Check if agent mentions the 35 EUR cap and handles the cumulative situation
    cap_mentions = []
    for txn in [txn009, txn010]:
        if txn:
            exp = (get_any_str(txn, "explanation", "reason", "note", "comment", "details") or "").lower()
            cap_mentions.append("35" in exp and any(kw in exp for kw in ["cap", "limit", "grenze", "per person", "pro person", "geschenk"]))

    # At minimum: the combined gift analysis should mention the 35 EUR cap
    # and indicate partial deductibility or cap exceeded
    gift_analysis_text = json.dumps(data).lower()
    gift_cap_mentioned = "35" in gift_analysis_text and any(
        kw in gift_analysis_text for kw in ["per person", "pro person", "geschenk", "gift cap", "gift limit", "grenze"]
    )
    # Also check if agent notes that cumulative > 35 EUR for Schmidt
    cap_exceeded_noted = any(kw in gift_analysis_text for kw in [
        "exceed", "überschreitet", "cumulative", "kumulativ", "über 35", "above 35", "43", "not fully deductible", "partially"
    ])

    gift_cap_correct = gift_cap_mentioned and cap_exceeded_noted
    checks.append({
        "name": "client_gift_35eur_per_person_cumulative_cap",
        "passed": gift_cap_correct,
        "detail": "TXN-009+TXN-010 total 43 EUR for same client exceeds 35 EUR cap. " + (
            "Agent correctly identified cap exceedance." if gift_cap_correct else
            "Agent failed to note cumulative 35 EUR/person/year cap exceedance."
        )
    })
    if gift_cap_correct:
        total_score += 0.10

    # =========================================================
    # CHECK 5: Mixed-use item (phone) - only business portion
    # TXN-020: mobile plan 39.99 EUR, 50% business => ~20 EUR deductible
    # =========================================================
    txn020 = find_txn("TXN-020")
    mixed_use_correct = False
    if txn020:
        exp = (get_any_str(txn020, "explanation", "reason", "note", "comment", "details") or "").lower()
        deductible_amount = txn020.get("deductible_amount") or txn020.get("suggested_deductible") or txn020.get("amount_deductible") or 0
        try:
            deductible_amount = float(deductible_amount)
        except:
            deductible_amount = 0

        mixed_use_correct = (
            any(kw in exp for kw in ["50%", "50 %", "business portion", "anteil", "mixed", "gemischt"]) and
            (abs(deductible_amount - 19.995) < 3.0 or "50" in exp)  # roughly half
        )
    checks.append({
        "name": "mixed_use_phone_50pct_business",
        "passed": mixed_use_correct,
        "detail": "TXN-020 mobile plan should only claim 50% business portion. " + (
            "Correctly handled mixed-use." if mixed_use_correct else "Did not correctly apply business-only portion for mixed-use phone."
        )
    })
    if mixed_use_correct:
        total_score += 0.07

    # =========================================================
    # CHECK 6: SKR04 category codes present and plausible
    # =========================================================
    skr_codes_valid = {
        "TXN-002": ["4813", "4980"],   # Adobe CC -> EDV/Software
        "TXN-007": ["4940", "4945"],   # Professional liability -> Versicherungen
        "TXN-011": ["4530", "4850", "4520"],  # Steuerberater -> Buchführungskosten/Beratung
        "TXN-014": ["4740"],           # Bank fees -> Kosten des Geldverkehrs
    }

    skr_score = 0
    skr_details = []
    for txn_id, valid_codes in skr_codes_valid.items():
        entry = find_txn(txn_id)
        if entry:
            skr_val = get_skr(entry)
            matched = any(code in skr_val for code in valid_codes)
            skr_score += 1 if matched else 0
            skr_details.append(f"{txn_id}: suggested={skr_val}, valid={valid_codes}, match={matched}")
        else:
            skr_details.append(f"{txn_id}: not found in deductions")

    skr_pass_threshold = skr_score >= 2  # at least 2 of 4 must have correct SKR04
    checks.append({
        "name": "skr04_codes_correct",
        "passed": skr_pass_threshold,
        "detail": f"SKR04 correctness: {skr_score}/4. Details: {'; '.join(skr_details)}"
    })
    if skr_pass_threshold:
        total_score += 0.08

    # =========================================================
    # CHECK 7: Tax savings estimate uses 30-42% range
    # =========================================================
    summary_text = json.dumps(summary).lower() + json.dumps(data).lower()
    has_30_pct = "30" in summary_text or "30%" in summary_text
    has_42_pct = "42" in summary_text or "42%" in summary_text
    has_37_pct = "37" in summary_text or "37%" in summary_text  # also acceptable (from tax_settings)
    rate_correct = (has_30_pct and has_42_pct) or has_37_pct

    checks.append({
        "name": "tax_savings_uses_correct_marginal_rate",
        "passed": rate_correct,
        "detail": "Summary should reference 30-42% marginal rate or the specific 37% from tax settings. " + (
            "Correct rate range found." if rate_correct else "Missing or incorrect marginal rate in summary."
        )
    })
    if rate_correct:
        total_score += 0.07

    # =========================================================
    # CHECK 8: Summary fields present with plausible values
    # =========================================================
    total_reviewed = (
        summary.get("transactions_reviewed") or
        summary.get("total_transactions") or
        data.get("transactions_reviewed") or
        data.get("total_reviewed")
    )
    total_deductions_count = (
        summary.get("missed_deductions_count") or
        summary.get("deductions_found") or
        summary.get("count") or
        len(deductions)
    )
    estimated_amount = (
        summary.get("additional_deductible_eur") or
        summary.get("total_deductible_amount") or
        summary.get("estimated_deductible") or
        summary.get("estimated_additional_deductible_eur") or
        data.get("total_deductible_eur")
    )

    try:
        total_reviewed_int = int(total_reviewed) if total_reviewed else 0
        total_deductions_int = int(total_deductions_count) if total_deductions_count else 0
        estimated_amount_float = float(estimated_amount) if estimated_amount else 0.0
    except:
        total_reviewed_int = 0
        total_deductions_int = 0
        estimated_amount_float = 0.0

    # 20 transactions in input; should review >= 15
    reviewed_ok = total_reviewed_int >= 15
    # Should find >= 8 missed deductions (there are ~14 flaggable items)
    count_ok = total_deductions_int >= 6
    # Total deductible should be somewhere reasonable > 200 EUR (conservative), < 10000 EUR
    amount_ok = 200.0 < estimated_amount_float < 10000.0

    checks.append({
        "name": "summary_transactions_reviewed",
        "passed": reviewed_ok,
        "detail": f"Reviewed={total_reviewed_int}, expected >=15. {'OK' if reviewed_ok else 'Too few'}"
    })
    checks.append({
        "name": "summary_deductions_count",
        "passed": count_ok,
        "detail": f"Deductions found={total_deductions_int}, expected >=6. {'OK' if count_ok else 'Too few'}"
    })
    checks.append({
        "name": "summary_estimated_deductible_amount",
        "passed": amount_ok,
        "detail": f"Estimated={estimated_amount_float} EUR, expected 200-10000. {'OK' if amount_ok else 'Out of range'}"
    })
    if reviewed_ok:
        total_score += 0.05
    if count_ok:
        total_score += 0.07
    if amount_ok:
        total_score += 0.05

    # =========================================================
    # CHECK 9: Internet/phone - home office proportional deduction noted
    # TXN-001: Vodafone internet, home_office_percentage=20% noted in company_details
    # =========================================================
    txn001 = find_txn("TXN-001")
    home_office_correct = False
    if txn001:
        exp = (get_any_str(txn001, "explanation", "reason", "note", "comment", "details") or "").lower()
        home_office_correct = any(kw in exp for kw in [
            "home office", "arbeitszimmer", "20%", "proportional", "anteil", "office portion", "büroanteil"
        ])
    checks.append({
        "name": "internet_home_office_proportional",
        "passed": home_office_correct,
        "detail": "TXN-001 internet should note home office proportional use (20% from company_details). " + (
            "Correctly mentioned." if home_office_correct else "Missing proportional deduction note."
        )
    })
    if home_office_correct:
        total_score += 0.06

    # Final pass determination: score >= 0.55 and critical checks pass
    critical_checks_passed = chk1_passed and (chk2a_passed or chk2b_passed) and rate_correct
    final_passed = total_score >= 0.55 and critical_checks_passed

    # Cap score at 1.0
    total_score = min(round(total_score, 3), 1.0)

    return {
        "passed": final_passed,
        "score": total_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))