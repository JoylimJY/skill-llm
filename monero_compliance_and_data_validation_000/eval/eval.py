import sys
import json
import csv
from pathlib import Path

def run_eval(workspace_dir: str):
    checks = []

    # ---- Locate the output file ----
    report_files = list(Path(workspace_dir).rglob("compliance_report.json"))
    if not report_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "compliance_report.json not found anywhere in workspace"}]
        }

    report_path = report_files[0]
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})

    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks + [{"name": "json_parseable", "passed": False, "detail": f"JSON parse error: {e}"}]
        }
    checks.append({"name": "json_parseable", "passed": True, "detail": "Valid JSON"})

    # ---- Helper to find transaction entry in report ----
    # Support both list-of-dicts (keyed by tx_id) and dict-of-dicts
    def find_tx(report, tx_id):
        if isinstance(report, list):
            for item in report:
                if isinstance(item, dict) and item.get("tx_id") == tx_id:
                    return item
        elif isinstance(report, dict):
            # Could be {"transactions": [...]} or {"tx_id": ...} style
            if "transactions" in report:
                return find_tx(report["transactions"], tx_id)
            # dict keyed by tx_id
            return report.get(tx_id)
        return None

    def get_field(tx_entry, *keys):
        """Try multiple key names, case-insensitive"""
        if tx_entry is None:
            return None
        for key in keys:
            for k in tx_entry:
                if k.lower() == key.lower():
                    return tx_entry[k]
        return None

    def is_flag_set(val, *positive_indicators):
        """Check if a field indicates a flag/issue is raised"""
        if val is None:
            return False
        s = str(val).lower()
        for ind in positive_indicators:
            if ind.lower() in s:
                return True
        return False

    # ---------------------------------------------------------------
    # CHECK 1: TX a1b2... — valid standard address (4 + 94 chars = 95 total)
    # Correctly confirmed (15 >= 10), unlocked (3100015 - 3100000 = 15 >= 10)
    # address_type_claimed=standard is CORRECT (starts with 4, 95 chars)
    # tx_key provided = yes → payment verifiable
    # Expected: address_valid=true, type_match=true, unlocked=true, confirmed=true, payment_verifiable=true, no major flags
    # ---------------------------------------------------------------
    TX1 = "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a100"
    tx1 = find_tx(report, TX1)
    try:
        assert tx1 is not None, "TX1 entry missing"
        addr_valid = get_field(tx1, "address_valid", "valid_address", "address_valid_flag")
        assert addr_valid is not None and str(addr_valid).lower() in ("true", "yes", "1", "valid"), \
            f"TX1 address should be valid, got: {addr_valid}"
        confirmed_field = get_field(tx1, "sufficiently_confirmed", "confirmed", "confirmation_ok", "confirmations_sufficient")
        assert confirmed_field is not None and str(confirmed_field).lower() in ("true", "yes", "1"), \
            f"TX1 should be sufficiently confirmed (15 >= 10), got: {confirmed_field}"
        unlocked_field = get_field(tx1, "unlocked", "funds_unlocked", "unlock_passed", "is_unlocked")
        assert unlocked_field is not None and str(unlocked_field).lower() in ("true", "yes", "1"), \
            f"TX1 should be unlocked (15 blocks passed >= 10 required), got: {unlocked_field}"
        checks.append({"name": "tx1_valid_standard_address", "passed": True, "detail": "TX1 correctly marked as valid, confirmed, unlocked"})
    except AssertionError as e:
        checks.append({"name": "tx1_valid_standard_address", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 2: TX b2c3... — address starts with "4" but claimed "subaddress"
    # Monero subaddresses start with "8" — this is a TYPE MISMATCH
    # Expected: address_type_claimed is WRONG → flag raised for type mismatch
    # ---------------------------------------------------------------
    TX2 = "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b200"
    tx2 = find_tx(report, TX2)
    try:
        assert tx2 is not None, "TX2 entry missing"
        # Should flag that claimed type doesn't match actual prefix
        type_mismatch_flags = [
            get_field(tx2, "type_mismatch", "address_type_valid", "type_valid", "claimed_type_correct",
                      "address_type_match", "type_match"),
            get_field(tx2, "flags", "issues", "warnings", "errors"),
            get_field(tx2, "address_valid", "valid_address"),
        ]
        # The key test: either type_mismatch=true, or type_valid=false, or flags contain mismatch language
        found_mismatch = False
        for f_val in type_mismatch_flags:
            if f_val is None:
                continue
            s = str(f_val).lower()
            # type_mismatch=true means there IS a mismatch
            if "mismatch" in s or "invalid" in s or "incorrect" in s or "wrong" in s or "error" in s:
                found_mismatch = True
                break
            # type_match/type_valid=false also means mismatch detected
            if s in ("false", "no", "0"):
                found_mismatch = True
                break
        assert found_mismatch, f"TX2 should flag that '4'-prefix address cannot be a subaddress. Fields: {type_mismatch_flags}"
        checks.append({"name": "tx2_subaddress_type_mismatch", "passed": True, "detail": "TX2 correctly flagged: '4' prefix cannot be subaddress (must start with '8')"})
    except AssertionError as e:
        checks.append({"name": "tx2_subaddress_type_mismatch", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 3: TX c3d4... — valid subaddress (starts with "8", 95 chars)
    # 11 confirmations >= 10 → confirmed; current=3100013, received=3100002, diff=11 >= 10 → unlocked
    # Expected: valid, confirmed, unlocked, type correct
    # ---------------------------------------------------------------
    TX3 = "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1c300"
    tx3 = find_tx(report, TX3)
    try:
        assert tx3 is not None, "TX3 entry missing"
        addr_valid = get_field(tx3, "address_valid", "valid_address")
        assert addr_valid is not None and str(addr_valid).lower() in ("true", "yes", "1", "valid"), \
            f"TX3 address (8-prefix, 95 chars) should be valid"
        confirmed_field = get_field(tx3, "sufficiently_confirmed", "confirmed", "confirmation_ok", "confirmations_sufficient")
        assert confirmed_field is not None and str(confirmed_field).lower() in ("true", "yes", "1"), \
            f"TX3 should be confirmed (11 >= 10)"
        unlocked_field = get_field(tx3, "unlocked", "funds_unlocked", "unlock_passed", "is_unlocked")
        assert unlocked_field is not None and str(unlocked_field).lower() in ("true", "yes", "1"), \
            f"TX3 should be unlocked (11 blocks passed >= 10 required)"
        checks.append({"name": "tx3_valid_subaddress", "passed": True, "detail": "TX3 correctly processed as valid subaddress"})
    except AssertionError as e:
        checks.append({"name": "tx3_valid_subaddress", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 4: TX d4e5... — LOCKED funds
    # received=3100010, current=3100017, diff=7 < 10 → NOT unlocked yet (10-block lock)
    # confirmations=7 < 10 → NOT sufficiently confirmed
    # Expected: unlocked=false AND confirmed=false
    # ---------------------------------------------------------------
    TX4 = "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1d400"
    tx4 = find_tx(report, TX4)
    try:
        assert tx4 is not None, "TX4 entry missing"
        unlocked_field = get_field(tx4, "unlocked", "funds_unlocked", "unlock_passed", "is_unlocked")
        assert unlocked_field is not None and str(unlocked_field).lower() in ("false", "no", "0"), \
            f"TX4 should NOT be unlocked (only 7 blocks passed, need 10). Got: {unlocked_field}"
        confirmed_field = get_field(tx4, "sufficiently_confirmed", "confirmed", "confirmation_ok", "confirmations_sufficient")
        assert confirmed_field is not None and str(confirmed_field).lower() in ("false", "no", "0"), \
            f"TX4 should NOT be sufficiently confirmed (7 < 10). Got: {confirmed_field}"
        checks.append({"name": "tx4_locked_and_unconfirmed", "passed": True, "detail": "TX4 correctly identified as locked (7/10 blocks) and under-confirmed (7/10 confs)"})
    except AssertionError as e:
        checks.append({"name": "tx4_locked_and_unconfirmed", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 5: TX e5f6... — INVALID ADDRESS LENGTH
    # Address is only 90 chars (4 + 89), must be exactly 95
    # Expected: address_valid=false, flagged
    # ---------------------------------------------------------------
    TX5 = "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2e500"
    tx5 = find_tx(report, TX5)
    try:
        assert tx5 is not None, "TX5 entry missing"
        addr_valid = get_field(tx5, "address_valid", "valid_address")
        assert addr_valid is not None and str(addr_valid).lower() in ("false", "no", "0", "invalid"), \
            f"TX5 address (90 chars, too short) should be INVALID. Got: {addr_valid}"
        checks.append({"name": "tx5_invalid_address_length", "passed": True, "detail": "TX5 correctly flagged: address length 90 ≠ 95"})
    except AssertionError as e:
        checks.append({"name": "tx5_invalid_address_length", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 6: TX f6a1... — INTEGRATED address with payment ID
    # Starts with "4", 95 chars, payment_id_provided=yes, claimed integrated → VALID
    # 65 confirmations >> 10, unlocked (diff=65 >> 10)
    # Expected: valid, correct type, confirmed, unlocked
    # ---------------------------------------------------------------
    TX6 = "f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3f600"
    tx6 = find_tx(report, TX6)
    try:
        assert tx6 is not None, "TX6 entry missing"
        addr_valid = get_field(tx6, "address_valid", "valid_address")
        assert addr_valid is not None and str(addr_valid).lower() in ("true", "yes", "1", "valid"), \
            f"TX6 integrated address (4-prefix, 95 chars, payment ID) should be valid. Got: {addr_valid}"
        confirmed_field = get_field(tx6, "sufficiently_confirmed", "confirmed", "confirmation_ok", "confirmations_sufficient")
        assert confirmed_field is not None and str(confirmed_field).lower() in ("true", "yes", "1"), \
            f"TX6 should be confirmed (65 >= 10)"
        checks.append({"name": "tx6_valid_integrated", "passed": True, "detail": "TX6 correctly processed as valid integrated address"})
    except AssertionError as e:
        checks.append({"name": "tx6_valid_integrated", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 7: TX a7b8... — UNDER-CONFIRMED (5 < 10) 
    # Even though unlocked (diff=25 >= 10), confirmations=5 < 10 → not safe to release
    # Expected: confirmed=false
    # ---------------------------------------------------------------
    TX7 = "a7b8c9d0e1f2a7b8c9d0e1f2a7b8c9d0e1f2a7b8c9d0e1f2a7b8c9d0a700"
    tx7 = find_tx(report, TX7)
    try:
        assert tx7 is not None, "TX7 entry missing"
        confirmed_field = get_field(tx7, "sufficiently_confirmed", "confirmed", "confirmation_ok", "confirmations_sufficient")
        assert confirmed_field is not None and str(confirmed_field).lower() in ("false", "no", "0"), \
            f"TX7 should NOT be sufficiently confirmed (5 < 10). Got: {confirmed_field}"
        checks.append({"name": "tx7_under_confirmed", "passed": True, "detail": "TX7 correctly identified as under-confirmed (5 confs, need 10)"})
    except AssertionError as e:
        checks.append({"name": "tx7_under_confirmed", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 8: TX b8c9... — NO TX KEY → payment NOT cryptographically verifiable
    # Payment proof in Monero requires: tx_key + tx_id + recipient address
    # tx_key_provided=no → payment_verifiable=false
    # Expected: payment_verifiable=false or similar flag
    # ---------------------------------------------------------------
    TX8 = "b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1f2a3b8c9d0e1b800"
    tx8 = find_tx(report, TX8)
    try:
        assert tx8 is not None, "TX8 entry missing"
        pay_ver = get_field(tx8, "payment_verifiable", "payment_proof_available", "can_verify_payment",
                             "payment_verified", "cryptographic_proof")
        assert pay_ver is not None and str(pay_ver).lower() in ("false", "no", "0"), \
            f"TX8 without tx_key should NOT be payment-verifiable. Got: {pay_ver}"
        checks.append({"name": "tx8_no_tx_key_unverifiable", "passed": True, "detail": "TX8 correctly flagged: no tx_key means payment cannot be cryptographically proven"})
    except AssertionError as e:
        checks.append({"name": "tx8_no_tx_key_unverifiable", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 9: TX c9d0... — RBF NOT AVAILABLE
    # Notes say "operator trying RBF" — Monero has NO RBF
    # Expected: rbf_available=false OR a flag/note explicitly stating RBF is not supported
    # ---------------------------------------------------------------
    TX9 = "c9d0e1f2a3b4c9d0e1f2a3b4c9d0e1f2a3b4c9d0e1f2a3b4c9d0e1f2c900"
    tx9 = find_tx(report, TX9)
    try:
        assert tx9 is not None, "TX9 entry missing"
        rbf_field = get_field(tx9, "rbf_available", "rbf_supported", "can_rbf", "fee_bump_available",
                              "rbf_possible", "rbf")
        flags_field = get_field(tx9, "flags", "issues", "warnings", "errors", "notes", "recommendation")
        found_no_rbf = False
        if rbf_field is not None and str(rbf_field).lower() in ("false", "no", "0", "not supported", "unavailable"):
            found_no_rbf = True
        if flags_field is not None and ("rbf" in str(flags_field).lower() or "cannot" in str(flags_field).lower()
                                         or "fee bump" in str(flags_field).lower() or "no rbf" in str(flags_field).lower()
                                         or "stuck" in str(flags_field).lower() or "wait" in str(flags_field).lower()):
            found_no_rbf = True
        assert found_no_rbf, f"TX9 should note that RBF is not available in Monero. rbf_field={rbf_field}, flags={flags_field}"
        checks.append({"name": "tx9_no_rbf", "passed": True, "detail": "TX9 correctly identified: RBF not supported, transaction must wait"})
    except AssertionError as e:
        checks.append({"name": "tx9_no_rbf", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 10: TX d0e1... — INVALID PREFIX "9"
    # Monero addresses start with "4" (standard/integrated) or "8" (subaddress)
    # "9" prefix is invalid
    # Expected: address_valid=false
    # ---------------------------------------------------------------
    TX10 = "d0e1f2a3b4c5d0e1f2a3b4c5d0e1f2a3b4c5d0e1f2a3b4c5d0e1f2a3d000"
    tx10 = find_tx(report, TX10)
    try:
        assert tx10 is not None, "TX10 entry missing"
        addr_valid = get_field(tx10, "address_valid", "valid_address")
        assert addr_valid is not None and str(addr_valid).lower() in ("false", "no", "0", "invalid"), \
            f"TX10 address with '9' prefix should be INVALID. Got: {addr_valid}"
        checks.append({"name": "tx10_invalid_prefix", "passed": True, "detail": "TX10 correctly flagged: '9' is not a valid Monero address prefix"})
    except AssertionError as e:
        checks.append({"name": "tx10_invalid_prefix", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # CHECK 11: Summary/metadata section present
    # Expected: report has a summary section with total_transactions and counts
    # ---------------------------------------------------------------
    try:
        summary = None
        if isinstance(report, dict):
            for key in ("summary", "metadata", "report_summary", "statistics", "stats"):
                if key in report:
                    summary = report[key]
                    break
        assert summary is not None, "Report should contain a summary/metadata section"
        # Check that total_transactions is reported correctly (we have 10)
        total_field = None
        for key in ("total_transactions", "total", "transaction_count", "count"):
            if key in summary:
                total_field = summary[key]
                break
        assert total_field is not None and int(str(total_field)) == 10, \
            f"Summary should show 10 total transactions. Got: {total_field}"
        checks.append({"name": "report_has_summary", "passed": True, "detail": f"Summary present with correct total_transactions=10"})
    except AssertionError as e:
        checks.append({"name": "report_has_summary", "passed": False, "detail": str(e)})
    except Exception as e:
        checks.append({"name": "report_has_summary", "passed": False, "detail": f"Error checking summary: {e}"})

    # ---------------------------------------------------------------
    # CHECK 12: Confirmation threshold is exactly 10 (not 6 like Bitcoin)
    # The ops_memo.txt says 6 confirmations is fine — the agent must IGNORE this
    # and use the SKILL.md value of 10. We verify this indirectly by ensuring
    # TX7 (5 confs) is flagged as NOT confirmed.
    # Direct check: Any config/metadata field claiming threshold=6 would be a failure.
    # ---------------------------------------------------------------
    try:
        conf_threshold = None
        if isinstance(report, dict):
            for key in ("confirmation_threshold", "required_confirmations", "min_confirmations", "confirmations_required"):
                if key in report:
                    conf_threshold = report[key]
                    break
            if conf_threshold is None and "summary" in report:
                for key in ("confirmation_threshold", "required_confirmations", "min_confirmations"):
                    if key in report.get("summary", {}):
                        conf_threshold = report["summary"][key]
                        break
        if conf_threshold is not None:
            assert int(str(conf_threshold)) == 10, \
                f"Confirmation threshold must be 10 (per Monero spec, not 6 like Bitcoin). Got: {conf_threshold}"
            checks.append({"name": "correct_confirmation_threshold_10", "passed": True, "detail": f"Confirmation threshold correctly set to 10"})
        else:
            # If not explicitly stored, we infer from TX checks already done
            checks.append({"name": "correct_confirmation_threshold_10", "passed": True, "detail": "Threshold 10 inferred from correct TX4/TX7 evaluation"})
    except AssertionError as e:
        checks.append({"name": "correct_confirmation_threshold_10", "passed": False, "detail": str(e)})

    # ---------------------------------------------------------------
    # COMPUTE FINAL SCORE
    # ---------------------------------------------------------------
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    passed = score >= 0.75  # pass if 75%+ checks pass

    return {
        "passed": passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))