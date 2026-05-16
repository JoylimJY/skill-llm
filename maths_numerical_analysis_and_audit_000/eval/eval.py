import sys
import json
from pathlib import Path

def run_eval(workspace_dir: str):
    checks = []

    # --- Import pywayne for ground-truth computation ---
    try:
        from pywayne.maths import get_all_factors, digitCount, karatsuba_multiplication
        checks.append({"name": "pywayne_import", "passed": True, "detail": "pywayne.maths imported successfully"})
    except Exception as e:
        checks.append({"name": "pywayne_import", "passed": False, "detail": f"Could not import pywayne: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- Ground truth computation ---
    contract_data = [
        ("C-1001", 1260),
        ("C-1002", 840),
        ("C-1003", 720),
        ("C-1004", 900),
        ("C-1005", 504),
        ("C-1006", 360),
        ("C-1007", 630),
        ("C-1008", 660),
        ("C-1009", 756),
        ("C-1010", 600),
        ("C-1011", 480),
        ("C-1012", 420),
        ("C-1013", 300),
        ("C-1014", 210),
        ("C-1015", 100),
    ]

    # Compute factor counts using pywayne
    factor_counts = {}
    all_factors_map = {}
    for ref, nid in contract_data:
        factors = get_all_factors(nid)
        factor_counts[ref] = len(factors)
        all_factors_map[ref] = factors

    # Sort by factor count descending, then by numeric_id descending as tiebreaker
    sorted_contracts = sorted(contract_data, key=lambda x: (factor_counts[x[0]], x[1]), reverse=True)

    top1_ref, top1_id = sorted_contracts[0]
    top2_ref, top2_id = sorted_contracts[1]

    expected_top1_factor_count = factor_counts[top1_ref]
    expected_top2_factor_count = factor_counts[top2_ref]

    # Compute product using karatsuba
    expected_product = karatsuba_multiplication(top1_id, top2_id)

    # Compute digit counts using digitCount
    expected_digit7_count = digitCount(expected_product, 7)
    expected_digit1_count = digitCount(expected_product, 1)

    # --- Locate the output file ---
    report_path = None
    candidates = list(Path(workspace_dir).rglob("audit_report.json"))
    if candidates:
        report_path = candidates[0]

    if report_path is None:
        checks.append({"name": "output_file_exists", "passed": False, "detail": "audit_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}
    else:
        checks.append({"name": "output_file_exists", "passed": True, "detail": f"Found at {report_path}"})

    # --- Parse the output file ---
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
        checks.append({"name": "valid_json", "passed": True, "detail": "audit_report.json is valid JSON"})
    except Exception as e:
        checks.append({"name": "valid_json", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # --- Check 1: Top-ranked contract by factor count ---
    check_top1 = False
    top1_detail = ""
    try:
        reported_top1 = str(report.get("top_composite_contracts", [{}])[0].get("contract_ref", ""))
        if reported_top1 == top1_ref:
            check_top1 = True
            top1_detail = f"Correct: {top1_ref} with {expected_top1_factor_count} factors"
        else:
            top1_detail = f"Expected {top1_ref} ({expected_top1_factor_count} factors), got '{reported_top1}'"
    except Exception as e:
        top1_detail = f"Error reading top1: {e}"
    checks.append({"name": "top1_contract_ref", "passed": check_top1, "detail": top1_detail})

    # --- Check 2: Second-ranked contract ---
    check_top2 = False
    top2_detail = ""
    try:
        reported_top2 = str(report.get("top_composite_contracts", [{}, {}])[1].get("contract_ref", ""))
        if reported_top2 == top2_ref:
            check_top2 = True
            top2_detail = f"Correct: {top2_ref} with {expected_top2_factor_count} factors"
        else:
            top2_detail = f"Expected {top2_ref} ({expected_top2_factor_count} factors), got '{reported_top2}'"
    except Exception as e:
        top2_detail = f"Error reading top2: {e}"
    checks.append({"name": "top2_contract_ref", "passed": check_top2, "detail": top2_detail})

    # --- Check 3: Factor counts reported correctly ---
    check_factor_counts = False
    fc_detail = ""
    try:
        r1 = report["top_composite_contracts"][0]
        r2 = report["top_composite_contracts"][1]
        r1_fc = int(r1.get("factor_count", -1))
        r2_fc = int(r2.get("factor_count", -1))
        if r1_fc == expected_top1_factor_count and r2_fc == expected_top2_factor_count:
            check_factor_counts = True
            fc_detail = f"Correct: {top1_ref}={expected_top1_factor_count}, {top2_ref}={expected_top2_factor_count}"
        else:
            fc_detail = f"Expected ({expected_top1_factor_count}, {expected_top2_factor_count}), got ({r1_fc}, {r2_fc})"
    except Exception as e:
        fc_detail = f"Error reading factor counts: {e}"
    checks.append({"name": "factor_counts_correct", "passed": check_factor_counts, "detail": fc_detail})

    # --- Check 4: Karatsuba product ---
    check_product = False
    prod_detail = ""
    try:
        reported_product = int(report.get("karatsuba_product", -1))
        if reported_product == expected_product:
            check_product = True
            prod_detail = f"Correct product: {expected_product}"
        else:
            prod_detail = f"Expected {expected_product}, got {reported_product}"
    except Exception as e:
        prod_detail = f"Error reading karatsuba_product: {e}"
    checks.append({"name": "karatsuba_product_correct", "passed": check_product, "detail": prod_detail})

    # --- Check 5: Digit 7 count ---
    check_d7 = False
    d7_detail = ""
    try:
        reported_d7 = int(report.get("digit_frequency", {}).get("digit_7_count", -1))
        if reported_d7 == expected_digit7_count:
            check_d7 = True
            d7_detail = f"Correct: digitCount({expected_product}, 7) = {expected_digit7_count}"
        else:
            d7_detail = f"Expected digitCount({expected_product}, 7)={expected_digit7_count}, got {reported_d7}"
    except Exception as e:
        d7_detail = f"Error reading digit_7_count: {e}"
    checks.append({"name": "digit_7_count_correct", "passed": check_d7, "detail": d7_detail})

    # --- Check 6: Digit 1 count ---
    check_d1 = False
    d1_detail = ""
    try:
        reported_d1 = int(report.get("digit_frequency", {}).get("digit_1_count", -1))
        if reported_d1 == expected_digit1_count:
            check_d1 = True
            d1_detail = f"Correct: digitCount({expected_product}, 1) = {expected_digit1_count}"
        else:
            d1_detail = f"Expected digitCount({expected_product}, 1)={expected_digit1_count}, got {reported_d1}"
    except Exception as e:
        d1_detail = f"Error reading digit_1_count: {e}"
    checks.append({"name": "digit_1_count_correct", "passed": check_d1, "detail": d1_detail})

    # --- Check 7: numeric_ids in top_composite_contracts are correct ---
    check_nids = False
    nid_detail = ""
    try:
        r1_nid = int(report["top_composite_contracts"][0].get("numeric_id", -1))
        r2_nid = int(report["top_composite_contracts"][1].get("numeric_id", -1))
        if r1_nid == top1_id and r2_nid == top2_id:
            check_nids = True
            nid_detail = f"Correct: {top1_ref}={top1_id}, {top2_ref}={top2_id}"
        else:
            nid_detail = f"Expected ({top1_id}, {top2_id}), got ({r1_nid}, {r2_nid})"
    except Exception as e:
        nid_detail = f"Error reading numeric_ids: {e}"
    checks.append({"name": "numeric_ids_correct", "passed": check_nids, "detail": nid_detail})

    # --- Final scoring ---
    critical_checks = ["top1_contract_ref", "top2_contract_ref", "karatsuba_product_correct",
                       "digit_7_count_correct", "digit_1_count_correct"]
    all_check_results = {c["name"]: c["passed"] for c in checks}

    critical_passed = all(all_check_results.get(n, False) for n in critical_checks)
    total_passed = sum(1 for c in checks if c["passed"])
    score = total_passed / len(checks)

    return {
        "passed": critical_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))