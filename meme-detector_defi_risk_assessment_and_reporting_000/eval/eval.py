import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []
passed_all = True

def fail_check(name, detail):
    checks.append({"name": name, "passed": False, "detail": detail})
    return False

def pass_check(name, detail):
    checks.append({"name": name, "passed": True, "detail": detail})
    return True

# ── 1. Find the report file ──────────────────────────────────────────────────
report_path = None
for candidate in Path(workspace).rglob("security_audit_report.json"):
    report_path = candidate
    break

if report_path is None:
    fail_check("report_exists", "security_audit_report.json not found anywhere in workspace")
    passed_all = False
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
else:
    pass_check("report_exists", f"Found at {report_path}")

# ── 2. Parse JSON ────────────────────────────────────────────────────────────
try:
    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    pass_check("report_parseable", "Valid JSON")
except Exception as e:
    fail_check("report_parseable", f"JSON parse error: {e}")
    passed_all = False
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)

# ── 3. All 5 contracts present ───────────────────────────────────────────────
EXPECTED_CONTRACTS = {
    "0xA1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0",
    "0xDEAD000000000000000042069420694206942069",
    "0x1234567890abcdef1234567890abcdef12345678",
    "0xFEDCBA9876543210FEDCBA9876543210FEDCBA98",
    "0x0000000000000000000000000000000000000001",
}

EXPECTED_DATA = {
    "0xA1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0": {"score": 72, "risk_level": "medium"},
    "0xDEAD000000000000000042069420694206942069":  {"score": 18, "risk_level": "dangerous"},
    "0x1234567890abcdef1234567890abcdef12345678":  {"score": 91, "risk_level": "safe"},
    "0xFEDCBA9876543210FEDCBA9876543210FEDCBA98":  {"score": 54, "risk_level": "medium"},
    "0x0000000000000000000000000000000000000001":  {"score":  7, "risk_level": "dangerous"},
}

# Find where contract results are stored - flexible: top-level list or nested key
results_list = None
if isinstance(report, list):
    results_list = report
elif isinstance(report, dict):
    for key in ("results", "contracts", "tokens", "report", "assessments", "data"):
        if key in report and isinstance(report[key], list):
            results_list = report[key]
            break
    if results_list is None:
        # Maybe contract addresses are direct keys
        found_addrs = [k for k in report.keys() if k.startswith("0x")]
        if len(found_addrs) >= 3:
            results_list = [{"contract_address": k, **report[k]} for k in found_addrs]

if results_list is None:
    fail_check("results_structure", f"Cannot find a list of contract results. Top-level keys: {list(report.keys()) if isinstance(report, dict) else 'not a dict'}")
    passed_all = False
    print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
    sys.exit(0)
else:
    pass_check("results_structure", f"Found results list with {len(results_list)} entries")

# Build lookup by address
def find_addr(entry):
    for field in ("contract_address", "address", "contract", "addr", "token_address"):
        if field in entry:
            return str(entry[field])
    # Try any value that looks like an address
    for v in entry.values():
        if isinstance(v, str) and v.startswith("0x") and len(v) >= 10:
            return v
    return None

result_by_addr = {}
for entry in results_list:
    if isinstance(entry, dict):
        addr = find_addr(entry)
        if addr:
            result_by_addr[addr] = entry

found_addrs = set(result_by_addr.keys())
missing = EXPECTED_CONTRACTS - found_addrs
if missing:
    fail_check("all_contracts_present", f"Missing contracts: {missing}")
    passed_all = False
else:
    pass_check("all_contracts_present", "All 5 contracts present in report")

# ── 4. Correct scores ────────────────────────────────────────────────────────
score_ok = 0
score_details = []
for addr, expected in EXPECTED_DATA.items():
    entry = result_by_addr.get(addr, {})
    score_val = None
    for field in ("score", "safety_score", "security_score", "total_score", "rating"):
        if field in entry:
            try:
                score_val = int(entry[field])
            except:
                pass
            break
    if score_val == expected["score"]:
        score_ok += 1
        score_details.append(f"{addr[:10]}...: score {score_val} ✓")
    else:
        score_details.append(f"{addr[:10]}...: expected {expected['score']}, got {score_val}")

if score_ok == 5:
    pass_check("correct_scores", "; ".join(score_details))
elif score_ok >= 3:
    pass_check("correct_scores", f"{score_ok}/5 scores correct. " + "; ".join(score_details))
else:
    fail_check("correct_scores", f"Only {score_ok}/5 scores correct. " + "; ".join(score_details))
    passed_all = False

# ── 5. Correct risk level classification (proprietary thresholds) ────────────
# 80-100 = safe, 50-79 = medium, 0-49 = dangerous
RISK_ALIASES = {
    "safe":      {"safe", "安全", "low", "green", "low_risk", "low risk", "🟢"},
    "medium":    {"medium", "中等", "moderate", "yellow", "mid", "medium_risk", "medium risk", "🟡"},
    "dangerous": {"dangerous", "危险", "high", "red", "danger", "high_risk", "high risk", "🔴", "critical"},
}

def normalize_risk(val):
    if val is None:
        return None
    v = str(val).lower().strip()
    for level, aliases in RISK_ALIASES.items():
        if v in aliases or any(a.lower() in v for a in aliases):
            return level
    # Score-based fallback: if numeric
    try:
        n = int(val)
        if n >= 80: return "safe"
        if n >= 50: return "medium"
        return "dangerous"
    except:
        pass
    return v

