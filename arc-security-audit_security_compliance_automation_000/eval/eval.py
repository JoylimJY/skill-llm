#!/usr/bin/env python3
"""
Evaluates the agent's output for the security-audit task.

Checks:
  1. fleet_audit.json exists and has correct top-level structure (full audit)
  2. fleet_audit.json summary fields are correct (counts, risk level)
  3. fleet_audit.json skill_reports are sorted by risk priority
  4. quant_engine_audit.json exists and is a single-skill audit for quant-engine
  5. quant_engine_audit.json includes a trust_attestation block (--attest was used)
  6. quant_engine_audit.json attestation status is FAILED (quant-engine doesn't pass all checks)
  7. consolidated_audit.json exists and correctly synthesises both audits
"""

import sys
import json
from pathlib import Path

def load_json(path: Path):
    with open(path) as f:
        return json.load(f)

def find_file(workspace: Path, name: str):
    candidates = list(workspace.rglob(name))
    # Exclude tmp/ distractor
    candidates = [c for c in candidates if "old_report" not in c.name]
    return candidates[0] if candidates else None

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    passed_all = True

    RISK_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "none": 4}

    # ── Check 1: fleet_audit.json exists ─────────────────────────────────────
    fleet_path = find_file(workspace, "fleet_audit.json")
    if fleet_path is None:
        checks.append({"name": "fleet_audit.json exists", "passed": False,
                        "detail": "fleet_audit.json not found anywhere in workspace"})
        passed_all = False
        fleet_data = None
    else:
        checks.append({"name": "fleet_audit.json exists", "passed": True,
                        "detail": str(fleet_path)})
        try:
            fleet_data = load_json(fleet_path)
        except Exception as e:
            fleet_data = None
            checks.append({"name": "fleet_audit.json is valid JSON", "passed": False,
                            "detail": str(e)})
            passed_all = False

    # ── Check 2: fleet_audit.json is a 'full' audit ──────────────────────────
    if fleet_data is not None:
        is_full = fleet_data.get("audit_type") == "full"
        checks.append({"name": "fleet_audit.json is a full audit",
                        "passed": is_full,
                        "detail": f"audit_type={fleet_data.get('audit_type')}"})
        if not is_full:
            passed_all = False

    # ── Check 3: fleet_audit.json summary fields ─────────────────────────────
    if fleet_data is not None:
        try:
            summary = fleet_data["summary"]
            total_skills = summary["total_skills_scanned"]
            expected_total = 5
            ok_total = total_skills == expected_total
            checks.append({"name": "fleet_audit summary: total_skills_scanned==5",
                            "passed": ok_total,
                            "detail": f"got {total_skills}"})
            if not ok_total:
                passed_all = False

            # Overall risk must be 'critical' (quant-engine is critical)
            overall_risk = summary.get("overall_risk_level")
            ok_risk = overall_risk == "critical"
            checks.append({"name": "fleet_audit summary: overall_risk_level==critical",
                            "passed": ok_risk,
                            "detail": f"got '{overall_risk}'"})
            if not ok_risk:
                passed_all = False

            # findings_by_severity must be present and correct
            fbs = summary.get("findings_by_severity", {})
            ok_crit = fbs.get("critical", -1) == 1
            ok_high = fbs.get("high", -1) == 2
            ok_med  = fbs.get("medium", -1) == 2
            ok_low  = fbs.get("low", -1) == 1
            sev_ok = ok_crit and ok_high and ok_med and ok_low
            checks.append({"name": "fleet_audit summary: findings_by_severity correct",
                            "passed": sev_ok,
                            "detail": f"got {fbs}, expected critical=1, high=2, medium=2, low=1"})
            if not sev_ok:
                passed_all = False
        except (KeyError, TypeError) as e:
            checks.append({"name": "fleet_audit summary fields readable", "passed": False,
                            "detail": str(e)})
            passed_all = False

    # ── Check 4: fleet_audit.json skill_reports sorted by risk ───────────────
    if fleet_data is not None:
        try:
            reports = fleet_data.get("skill_reports", [])
            risk_values = [RISK_ORDER.get(r.get("overall_risk", "none"), 99) for r in reports]
            sorted_ok = risk_values == sorted(risk_values)
            checks.append({"name": "fleet_audit skill_reports sorted by risk (critical first)",
                            "passed": sorted_ok,
                            "detail": f"risk order: {[r.get('overall_risk') for r in reports]}"})
            if not sorted_ok:
                passed_all = False
        except Exception as e:
            checks.append({"name": "fleet_audit skill_reports sortable", "passed": False,
                            "detail": str(e)})
            passed_all = False

    # ── Check 5: quant_engine_audit.json exists ───────────────────────────────
    qe_path = find_file(workspace, "quant_engine_audit.json")
    if qe_path is None:
        checks.append({"name": "quant_engine_audit.json exists", "passed": False,
                        "detail": "quant_engine_audit.json not found in workspace"})
        passed_all = False
        qe_data = None
    else:
        checks.append({"name": "quant_engine_audit.json exists", "passed": True,
                        "detail": str(qe_path)})
        try:
            qe_data = load_json(qe_path)
        except Exception as e:
            qe_data = None
            checks.append({"name": "quant_engine_audit.json is valid JSON", "passed": False,
                            "detail": str(e)})
            passed_all = False

    # ── Check 6: quant_engine_audit is a 'single' audit for quant-engine ─────
    if qe_data is not None:
        is_single = qe_data.get("audit_type") == "single"
        checks.append({"name": "quant_engine_audit.json is a single-skill audit",
                        "passed": is_single,
                        "detail": f"audit_type={qe_data.get('audit_type')}"})
        if not is_single:
            passed_all = False

        try:
            skill_name = qe_data["skill_reports"][0]["skill"]
            is_qe = skill_name == "quant-engine"
            checks.append({"name": "quant_engine_audit.json targets quant-engine",
                            "passed": is_qe,
                            "detail": f"skill={skill_name}"})
            if not is_qe:
                passed_all = False
        except Exception as e:
            checks.append({"name": "quant_engine_audit skill name readable", "passed": False,
                            "detail": str(e)})
            passed_all = False

    # ── Check 7: trust_attestation present and status==FAILED (--attest used) ─
    if qe_data is not None:
        try:
            attest = qe_data["skill_reports"][0].get("trust_attestation")
            has_attest = attest is not None
            checks.append({"name": "quant_engine_audit.json has trust_attestation block (--attest used)",
                            "passed": has_attest,
                            "detail": str(attest)})
            if not has_attest:
                passed_all = False
            else:
                attest_status = attest.get("status")
                status_ok = attest_status == "FAILED"
                checks.append({"name": "quant-engine attestation status==FAILED (did not pass checks)",
                                "passed": status_ok,
                                "detail": f"status={attest_status}"})
                if not status_ok:
                    passed_all = False
        except Exception as e:
            checks.append({"name": "trust_attestation readable", "passed": False,
                            "detail": str(e)})
            passed_all = False

    # ── Check 8: consolidated_audit.json exists and synthesises both ──────────
    consol_path = find_file(workspace, "consolidated_audit.json")
    if consol_path is None:
        checks.append({"name": "consolidated_audit.json exists", "passed": False,
                        "detail": "consolidated_audit.json not found in workspace"})
        passed_all = False
    else:
        checks.append({"name": "consolidated_audit.json exists", "passed": True,
                        "detail": str(consol_path)})
        try:
            consol = load_json(consol_path)

            # Must reference fleet-level summary
            has_fleet = "fleet_summary" in consol or "full_audit" in consol or "fleet_audit" in consol
            checks.append({"name": "consolidated_audit.json references fleet audit data",
                            "passed": has_fleet,
                            "detail": f"top-level keys: {list(consol.keys())}"})
            if not has_fleet:
                passed_all = False

            # Must reference quant-engine deep-dive
            consol_str = json.dumps(consol)
            has_qe = "quant-engine" in consol_str
            checks.append({"name": "consolidated_audit.json references quant-engine deep-dive",
                            "passed": has_qe,
                            "detail": "checked for 'quant-engine' string in consolidated output"})
            if not has_qe:
                passed_all = False

            # Must include overall risk level from fleet
            has_risk = "critical" in consol_str
            checks.append({"name": "consolidated_audit.json reflects critical overall risk",
                            "passed": has_risk,
                            "detail": "checked for 'critical' risk level in consolidated output"})
            if not has_risk:
                passed_all = False

        except Exception as e:
            checks.append({"name": "consolidated_audit.json readable", "passed": False,
                            "detail": str(e)})
            passed_all = False

    # ── Score ─────────────────────────────────────────────────────────────────
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / len(checks), 3) if checks else 0.0

    result = {
        "passed": passed_all,
        "score": score,
        "checks": checks,
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(ws)