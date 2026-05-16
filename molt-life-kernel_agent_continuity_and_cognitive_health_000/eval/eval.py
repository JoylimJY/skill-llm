import sys
import json
import subprocess
from pathlib import Path

def main():
    workspace = Path(sys.argv[1])
    checks = []
    total_score = 0.0

    # Find the report file
    report_path = None
    candidates = list(workspace.rglob("kernel_audit_report.json"))
    if candidates:
        report_path = candidates[0]

    # CHECK 1: Report file exists
    file_exists = report_path is not None and report_path.is_file()
    checks.append({
        "name": "kernel_audit_report.json exists",
        "passed": file_exists,
        "detail": str(report_path) if file_exists else "File not found anywhere in workspace"
    })
    if not file_exists:
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    # Parse the report
    try:
        report = json.loads(report_path.read_text())
    except Exception as e:
        checks.append({"name": "Report is valid JSON", "passed": False, "detail": str(e)})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "Report is valid JSON", "passed": True, "detail": "Parsed successfully"})

    # CHECK 2: total_entries_after_rehydration
    # Agent must append 70 events, get snapshot, rehydrate, and report ledger length
    # The ledger after rehydration must have at least 70 entries (could be more if they appended extra)
    try:
        total_entries = report.get("total_entries_after_rehydration")
        # Must be a number >= 70 (all 70 session events were appended)
        entries_ok = isinstance(total_entries, (int, float)) and total_entries >= 70
        checks.append({
            "name": "total_entries_after_rehydration >= 70",
            "passed": entries_ok,
            "detail": f"Got: {total_entries!r} (expected int >= 70)"
        })
        if entries_ok:
            total_score += 0.25
    except Exception as e:
        checks.append({"name": "total_entries_after_rehydration >= 70", "passed": False, "detail": str(e)})

    # CHECK 3: snapshot_integrity — rehydration must succeed and ledger must match
    try:
        integrity = report.get("snapshot_integrity")
        integrity_ok = integrity is True or (isinstance(integrity, str) and integrity.lower() in ("true", "ok", "pass", "success"))
        checks.append({
            "name": "snapshot_integrity is true (rehydration succeeded)",
            "passed": integrity_ok,
            "detail": f"Got: {integrity!r} (expected truthy boolean)"
        })
        if integrity_ok:
            total_score += 0.25
    except Exception as e:
        checks.append({"name": "snapshot_integrity is true", "passed": False, "detail": str(e)})

    # CHECK 4: coherence_status — must be a non-null result from enforceCoherence(50)
    # enforceCoherence returns an object or status — must be present and non-null
    try:
        coherence = report.get("coherence_status")
        # It must exist and not be None/null
        coherence_present = coherence is not None
        # It should be either a dict/object (from the kernel return value) or a string status
        coherence_meaningful = coherence_present and (
            isinstance(coherence, (dict, str, bool, int, float)) and coherence != ""
        )
        # Bonus discriminative check: if it's a dict, it might contain entropy-related keys
        detail_msg = f"Got: {json.dumps(coherence)[:200]}"
        checks.append({
            "name": "coherence_status present and non-null (from enforceCoherence(50))",
            "passed": coherence_meaningful,
            "detail": detail_msg
        })
        if coherence_meaningful:
            total_score += 0.25
    except Exception as e:
        checks.append({"name": "coherence_status present and non-null", "passed": False, "detail": str(e)})

    # CHECK 5: witness_approved — must be true (auto-approved liquidation)
    try:
        witness_approved = report.get("witness_approved")
        # Must be truthy boolean true
        witness_ok = witness_approved is True or witness_approved == "true" or witness_approved == 1
        checks.append({
            "name": "witness_approved is true (liquidation action was auto-approved)",
            "passed": witness_ok,
            "detail": f"Got: {witness_approved!r} (expected true)"
        })
        if witness_ok:
            total_score += 0.25
    except Exception as e:
        checks.append({"name": "witness_approved is true", "passed": False, "detail": str(e)})

    # BONUS discriminative check: verify that the agent actually used molt-life-kernel
    # by looking for a .js script or checking for node_modules/molt-life-kernel usage
    try:
        # Look for any .js file in workspace that references molt-life-kernel
        js_files = list(workspace.rglob("*.js"))
        # Exclude node_modules
        js_files = [f for f in js_files if "node_modules" not in str(f)]
        molt_usage_found = False
        for jsf in js_files:
            try:
                content = jsf.read_text(errors="replace")
                if "molt-life-kernel" in content or "MoltLifeKernel" in content or "molt_life_kernel" in content:
                    molt_usage_found = True
                    break
            except Exception:
                pass
        checks.append({
            "name": "Evidence of molt-life-kernel usage in agent scripts",
            "passed": molt_usage_found,
            "detail": f"Found usage: {molt_usage_found}. JS files checked (excl. node_modules): {[str(f) for f in js_files[:5]]}"
        })
        # This is a discriminative check but doesn't add to score (score is based on output correctness)
    except Exception as e:
        checks.append({"name": "Evidence of molt-life-kernel usage", "passed": False, "detail": str(e)})

    all_core_passed = all(c["passed"] for c in checks[2:6])  # checks 2-5 are the 4 core checks
    final_passed = file_exists and all_core_passed

    print(json.dumps({
        "passed": final_passed,
        "score": round(total_score, 4),
        "checks": checks
    }, indent=2))


if __name__ == "__main__":
    main()