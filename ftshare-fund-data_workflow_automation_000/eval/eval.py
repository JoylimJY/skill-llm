import sys
import json
import os
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

def check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})

# Find the output file
output_files = list(workspace.rglob("fund_performance_report.json"))

if not output_files:
    check("output_file_exists", False, "fund_performance_report.json not found anywhere in workspace")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

output_file = output_files[0]
check("output_file_exists", True, f"Found at {output_file}")

try:
    data = json.loads(output_file.read_text(encoding="utf-8"))
except Exception as e:
    check("valid_json", False, f"Could not parse JSON: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

check("valid_json", True, "File is valid JSON")

# ── Check 1: Both target funds present ─────────────────────────────────────────
funds_data = None
# Accept either a list or a dict with a funds key
if isinstance(data, list):
    funds_data = data
elif isinstance(data, dict):
    # Try common keys
    for key in ("funds", "data", "results", "report"):
        if key in data and isinstance(data[key], list):
            funds_data = data[key]
            break
    if funds_data is None:
        # Maybe dict keyed by code or name
        funds_data = list(data.values()) if all(isinstance(v, dict) for v in data.values()) else None

if funds_data is None:
    check("funds_structure", False, "Cannot locate list of fund entries in JSON")
    result = {"passed": False, "score": 1/6, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

check("funds_structure", True, f"Found fund list with {len(funds_data)} entries")

def find_fund(funds, code=None, name_fragment=None):
    for f in funds:
        if not isinstance(f, dict):
            continue
        # Check by code
        for k in ("code", "institution_code", "fund_code", "id"):
            if str(f.get(k, "")).strip() == str(code):
                return f
        # Check by name fragment
        if name_fragment:
            for k in ("name", "fund_name", "fullname", "title"):
                if name_fragment in str(f.get(k, "")):
                    return f
    return None

fund_a = find_fund(funds_data, code="159619", name_fragment="华泰柏瑞")
fund_b = find_fund(funds_data, code="110022", name_fragment="易方达消费")

check("fund_159619_present", fund_a is not None,
      f"Fund 159619 (华泰柏瑞中证A500ETF) found: {fund_a is not None}")
check("fund_110022_present", fund_b is not None,
      f"Fund 110022 (易方达消费行业股票) found: {fund_b is not None}")

# ── Check 2: Institution codes are correct ─────────────────────────────────────
def has_correct_code(fund_obj, expected_code):
    if fund_obj is None:
        return False
    for k in ("code", "institution_code", "fund_code", "id"):
        if str(fund_obj.get(k, "")).strip() == expected_code:
            return True
    return False

code_a_ok = has_correct_code(fund_a, "159619")
code_b_ok = has_correct_code(fund_b, "110022")
check("correct_institution_codes", code_a_ok and code_b_ok,
      f"159619 code correct: {code_a_ok}, 110022 code correct: {code_b_ok}")

# ── Check 3: 1Y return data present for both funds ────────────────────────────
def has_return_data(fund_obj, period_key):
    """Check if fund_obj contains return data for the given period (1Y or 3M)."""
    if fund_obj is None:
        return False, "fund_obj is None"
    # Look for nested return data
    text = json.dumps(fund_obj, ensure_ascii=False).lower()
    period_lower = period_key.lower()
    has_period = period_lower in text or period_key in json.dumps(fund_obj)
    if not has_period:
        return False, f"Period '{period_key}' not found in fund data"
    # Check for actual return values (list of dicts with date+return_rate, or similar)
    for k in ("returns", "return_data", "cal_return", "data", "history", period_key, "1y", "3m"):
        v = fund_obj.get(k)
        if v is None:
            # Try case-insensitive
            for fk in fund_obj:
                if fk.lower() == k.lower():
                    v = fund_obj[fk]
                    break
        if isinstance(v, list) and len(v) > 0:
            return True, f"Found return list under key '{k}' with {len(v)} entries"
        if isinstance(v, dict) and period_key in str(v):
            return True, f"Found nested return data under key '{k}'"
    # Maybe returns are stored flat
    if "return_rate" in text or "cumulative" in text or "收益" in text:
        return True, "Return rate data detected in fund object"
    return False, f"No list-form return data found; keys present: {list(fund_obj.keys())}"

# Check 1Y for both
has_1y_a, detail_1y_a = has_return_data(fund_a, "1Y")
has_1y_b, detail_1y_b = has_return_data(fund_b, "1Y")
check("fund_159619_1Y_returns", has_1y_a, f"159619 1Y returns: {detail_1y_a}")
check("fund_110022_1Y_returns", has_1y_b, f"110022 1Y returns: {detail_1y_b}")

# Check 3M for both
has_3m_a, detail_3m_a = has_return_data(fund_a, "3M")
has_3m_b, detail_3m_b = has_return_data(fund_b, "3M")
check("fund_159619_3M_returns", has_3m_a, f"159619 3M returns: {detail_3m_a}")
check("fund_110022_3M_returns", has_3m_b, f"110022 3M returns: {detail_3m_b}")

# ── Check 4: Basic info fields present (fund type, manager, etc.) ─────────────
def has_basicinfo(fund_obj):
    if fund_obj is None:
        return False, "fund_obj is None"
    text = json.dumps(fund_obj, ensure_ascii=False)
    # Must have at least one of: fund_type/manager_company/fund_manager/investment_objective
    indicators = [
        "fund_type", "manager_company", "fund_manager", "investment_objective",
        "基金类型", "管理人", "基金经理", "投资目标", "股票型", "易方达", "华泰柏瑞", "萧楠", "柳军"
    ]
    found = [ind for ind in indicators if ind in text]
    if len(found) >= 2:
        return True, f"Basic info indicators found: {found[:4]}"
    return False, f"Too few basic info fields. Found: {found}"

bi_a, detail_bi_a = has_basicinfo(fund_a)
bi_b, detail_bi_b = has_basicinfo(fund_b)
check("fund_159619_basicinfo", bi_a, f"159619 basic info: {detail_bi_a}")
check("fund_110022_basicinfo", bi_b, f"110022 basic info: {detail_bi_b}")

# ── Scoring ───────────────────────────────────────────────────────────────────
passed_checks = [c for c in checks if c["passed"]]
total_checks = len(checks)
score = round(len(passed_checks) / total_checks, 3)

# Must pass critical checks to be overall passing
critical = ["output_file_exists", "valid_json", "fund_159619_present", "fund_110022_present",
            "correct_institution_codes", "fund_159619_1Y_returns", "fund_110022_1Y_returns",
            "fund_159619_3M_returns", "fund_110022_3M_returns"]
critical_passed = all(c["passed"] for c in checks if c["name"] in critical)

result = {
    "passed": critical_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))