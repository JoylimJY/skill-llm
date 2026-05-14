import sys
import json
import re
from pathlib import Path

def load_json_summary(workspace, year_month):
    """Run the summary command programmatically by parsing the markdown file."""
    expenses_dir = Path(workspace) / "expenses"
    filepath = expenses_dir / f"{year_month}.md"
    if not filepath.exists():
        return None, f"File {filepath} does not exist"

    expenses = []
    try:
        with open(filepath, "r") as f:
            lines = f.readlines()
    except Exception as e:
        return None, str(e)

    in_table = False
    header_passed = False
    for line in lines:
        line = line.strip()
        if line.startswith("| Date |"):
            in_table = True
            header_passed = False
            continue
        if in_table and line.startswith("|---"):
            header_passed = True
            continue
        if in_table and header_passed and line.startswith("|"):
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) >= 3:
                try:
                    amount = int(parts[2].replace(",", ""))
                    expenses.append({
                        "date": parts[0],
                        "category": parts[1],
                        "amount": amount,
                        "description": parts[3] if len(parts) > 3 else "",
                        "tags": parts[4] if len(parts) > 4 else "",
                    })
                except (ValueError, IndexError):
                    continue

    return expenses, None

def evaluate(workspace):
    checks = []
    workspace = Path(workspace)

    # ---- EXPECTED DATA ----
    # March 2026 expenses (amounts in VND, categories must be canonical)
    march_expected = [
        {"date": "2026-03-01", "category": "Coffee",        "amount": 55000},
        {"date": "2026-03-01", "category": "Dining",        "amount": 180000},
        {"date": "2026-03-03", "category": "Vehicle",       "amount": 95000},
        {"date": "2026-03-05", "category": "Electronics",   "amount": 1200000},
        {"date": "2026-03-10", "category": "Subscriptions", "amount": 260000},
        {"date": "2026-03-12", "category": "Healthcare",    "amount": 450000},
        {"date": "2026-03-15", "category": "Coffee",        "amount": 75000},
        {"date": "2026-03-20", "category": "Groceries",     "amount": 620000},
        {"date": "2026-03-25", "category": "Utilities",     "amount": 850000},
        {"date": "2026-03-28", "category": "Social",        "amount": 350000},
    ]
    april_expected = [
        {"date": "2026-04-02", "category": "Coffee",          "amount": 65000},
        {"date": "2026-04-05", "category": "Dining",          "amount": 720000},
        {"date": "2026-04-08", "category": "Subscriptions",   "amount": 215000},
        {"date": "2026-04-10", "category": "Public Transport","amount": 145000},
        {"date": "2026-04-14", "category": "Gifts",           "amount": 500000},
        {"date": "2026-04-18", "category": "Education",       "amount": 399000},
        {"date": "2026-04-22", "category": "Travel",          "amount": 2500000},
        {"date": "2026-04-25", "category": "Vehicle",         "amount": 320000},
        {"date": "2026-04-28", "category": "Coffee",          "amount": 95000},
        {"date": "2026-04-30", "category": "Fitness",         "amount": 500000},
    ]

    march_total_expected = sum(e["amount"] for e in march_expected)
    april_total_expected = sum(e["amount"] for e in april_expected)

    # ---- CHECK 1: March expense file exists ----
    march_file = workspace / "expenses" / "2026-03.md"
    check1_passed = march_file.exists()
    checks.append({
        "name": "march_expense_file_exists",
        "passed": check1_passed,
        "detail": f"expenses/2026-03.md {'found' if check1_passed else 'NOT found'}"
    })

    # ---- CHECK 2: April expense file exists ----
    april_file = workspace / "expenses" / "2026-04.md"
    check2_passed = april_file.exists()
    checks.append({
        "name": "april_expense_file_exists",
        "passed": check2_passed,
        "detail": f"expenses/2026-04.md {'found' if check2_passed else 'NOT found'}"
    })

    # ---- CHECK 3: March file has correct number of entries ----
    march_expenses, march_err = load_json_summary(workspace, "2026-03")
    if march_err or march_expenses is None:
        checks.append({
            "name": "march_entry_count",
            "passed": False,
            "detail": f"Could not parse March file: {march_err}"
        })
    else:
        check3_passed = len(march_expenses) == len(march_expected)
        checks.append({
            "name": "march_entry_count",
            "passed": check3_passed,
            "detail": f"Expected {len(march_expected)} entries, found {len(march_expenses)}"
        })

    # ---- CHECK 4: March total amount correct ----
    if march_expenses:
        march_total_actual = sum(e["amount"] for e in march_expenses)
        check4_passed = march_total_actual == march_total_expected
        checks.append({
            "name": "march_total_amount",
            "passed": check4_passed,
            "detail": f"Expected {march_total_expected:,} VND, got {march_total_actual:,} VND"
        })
    else:
        checks.append({
            "name": "march_total_amount",
            "passed": False,
            "detail": "Could not compute march total (no expenses loaded)"
        })

    # ---- CHECK 5: April file has correct number of entries ----
    april_expenses, april_err = load_json_summary(workspace, "2026-04")
    if april_err or april_expenses is None:
        checks.append({
            "name": "april_entry_count",
            "passed": False,
            "detail": f"Could not parse April file: {april_err}"
        })
    else:
        check5_passed = len(april_expenses) == len(april_expected)
        checks.append({
            "name": "april_entry_count",
            "passed": check5_passed,
            "detail": f"Expected {len(april_expected)} entries, found {len(april_expenses)}"
        })

    # ---- CHECK 6: April total amount correct ----
    if april_expenses:
        april_total_actual = sum(e["amount"] for e in april_expenses)
        check6_passed = april_total_actual == april_total_expected
        checks.append({
            "name": "april_total_amount",
            "passed": check6_passed,
            "detail": f"Expected {april_total_expected:,} VND, got {april_total_actual:,} VND"
        })
    else:
        checks.append({
            "name": "april_total_amount",
            "passed": False,
            "detail": "Could not compute april total (no expenses loaded)"
        })

    # ---- CHECK 7: Dates are correct (backdating used for all entries) ----
    march_date_check = True
    march_date_detail = "All March dates correct"
    if march_expenses:
        march_actual_dates = sorted(set(e["date"] for e in march_expenses))
        expected_march_dates = sorted(set(e["date"] for e in march_expected))
        # All entries should have dates in March 2026
        bad_dates = [e["date"] for e in march_expenses if not e["date"].startswith("2026-03")]
        if bad_dates:
            march_date_check = False
            march_date_detail = f"Found entries with non-March dates: {bad_dates}"
    else:
        march_date_check = False
        march_date_detail = "No march expenses to check"
    checks.append({
        "name": "march_dates_correct",
        "passed": march_date_check,
        "detail": march_date_detail
    })

    # ---- CHECK 8: April dates correct ----
    april_date_check = True
    april_date_detail = "All April dates correct"
    if april_expenses:
        bad_dates = [e["date"] for e in april_expenses if not e["date"].startswith("2026-04")]
        if bad_dates:
            april_date_check = False
            april_date_detail = f"Found entries with non-April dates: {bad_dates}"
    else:
        april_date_check = False
        april_date_detail = "No april expenses to check"
    checks.append({
        "name": "april_dates_correct",
        "passed": april_date_check,
        "detail": april_date_detail
    })

    # ---- CHECK 9: JSON summary file for comparison exists ----
    # Agent must produce a JSON comparison file named comparison_report.json
    comparison_files = list(workspace.rglob("comparison_report.json"))
    check9_passed = len(comparison_files) > 0
    checks.append({
        "name": "comparison_report_json_exists",
        "passed": check9_passed,
        "detail": f"comparison_report.json {'found at ' + str(comparison_files[0]) if check9_passed else 'NOT found anywhere in workspace'}"
    })

    # ---- CHECK 10: comparison_report.json has correct structure and data ----
    if comparison_files:
        try:
            with open(comparison_files[0], "r") as f:
                comparison = json.load(f)

            required_keys = {"2026-03", "2026-04"}
            has_keys = required_keys.issubset(set(comparison.keys()))
            
            march_data = comparison.get("2026-03", {})
            april_data = comparison.get("2026-04", {})

            # Check totals are present and roughly correct (within 1 VND rounding)
            march_total_ok = abs(march_data.get("total", 0) - march_total_expected) == 0
            april_total_ok = abs(april_data.get("total", 0) - april_total_expected) == 0

            check10_passed = has_keys and march_total_ok and april_total_ok
            detail = (
                f"Keys present: {has_keys}. "
                f"March total: got {march_data.get('total',0):,}, expected {march_total_expected:,}. "
                f"April total: got {april_data.get('total',0):,}, expected {april_total_expected:,}."
            )
            checks.append({
                "name": "comparison_report_correctness",
                "passed": check10_passed,
                "detail": detail
            })
        except Exception as e:
            checks.append({
                "name": "comparison_report_correctness",
                "passed": False,
                "detail": f"Error reading/parsing comparison_report.json: {e}"
            })
    else:
        checks.append({
            "name": "comparison_report_correctness",
            "passed": False,
            "detail": "comparison_report.json not found, cannot verify correctness"
        })

    # ---- CHECK 11: March categories use canonical names ----
    canonical_cats = {
        "Coffee", "Dining", "Vehicle", "Electronics", "Subscriptions",
        "Healthcare", "Groceries", "Utilities", "Social", "Public Transport",
        "Gifts", "Education", "Travel", "Fitness", "Shopping", "Entertainment",
        "Housing", "Savings", "Debt Payment", "Miscellaneous", "Clothing",
        "Personal Care", "Work Expenses", "Professional", "Insurance",
        "Fees", "Home", "Fitness", "Pet", "Emergency", "Transfer", "Snacks",
        "Parking"
    }
    canonical_cats_lower = {c.lower() for c in canonical_cats}
    
    bad_cats_march = []
    if march_expenses:
        for e in march_expenses:
            if e["category"].lower() not in canonical_cats_lower:
                bad_cats_march.append(e["category"])
    
    bad_cats_april = []
    if april_expenses:
        for e in april_expenses:
            if e["category"].lower() not in canonical_cats_lower:
                bad_cats_april.append(e["category"])

    all_bad = list(set(bad_cats_march + bad_cats_april))
    check11_passed = len(all_bad) == 0
    checks.append({
        "name": "canonical_category_names",
        "passed": check11_passed,
        "detail": f"Non-canonical categories found: {all_bad}" if all_bad else "All categories are canonical"
    })

    # Calculate final score
    total_checks = len(checks)
    passed_checks = sum(1 for c in checks if c["passed"])
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    overall_passed = score >= 0.75  # Must pass at least 75% of checks

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "setup", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))