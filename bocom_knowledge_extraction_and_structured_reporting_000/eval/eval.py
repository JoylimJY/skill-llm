import sys
import json
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    total_score = 0.0
    
    # Find the output file
    target_files = list(Path(workspace).rglob("bocom_product_audit.json"))
    
    file_found = len(target_files) > 0
    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found {len(target_files)} file(s) named 'bocom_product_audit.json'" if file_found else "File 'bocom_product_audit.json' not found anywhere in workspace"
    })
    
    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}
    
    # Load the JSON
    try:
        with open(target_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "File is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # Helper: safely navigate nested dict
    def get_nested(d, *keys):
        for k in keys:
            if isinstance(d, dict):
                d = d.get(k)
            else:
                return None
        return d

    # ============================================================
    # CHECK 1: Huimin Loan annual rate starts at 3.6%
    # ============================================================
    try:
        val = get_nested(data, "loans", "huimin_loan", "annual_rate_start_pct")
        passed = val is not None and abs(float(val) - 3.6) < 0.01
        checks.append({
            "name": "huimin_loan_rate_3.6pct",
            "passed": passed,
            "detail": f"huimin_loan.annual_rate_start_pct = {val} (expected 3.6)"
        })
    except Exception as e:
        checks.append({"name": "huimin_loan_rate_3.6pct", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 2: Huimin Loan max term is 3 years (not 5)
    # ============================================================
    try:
        val = get_nested(data, "loans", "huimin_loan", "max_term_years")
        passed = val is not None and int(val) == 3
        checks.append({
            "name": "huimin_loan_max_term_3yr",
            "passed": passed,
            "detail": f"huimin_loan.max_term_years = {val} (expected 3)"
        })
    except Exception as e:
        checks.append({"name": "huimin_loan_max_term_3yr", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 3: Large CD minimum deposit is 20万 (200000 yuan)
    # ============================================================
    try:
        val = get_nested(data, "deposits", "large_cd", "min_deposit_yuan")
        # Accept 200000 or 20 (万) — we'll accept either 200000 or "20万" string, or numeric 200000
        passed = False
        if val is not None:
            try:
                numeric = float(str(val).replace("万", "").replace(",", ""))
                # If stored as 万-units: 20; if stored as yuan: 200000
                passed = abs(numeric - 200000) < 1 or abs(numeric - 20) < 0.1
            except:
                passed = str(val) in ["20万", "200000", "200,000"]
        checks.append({
            "name": "large_cd_min_deposit_20wan",
            "passed": passed,
            "detail": f"large_cd.min_deposit_yuan = {val} (expected 200000 or 20万)"
        })
    except Exception as e:
        checks.append({"name": "large_cd_min_deposit_20wan", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 4: Large CD 3-year rate is 3.13%
    # ============================================================
    try:
        val = get_nested(data, "deposits", "large_cd", "rate_3yr_pct")
        passed = val is not None and abs(float(val) - 3.13) < 0.01
        checks.append({
            "name": "large_cd_3yr_rate_3.13pct",
            "passed": passed,
            "detail": f"large_cd.rate_3yr_pct = {val} (expected 3.13)"
        })
    except Exception as e:
        checks.append({"name": "large_cd_3yr_rate_3.13pct", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 5: Cross-border remittance fee is 1‰ (per mille)
    # ============================================================
    try:
        val = get_nested(data, "forex", "remittance", "fee_rate_permille")
        passed = val is not None and abs(float(val) - 1.0) < 0.01
        checks.append({
            "name": "remittance_fee_1_permille",
            "passed": passed,
            "detail": f"remittance.fee_rate_permille = {val} (expected 1.0)"
        })
    except Exception as e:
        checks.append({"name": "remittance_fee_1_permille", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 6: Remittance min fee 50 yuan
    # ============================================================
    try:
        val = get_nested(data, "forex", "remittance", "fee_min_yuan")
        passed = val is not None and abs(float(val) - 50) < 0.1
        checks.append({
            "name": "remittance_fee_min_50yuan",
            "passed": passed,
            "detail": f"remittance.fee_min_yuan = {val} (expected 50)"
        })
    except Exception as e:
        checks.append({"name": "remittance_fee_min_50yuan", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 7: Remittance max fee 260 yuan
    # ============================================================
    try:
        val = get_nested(data, "forex", "remittance", "fee_max_yuan")
        passed = val is not None and abs(float(val) - 260) < 0.1
        checks.append({
            "name": "remittance_fee_max_260yuan",
            "passed": passed,
            "detail": f"remittance.fee_max_yuan = {val} (expected 260)"
        })
    except Exception as e:
        checks.append({"name": "remittance_fee_max_260yuan", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 8: Gold card annual fee is 100 yuan, waived after 6 swipes
    # ============================================================
    try:
        val_fee = get_nested(data, "credit_cards", "gold_card", "annual_fee_yuan")
        passed_fee = val_fee is not None and abs(float(val_fee) - 100) < 0.1
        checks.append({
            "name": "gold_card_annual_fee_100yuan",
            "passed": passed_fee,
            "detail": f"gold_card.annual_fee_yuan = {val_fee} (expected 100)"
        })
    except Exception as e:
        checks.append({"name": "gold_card_annual_fee_100yuan", "passed": False, "detail": f"Error: {e}"})

    try:
        val_waiver = get_nested(data, "credit_cards", "gold_card", "fee_waiver_swipes")
        passed_waiver = val_waiver is not None and int(val_waiver) == 6
        checks.append({
            "name": "gold_card_waiver_6_swipes",
            "passed": passed_waiver,
            "detail": f"gold_card.fee_waiver_swipes = {val_waiver} (expected 6)"
        })
    except Exception as e:
        checks.append({"name": "gold_card_waiver_6_swipes", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 9: Mobile banking single transfer limit 500000 yuan
    # ============================================================
    try:
        val = get_nested(data, "digital_banking", "mobile_app", "transfer_single_limit_yuan")
        passed = val is not None and abs(float(val) - 500000) < 1
        checks.append({
            "name": "mobile_transfer_single_500000yuan",
            "passed": passed,
            "detail": f"mobile_app.transfer_single_limit_yuan = {val} (expected 500000)"
        })
    except Exception as e:
        checks.append({"name": "mobile_transfer_single_500000yuan", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 10: Mobile banking daily transfer limit 1000000 yuan
    # ============================================================
    try:
        val = get_nested(data, "digital_banking", "mobile_app", "transfer_daily_limit_yuan")
        passed = val is not None and abs(float(val) - 1000000) < 1
        checks.append({
            "name": "mobile_transfer_daily_1000000yuan",
            "passed": passed,
            "detail": f"mobile_app.transfer_daily_limit_yuan = {val} (expected 1000000)"
        })
    except Exception as e:
        checks.append({"name": "mobile_transfer_daily_1000000yuan", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 11: Credit card minimum payment daily interest rate 0.05%
    # ============================================================
    try:
        val = get_nested(data, "credit_cards", "minimum_payment", "daily_interest_rate_pct")
        passed = val is not None and abs(float(val) - 0.05) < 0.001
        checks.append({
            "name": "credit_card_daily_interest_0.05pct",
            "passed": passed,
            "detail": f"minimum_payment.daily_interest_rate_pct = {val} (expected 0.05)"
        })
    except Exception as e:
        checks.append({"name": "credit_card_daily_interest_0.05pct", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 12: Savings bond (电子式储蓄国债) 3yr rate 2.98%
    # ============================================================
    try:
        val = get_nested(data, "deposits", "savings_bond", "rate_3yr_pct")
        passed = val is not None and abs(float(val) - 2.98) < 0.01
        checks.append({
            "name": "savings_bond_3yr_rate_2.98pct",
            "passed": passed,
            "detail": f"savings_bond.rate_3yr_pct = {val} (expected 2.98)"
        })
    except Exception as e:
        checks.append({"name": "savings_bond_3yr_rate_2.98pct", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 13: Savings bond sale date - 10th of each month at 8:30
    # ============================================================
    try:
        val_day = get_nested(data, "deposits", "savings_bond", "sale_day_of_month")
        val_time = get_nested(data, "deposits", "savings_bond", "sale_start_time")
        passed_day = val_day is not None and int(val_day) == 10
        passed_time = val_time is not None and "8:30" in str(val_time).replace("08:30","8:30")
        checks.append({
            "name": "savings_bond_sale_day_10th",
            "passed": passed_day,
            "detail": f"savings_bond.sale_day_of_month = {val_day} (expected 10)"
        })
        checks.append({
            "name": "savings_bond_sale_time_8h30",
            "passed": passed_time,
            "detail": f"savings_bond.sale_start_time = {val_time} (expected 8:30)"
        })
    except Exception as e:
        checks.append({"name": "savings_bond_sale_info", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # CHECK 14: Personal annual forex convenience quota 50,000 USD
    # ============================================================
    try:
        val = get_nested(data, "forex", "individual_annual_quota_usd")
        passed = val is not None and abs(float(val) - 50000) < 1
        checks.append({
            "name": "forex_individual_quota_50000usd",
            "passed": passed,
            "detail": f"forex.individual_annual_quota_usd = {val} (expected 50000)"
        })
    except Exception as e:
        checks.append({"name": "forex_individual_quota_50000usd", "passed": False, "detail": f"Error: {e}"})

    # ============================================================
    # Compute score
    # ============================================================
    passed_checks = [c for c in checks if c["passed"]]
    total_checks = len(checks)
    score = len(passed_checks) / total_checks if total_checks > 0 else 0.0
    overall_passed = score >= 0.75  # need 75% to pass

    return {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))