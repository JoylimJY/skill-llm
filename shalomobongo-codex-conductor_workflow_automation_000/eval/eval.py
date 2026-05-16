import sys
import json
import subprocess
from pathlib import Path

def run_checks(workspace: str):
    root = Path(workspace)
    project_root = root / "finpipe-modernization"
    orch_dir = project_root / ".orchestrator"
    checks = []
    score = 0.0

    def check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return passed

    # ── CHECK 1: init_project_docs ran in brownfield mode ─────────────────────
    try:
        status_file = orch_dir / "status.json"
        context_file = orch_dir / "context.json"
        agents_md = project_root / "AGENTS.md"

        c1a = status_file.exists()
        c1b = context_file.exists()
        c1c = agents_md.exists()

        if c1a:
            status_data = json.loads(status_file.read_text())
            c1d = status_data.get("project_mode") == "brownfield"
        else:
            c1d = False

        if c1b:
            ctx = json.loads(context_file.read_text())
            c1e = ctx.get("project_mode") == "brownfield"
        else:
            c1e = False

        passed = all([c1a, c1b, c1c, c1d, c1e])
        detail = (f"status.json={c1a}, context.json={c1b}, AGENTS.md={c1c}, "
                  f"project_mode=brownfield in status={c1d}, in context={c1e}")
        if check("init_project_docs_brownfield_mode", passed, detail):
            score += 0.10
    except Exception as e:
        check("init_project_docs_brownfield_mode", False, f"Exception: {e}")

    # ── CHECK 2: Brownfield-specific docs exist ────────────────────────────────
    try:
        brownfield_docs = [
            "docs/as-is-architecture.md",
            "docs/dependency-map.md",
            "docs/risk-register.md",
            "docs/migration-strategy.md",
            "docs/characterization-tests.md",
            "docs/agent-handoff.md",
            "docs/validation-log.md",
        ]
        missing = [d for d in brownfield_docs if not (project_root / d).exists()]
        passed = len(missing) == 0
        detail = f"Missing brownfield docs: {missing}" if missing else "All brownfield docs present"
        if check("brownfield_docs_scaffolded", passed, detail):
            score += 0.05
    except Exception as e:
        check("brownfield_docs_scaffolded", False, f"Exception: {e}")

    # ── CHECK 3: Gate sequence — G0 and G1 set to PASS (prerequisite chain) ───
    try:
        status_data = json.loads((orch_dir / "status.json").read_text())
        g0_state = status_data["gates"]["G0"]["state"]
        g1_state = status_data["gates"]["G1"]["state"]
        passed_g0 = g0_state == "PASS"
        passed_g1 = g1_state == "PASS"
        passed = passed_g0 and passed_g1
        detail = f"G0={g0_state}, G1={g1_state}"
        if check("gates_G0_G1_pass", passed, detail):
            score += 0.10
    except Exception as e:
        check("gates_G0_G1_pass", False, f"Exception: {e}")

    # ── CHECK 4: G1 brownfield gate_status enforcement — docs must be substantive
    try:
        as_is = (project_root / "docs/as-is-architecture.md").read_text()
        dep_map = (project_root / "docs/dependency-map.md").read_text()
        # Must not be placeholder
        as_is_ok = "_To be completed._" not in as_is and len(as_is.strip()) > 50
        dep_ok = "_To be completed._" not in dep_map and len(dep_map.strip()) > 50
        passed = as_is_ok and dep_ok
        detail = (f"as-is-architecture substantive={as_is_ok} (len={len(as_is.strip())}), "
                  f"dependency-map substantive={dep_ok} (len={len(dep_map.strip())})")
        if check("brownfield_g1_docs_substantive", passed, detail):
            score += 0.10
    except Exception as e:
        check("brownfield_g1_docs_substantive", False, f"Exception: {e}")

    # ── CHECK 5: G2 brownfield docs substantive (risk-register + migration-strategy) ─
    try:
        risk = (project_root / "docs/risk-register.md").read_text()
        migration = (project_root / "docs/migration-strategy.md").read_text()
        risk_ok = "_To be completed._" not in risk and len(risk.strip()) > 50
        migration_ok = "_To be completed._" not in migration and len(migration.strip()) > 50
        passed = risk_ok and migration_ok
        detail = (f"risk-register substantive={risk_ok}, migration-strategy substantive={migration_ok}")
        if check("brownfield_g2_docs_substantive", passed, detail):
            score += 0.10
    except Exception as e:
        check("brownfield_g2_docs_substantive", False, f"Exception: {e}")

    # ── CHECK 6: G2 PASS in status.json ───────────────────────────────────────
    try:
        status_data = json.loads((orch_dir / "status.json").read_text())
        g2_state = status_data["gates"]["G2"]["state"]
        passed = g2_state == "PASS"
        detail = f"G2 state = {g2_state}"
        if check("gate_G2_pass", passed, detail):
            score += 0.05
    except Exception as e:
        check("gate_G2_pass", False, f"Exception: {e}")

    # ── CHECK 7: change_impact was run (impact record exists) ─────────────────
    try:
        impact_dir = orch_dir / "change-impacts"
        impact_files = list(impact_dir.glob("CR-*.json")) if impact_dir.exists() else []
        passed = len(impact_files) >= 1
        if passed:
            impact_data = json.loads(impact_files[0].read_text())
            has_request = bool(impact_data.get("request", "").strip())
            has_impacted = len(impact_data.get("impacted_docs", [])) > 0
            passed = has_request and has_impacted
            detail = f"Found {len(impact_files)} impact record(s). request={has_request}, impacted_docs={has_impacted}"
        else:
            detail = "No CR-*.json impact files found in .orchestrator/change-impacts/"
        if check("change_impact_ran", passed, detail):
            score += 0.05
    except Exception as e:
        check("change_impact_ran", False, f"Exception: {e}")

    # ── CHECK 8: change_impact TODOs completed (change-log, traceability updated) ─
    try:
        change_log = (project_root / "docs/change-log.md").read_text()
        traceability = (project_root / "docs/traceability.md").read_text()
        cl_ok = "_To be completed._" not in change_log and len(change_log.strip()) > 60
        tr_ok = "_To be completed._" not in traceability and len(traceability.strip()) > 60
        passed = cl_ok and tr_ok
        detail = (f"change-log substantive={cl_ok} (len={len(change_log.strip())}), "
                  f"traceability substantive={tr_ok} (len={len(traceability.strip())})")
        if check("change_impact_todos_completed", passed, detail):
            score += 0.10
    except Exception as e:
        check("change_impact_todos_completed", False, f"Exception: {e}")

    # ── CHECK 9: G3 gate run with --spec-ref (proprietary enforcement) ─────────
    try:
        status_data = json.loads((orch_dir / "status.json").read_text())
        g3 = status_data["gates"].get("G3", {})
        g3_state = g3.get("state", "PENDING")
        # Must have spec_ref recorded (run_gate writes it to status.json)
        g3_spec_ref = g3.get("spec_ref", "")
        g3_agent = g3.get("agent", "")
        g3_fallback = g3.get("fallback_agent", "")
        passed_state = g3_state in ("IN_PROGRESS", "PASS")
        passed_spec = bool(g3_spec_ref.strip())
        passed_agent = bool(g3_agent.strip())
        passed_fallback = bool(g3_fallback.strip())
        passed = passed_state and passed_spec and passed_agent and passed_fallback
        detail = (f"G3 state={g3_state}, spec_ref='{g3_spec_ref}', "
                  f"agent='{g3_agent}', fallback_agent='{g3_fallback}'")
        if check("g3_run_gate_with_spec_ref", passed, detail):
            score += 0.10
    except Exception as e:
        check("g3_run_gate_with_spec_ref", False, f"Exception: {e}")

    # ── CHECK 10: G3 PASS enforced — validate-cmd must be present in validation-log ─
    try:
        val_log = (project_root / "docs/validation-log.md").read_text()
        # Must contain a G3 PASS entry
        has_g3_entry = "G3" in val_log
        has_validate_cmd = "Validate Cmd:" in val_log
        # Must not show "N/A" as validate-cmd for a PASS entry near G3
        import re
        # Find G3 section
        g3_section = ""
        m = re.search(r"## G3.*?(?=## G[0-9]|\Z)", val_log, re.DOTALL)
        if m:
            g3_section = m.group(0)
        has_real_validate_cmd = (
            "Validate Cmd: N/A" not in g3_section and
            "Validate Cmd:" in g3_section and
            len(g3_section.strip()) > 30
        )
        passed = has_g3_entry and has_validate_cmd and has_real_validate_cmd
        detail = (f"G3 in validation-log={has_g3_entry}, has Validate Cmd={has_validate_cmd}, "
                  f"real cmd in G3 section={has_real_validate_cmd}")
        if check("g3_validation_log_recorded", passed, detail):
            score += 0.10
    except Exception as e:
        check("g3_validation_log_recorded", False, f"Exception: {e}")

    # ── CHECK 11: gate_status validate passes ─────────────────────────────────
    try:
        result = subprocess.run(
            ["python3", str(root / "scripts/gate_status.py"), "validate",
             "--root", str(project_root)],
            capture_output=True, text=True
        )
        passed = result.returncode == 0
        detail = (result.stdout + result.stderr).strip()
        if check("gate_status_validate_passes", passed, detail):
            score += 0.05
    except Exception as e:
        check("gate_status_validate_passes", False, f"Exception: {e}")

    # ── CHECK 12: docs/agent-handoff.md has content from run_gate ─────────────
    try:
        handoff = (project_root / "docs/agent-handoff.md").read_text()
        has_handoff_entry = "## Handoff:" in handoff
        has_agent_info = "Agent:" in handoff
        passed = has_handoff_entry and has_agent_info
        detail = f"agent-handoff.md has_handoff_entry={has_handoff_entry}, has_agent_info={has_agent_info}"
        if check("agent_handoff_updated", passed, detail):
            score += 0.05
    except Exception as e:
        check("agent_handoff_updated", False, f"Exception: {e}")

    # ── CHECK 13: G4 task plan created with all tasks checked (no unchecked) ──
    try:
        g4plan = (project_root / "docs/g4-task-plan.md").read_text()
        has_unchecked = "- [ ]" in g4plan
        has_checked = "- [x]" in g4plan or "- [X]" in g4plan
        # If G4 was attempted as PASS, unchecked tasks must not exist
        status_data = json.loads((orch_dir / "status.json").read_text())
        g4_state = status_data["gates"].get("G4", {}).get("state", "PENDING")
        if g4_state == "PASS":
            passed = not has_unchecked and has_checked
            detail = f"G4=PASS, unchecked tasks={has_unchecked}, has checked={has_checked}"
        else:
            # G4 not yet PASS — just check plan exists with some content
            passed = len(g4plan.strip()) > 30
            detail = f"G4={g4_state}, g4-task-plan.md len={len(g4plan.strip())}"
        if check("g4_task_plan_valid", passed, detail):
            score += 0.05
    except Exception as e:
        check("g4_task_plan_valid", False, f"Exception: {e}")

    # ── CHECK 14: requirements.md (spec) has proper spec structure ────────────
    try:
        spec = (project_root / "docs/requirements.md").read_text()
        # Must have at least: What/Why/Acceptance Criteria/Constraints sections
        has_what = "what" in spec.lower() or "# requirements" in spec.lower()
        has_acceptance = "acceptance" in spec.lower() or "criteria" in spec.lower()
        has_constraints = "constraint" in spec.lower() or "scope" in spec.lower() or "out of scope" in spec.lower()
        not_placeholder = "_To be completed._" not in spec and len(spec.strip()) > 100
        passed = has_what and has_acceptance and has_constraints and not_placeholder
        detail = (f"has_what={has_what}, has_acceptance={has_acceptance}, "
                  f"has_constraints={has_constraints}, not_placeholder={not_placeholder}, "
                  f"len={len(spec.strip())}")
        if check("spec_requirements_md_structured", passed, detail):
            score += 0.10
    except Exception as e:
        check("spec_requirements_md_structured", False, f"Exception: {e}")

    total_passed = sum(1 for c in checks if c["passed"])
    final_score = round(score, 3)

    return {
        "passed": final_score >= 0.60,
        "score": final_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_checks(workspace)
    print(json.dumps(result, indent=2))