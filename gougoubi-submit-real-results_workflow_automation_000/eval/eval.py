import sys
import json
import os
from pathlib import Path

def run_eval(workspace: str):
    checks = []
    
    EXPECTED_PROPOSAL = "0xABCDEF1234567890abcdef1234567890ABCDEF12"
    EXPECTED_MODE = "resolved-only"
    EXPECTED_SUBMITTED_COUNT = 2
    EXPECTED_SKIPPED_COUNT = 1
    EXPECTED_FAILED_COUNT = 0
    SKILLS_DERIVED_TX_HASHES = {
        "0xaabbccdd11223344aabbccdd11223344aabbccdd11223344aabbccdd11223344",
        "0xdeadbeef99887766deadbeef99887766deadbeef99887766deadbeef99887766"
    }
    FIXED_SIDE_TX_MARKER = "0xfixedside"

    # ── Find submission_report.json ───────────────────────────────────────────
    report_path = None
    candidates = list(Path(workspace).rglob("submission_report.json"))
    if candidates:
        report_path = candidates[0]

    file_found = report_path is not None and report_path.exists()
    checks.append({
        "name": "submission_report.json exists",
        "passed": file_found,
        "detail": f"Found at {report_path}" if file_found else "File not found anywhere in workspace"
    })

    if not file_found:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Parse JSON ────────────────────────────────────────────────────────────
    try:
        with open(report_path, "r") as f:
            data = json.load(f)
        checks.append({"name": "Valid JSON format", "passed": True, "detail": "Parsed successfully"})
    except Exception as e:
        checks.append({"name": "Valid JSON format", "passed": False, "detail": f"JSON parse error: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Check top-level ok=true ───────────────────────────────────────────────
    ok_val = data.get("ok")
    ok_passed = ok_val is True
    checks.append({
        "name": "ok == true",
        "passed": ok_passed,
        "detail": f"ok={ok_val}"
    })

    # ── Check proposalAddress ─────────────────────────────────────────────────
    prop_addr = data.get("proposalAddress", "")
    addr_passed = isinstance(prop_addr, str) and prop_addr.lower() == EXPECTED_PROPOSAL.lower()
    checks.append({
        "name": f"proposalAddress matches {EXPECTED_PROPOSAL}",
        "passed": addr_passed,
        "detail": f"Got: {prop_addr}"
    })

    # ── Check mode == resolved-only ───────────────────────────────────────────
    mode_val = data.get("mode", "")
    mode_passed = mode_val == EXPECTED_MODE
    checks.append({
        "name": f"mode == '{EXPECTED_MODE}'",
        "passed": mode_passed,
        "detail": f"Got: '{mode_val}'. The default mode per SKILL.md is resolved-only."
    })

    # ── Check submittedCount == 2 ─────────────────────────────────────────────
    submitted_count = data.get("submittedCount", -1)
    sc_passed = submitted_count == EXPECTED_SUBMITTED_COUNT
    checks.append({
        "name": f"submittedCount == {EXPECTED_SUBMITTED_COUNT}",
        "passed": sc_passed,
        "detail": f"Got: {submitted_count}"
    })

    # ── Check skippedCount == 1 ───────────────────────────────────────────────
    skipped_count = data.get("skippedCount", -1)
    sk_passed = skipped_count == EXPECTED_SKIPPED_COUNT
    checks.append({
        "name": f"skippedCount == {EXPECTED_SKIPPED_COUNT} (already-settled condition)",
        "passed": sk_passed,
        "detail": f"Got: {skipped_count}. SKILL.md: skip if result != 0."
    })

    # ── Check failedCount == 0 ────────────────────────────────────────────────
    failed_count = data.get("failedCount", -1)
    fc_passed = failed_count == EXPECTED_FAILED_COUNT
    checks.append({
        "name": f"failedCount == {EXPECTED_FAILED_COUNT}",
        "passed": fc_passed,
        "detail": f"Got: {failed_count}"
    })

    # ── Check submitted array structure ───────────────────────────────────────
    submitted = data.get("submitted", [])
    submitted_is_list = isinstance(submitted, list) and len(submitted) == 2
    checks.append({
        "name": "submitted is a list of 2 entries",
        "passed": submitted_is_list,
        "detail": f"Got {len(submitted) if isinstance(submitted, list) else type(submitted)} entries"
    })

    # ── Check that skills-derived script was used (not fixed-side) ────────────
    # The skills-derived script produces specific tx hashes; fixed-side produces 0xfixedside... hashes
    tx_hashes_in_report = set()
    has_condition_names = False
    if isinstance(submitted, list):
        for entry in submitted:
            if isinstance(entry, dict):
                tx = entry.get("txHash", "")
                if tx:
                    tx_hashes_in_report.add(tx.lower())
                cname = entry.get("conditionName", "")
                if cname and cname.strip():
                    has_condition_names = True

    # Check NOT fixed-side (trap detection)
    used_fixed_side = any(FIXED_SIDE_TX_MARKER in tx for tx in tx_hashes_in_report)
    not_fixed_side_passed = not used_fixed_side
    checks.append({
        "name": "Skills-derived script used (not fixed-side)",
        "passed": not_fixed_side_passed,
        "detail": (
            "FAIL: Fixed-side tx hashes detected. Should use pbft-submit-results-from-skills-once.mjs, "
            "not pbft-submit-all-condition-results.mjs"
        ) if used_fixed_side else "Correct: no fixed-side tx hashes found"
    })

    # ── Check correct tx hashes from skills-derived script ────────────────────
    expected_txs_lower = {tx.lower() for tx in SKILLS_DERIVED_TX_HASHES}
    correct_txs = tx_hashes_in_report == expected_txs_lower
    checks.append({
        "name": "Submitted tx hashes match skills-derived script output",
        "passed": correct_txs,
        "detail": f"Expected: {expected_txs_lower}\nGot: {tx_hashes_in_report}"
    })

    # ── Check conditionName is populated ──────────────────────────────────────
    checks.append({
        "name": "conditionName fields are populated in submitted entries",
        "passed": has_condition_names,
        "detail": "SKILL.md requires evidence mapping preserved with condition names" if not has_condition_names else "OK"
    })

    # ── Check skipped array has the right condition ───────────────────────────
    skipped = data.get("skipped", [])
    skipped_condition_ok = False
    if isinstance(skipped, list) and len(skipped) == 1:
        sk = skipped[0]
        if isinstance(sk, dict):
            # Should be the FED rate condition (index 2) with already-settled reason
            reason = sk.get("reason", "").lower()
            idx = sk.get("index", -1)
            skipped_condition_ok = idx == 2 and ("result" in reason or "settled" in reason or "already" in reason or "0" in reason)
    checks.append({
        "name": "Skipped entry is the already-settled condition (index=2, reason mentions result!=0)",
        "passed": skipped_condition_ok,
        "detail": f"skipped array: {json.dumps(skipped)}"
    })

    # ── Check result values in submitted entries are 1 (Yes) ─────────────────
    result_values_ok = False
    if isinstance(submitted, list) and len(submitted) >= 2:
        result_values_ok = all(
            isinstance(e, dict) and e.get("result") == 1
            for e in submitted
        )
    checks.append({
        "name": "Result values in submitted entries are 1 (Yes/resolved)",
        "passed": result_values_ok,
        "detail": f"submitted results: {[e.get('result') for e in submitted if isinstance(e, dict)]}"
    })

    # ── Check required top-level keys (full schema compliance) ───────────────
    required_keys = {"ok", "proposalAddress", "mode", "submittedCount", "skippedCount",
                     "failedCount", "submitted", "skipped", "failed", "warnings"}
    present_keys = set(data.keys())
    missing_keys = required_keys - present_keys
    schema_ok = len(missing_keys) == 0
    checks.append({
        "name": "All required SKILL.md output schema keys present",
        "passed": schema_ok,
        "detail": f"Missing keys: {missing_keys}" if missing_keys else "All keys present"
    })

    # ── Compute score ─────────────────────────────────────────────────────────
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)
    overall_passed = all(c["passed"] for c in checks)

    return {"passed": overall_passed, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace_dir)
    print(json.dumps(result, indent=2))