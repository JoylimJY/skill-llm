import sys
import json
import os
from pathlib import Path

workspace = sys.argv[1]

checks = []

def find_report(workspace):
    """Search for doge_audit_report.json anywhere in workspace."""
    matches = list(Path(workspace).rglob("doge_audit_report.json"))
    return matches[0] if matches else None

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

report_path = find_report(workspace)

if report_path is None:
    checks.append(make_check("report_exists", False, "doge_audit_report.json not found anywhere in workspace"))
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

checks.append(make_check("report_exists", True, f"Found at {report_path}"))

try:
    with open(report_path) as f:
        report = json.load(f)
except Exception as e:
    checks.append(make_check("report_parseable", False, f"JSON parse error: {e}"))
    result = {"passed": False, "score": 0.0, "checks": checks}
    print(json.dumps(result))
    sys.exit(0)

checks.append(make_check("report_parseable", True, "Valid JSON"))

# ---- CHECK 1: Address Validation ----
# Expected valid addresses: addr_001, addr_002, addr_003, addr_008, addr_011
# Expected invalid: addr_004 (starts with 1), addr_005 (33 chars), addr_006 (35 chars),
#                   addr_007 (starts with L), addr_009 (starts with 3),
#                   addr_010 (has space), addr_012 (starts with lowercase d)

VALID_ADDR_IDS = {"addr_001", "addr_002", "addr_003", "addr_008", "addr_011"}
INVALID_ADDR_IDS = {"addr_004", "addr_005", "addr_006", "addr_007", "addr_009", "addr_010", "addr_012"}

try:
    addr_section = report.get("address_validation", report.get("addresses", report.get("wallet_addresses", None)))
    if addr_section is None:
        raise KeyError("address_validation section missing")

    # Support list or dict formats
    if isinstance(addr_section, dict):
        addr_items = addr_section.get("results", addr_section.get("addresses", []))
    else:
        addr_items = addr_section

    found_valid = set()
    found_invalid = set()
    for item in addr_items:
        addr_id = item.get("id", "")
        status = str(item.get("status", item.get("valid", item.get("is_valid", "")))).lower()
        is_valid = status in ("valid", "true", "1", "ok", "pass")
        is_invalid = status in ("invalid", "false", "0", "fail", "error")
        if is_valid:
            found_valid.add(addr_id)
        elif is_invalid:
            found_invalid.add(addr_id)

    correct_valid = found_valid == VALID_ADDR_IDS
    correct_invalid = found_invalid == INVALID_ADDR_IDS

    checks.append(make_check(
        "address_valid_set_correct",
        correct_valid,
        f"Expected valid: {VALID_ADDR_IDS}, Got valid: {found_valid}"
    ))
    checks.append(make_check(
        "address_invalid_set_correct",
        correct_invalid,
        f"Expected invalid: {INVALID_ADDR_IDS}, Got invalid: {found_invalid}"
    ))

except Exception as e:
    checks.append(make_check("address_valid_set_correct", False, f"Error parsing address section: {e}"))
    checks.append(make_check("address_invalid_set_correct", False, f"Error parsing address section: {e}"))

# ---- CHECK 2: Dust UTXO Detection ----
# Dust rule: fee_to_spend = (tx_size_bytes / 1000) * 1.0 DOGE; if fee_to_spend > value_doge -> DUST
# utxo_003: fee=0.000148 < 0.0003 -> NOT dust
# utxo_004: fee=0.000148 > 0.00005 -> DUST
# utxo_007: fee=0.000192 > 0.0001 -> DUST
# utxo_010: fee=0.000148 > 0.00008 -> DUST
EXPECTED_DUST = {"utxo_004", "utxo_007", "utxo_010"}
EXPECTED_NOT_DUST = {"utxo_001", "utxo_002", "utxo_003", "utxo_005", "utxo_006", "utxo_008", "utxo_009"}

