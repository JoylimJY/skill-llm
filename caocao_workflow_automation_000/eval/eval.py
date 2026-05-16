import sys
import json
import re
from pathlib import Path

workspace = sys.argv[1]

checks = []

def find_report():
    candidates = list(Path(workspace).rglob("caocao_travel_report.json"))
    return candidates[0] if candidates else None

def add_check(name, passed, detail):
    checks.append({"name": name, "passed": passed, "detail": detail})
    return passed

report_path = find_report()

if not report_path:
    add_check("report_file_exists", False, "caocao_travel_report.json not found anywhere in workspace")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

add_check("report_file_exists", True, f"Found at {report_path}")

try:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    add_check("valid_json", True, "File is valid JSON")
except Exception as e:
    add_check("valid_json", False, f"JSON parse error: {e}")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

# Check top-level structure: must have scenarios array
if not isinstance(report, dict):
    add_check("top_level_structure", False, "Report must be a JSON object/dict")
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)

# Find scenarios list
scenarios = None
for key in report:
    val = report[key]
    if isinstance(val, list) and len(val) >= 4:
        # Check if items have IDs matching S001-S004
        ids = [str(item.get("id", "")) for item in val if isinstance(item, dict)]
        if any("S001" in i or "S002" in i or "S003" in i or "S004" in i for i in ids):
            scenarios = val
            break

if scenarios is None:
    # Try nested
    for key in report:
        if isinstance(report[key], dict):
            for k2 in report[key]:
                val = report[key][k2]
                if isinstance(val, list) and len(val) >= 4:
                    scenarios = val
                    break

add_check("scenarios_present", scenarios is not None,
          f"Found {len(scenarios) if scenarios else 0} scenarios" if scenarios else "No scenario array with S001-S004 found")

def find_scenario(sid):
    if not scenarios:
        return None
    for s in scenarios:
        if isinstance(s, dict) and (str(s.get("id", "")) == sid or sid in str(s.get("id", ""))):
            return s
    return None

def extract_number(val):
    """Extract a float from various representations."""
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        nums = re.findall(r'\d+\.?\d*', val)
        if nums:
            return float(nums[0])
    return None

# =========================================================
# S001: 惠选服务, 张伟, 杭州, 8km, 25min, daytime
# 惠选 pricing ~ same formula as 专车 but lower end:
# base fare 12-15 (say 12 for 惠选/economy), but SKILL says 惠选 is 经济实惠
# For eval: recommend 惠选 (not 专车, not 顺风车)
# Cost estimate using 专车 formula (lower bound): 12 + (8-3)*2.5 + 25*0.5 = 12+12.5+12.5 = 37
# Upper bound: 15 + (8-3)*3.0 + 25*0.8 = 15+15+20 = 50
# Accept any cost in range [30, 60] for inbound/outbound rounding
# =========================================================
s001 = find_scenario("S001")
s001_ok = s001 is not None

# Service type check for S001 — should be 惠选
s001_service_ok = False
s001_service_detail = "S001 not found"
if s001:
    content = json.dumps(s001, ensure_ascii=False).lower()
    # 惠选 is the correct answer for budget daily commute
    if "惠选" in content:
        s001_service_ok = True
        s001_service_detail = "Correctly recommended 惠选 for S001"
    else:
        s001_service_detail = f"Expected 惠选 for budget commute, got: {content[:200]}"

add_check("S001_service_recommendation", s001_service_ok, s001_service_detail)

# Cost check for S001
s001_cost_ok = False
s001_cost_detail = "Cannot find cost for S001"
if s001:
    content_str = json.dumps(s001, ensure_ascii=False)
    nums = re.findall(r'\d+\.?\d*', content_str)
    floats = [float(n) for n in nums if 25 <= float(n) <= 80]
    if floats:
        s001_cost_ok = True
        s001_cost_detail = f"Found plausible cost values: {floats[:5]}"
    else:
        s001_cost_detail = f"No cost in plausible range [25-80] found. Numbers: {[float(n) for n in nums[:10]]}"

add_check("S001_cost_estimate_plausible", s001_cost_ok, s001_cost_detail)

# =========================================================
# S002: 专车服务, 王芳, 上海, 12km, 30min, business reception
# Must recommend 专车 (not 惠选)
# Cost: 12 + (12-3)*2.5 + 30*0.5 = 12+22.5+15 = 49.5 (lower)
#       15 + (12-3)*3.0 + 30*0.8 = 15+27+24 = 66 (upper)
# Accept range [40, 85]
# =========================================================
s002 = find_scenario("S002")

s002_service_ok = False
s002_service_detail = "S002 not found"
if s002:
    content = json.dumps(s002, ensure_ascii=False)
    if "专车" in content:
        s002_service_ok = True
        s002_service_detail = "Correctly recommended 专车 for S002"
    else:
        s002_service_detail = f"Expected 专车 for business reception. Got: {content[:200]}"

add_check("S002_service_recommendation_专车", s002_service_ok, s002_service_detail)

