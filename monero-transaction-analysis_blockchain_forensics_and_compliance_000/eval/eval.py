import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # --- Find forensic_report.json ---
    report_files = list(workspace.rglob("forensic_report.json"))

    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "forensic_report.json not found anywhere in workspace"}]
        }

    report_path = report_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})

    # --- Load JSON ---
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "json_valid", "passed": False, "detail": f"Failed to parse JSON: {e}"}]
        }
    checks.append({"name": "json_valid", "passed": True, "detail": "JSON parses correctly"})

    # --- Expected values per txid ---
    expected = {
        "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2": {
            "ring_size": 7,
            "mixin_count": 6,
            "input_count": 2,
            "privacy_score_numerator": 4,
            "privacy_adequate": False,   # ring_size < 11 => NOT adequate per skill
            "fee": "0.000123450000",
        },
        "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1": {
            "ring_size": 11,
            "mixin_count": 10,
            "input_count": 1,
            "privacy_score_numerator": 7,
            "privacy_adequate": True,    # ring_size == 11 => adequate
            "fee": "0.000087230000",
        },
        "9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7": {
            "ring_size": 16,
            "mixin_count": 15,
            "input_count": 4,
            "privacy_score_numerator": 9,
            "privacy_adequate": True,    # ring_size > 11 => adequate
            "fee": "0.000210000000",
        },
    }

    # --- Locate transactions in report ---
    # Support both list-of-dicts and dict-keyed formats
    transactions_list = None
    if isinstance(report, list):
        transactions_list = report
    elif isinstance(report, dict):
        # Could be {"transactions": [...]} or {"case_id": ..., "transactions": [...]}
        if "transactions" in report:
            val = report["transactions"]
            if isinstance(val, list):
                transactions_list = val
            elif isinstance(val, dict):
                transactions_list = list(val.values())
        else:
            # Maybe the top level IS the dict keyed by txid
            # Check if top-level keys look like txids
            potential_txids = [k for k in report.keys() if len(k) >= 32]
            if potential_txids:
                transactions_list = [{"txid": k, **v} if isinstance(v, dict) else {"txid": k} for k, v in report.items()]
            else:
                transactions_list = []

    if transactions_list is None or len(transactions_list) == 0:
        checks.append({"name": "transactions_present", "passed": False, "detail": "No transactions array found in report"})
        return {"passed": False, "score": 0.05, "checks": checks}

    checks.append({
        "name": "transactions_present",
        "passed": len(transactions_list) >= 3,
        "detail": f"Found {len(transactions_list)} transaction entries (expected 3)"
    })

    # Build txid -> entry lookup
    def find_entry_by_txid(tx_list, txid):
        for entry in tx_list:
            if isinstance(entry, dict):
                # Check various possible txid field names
                for field in ["txid", "transaction_id", "tx_id", "id", "hash"]:
                    val = entry.get(field, "")
                    if val and txid in str(val):
                        return entry
        return None

    # Also try top-level dict keyed by txid
    def find_entry(report_obj, tx_list, txid):
        # Try list first
        entry = find_entry_by_txid(tx_list, txid)
        if entry:
            return entry
        # Try dict keyed by txid
        if isinstance(report_obj, dict):
            for k, v in report_obj.items():
                if txid in k and isinstance(v, dict):
                    v["txid"] = k
                    return v
        return None

    found_entries = {}
    for txid in expected:
        entry = find_entry(report, transactions_list, txid)
        found_entries[txid] = entry

    # Check: all 3 txids present
    all_found = all(v is not None for v in found_entries.values())
    checks.append({
        "name": "all_txids_present",
        "passed": all_found,
        "detail": f"Found entries for: {[txid[:16]+'...' for txid, v in found_entries.items() if v is not None]}"
    })

    # --- Per-transaction detailed checks ---
    score_weights = {
        "ring_size": 0.10,
        "mixin_count": 0.08,
        "input_count": 0.07,
        "privacy_score": 0.10,
        "privacy_adequate": 0.15,   # Most important - tests knowledge of 11+ threshold
    }

    # Normalize all weights over 3 txids
    per_tx_max = sum(score_weights.values())  # 0.50 per tx, 3 txids = 1.5 -- rescale below

    def extract_numeric(val):
        """Extract numeric value from various formats."""
        if val is None:
            return None
        if isinstance(val, (int, float)):
            return val
        s = str(val)
        # Handle "4/10" format
        m = re.match(r'^(\d+)\s*/\s*10', s)
        if m:
            return int(m.group(1))
        m = re.match(r'^(\d+)', s)
        if m:
            return int(m.group(1))
        return None

    tx_check_results = []

    for txid, exp in expected.items():
        entry = found_entries.get(txid)
        tx_label = txid[:16] + "..."

        if entry is None:
            tx_check_results.append({
                "name": f"tx_{tx_label}_found",
                "passed": False,
                "detail": f"No entry found for txid {tx_label}"
            })
            continue

        # ring_size check
        ring_val = entry.get("ring_size") or entry.get("ringSize") or entry.get("ring size")
        ring_num = extract_numeric(ring_val)
        ring_ok = (ring_num == exp["ring_size"])
        tx_check_results.append({
            "name": f"tx_{tx_label}_ring_size",
            "passed": ring_ok,
            "detail": f"Expected ring_size={exp['ring_size']}, got {ring_val} (parsed: {ring_num})"
        })

        # mixin_count check
        mixin_val = (entry.get("mixin_count") or entry.get("mixin count") or
                     entry.get("mixinCount") or entry.get("mixin"))
        mixin_num = extract_numeric(mixin_val)
        mixin_ok = (mixin_num == exp["mixin_count"])
        tx_check_results.append({
            "name": f"tx_{tx_label}_mixin_count",
            "passed": mixin_ok,
            "detail": f"Expected mixin_count={exp['mixin_count']}, got {mixin_val} (parsed: {mixin_num})"
        })

        # input_count check
        input_val = (entry.get("input_count") or entry.get("input count") or
                     entry.get("inputCount") or entry.get("inputs"))
        input_num = extract_numeric(input_val)
        input_ok = (input_num == exp["input_count"])
        tx_check_results.append({
            "name": f"tx_{tx_label}_input_count",
            "passed": input_ok,
            "detail": f"Expected input_count={exp['input_count']}, got {input_val} (parsed: {input_num})"
        })

        # privacy_score check - must match numerator from "X/10" format
        ps_val = (entry.get("privacy_score") or entry.get("privacyScore") or
                  entry.get("privacy score"))
        ps_num = extract_numeric(ps_val)
        ps_ok = (ps_num == exp["privacy_score_numerator"])
        tx_check_results.append({
            "name": f"tx_{tx_label}_privacy_score",
            "passed": ps_ok,
            "detail": f"Expected privacy_score={exp['privacy_score_numerator']}/10, got {ps_val} (parsed: {ps_num})"
        })

        # privacy_adequate check - THE KEY PROPRIETARY TRAP (ring_size >= 11)
        pa_val = (entry.get("privacy_adequate") or entry.get("privacyAdequate") or
                  entry.get("privacy_adequate") or entry.get("adequate") or
                  entry.get("meets_standard") or entry.get("meets_minimum"))
        if pa_val is None:
            # Try to infer from other fields like "flag", "warning", "status"
            status_val = entry.get("status", "")
            if isinstance(status_val, str):
                if "inadequate" in status_val.lower() or "fail" in status_val.lower() or "warn" in status_val.lower():
                    pa_val = False
                elif "adequate" in status_val.lower() or "pass" in status_val.lower() or "ok" in status_val.lower():
                    pa_val = True

        if isinstance(pa_val, str):
            pa_val = pa_val.lower() in ("true", "yes", "1", "adequate", "pass", "ok")

        pa_ok = (pa_val == exp["privacy_adequate"])
        tx_check_results.append({
            "name": f"tx_{tx_label}_privacy_adequate",
            "passed": pa_ok,
            "detail": (
                f"Expected privacy_adequate={exp['privacy_adequate']} "
                f"(ring_size={exp['ring_size']}, threshold=11+), "
                f"got {pa_val}"
            )
        })

    checks.extend(tx_check_results)

    # --- CRITICAL: Verify the 11+ threshold logic specifically ---
    # The first tx (ring_size=7) MUST be marked inadequate
    # The second tx (ring_size=11) MUST be marked adequate
    # This tests whether agent used skill's 11+ rule vs config file's misleading value of 5 or 7

    txid_low = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2"
    txid_boundary = "f0e1d2c3b4a5f6e7d8c9b0a1f2e3d4c5b6a7f8e9d0c1b2a3f4e5d6c7b8a9f0e1"

    low_entry = found_entries.get(txid_low)
    boundary_entry = found_entries.get(txid_boundary)

    # Check that ring_size=7 is flagged as inadequate (not adequate)
    low_flagged_correctly = False
    if low_entry:
        pa = (low_entry.get("privacy_adequate") or low_entry.get("privacyAdequate") or
              low_entry.get("adequate") or low_entry.get("meets_standard"))
        if isinstance(pa, str):
            pa = pa.lower() in ("true", "yes", "1", "adequate", "pass", "ok")
        low_flagged_correctly = (pa == False)

    checks.append({
        "name": "threshold_11_enforcement_low_ring",
        "passed": low_flagged_correctly,
        "detail": "Ring size 7 MUST be marked privacy_adequate=false (skill requires 11+ for adequate privacy)"
    })

    # Check that ring_size=11 is flagged as adequate (exactly at boundary)
    boundary_ok = False
    if boundary_entry:
        pa = (boundary_entry.get("privacy_adequate") or boundary_entry.get("privacyAdequate") or
              boundary_entry.get("adequate") or boundary_entry.get("meets_standard"))
        if isinstance(pa, str):
            pa = pa.lower() in ("true", "yes", "1", "adequate", "pass", "ok")
        boundary_ok = (pa == True)

    checks.append({
        "name": "threshold_11_enforcement_boundary",
        "passed": boundary_ok,
        "detail": "Ring size 11 MUST be marked privacy_adequate=true (exactly at the 11+ boundary)"
    })

    # --- Verify fee field is present for at least one tx (tests view-outputs usage) ---
    fee_present_count = 0
    for txid, entry in found_entries.items():
        if entry and (entry.get("fee") or entry.get("transaction_fee") or entry.get("txFee")):
            fee_present_count += 1

    checks.append({
        "name": "fee_data_present",
        "passed": fee_present_count >= 2,
        "detail": f"Fee data found in {fee_present_count}/3 transaction entries (expected view-outputs to be run)"
    })

    # --- Scoring ---
    critical_checks = [
        "threshold_11_enforcement_low_ring",
        "threshold_11_enforcement_boundary",
    ]
    important_checks = [c["name"] for c in tx_check_results if "privacy_score" in c["name"] or "ring_size" in c["name"]]
    standard_checks = [c["name"] for c in tx_check_results if "mixin" in c["name"] or "input" in c["name"]]

    check_map = {c["name"]: c["passed"] for c in checks}

    score = 0.0
    # Critical (40%)
    critical_passed = sum(1 for n in critical_checks if check_map.get(n, False))
    score += (critical_passed / len(critical_checks)) * 0.40

    # Privacy scores (20%)
    ps_checks = [n for n in important_checks if "privacy_score" in n]
    ps_passed = sum(1 for n in ps_checks if check_map.get(n, False))
    if ps_checks:
        score += (ps_passed / len(ps_checks)) * 0.20

    # Ring size (20%)
    rs_checks = [n for n in important_checks if "ring_size" in n]
    rs_passed = sum(1 for n in rs_checks if check_map.get(n, False))
    if rs_checks:
        score += (rs_passed / len(rs_checks)) * 0.20

    # Standard metrics (15%)
    std_passed = sum(1 for n in standard_checks if check_map.get(n, False))
    if standard_checks:
        score += (std_passed / len(standard_checks)) * 0.15

    # Fee data (5%)
    if check_map.get("fee_data_present", False):
        score += 0.05

    score = round(min(score, 1.0), 3)

    # Overall pass: must get both critical checks AND at least 5 of the per-tx checks
    per_tx_passed = sum(1 for c in tx_check_results if c["passed"])
    overall_passed = (
        check_map.get("threshold_11_enforcement_low_ring", False) and
        check_map.get("threshold_11_enforcement_boundary", False) and
        per_tx_passed >= 5 and
        check_map.get("all_txids_present", False)
    )

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "invocation", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = evaluate(sys.argv[1])
    print(json.dumps(result, indent=2))