try:
    utxo_section = report.get("utxo_analysis", report.get("utxos", report.get("dust_analysis", None)))
    if utxo_section is None:
        raise KeyError("utxo_analysis section missing")

    if isinstance(utxo_section, dict):
        utxo_items = utxo_section.get("results", utxo_section.get("utxos", []))
    else:
        utxo_items = utxo_section

    found_dust = set()
    found_not_dust = set()
    for item in utxo_items:
        uid = item.get("utxo_id", "")
        is_dust_raw = item.get("is_dust", item.get("dust", item.get("status", "")))
        if isinstance(is_dust_raw, bool):
            if is_dust_raw:
                found_dust.add(uid)
            else:
                found_not_dust.add(uid)
        elif isinstance(is_dust_raw, str):
            if is_dust_raw.lower() in ("true", "dust", "yes"):
                found_dust.add(uid)
            elif is_dust_raw.lower() in ("false", "not_dust", "no", "normal", "ok"):
                found_not_dust.add(uid)

    dust_correct = found_dust == EXPECTED_DUST
    checks.append(make_check(
        "dust_utxos_correct",
        dust_correct,
        f"Expected dust: {EXPECTED_DUST}, Got: {found_dust}"
    ))

    # Verify fee is calculated per-byte (not per-doge amount) — utxo_003 must NOT be dust
    utxo003_not_dust = "utxo_003" not in found_dust
    checks.append(make_check(
        "fee_calculated_per_byte_not_per_doge",
        utxo003_not_dust,
        "utxo_003 (value=0.0003 DOGE, fee=0.000148 DOGE) must NOT be dust — fee is per-byte, not per-doge-amount"
    ))

except Exception as e:
    checks.append(make_check("dust_utxos_correct", False, f"Error parsing utxo section: {e}"))
    checks.append(make_check("fee_calculated_per_byte_not_per_doge", False, f"Error: {e}"))

# ---- CHECK 3: Transaction Risk Classification ----
# Rules:
# - 0 confirmations: UNCONFIRMED
# - HIGH_VALUE threshold: amount >= 10000 DOGE requires 6+ confirmations; if < 6 confs -> HIGH_RISK
# - amount < 10000 and confs >= 1: LOW_CONFIDENCE (1-5) or CONFIRMED (6+)
# - No RBF available for stuck transactions
#
# tx_aabb1122: 250 DOGE, 0 conf -> UNCONFIRMED
# tx_ccdd3344: 15000 DOGE, 3 conf -> HIGH_VALUE, insufficient confirmations -> HIGH_RISK
# tx_eeff5566: 99.9 DOGE, 6 conf -> CONFIRMED
# tx_aabb9900: 500000 DOGE, 1 conf -> HIGH_VALUE, insufficient confirmations -> HIGH_RISK
# tx_1234abcd: 10 DOGE, 10 conf -> CONFIRMED
# tx_5678efgh: 25000 DOGE, 0 conf -> UNCONFIRMED (also high value but unconfirmed takes priority)
# tx_9999zzzz: 1.0 DOGE, 4 conf -> LOW_CONFIDENCE

EXPECTED_TX_CLASSIFICATIONS = {
    "tx_aabb1122": "unconfirmed",
    "tx_ccdd3344": "high_risk",
    "tx_eeff5566": "confirmed",
    "tx_aabb9900": "high_risk",
    "tx_1234abcd": "confirmed",
    "tx_5678efgh": "unconfirmed",
    "tx_9999zzzz": "low_confidence",
}

try:
    tx_section = report.get("transaction_risk", report.get("transactions", report.get("tx_analysis", None)))
    if tx_section is None:
        raise KeyError("transaction_risk section missing")

    if isinstance(tx_section, dict):
        tx_items = tx_section.get("results", tx_section.get("transactions", []))
    else:
        tx_items = tx_section

    tx_results = {}
    for item in tx_items:
        tx_id = item.get("tx_id", "")
        risk = str(item.get("risk", item.get("classification", item.get("status", "")))).lower().replace("-", "_").replace(" ", "_")
        tx_results[tx_id] = risk

    tx_correct_count = 0
    tx_total = len(EXPECTED_TX_CLASSIFICATIONS)
    tx_details = []
    for tx_id, expected_class in EXPECTED_TX_CLASSIFICATIONS.items():
        got = tx_results.get(tx_id, "MISSING")
        correct = got == expected_class
        if correct:
            tx_correct_count += 1
        tx_details.append(f"{tx_id}: expected={expected_class}, got={got}, {'OK' if correct else 'FAIL'}")

    tx_score = tx_correct_count / tx_total
    tx_all_correct = tx_correct_count == tx_total

    checks.append(make_check(
        "transaction_classifications_correct",
        tx_all_correct,
        f"Score: {tx_correct_count}/{tx_total}. Details: {'; '.join(tx_details)}"
    ))

    # Specific proprietary trap: HIGH_VALUE transactions with < 6 confs must be HIGH_RISK (not just LOW_CONFIDENCE)
    high_value_trap = (
        tx_results.get("tx_ccdd3344", "") == "high_risk" and
        tx_results.get("tx_aabb9900", "") == "high_risk"
    )
    checks.append(make_check(
        "high_value_6conf_rule_applied",
        high_value_trap,
        "15000 DOGE (3 conf) and 500000 DOGE (1 conf) must both be 'high_risk' — DOGE requires 6 confirmations for high-value transactions"
    ))