# Check S002 mentions standard service features (着装/开门/备水 or similar)
s002_features_ok = False
s002_features_detail = "S002 not found"
if s002:
    content = json.dumps(s002, ensure_ascii=False)
    feature_keywords = ["着装", "开门", "备水", "规范", "商务", "高端", "标准"]
    found = [kw for kw in feature_keywords if kw in content]
    if len(found) >= 1:
        s002_features_ok = True
        s002_features_detail = f"Found 专车 feature keywords: {found}"
    else:
        s002_features_detail = f"No 专车 feature keywords found. Content: {content[:300]}"

add_check("S002_专车_features_mentioned", s002_features_ok, s002_features_detail)

# =========================================================
# S003: 专车 or 惠选, 李娜, 北京, 15km, 35min, 凌晨1点 (NIGHT: 23:00-06:00 → surcharge applies)
# Night surcharge MUST be mentioned
# Also: 安全功能 (行程分享, SOS, 录音 etc.) must be mentioned
# Enterprise account (公司报销) should be mentioned
# Base cost (专车 lower): 12 + (15-3)*2.5 + 35*0.5 = 12+30+17.5 = 59.5 → plus night surcharge → ~65-75+
# Accept any mention of night fee/surcharge
# =========================================================
s003 = find_scenario("S003")

s003_night_ok = False
s003_night_detail = "S003 not found"
if s003:
    content = json.dumps(s003, ensure_ascii=False)
    night_keywords = ["夜间", "深夜", "23:00", "23时", "凌晨", "夜间服务费", "夜间费", "附加"]
    found = [kw for kw in night_keywords if kw in content]
    if found:
        s003_night_ok = True
        s003_night_detail = f"Night surcharge correctly mentioned: {found}"
    else:
        s003_night_detail = f"No night surcharge keywords found in S003. Content: {content[:300]}"

add_check("S003_night_surcharge_mentioned", s003_night_ok, s003_night_detail)

s003_safety_ok = False
s003_safety_detail = "S003 not found"
if s003:
    content = json.dumps(s003, ensure_ascii=False)
    safety_keywords = ["行程分享", "SOS", "紧急", "录音", "人脸", "安全", "求助"]
    found = [kw for kw in safety_keywords if kw in content]
    if len(found) >= 1:
        s003_safety_ok = True
        s003_safety_detail = f"Safety features mentioned: {found}"
    else:
        s003_safety_detail = f"No safety feature keywords in S003. Content: {content[:300]}"

add_check("S003_safety_features_mentioned", s003_safety_ok, s003_safety_detail)

s003_enterprise_ok = False
s003_enterprise_detail = "S003 not found"
if s003:
    content = json.dumps(s003, ensure_ascii=False)
    ent_keywords = ["企业", "公司账户", "报销", "加班", "公司", "账单"]
    found = [kw for kw in ent_keywords if kw in content]
    if found:
        s003_enterprise_ok = True
        s003_enterprise_detail = f"Enterprise/reimbursement mentioned: {found}"
    else:
        s003_enterprise_detail = f"No enterprise/reimbursement mention for S003. Content: {content[:300]}"

add_check("S003_enterprise_reimbursement_mentioned", s003_enterprise_ok, s003_enterprise_detail)

# =========================================================
# S004: 顺风车, 赵明, 杭州→苏州, 170km, 130min, 不赶时间
# Must recommend 顺风车 (not 惠选, not 专车)
# Key: 长途, 不赶时间, 等待, 最低价格
# =========================================================
s004 = find_scenario("S004")

s004_service_ok = False
s004_service_detail = "S004 not found"
if s004:
    content = json.dumps(s004, ensure_ascii=False)
    if "顺风车" in content:
        s004_service_ok = True
        s004_service_detail = "Correctly recommended 顺风车 for long-distance, no-rush scenario"
    else:
        s004_service_detail = f"Expected 顺风车. Got: {content[:200]}"

add_check("S004_service_recommendation_顺风车", s004_service_ok, s004_service_detail)

# =========================================================
# Global: Customer service hotline must be correct: 400-608-1111
# =========================================================
full_content = json.dumps(report, ensure_ascii=False)

hotline_ok = "400-608-1111" in full_content
add_check("correct_customer_service_hotline",
          hotline_ok,
          "Found 400-608-1111" if hotline_ok else "400-608-1111 not found or wrong hotline provided")

# =========================================================
# Global: Enterprise account features mentioned (统一管理/账单/发票/用车规则)
# =========================================================
ent_global_keywords = ["企业账户", "统一管理", "月度账单", "发票", "用车规则", "管理后台", "商务"]
ent_found = [kw for kw in ent_global_keywords if kw in full_content]
ent_global_ok = len(ent_found) >= 2
add_check("enterprise_account_features_described",
          ent_global_ok,
          f"Enterprise features found: {ent_found}" if ent_global_ok else f"Only found: {ent_found}, need ≥2")

# =========================================================
# Global: Coverage city check —杭州, 上海, 北京 must be confirmed as covered
# =========================================================
city_ok = all(city in full_content for city in ["杭州", "上海", "北京"])
add_check("coverage_cities_confirmed",
          city_ok,
          "杭州/上海/北京 coverage confirmed" if city_ok else "Missing city coverage info for one of: 杭州, 上海, 北京")

# =========================================================
# Score computation
# =========================================================
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4)
all_passed = passed_count == total

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}
print(json.dumps(result, ensure_ascii=False, indent=2))