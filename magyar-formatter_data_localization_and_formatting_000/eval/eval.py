import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def find_output(workspace):
    candidates = list(Path(workspace).rglob("customer_report_hu.json"))
    return candidates[0] if candidates else None

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

output_path = find_output(workspace)

if output_path is None:
    add_check("output_file_exists", False, "customer_report_hu.json not found anywhere in workspace")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

add_check("output_file_exists", True, f"Found at {output_path}")

try:
    with open(output_path, "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception as e:
    add_check("json_parseable", False, f"Could not parse JSON: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

add_check("json_parseable", True, "Valid JSON")

# Must be a list with 5 entries
if not isinstance(data, list) or len(data) != 5:
    add_check("record_count", False, f"Expected list of 5, got {type(data).__name__} length {len(data) if isinstance(data, list) else 'N/A'}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

add_check("record_count", True, "5 records present")

# Index by id
records = {}
for rec in data:
    if isinstance(rec, dict) and "id" in rec:
        records[rec["id"]] = rec

# ── CHECK 1: Date formatting ────────────────────────────────────────────────
# Expected: YYYY. MM. DD.  (with trailing dot, zero-padded month/day)
date_checks_pass = 0
date_cases = [
    ("C001", "birth_date", "1978. 03. 15."),
    ("C002", "birth_date", "1990. 11. 02."),
    ("C003", "birth_date", "2001. 07. 28."),
    ("C004", "birth_date", "1965. 01. 09."),
    ("C005", "birth_date", "1983. 06. 30."),
]
date_errors = []
for cid, field, expected in date_cases:
    rec = records.get(cid, {})
    actual = rec.get(field, rec.get("birth_date", None))
    # also allow nested keys
    if actual is None:
        for v in rec.values():
            if isinstance(v, str) and re.match(r'\d{4}\.\s\d{2}\.\s\d{2}\.', v):
                actual = v
                break
    if actual == expected:
        date_checks_pass += 1
    else:
        date_errors.append(f"{cid}: expected '{expected}', got '{actual}'")

if date_checks_pass == 5:
    add_check("date_format_hungarian", True, "All 5 dates correctly formatted as YYYY. MM. DD.")
else:
    add_check("date_format_hungarian", False, f"{date_checks_pass}/5 correct. Errors: {'; '.join(date_errors)}")

# ── CHECK 2: Currency formatting (account_balance) ─────────────────────────
# Rules: space thousands, comma decimal, space + Ft suffix
# e.g. 2345678.50 -> "2 345 678,50 Ft"
# 750000.00 -> "750 000,00 Ft"
# 12500.25 -> "12 500,25 Ft"
# 9876543.00 -> "9 876 543,00 Ft"
# 333333.33 -> "333 333,33 Ft"

currency_cases = [
    ("C001", "account_balance", "2 345 678,50 Ft"),
    ("C002", "account_balance", "750 000,00 Ft"),
    ("C003", "account_balance", "12 500,25 Ft"),
    ("C004", "account_balance", "9 876 543,00 Ft"),
    ("C005", "account_balance", "333 333,33 Ft"),
]
currency_pass = 0
currency_errors = []
for cid, field, expected in currency_cases:
    rec = records.get(cid, {})
    actual = rec.get(field, rec.get("account_balance", None))
    if actual == expected:
        currency_pass += 1
    else:
        currency_errors.append(f"{cid}: expected '{expected}', got '{actual}'")

if currency_pass == 5:
    add_check("currency_format_forint", True, "All 5 balances correctly formatted with space-thousands, comma decimal, Ft suffix")
else:
    add_check("currency_format_forint", False, f"{currency_pass}/5 correct. Errors: {'; '.join(currency_errors)}")

# ── CHECK 3: Income formatting ─────────────────────────────────────────────
# 485000.00 -> "485 000,00 Ft"
# 320000.75 -> "320 000,75 Ft"
# 195000.00 -> "195 000,00 Ft"
# 1200000.00 -> "1 200 000,00 Ft"
# 410000.50 -> "410 000,50 Ft"
income_cases = [
    ("C001", "monthly_income", "485 000,00 Ft"),
    ("C002", "monthly_income", "320 000,75 Ft"),
    ("C003", "monthly_income", "195 000,00 Ft"),
    ("C004", "monthly_income", "1 200 000,00 Ft"),
    ("C005", "monthly_income", "410 000,50 Ft"),
]
income_pass = 0
income_errors = []
for cid, field, expected in income_cases:
    rec = records.get(cid, {})
    actual = rec.get(field, rec.get("monthly_income", None))
    if actual == expected:
        income_pass += 1
    else:
        income_errors.append(f"{cid}: expected '{expected}', got '{actual}'")

if income_pass == 5:
    add_check("income_format_forint", True, "All 5 incomes correctly formatted")
else:
    add_check("income_format_forint", False, f"{income_pass}/5 correct. Errors: {'; '.join(income_errors)}")

# ── CHECK 4: Phone number formatting ──────────────────────────────────────
# Raw: "36301234567" -> "+36 30 123 4567"
# Raw: "36209876543" -> "+36 20 987 6543"
# Raw: "36703334444" -> "+36 70 333 4444"
# Raw: "36201112233" -> "+36 20 111 2233"
# Raw: "36305556677" -> "+36 30 555 6677"
phone_cases = [
    ("C001", "phone", "+36 30 123 4567"),
    ("C002", "phone", "+36 20 987 6543"),
    ("C003", "phone", "+36 70 333 4444"),
    ("C004", "phone", "+36 20 111 2233"),
    ("C005", "phone", "+36 30 555 6677"),
]
phone_pass = 0
phone_errors = []
for cid, field, expected in phone_cases:
    rec = records.get(cid, {})
    actual = rec.get(field, rec.get("phone_number", rec.get("phone_digits", None)))
    if actual == expected:
        phone_pass += 1
    else:
        phone_errors.append(f"{cid}: expected '{expected}', got '{actual}'")

if phone_pass == 5:
    add_check("phone_format_hungarian", True, "All 5 phones correctly formatted as +36 XX XXX XXXX")
else:
    add_check("phone_format_hungarian", False, f"{phone_pass}/5 correct. Errors: {'; '.join(phone_errors)}")

# ── CHECK 5: Address formatting ────────────────────────────────────────────
# Rule: "irányítószám város, utca házszám emelet. ajtó."  
# e.g. "1051 Budapest, Vörösmarty tér 5. 2. em. 14. ajtó"  -- flexible
# Minimum requirements: zip comes first, then city with comma, then street+house, then floor+door
# We check structural pattern: starts with zip, contains city, contains street
addr_cases = [
    ("C001", "1051", "Budapest", "Vörösmarty tér", "5", "2", "14"),
    ("C002", "4024", "Debrecen", "Piac utca", "18", "fsz", "3"),
    ("C003", "7621", "Pécs", "Király utca", "33", "1", "6"),
    ("C004", "9700", "Szombathely", "Fő tér", "2", "3", "1"),
    ("C005", "6720", "Szeged", "Dugonics tér", "10", "fsz", "2"),
]
addr_pass = 0
addr_errors = []
for cid, zipcode, city, street, house, floor, door in addr_cases:
    rec = records.get(cid, {})
    actual = rec.get("address", rec.get("cim", rec.get("address_hu", None)))
    if actual is None:
        addr_errors.append(f"{cid}: no address field found")
        continue
    actual_str = str(actual)
    # Must start with zip code
    starts_with_zip = actual_str.startswith(zipcode)
    # Must contain city after zip, separated by space
    has_city = city in actual_str
    # zip must appear before city
    zip_before_city = actual_str.index(zipcode) < actual_str.index(city) if (zipcode in actual_str and city in actual_str) else False
    # Must contain street name
    has_street = street in actual_str
    # Must contain house number
    has_house = house in actual_str
    # Must contain floor and door
    has_floor = floor in actual_str
    has_door = door in actual_str
    # City must be followed by comma (Hungarian address convention)
    has_city_comma = (city + ",") in actual_str or (city + " ,") in actual_str

    all_ok = starts_with_zip and has_city and zip_before_city and has_street and has_house and has_floor and has_door and has_city_comma
    if all_ok:
        addr_pass += 1
    else:
        reasons = []
        if not starts_with_zip: reasons.append(f"does not start with zip '{zipcode}'")
        if not has_city: reasons.append(f"missing city '{city}'")
        if not zip_before_city: reasons.append("zip not before city")
        if not has_street: reasons.append(f"missing street '{street}'")
        if not has_house: reasons.append(f"missing house '{house}'")
        if not has_floor: reasons.append(f"missing floor '{floor}'")
        if not has_door: reasons.append(f"missing door '{door}'")
        if not has_city_comma: reasons.append("city not followed by comma")
        addr_errors.append(f"{cid} ('{actual_str}'): {', '.join(reasons)}")

if addr_pass == 5:
    add_check("address_format_hungarian", True, "All 5 addresses correctly structured in Hungarian format")
else:
    add_check("address_format_hungarian", False, f"{addr_pass}/5 correct. Errors: {'; '.join(addr_errors)}")

# ── CHECK 6: Decimal separator is comma, not dot ──────────────────────────
# Scan all string values for any monetary/number field with a dot as decimal separator
dot_decimal_violation = False
dot_examples = []
for rec in data:
    if not isinstance(rec, dict):
        continue
    for k, v in rec.items():
        if isinstance(v, str) and k in ("account_balance", "monthly_income"):
            # Should NOT contain a dot as decimal separator
            if re.search(r'\d\.\d{2}\s*Ft', v):
                dot_decimal_violation = True
                dot_examples.append(f"{rec.get('id','?')}.{k}='{v}'")

if not dot_decimal_violation:
    add_check("no_dot_decimal_in_currency", True, "No dot used as decimal separator in currency fields")
else:
    add_check("no_dot_decimal_in_currency", False, f"Found dot decimal separator: {'; '.join(dot_examples)}")

# ── CHECK 7: Ft suffix placement ──────────────────────────────────────────
ft_placement_ok = True
ft_errors = []
for rec in data:
    if not isinstance(rec, dict):
        continue
    for k in ("account_balance", "monthly_income"):
        v = rec.get(k, "")
        if isinstance(v, str) and v:
            # Must end with " Ft"
            if not v.strip().endswith(" Ft"):
                ft_placement_ok = False
                ft_errors.append(f"{rec.get('id','?')}.{k}='{v}'")
            # Must NOT start with Ft
            if v.strip().startswith("Ft"):
                ft_placement_ok = False
                ft_errors.append(f"{rec.get('id','?')}.{k}='{v}' (Ft at start)")

if ft_placement_ok:
    add_check("ft_suffix_placement", True, "Ft correctly placed after number with a space")
else:
    add_check("ft_suffix_placement", False, f"Ft placement errors: {'; '.join(ft_errors)}")

# ── Final score ────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
overall_passed = all(c["passed"] for c in checks)

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks,
}
print(json.dumps(result, ensure_ascii=False, indent=2))