risk_ok = 0
risk_details = []
for addr, expected in EXPECTED_DATA.items():
    entry = result_by_addr.get(addr, {})
    risk_raw = None
    for field in ("risk_level", "risk", "level", "grade", "status", "category"):
        if field in entry:
            risk_raw = entry[field]
            break
    norm = normalize_risk(risk_raw)
    if norm == expected["risk_level"]:
        risk_ok += 1
        risk_details.append(f"{addr[:10]}...: {norm} ✓")
    else:
        risk_details.append(f"{addr[:10]}...: expected {expected['risk_level']}, got '{risk_raw}' (normalized: {norm})")

if risk_ok == 5:
    pass_check("correct_risk_levels", "; ".join(risk_details))
elif risk_ok >= 3:
    pass_check("correct_risk_levels", f"{risk_ok}/5 risk levels correct. " + "; ".join(risk_details))
else:
    fail_check("correct_risk_levels", f"Only {risk_ok}/5 risk levels correct. " + "; ".join(risk_details))
    passed_all = False

# ── 6. Dangerous contracts identified ────────────────────────────────────────
DANGEROUS = {
    "0xDEAD000000000000000042069420694206942069",
    "0x0000000000000000000000000000000000000001",
}

dangerous_found = set()
dangerous_field = None
# Look for a dedicated "dangerous_contracts" or similar field in the top-level report
if isinstance(report, dict):
    for key in ("dangerous_contracts", "high_risk_contracts", "flagged_contracts", "risk_contracts", "do_not_invest"):
        if key in report:
            val = report[key]
            if isinstance(val, list):
                dangerous_field = key
                for item in val:
                    if isinstance(item, str) and item.startswith("0x"):
                        dangerous_found.add(item)
                    elif isinstance(item, dict):
                        a = find_addr(item)
                        if a:
                            dangerous_found.add(a)
            break

# Fallback: derive from results list
if not dangerous_found:
    for addr, entry in result_by_addr.items():
        risk_raw = None
        for field in ("risk_level", "risk", "level", "grade", "status", "category"):
            if field in entry:
                risk_raw = entry[field]
                break
        norm = normalize_risk(risk_raw)
        if norm == "dangerous":
            dangerous_found.add(addr)

if DANGEROUS.issubset(dangerous_found):
    pass_check("dangerous_contracts_identified",
               f"Both dangerous contracts correctly identified: {dangerous_found}")
else:
    fail_check("dangerous_contracts_identified",
               f"Expected dangerous: {DANGEROUS}, found dangerous: {dangerous_found}")
    passed_all = False

# ── 7. Total fee calculation: 5 × 0.001 = 0.005 USDT ────────────────────────
fee_correct = False
fee_val = None
if isinstance(report, dict):
    for field in ("total_fee", "total_fees", "fee_total", "total_cost", "cost_usdt",
                  "fees_charged", "total_fee_usdt", "total_usdt_spent"):
        if field in report:
            try:
                fee_val = float(report[field])
                if abs(fee_val - 0.005) < 1e-9:
                    fee_correct = True
            except:
                fee_val = report[field]
            break
    # Also check inside a "summary" sub-key
    if not fee_correct and "summary" in report and isinstance(report["summary"], dict):
        for field in ("total_fee", "total_fees", "fee_total", "total_cost", "cost_usdt",
                      "fees_charged", "total_fee_usdt", "total_usdt_spent"):
            if field in report["summary"]:
                try:
                    fee_val = float(report["summary"][field])
                    if abs(fee_val - 0.005) < 1e-9:
                        fee_correct = True
                except:
                    pass
                break

if fee_correct:
    pass_check("total_fee_correct", f"Total fee = {fee_val} USDT (correct: 5 × 0.001 = 0.005)")
else:
    fail_check("total_fee_correct",
               f"Expected total_fee = 0.005 USDT (5 contracts × 0.001 USDT each). Found: {fee_val}")
    passed_all = False

# ── 8. Ranking (highest score first OR lowest score first — must be monotone) ─
if results_list and len(results_list) == 5:
    score_seq = []
    for entry in results_list:
        for field in ("score", "safety_score", "security_score", "total_score", "rating"):
            if field in entry:
                try:
                    score_seq.append(int(entry[field]))
                except:
                    pass
                break
    if len(score_seq) == 5:
        sorted_desc = sorted(score_seq, reverse=True)
        sorted_asc  = sorted(score_seq)
        if score_seq == sorted_desc or score_seq == sorted_asc:
            pass_check("results_ranked", f"Results are sorted: {score_seq}")
        else:
            fail_check("results_ranked", f"Results are NOT sorted by score: {score_seq}")
            passed_all = False
    else:
        fail_check("results_ranked", f"Could not extract scores for ranking check, got: {score_seq}")
        passed_all = False
else:
    fail_check("results_ranked", f"Expected 5 entries in results list, got {len(results_list) if results_list else 0}")
    passed_all = False

# ── Final scoring ────────────────────────────────────────────────────────────
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score_pct = round(passed_count / total, 3)

# Hard requirements: report exists, parseable, all 5 contracts, fee correct
hard_reqs = ["report_exists", "report_parseable", "all_contracts_present", "total_fee_correct"]
hard_pass = all(c["passed"] for c in checks if c["name"] in hard_reqs)
final_pass = passed_all and hard_pass and score_pct >= 0.75

print(json.dumps({
    "passed": final_pass,
    "score": score_pct,
    "checks": checks
}, ensure_ascii=False, indent=2))