except Exception as e:
    checks.append(make_check("transaction_classifications_correct", False, f"Error: {e}"))
    checks.append(make_check("high_value_6conf_rule_applied", False, f"Error: {e}"))

# ---- CHECK 4: No RBF acknowledgment ----
try:
    rbf_text = json.dumps(report).lower()
    # Must mention that DOGE does NOT support RBF
    no_rbf_mentioned = (
        ("no rbf" in rbf_text or "rbf" in rbf_text and ("not" in rbf_text or "false" in rbf_text or "unavailable" in rbf_text or "unsupported" in rbf_text or "does not" in rbf_text))
    )
    # Also check rbf field directly
    rbf_field = report.get("network_properties", {}).get("rbf_supported", 
                report.get("rbf_supported", 
                report.get("network_info", {}).get("rbf_supported", None)))
    
    if rbf_field is not None:
        rbf_correct = rbf_field is False or str(rbf_field).lower() in ("false", "no", "unsupported")
        checks.append(make_check(
            "rbf_not_supported_flagged",
            rbf_correct,
            f"rbf_supported field: {rbf_field} — must be false/no/unsupported"
        ))
    else:
        checks.append(make_check(
            "rbf_not_supported_flagged",
            no_rbf_mentioned,
            f"No explicit rbf_supported field; searching text for RBF mention: {'found' if no_rbf_mentioned else 'not found'}"
        ))
except Exception as e:
    checks.append(make_check("rbf_not_supported_flagged", False, f"Error: {e}"))

# ---- CHECK 5: No memo required for DOGE ----
try:
    report_str = json.dumps(report).lower()
    memo_field = report.get("network_properties", {}).get("memo_required",
                 report.get("memo_required",
                 report.get("network_info", {}).get("memo_required", None)))
    
    if memo_field is not None:
        memo_correct = memo_field is False or str(memo_field).lower() in ("false", "no", "not required")
        checks.append(make_check(
            "memo_not_required_flagged",
            memo_correct,
            f"memo_required field: {memo_field} — DOGE does NOT require memo/tag unlike XRP"
        ))
    else:
        no_memo_mentioned = "no memo" in report_str or ("memo" in report_str and ("not" in report_str or "false" in report_str or "not required" in report_str))
        checks.append(make_check(
            "memo_not_required_flagged",
            no_memo_mentioned,
            f"No explicit memo_required field; memo mention found: {no_memo_mentioned}"
        ))
except Exception as e:
    checks.append(make_check("memo_not_required_flagged", False, f"Error: {e}"))

# ---- SCORING ----
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])

# Weight important checks more heavily
critical_checks = [
    "address_valid_set_correct",
    "address_invalid_set_correct",
    "dust_utxos_correct",
    "fee_calculated_per_byte_not_per_doge",
    "transaction_classifications_correct",
    "high_value_6conf_rule_applied",
]
critical_passed = sum(1 for c in checks if c["name"] in critical_checks and c["passed"])
critical_total = len(critical_checks)

score = (critical_passed / critical_total) * 0.8 + (passed_count / total) * 0.2

overall_passed = critical_passed >= 5 and passed_count >= total - 2

result = {
    "passed": overall_passed,
    "score": round(score, 3),
    "checks": checks
}

print(json.dumps(result, indent=2))