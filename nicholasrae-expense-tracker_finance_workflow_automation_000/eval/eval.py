import json
import sys
import subprocess
from pathlib import Path

def run_check(name, fn):
    try:
        passed, detail = fn()
        return {"name": name, "passed": passed, "detail": detail}
    except Exception as e:
        return {"name": name, "passed": False, "detail": f"Exception: {e}"}

def load_ledger(workspace):
    ledger_path = Path(workspace) / "skills" / "expense-tracker" / "expenses" / "ledger.json"
    if not ledger_path.exists():
        raise FileNotFoundError(f"Ledger not found at {ledger_path}")
    with open(ledger_path) as f:
        return json.load(f)

def load_budgets(workspace):
    budget_path = Path(workspace) / "skills" / "expense-tracker" / "references" / "budgets.json"
    with open(budget_path) as f:
        return json.load(f)

def check_entry_exists(entries, vendor_substr, category, amount_check_fn, notes_substr=None):
    """Helper: find a ledger entry matching criteria."""
    vendor_substr_low = vendor_substr.lower()
    for e in entries:
        v_match = vendor_substr_low in e.get("vendor", "").lower()
        c_match = e.get("category", "") == category
        a_match = amount_check_fn(e.get("amount", 0))
        n_match = True
        if notes_substr:
            n_match = notes_substr.lower() in e.get("notes", "").lower()
        if v_match and c_match and a_match and n_match:
            return True, e
    return False, None

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []
    all_passed = True

    # --- Load ledger ---
    try:
        entries = load_ledger(workspace)
    except Exception as e:
        print(json.dumps({
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "ledger_loadable", "passed": False, "detail": str(e)}]
        }))
        return

    # ---- CHECK 1: Costco groceries $67 logged correctly ----
    def check_costco():
        found, entry = check_entry_exists(
            entries, "costco", "Groceries",
            lambda a: abs(a - 67.0) < 0.01
        )
        if found:
            return True, f"Found Costco Groceries $67.00: {entry}"
        return False, f"No Costco/Groceries/$67.00 entry found. Entries: {entries}"

    checks.append(run_check("costco_groceries_logged", check_costco))

    # ---- CHECK 2: Dinner SPLIT — must log $45 (half of $90), not $90 ----
    def check_split_dinner():
        # Looking for a Dining entry around $45 (split of $90 dinner)
        found, entry = check_entry_exists(
            entries, "", "Dining",
            lambda a: abs(a - 45.0) < 0.51  # allow $44.50–$45.50
        )
        if found:
            return True, f"Found split dinner ~$45 in Dining: {entry}"
        # Also check: ensure $90 Dining entry does NOT exist (wrong split)
        wrong, wrong_entry = check_entry_exists(
            entries, "", "Dining",
            lambda a: abs(a - 90.0) < 0.01
        )
        if wrong:
            return False, f"Agent logged full $90 dinner instead of split $45. Entry: {wrong_entry}"
        return False, f"No Dining entry near $45 found for the split dinner. Entries: {entries}"

    checks.append(run_check("dinner_split_logged_correctly", check_split_dinner))

    # ---- CHECK 3: Amazon refund must be NEGATIVE amount ----
    def check_amazon_refund():
        found, entry = check_entry_exists(
            entries, "amazon", "Shopping",
            lambda a: a < 0 and abs(a - (-38.0)) < 0.01
        )
        if found:
            return True, f"Found Amazon refund as negative: {entry}"
        # Check if positive was logged (wrong)
        found_pos, pos_entry = check_entry_exists(
            entries, "amazon", "Shopping",
            lambda a: a > 0 and abs(a - 38.0) < 0.01
        )
        if found_pos:
            return False, f"Amazon refund logged as POSITIVE $38 (should be -$38). Entry: {pos_entry}"
        return False, f"No Amazon Shopping refund entry (-$38) found. Entries: {entries}"

    checks.append(run_check("amazon_refund_negative_amount", check_amazon_refund))

    # ---- CHECK 4: Paris restaurant must be in Travel category ----
    def check_paris_travel():
        # Expect a Travel entry (Paris restaurant / foreign currency)
        # Amount should be positive (USD equivalent of €60, roughly $60-$70 range, or exactly $65 if agent used a rate)
        found, entry = check_entry_exists(
            entries, "", "Travel",
            lambda a: 50.0 <= a <= 80.0  # reasonable USD range for €60
        )
        if found:
            # Also check notes mention EUR or €
            notes = entry.get("notes", "").lower()
            vendor = entry.get("vendor", "").lower()
            has_currency_note = "eur" in notes or "€" in notes or "paris" in vendor or "paris" in notes
            if has_currency_note:
                return True, f"Paris Travel entry found with currency note: {entry}"
            return True, f"Paris Travel entry found (no EUR note but amount/category correct): {entry}"
        return False, f"No Travel category entry in $50-$80 range found for Paris restaurant (€60). Entries: {entries}"

    checks.append(run_check("paris_restaurant_travel_category", check_paris_travel))

    # ---- CHECK 5: Shell gas station logged as Gas/Transport ----
    def check_shell_gas():
        found, entry = check_entry_exists(
            entries, "shell", "Gas/Transport",
            lambda a: abs(a - 52.0) < 0.51
        )
        if found:
            return True, f"Found Shell Gas/Transport ~$52: {entry}"
        return False, f"No Shell Gas/Transport ~$52 entry found. Entries: {entries}"

    checks.append(run_check("shell_gas_transport_logged", check_shell_gas))

    # ---- CHECK 6: Dining budget updated to $400 ----
    def check_dining_budget():
        budgets = load_budgets(workspace)
        dining_limit = budgets.get("limits", {}).get("Dining", None)
        if dining_limit is None:
            return False, "Dining key missing from budgets.json limits"
        if abs(dining_limit - 400) < 0.01:
            return True, f"Dining budget correctly set to $400 (was $250)"
        return False, f"Dining budget is {dining_limit}, expected 400"

    checks.append(run_check("dining_budget_updated_to_400", check_dining_budget))

    # ---- CHECK 7: Ledger IDs are unique incrementing integers ----
    def check_id_integrity():
        ids = [e.get("id") for e in entries]
        if not ids:
            return False, "No entries in ledger"
        all_int = all(isinstance(i, int) for i in ids)
        unique = len(ids) == len(set(ids))
        all_positive = all(i > 0 for i in ids)
        if all_int and unique and all_positive:
            return True, f"All {len(ids)} IDs are unique positive integers: {sorted(ids)}"
        return False, f"ID integrity issue. IDs: {ids}. all_int={all_int}, unique={unique}, all_positive={all_positive}"

    checks.append(run_check("ledger_id_integrity", check_id_integrity))

    # ---- CHECK 8: Dates are in ISO 8601 YYYY-MM-DD format ----
    def check_date_format():
        import re
        pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        bad = [e for e in entries if not pattern.match(e.get("date", ""))]
        if not bad:
            return True, f"All {len(entries)} entries have valid YYYY-MM-DD dates"
        return False, f"Entries with invalid date format: {bad}"

    checks.append(run_check("dates_iso8601_format", check_date_format))

    # ---- CHECK 9: Categories are from valid list ----
    def check_valid_categories():
        valid = {"Groceries","Dining","Gas/Transport","Subscriptions","Health/Fitness",
                 "Entertainment","Shopping","Utilities","Housing","Personal Care",
                 "Education","Gifts","Travel","Insurance","Pets","Miscellaneous"}
        invalid = [e for e in entries if e.get("category", "") not in valid]
        if not invalid:
            return True, f"All {len(entries)} entries use valid categories"
        return False, f"Entries with invalid categories: {invalid}"

    checks.append(run_check("all_categories_valid", check_valid_categories))

    # ---- CHECK 10: Minimum number of entries (at least 5 logged) ----
    def check_min_entries():
        if len(entries) >= 5:
            return True, f"Ledger has {len(entries)} entries (minimum 5 required)"
        return False, f"Only {len(entries)} entries in ledger, expected at least 5"

    checks.append(run_check("minimum_expense_entries", check_min_entries))

    # ---- CHECK 11: Amounts are numbers (not strings) ----
    def check_amount_types():
        bad = [e for e in entries if not isinstance(e.get("amount"), (int, float))]
        if not bad:
            return True, "All amounts are numeric types"
        return False, f"Entries with non-numeric amounts: {bad}"

    checks.append(run_check("amounts_are_numeric", check_amount_types))

    # ---- CHECK 12: query.sh produces JSON output for the month ----
    def check_query_script():
        result = subprocess.run(
            ["bash", "skills/expense-tracker/scripts/query.sh",
             "--from", "2026-06-01", "--to", "2026-06-30", "--format", "json"],
            capture_output=True, text=True, cwd=workspace
        )
        if result.returncode != 0:
            return False, f"query.sh failed: {result.stderr}"
        try:
            data = json.loads(result.stdout)
            if isinstance(data, list):
                return True, f"query.sh returns valid JSON list with {len(data)} entries"
            return False, f"query.sh returned non-list JSON: {type(data)}"
        except json.JSONDecodeError as e:
            return False, f"query.sh output is not valid JSON: {e}. Output: {result.stdout[:300]}"

    checks.append(run_check("query_script_json_output", check_query_script))

    # ---- Scoring ----
    passed_count = sum(1 for c in checks if c["passed"])
    total = len(checks)
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    output = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()