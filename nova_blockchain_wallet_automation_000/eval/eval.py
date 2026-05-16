#!/usr/bin/env python3
"""
Evaluation script for the nova wallet testnet audit task.
Usage: python3 eval_script.py <workspace_dir>
"""
import sys
import json
import os
from pathlib import Path

def load_report(workspace):
    """Search for audit_report.json anywhere in the workspace."""
    candidates = list(Path(workspace).rglob("audit_report.json"))
    if not candidates:
        return None, "audit_report.json not found anywhere in workspace"
    # Pick the most recently modified if multiple
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    try:
        with open(candidates[0]) as f:
            data = json.load(f)
        return data, str(candidates[0])
    except Exception as e:
        return None, f"Failed to parse JSON: {e}"

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Load the report ───────────────────────────────────────────────────────
    report, report_path = load_report(workspace)

    if report is None:
        checks.append({
            "name": "report_exists",
            "passed": False,
            "detail": report_path
        })
        result = {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }
        print(json.dumps(result, indent=2))
        return

    checks.append({
        "name": "report_exists",
        "passed": True,
        "detail": f"Found at {report_path}"
    })

    # ── CHECK 1: Network verification present ─────────────────────────────────
    # The report must capture that the network is "testnet"
    network_ok = False
    network_detail = "No 'network' field found in report"
    try:
        # Accept network at top level or nested
        def find_network(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() == 'network':
                        if isinstance(v, str) and 'testnet' in v.lower():
                            return True
                    result = find_network(v)
                    if result:
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if find_network(item):
                        return True
            return False

        if find_network(report):
            network_ok = True
            network_detail = "Report correctly identifies network as testnet"
        else:
            network_detail = f"'testnet' not found as network value in report. Report keys: {list(report.keys()) if isinstance(report, dict) else 'not a dict'}"
    except Exception as e:
        network_detail = f"Error checking network: {e}"

    checks.append({
        "name": "network_is_testnet",
        "passed": network_ok,
        "detail": network_detail
    })

    # ── CHECK 2: Balance is captured ──────────────────────────────────────────
    balance_ok = False
    balance_detail = "No balance field found in report"
    try:
        def find_balance(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() in ('balance', 'balance_usd', 'amount', 'wallet_balance'):
                        # The mock returns "312.47"
                        if isinstance(v, (str, float, int)):
                            val = str(v)
                            if '312' in val:
                                return True, f"Balance found: {v}"
                    sub_ok, sub_detail = find_balance(v)
                    if sub_ok:
                        return sub_ok, sub_detail
            elif isinstance(obj, list):
                for item in obj:
                    sub_ok, sub_detail = find_balance(item)
                    if sub_ok:
                        return sub_ok, sub_detail
            return False, ""

        bal_ok, bal_msg = find_balance(report)
        if bal_ok:
            balance_ok = True
            balance_detail = bal_msg
        else:
            balance_detail = f"Balance value '312.47' not found in report structure"
    except Exception as e:
        balance_detail = f"Error checking balance: {e}"

    checks.append({
        "name": "balance_captured",
        "passed": balance_ok,
        "detail": balance_detail
    })

    # ── CHECK 3: Correct stablecoin used (USDT for testnet/sui) ─────────────
    # CRITICAL PROPRIETARY TRAP: testnet sui -> USDT (NOT USDC)
    stablecoin_ok = False
    stablecoin_detail = "Stablecoin field not found or incorrect"
    wrong_stablecoin_detail = ""
    try:
        report_str = json.dumps(report).upper()

        # Check for USDT presence related to sui withdrawal
        has_usdt = 'USDT' in report_str
        has_usdc_wrong = False

        # More nuanced: look for stablecoin field in withdrawal section
        def find_withdrawal_stablecoin(obj):
            """Returns (stablecoin_value, found)"""
            if isinstance(obj, dict):
                # Look for a withdrawal-related section
                for k, v in obj.items():
                    if any(kw in k.lower() for kw in ('withdraw', 'dry_run', 'dryrun', 'withdrawal', 'transaction')):
                        if isinstance(v, dict):
                            for sk, sv in v.items():
                                if 'stablecoin' in sk.lower() or 'coin' in sk.lower() or 'token' in sk.lower() or 'currency' in sk.lower():
                                    return str(sv), True
                    # recurse
                    val, found = find_withdrawal_stablecoin(v)
                    if found:
                        return val, found
            elif isinstance(obj, list):
                for item in obj:
                    val, found = find_withdrawal_stablecoin(item)
                    if found:
                        return val, found
            return "", False

        coin_val, coin_found = find_withdrawal_stablecoin(report)

        if coin_found:
            if 'USDT' in coin_val.upper():
                stablecoin_ok = True
                stablecoin_detail = f"Correct stablecoin USDT found in withdrawal section: '{coin_val}'"
            elif 'USDC' in coin_val.upper():
                stablecoin_ok = False
                stablecoin_detail = f"WRONG stablecoin: found USDC but testnet/sui requires USDT. Value: '{coin_val}'"
            else:
                stablecoin_detail = f"Unrecognized stablecoin value: '{coin_val}'"
        else:
            # Fall back to checking if USDT appears and USDC is not the withdrawal coin
            # Accept if USDT is in report and the dry-run result has valid:true
            def find_valid_dryrun(obj):
                if isinstance(obj, dict):
                    has_valid = obj.get('valid') == True or obj.get('valid') == 'true'
                    has_dryrun = obj.get('dryRun') == True or obj.get('dry_run') == True
                    stablecoin_here = obj.get('stablecoin', '')
                    if has_usdt and (has_valid or has_dryrun):
                        return True
                    for v in obj.values():
                        if find_valid_dryrun(v):
                            return True
                elif isinstance(obj, list):
                    for item in obj:
                        if find_valid_dryrun(item):
                            return True
                return False

            if has_usdt and find_valid_dryrun(report):
                stablecoin_ok = True
                stablecoin_detail = "USDT found in report with valid dry-run indicator"
            elif has_usdt:
                stablecoin_ok = True
                stablecoin_detail = "USDT correctly referenced in report (testnet/sui requires USDT)"
            else:
                stablecoin_detail = "USDT not found in report. For testnet sui, USDT is required (not USDC)."
    except Exception as e:
        stablecoin_detail = f"Error checking stablecoin: {e}"

    checks.append({
        "name": "correct_stablecoin_usdt_for_testnet_sui",
        "passed": stablecoin_ok,
        "detail": stablecoin_detail
    })

    # ── CHECK 4: Dry-run was used (not a real withdrawal) ────────────────────
    dryrun_ok = False
    dryrun_detail = "No dry-run indicator found in report"
    try:
        report_str_lower = json.dumps(report).lower()
        # Check for dry_run, dryrun, dry-run, valid: true from dry-run result
        if any(kw in report_str_lower for kw in ('dryrun', 'dry_run', 'dry-run', '"valid": true', '"valid":true')):
            dryrun_ok = True
            dryrun_detail = "Dry-run indicator found in report"
        # Also check if the nova mock's dryRun:true is reflected
        def find_dryrun_field(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if 'dry' in k.lower():
                        return True
                    if find_dryrun_field(v):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if find_dryrun_field(item):
                        return True
            return False

        if not dryrun_ok and find_dryrun_field(report):
            dryrun_ok = True
            dryrun_detail = "Dry-run field found in report structure"
    except Exception as e:
        dryrun_detail = f"Error checking dry-run: {e}"

    checks.append({
        "name": "dry_run_used",
        "passed": dryrun_ok,
        "detail": dryrun_detail
    })

    # ── CHECK 5: SUI blockchain and destination address in report ─────────────
    sui_address_ok = False
    sui_address_detail = "SUI address or blockchain not found in report"
    try:
        expected_addr = "0xa1b2c3d4e5f60718293a4b5c6d7e8f90a1b2c3d4e5f60718293a4b5c6d7e8f9"
        report_str = json.dumps(report)

        has_sui = 'sui' in report_str.lower()
        has_addr = expected_addr.lower() in report_str.lower() or '0xa1b2c3d4' in report_str.lower()

        if has_sui and has_addr:
            sui_address_ok = True
            sui_address_detail = "SUI blockchain and destination address both found in report"
        elif has_sui:
            sui_address_detail = "SUI blockchain found but destination address missing from report"
        elif has_addr:
            sui_address_detail = "Destination address found but 'sui' blockchain not referenced"
        else:
            sui_address_detail = "Neither SUI blockchain nor destination address found in report"
    except Exception as e:
        sui_address_detail = f"Error checking SUI/address: {e}"

    checks.append({
        "name": "sui_blockchain_and_address_recorded",
        "passed": sui_address_ok,
        "detail": sui_address_detail
    })

    # ── CHECK 6: Withdrawal amount is 50 ─────────────────────────────────────
    amount_ok = False
    amount_detail = "Amount '50' not found in withdrawal section of report"
    try:
        def find_amount_50(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() in ('amount', 'withdrawal_amount', 'value', 'sum'):
                        if str(v) in ('50', '50.0', '50.00'):
                            return True
                    if find_amount_50(v):
                        return True
            elif isinstance(obj, list):
                for item in obj:
                    if find_amount_50(item):
                        return True
            return False

        if find_amount_50(report):
            amount_ok = True
            amount_detail = "Amount 50 found in report"
        else:
            # Check raw string
            report_str = json.dumps(report)
            if '"50"' in report_str or ': 50,' in report_str or ':50,' in report_str or '"50.0"' in report_str:
                amount_ok = True
                amount_detail = "Amount 50 found in report (string search)"
    except Exception as e:
        amount_detail = f"Error checking amount: {e}"

    checks.append({
        "name": "withdrawal_amount_is_50",
        "passed": amount_ok,
        "detail": amount_detail
    })

    # ── CHECK 7: Withdrawal dry-run status is ok/valid ────────────────────────
    dryrun_valid_ok = False
    dryrun_valid_detail = "No successful dry-run status found in report"
    try:
        report_str = json.dumps(report)
        # Look for status: ok or valid: true
        if ('"status": "ok"' in report_str or '"status":"ok"' in report_str or
            '"valid": true' in report_str or '"valid":true' in report_str or
            'valid: true' in report_str.lower() or '"passed": true' in report_str):
            dryrun_valid_ok = True
            dryrun_valid_detail = "Successful dry-run status (ok/valid) recorded in report"
    except Exception as e:
        dryrun_valid_detail = f"Error checking dry-run validity: {e}"

    checks.append({
        "name": "dryrun_result_is_valid",
        "passed": dryrun_valid_ok,
        "detail": dryrun_valid_detail
    })

    # ── SCORING ───────────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    total = len(checks)
    score = len(passed_checks) / total

    # Task passes if all critical checks pass:
    # - report_exists (mandatory)
    # - correct_stablecoin (most critical trap)
    # - dry_run_used (safety requirement)
    # - balance_captured
    critical_checks = {
        "report_exists",
        "correct_stablecoin_usdt_for_testnet_sui",
        "dry_run_used",
        "balance_captured",
    }
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )

    overall_passed = critical_passed and score >= 0.70

    result = {
        "passed": overall_passed,
        "score": round(score, 4),
        "checks": checks
    }
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()