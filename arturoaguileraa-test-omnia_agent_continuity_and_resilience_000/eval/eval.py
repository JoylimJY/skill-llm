import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    ws = Path(workspace)
    checks = []
    overall_passed = True

    # ── Helper ────────────────────────────────────────────────────────────────
    def add(name, passed, detail):
        nonlocal overall_passed
        checks.append({"name": name, "passed": passed, "detail": detail})
        if not passed:
            overall_passed = False

    # ── 1. Find the demo script ───────────────────────────────────────────────
    demo_script = ws / "scripts" / "resilience_demo.js"
    if not demo_script.exists():
        # Also accept it directly in workspace root
        alt = ws / "resilience_demo.js"
        if alt.exists():
            demo_script = alt

    add("demo_script_exists",
        demo_script.exists(),
        f"Looking for scripts/resilience_demo.js (or resilience_demo.js). Found: {demo_script.exists()}")

    if not demo_script.exists():
        # Cannot proceed further without the script
        for name in [
            "script_runs_successfully",
            "report_file_exists",
            "ledger_entry_count_positive",
            "snapshot_taken",
            "rehydration_successful",
            "coherence_passed",
            "witness_approved",
            "recovered_entry_count_matches_or_exceeds",
            "uses_molt_life_kernel_append",
            "uses_rehydrate_with_two_args",
        ]:
            add(name, False, "Demo script not found — skipping this check.")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    # ── 2. Static analysis of the script ─────────────────────────────────────
    try:
        script_src = demo_script.read_text()
    except Exception as e:
        add("script_readable", False, str(e))
        script_src = ""

    # Check it imports/requires molt-life-kernel
    uses_mlk = ("molt-life-kernel" in script_src or "MoltLifeKernel" in script_src)
    add("uses_molt_life_kernel_import",
        uses_mlk,
        "Script must import from 'molt-life-kernel' or reference MoltLifeKernel.")

    # Check kernel.append is called
    uses_append = "kernel.append" in script_src or ".append(" in script_src
    add("uses_molt_life_kernel_append",
        uses_append,
        "Script must call kernel.append() to build the ledger (Tenet 1).")

    # Check getSnapshot + rehydrate are both present
    uses_snapshot = "getSnapshot" in script_src
    uses_rehydrate = "rehydrate" in script_src
    add("uses_get_snapshot",
        uses_snapshot,
        "Script must call kernel.getSnapshot() before simulating crash.")
    add("uses_rehydrate",
        uses_rehydrate,
        "Script must call kernel.rehydrate() to recover from crash (Tenet 2).")

    # Check rehydrate is called with TWO arguments (capsule AND ledger — the proprietary trap)
    # Pattern: rehydrate(snapshot.capsule, snapshot.ledger) or similar two-arg form
    import re
    rehydrate_calls = re.findall(r'rehydrate\s*\(([^)]+)\)', script_src)
    two_arg_rehydrate = False
    for call in rehydrate_calls:
        # Count comma-separated top-level arguments
        depth = 0
        commas = 0
        for ch in call:
            if ch in '([{':
                depth += 1
            elif ch in ')]}':
                depth -= 1
            elif ch == ',' and depth == 0:
                commas += 1
        if commas >= 1:  # at least 2 arguments
            two_arg_rehydrate = True
    add("uses_rehydrate_with_two_args",
        two_arg_rehydrate,
        f"rehydrate() MUST be called with two args: capsule and ledger. Found calls: {rehydrate_calls}")

    # Check enforceCoherence is called
    uses_coherence = "enforceCoherence" in script_src
    add("uses_enforce_coherence",
        uses_coherence,
        "Script must call kernel.enforceCoherence(N) to check cognitive health (Tenet 5).")

    # Check witness is called
    uses_witness = "witness" in script_src and "kernel.witness" in script_src
    add("uses_witness",
        uses_witness,
        "Script must call kernel.witness() for human-gated approval (Tenet 3).")

    # Check witnessCallback is provided at construction (not a runtime arg)
    witness_callback_in_constructor = (
        "witnessCallback" in script_src and
        ("new MoltLifeKernel" in script_src or "MoltLifeKernel(" in script_src)
    )
    add("witness_callback_in_constructor",
        witness_callback_in_constructor,
        "witnessCallback must be passed as a constructor option to MoltLifeKernel, not at call time.")

    # Check heartbeatMs used (not heartbeatInterval or heartbeatSeconds)
    uses_heartbeat_ms = "heartbeatMs" in script_src
    add("uses_heartbeat_ms_param",
        uses_heartbeat_ms,
        "Constructor must use 'heartbeatMs' (milliseconds) — not heartbeatInterval or heartbeatSeconds.")

    # ── 3. Execute the script and capture output ──────────────────────────────
    try:
        result = subprocess.run(
            ["node", str(demo_script)],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60
        )
        script_ok = result.returncode == 0
        add("script_runs_successfully",
            script_ok,
            f"Exit code: {result.returncode}. stderr: {result.stderr[:500] if result.stderr else 'none'}")
    except subprocess.TimeoutExpired:
        add("script_runs_successfully", False, "Script timed out after 60 seconds.")
        script_ok = False
    except Exception as e:
        add("script_runs_successfully", False, str(e))
        script_ok = False

    # ── 4. Find and validate agent_audit_report.json ─────────────────────────
    report_path = ws / "agent_audit_report.json"
    if not report_path.exists():
        # Search recursively as fallback
        found = list(ws.rglob("agent_audit_report.json"))
        if found:
            report_path = found[0]

    add("report_file_exists",
        report_path.exists(),
        f"agent_audit_report.json must exist. Found at: {report_path if report_path.exists() else 'NOT FOUND'}")

    if not report_path.exists():
        for name in [
            "ledger_entry_count_positive",
            "snapshot_taken",
            "rehydration_successful",
            "coherence_passed",
            "witness_approved",
            "recovered_entry_count_matches_or_exceeds",
        ]:
            add(name, False, "Report file not found — cannot validate fields.")
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    try:
        report = json.loads(report_path.read_text())
    except Exception as e:
        add("report_json_valid", False, f"Could not parse JSON: {e}")
        score = sum(1 for c in checks if c["passed"]) / len(checks)
        return {"passed": False, "score": round(score, 3), "checks": checks}

    # ledger_entry_count: must be a positive integer
    lec = report.get("ledger_entry_count")
    add("ledger_entry_count_positive",
        isinstance(lec, int) and lec > 0,
        f"ledger_entry_count must be a positive integer. Got: {lec!r}")

    # snapshot_taken: must be True
    st = report.get("snapshot_taken")
    add("snapshot_taken",
        st is True,
        f"snapshot_taken must be true. Got: {st!r}")

    # rehydration_successful: must be True
    rs = report.get("rehydration_successful")
    add("rehydration_successful",
        rs is True,
        f"rehydration_successful must be true. Got: {rs!r}")

    # coherence_passed: must be True
    cp = report.get("coherence_passed")
    add("coherence_passed",
        cp is True,
        f"coherence_passed must be true. Got: {cp!r}")

    # witness_approved: must be True
    wa = report.get("witness_approved")
    add("witness_approved",
        wa is True,
        f"witness_approved must be true. Got: {wa!r}")

    # recovered_entry_count: must be int >= ledger_entry_count (recovery restores at least what was snapshotted)
    rec = report.get("recovered_entry_count")
    lec_val = lec if isinstance(lec, int) else 0
    add("recovered_entry_count_matches_or_exceeds",
        isinstance(rec, int) and rec >= lec_val and rec > 0,
        f"recovered_entry_count ({rec!r}) must be >= ledger_entry_count ({lec_val}) and > 0.")

    # ── 5. Score ─────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3)
    final_pass = overall_passed and score >= 0.85

    return {"passed": final_pass, "score": score, "checks": checks}


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    output = run_checks(workspace_dir)
    print(json.dumps(output, indent=2))