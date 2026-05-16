import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

workspace = sys.argv[1]

checks = []
passed_all = True

def add_check(name, passed, detail):
    global passed_all
    checks.append({"name": name, "passed": passed, "detail": detail})
    if not passed:
        passed_all = False

# --- Find the output file ---
output_file = None
candidates = list(Path(workspace).rglob("financial_report_2025.json"))
if not candidates:
    # Try alternate names agent might use
    candidates = list(Path(workspace).rglob("*report*2025*.json")) + list(Path(workspace).rglob("*transaction*report*.json"))

if not candidates:
    add_check("output_file_exists", False, "Could not find financial_report_2025.json anywhere in workspace")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

output_file = candidates[0]
add_check("output_file_exists", True, f"Found output file at: {output_file}")

# --- Load JSON ---
try:
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    add_check("valid_json", True, f"File is valid JSON with {len(data)} records")
except Exception as e:
    add_check("valid_json", False, f"Failed to parse JSON: {e}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# --- Check it's a list with 10 records ---
if not isinstance(data, list):
    add_check("is_list_of_records", False, f"Expected JSON array, got {type(data)}")
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

if len(data) != 10:
    add_check("record_count", False, f"Expected 10 records, got {len(data)}")
else:
    add_check("record_count", True, "Correct 10 records")

# --- Build lookup by transaction ID ---
records_by_id = {}
for item in data:
    if isinstance(item, dict):
        for key in ["交易编号", "id", "transaction_id", "txn_id"]:
            if key in item:
                records_by_id[item[key]] = item
                break

# --- Helper: call scripts for ground truth ---
def call_script(script_name, arg):
    try:
        result = subprocess.run(
            ["python3", f"{workspace}/scripts/{script_name}", arg],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout.strip()
    except Exception as e:
        return None

# --- Expected ground truth ---
test_cases = [
    ("TXN-2025-001", "2025-01-15", "88000.00"),
    ("TXN-2025-002", "2025-02-03", "12345.67"),
    ("TXN-2025-003", "2025-03-16", "500.00"),
    ("TXN-2025-004", "2025-04-05", "999999.99"),
    ("TXN-2025-005", "2025-05-15", "7800.50"),
    ("TXN-2025-006", "2025-06-02", "23000.00"),
    ("TXN-2025-007", "2025-07-18", "456.78"),
    ("TXN-2025-008", "2025-09-28", "1000000.00"),
    ("TXN-2025-009", "2025-10-03", "33333.33"),
    ("TXN-2025-010", "2025-12-25", "5500.00"),
]

# --- Check required fields exist ---
required_field_variants = {
    "lunar": ["农历日期", "lunar_date", "lunar", "农历"],
    "amount_cn": ["金额大写", "amount_chinese", "amount_cn", "大写金额", "chinese_amount"],
    "is_workday": ["是否工作日", "is_workday", "workday", "工作日"],
}

sample_record = data[0] if data else {}
fields_present = {}
for concept, variants in required_field_variants.items():
    found = None
    for v in variants:
        if v in sample_record:
            found = v
            break
    fields_present[concept] = found

for concept, field in fields_present.items():
    if field:
        add_check(f"field_{concept}_exists", True, f"Found field '{field}' for {concept}")
    else:
        add_check(f"field_{concept}_exists", False, f"Missing field for {concept}. Checked variants: {required_field_variants[concept]}")

# --- Validate lunar dates for 3 specific records ---
lunar_checks_passed = 0
for txn_id, date_str, _ in test_cases[:4]:
    expected_lunar = call_script("lunar_convert.py", date_str)
    record = records_by_id.get(txn_id)
    if record is None:
        add_check(f"lunar_{txn_id}", False, f"Record {txn_id} not found in output")
        continue
    
    lunar_field = fields_present.get("lunar")
    if not lunar_field:
        add_check(f"lunar_{txn_id}", False, "No lunar field found in records")
        continue
    
    actual_lunar = str(record.get(lunar_field, ""))
    # The lunar string should contain Chinese characters from zhdate
    # zhdate produces strings like "2025年正月初一" or similar
    if expected_lunar and actual_lunar:
        # Check key parts: year numbers and some Chinese calendar terms
        # zhdate format: typically contains year + 月 + day
        lunar_valid = (
            ("月" in actual_lunar or "月" in expected_lunar) and
            len(actual_lunar) >= 5 and
            any(c.isdigit() or c in "一二三四五六七八九十百千万零" for c in actual_lunar)
        )
        # More strict: check if it matches expected output from the script
        scripts_match = (actual_lunar == expected_lunar) or (expected_lunar and expected_lunar in actual_lunar)
        
        if scripts_match:
            add_check(f"lunar_{txn_id}", True, f"Lunar date matches: '{actual_lunar}' (expected: '{expected_lunar}')")
            lunar_checks_passed += 1
        elif lunar_valid:
            add_check(f"lunar_{txn_id}", True, f"Lunar date format valid: '{actual_lunar}' (script output: '{expected_lunar}')")
            lunar_checks_passed += 1
        else:
            add_check(f"lunar_{txn_id}", False, f"Lunar date invalid: '{actual_lunar}' (expected from script: '{expected_lunar}')")
    else:
        add_check(f"lunar_{txn_id}", False, f"Empty lunar date. Got: '{actual_lunar}', Script: '{expected_lunar}'")

# --- Validate Chinese uppercase amounts for 3 records ---
amount_spot_checks = [
    ("TXN-2025-002", "12345.67"),
    ("TXN-2025-005", "7800.50"),
    ("TXN-2025-008", "1000000.00"),
]

for txn_id, amount_str in amount_spot_checks:
    expected_cn = call_script("number_to_chinese.py", amount_str)
    record = records_by_id.get(txn_id)
    if record is None:
        add_check(f"amount_cn_{txn_id}", False, f"Record {txn_id} not found")
        continue
    
    amount_field = fields_present.get("amount_cn")
    if not amount_field:
        add_check(f"amount_cn_{txn_id}", False, "No amount_cn field in records")
        continue
    
    actual_cn = str(record.get(amount_field, ""))
    
    # Check for Chinese financial digits
    chinese_digits = set("零壹贰叁肆伍陆柒捌玖")
    chinese_units = set("元角分整万亿仟佰拾")
    
    has_digits = any(c in chinese_digits for c in actual_cn)
    has_units = any(c in chinese_units for c in actual_cn)
    
    if expected_cn and actual_cn == expected_cn:
        add_check(f"amount_cn_{txn_id}", True, f"Amount matches exactly: '{actual_cn}'")
    elif has_digits and has_units:
        # Partial credit - correct format even if slightly different
        add_check(f"amount_cn_{txn_id}", True, f"Amount in valid Chinese financial format: '{actual_cn}' (script: '{expected_cn}')")
    else:
        add_check(f"amount_cn_{txn_id}", False, f"Invalid Chinese amount: '{actual_cn}' (expected: '{expected_cn}')")

# --- Validate workday flags for specific known cases ---
workday_cases = [
    # (txn_id, date, expected_is_workday based on script)
    ("TXN-2025-003", "2025-03-16", None),  # Sunday - holiday
    ("TXN-2025-004", "2025-04-05", None),  # 清明 - holiday
    ("TXN-2025-008", "2025-09-28", None),  # 调休补班 - workday
    ("TXN-2025-005", "2025-05-15", None),  # Thursday - workday
]

# Get ground truth from script
for i, (txn_id, date_str, _) in enumerate(workday_cases):
    script_output = call_script("workday_check.py", date_str)
    expected_is_workday = (script_output == "workday") if script_output else None
    workday_cases[i] = (txn_id, date_str, expected_is_workday)

for txn_id, date_str, expected_workday in workday_cases:
    record = records_by_id.get(txn_id)
    if record is None:
        add_check(f"workday_{txn_id}", False, f"Record {txn_id} not found")
        continue
    
    workday_field = fields_present.get("is_workday")
    if not workday_field:
        add_check(f"workday_{txn_id}", False, "No workday field in records")
        continue
    
    actual_val = record.get(workday_field)
    
    # Normalize the actual value to bool-like
    if isinstance(actual_val, bool):
        actual_bool = actual_val
    elif isinstance(actual_val, str):
        actual_bool = actual_val.lower() in ["true", "yes", "workday", "是", "工作日"]
        if actual_val.lower() in ["false", "no", "holiday", "否", "非工作日", "节假日", "休息日"]:
            actual_bool = False
    elif isinstance(actual_val, int):
        actual_bool = bool(actual_val)
    else:
        actual_bool = None
    
    if expected_workday is None:
        add_check(f"workday_{txn_id}", False, f"Could not determine expected workday for {date_str} from script")
    elif actual_bool == expected_workday:
        add_check(f"workday_{txn_id}", True, f"{txn_id} ({date_str}): workday={actual_bool} matches expected={expected_workday}")
    else:
        add_check(f"workday_{txn_id}", False, f"{txn_id} ({date_str}): got workday={actual_bool} (raw: '{actual_val}'), expected={expected_workday} (script: '{call_script('workday_check.py', date_str)}')")

# --- Check the tricky makeup workday (调休补班) is correctly identified ---
txn_008 = records_by_id.get("TXN-2025-008")
if txn_008:
    wf = fields_present.get("is_workday")
    if wf:
        val = txn_008.get(wf)
        if isinstance(val, bool):
            actual_bool = val
        elif isinstance(val, str):
            actual_bool = val.lower() in ["true", "yes", "workday", "是", "工作日"]
        else:
            actual_bool = None
        
        if actual_bool == True:
            add_check("makeup_workday_2025-09-28", True, "Correctly identified 2025-09-28 as a makeup workday (调休补班)")
        else:
            add_check("makeup_workday_2025-09-28", False, f"Failed to identify 2025-09-28 as makeup workday. Got: {val}")

# --- Final score ---
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = passed_count / total if total > 0 else 0.0

# Minimum bar: must pass the field checks, at least 2 lunar, 2 amount, 2 workday checks
critical_checks = [
    "output_file_exists", "valid_json", "record_count",
    "field_lunar_exists", "field_amount_cn_exists", "field_is_workday_exists",
]
critical_passed = all(c["passed"] for c in checks if c["name"] in critical_checks)
some_lunar = sum(1 for c in checks if c["name"].startswith("lunar_") and c["passed"]) >= 2
some_amount = sum(1 for c in checks if c["name"].startswith("amount_cn_") and c["passed"]) >= 2
some_workday = sum(1 for c in checks if c["name"].startswith("workday_") and c["passed"]) >= 2

overall_passed = critical_passed and some_lunar and some_amount and some_workday and score >= 0.65

print(json.dumps({
    "passed": overall_passed,
    "score": round(score, 3),
    "checks": checks
}, ensure_ascii=False, indent=2))