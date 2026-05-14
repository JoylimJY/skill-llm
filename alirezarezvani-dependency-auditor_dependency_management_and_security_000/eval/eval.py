import sys
import json
import os
from pathlib import Path

def find_file(workspace: Path, filename: str):
    """Search for a file recursively in the workspace."""
    matches = list(workspace.rglob(filename))
    if matches:
        return matches[0]
    return None

def load_json(path: Path):
    with open(path, 'r') as f:
        return json.load(f)

def evaluate(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0

    # ─── CHECK 1: Vulnerability scan JSON output exists ───────────────────────
    scan_file = find_file(workspace, "scan_results.json")
    if scan_file is None:
        # Also try common alt names
        for alt in ["scan.json", "vuln_scan.json", "dependency_scan.json", "vulnerabilities.json"]:
            scan_file = find_file(workspace, alt)
            if scan_file:
                break

    check1_passed = False
    scan_data = None
    detail1 = "scan_results.json (or equivalent) not found anywhere in workspace."
    if scan_file:
        try:
            scan_data = load_json(scan_file)
            # Must have 'dependencies' key with a list
            if isinstance(scan_data, dict) and "dependencies" in scan_data:
                deps = scan_data["dependencies"]
                if isinstance(deps, list) and len(deps) >= 5:
                    check1_passed = True
                    detail1 = f"Found scan output at {scan_file} with {len(deps)} dependencies."
                else:
                    detail1 = f"File {scan_file} has 'dependencies' key but only {len(deps) if isinstance(deps, list) else 'N/A'} entries (expected >= 5)."
            else:
                detail1 = f"File {scan_file} missing 'dependencies' key or wrong structure. Keys: {list(scan_data.keys()) if isinstance(scan_data, dict) else 'not a dict'}"
        except Exception as e:
            detail1 = f"Found {scan_file} but failed to parse JSON: {e}"
    checks.append({"name": "scan_json_output_exists_and_valid", "passed": check1_passed, "detail": detail1})
    if check1_passed:
        total_score += 0.25

    # ─── CHECK 2: Scan covers multiple ecosystems (npm + pip at minimum) ──────
    check2_passed = False
    detail2 = "Cannot check ecosystems: scan data unavailable or invalid."
    if scan_data and check1_passed:
        try:
            ecosystems = set()
            for dep in scan_data.get("dependencies", []):
                eco = dep.get("ecosystem", "").lower()
                if eco:
                    ecosystems.add(eco)
            # Should have found both npm and pip/python ecosystem deps
            has_npm = any(e in ecosystems for e in ["npm", "node", "javascript"])
            has_python = any(e in ecosystems for e in ["pip", "python", "pypi"])
            if has_npm and has_python:
                check2_passed = True
                detail2 = f"Scan covers multiple ecosystems: {sorted(ecosystems)}"
            else:
                detail2 = f"Scan ecosystems found: {sorted(ecosystems)}. Expected both npm and python/pip."
        except Exception as e:
            detail2 = f"Error checking ecosystems: {e}"
    checks.append({"name": "scan_covers_multiple_ecosystems", "passed": check2_passed, "detail": detail2})
    if check2_passed:
        total_score += 0.20

    # ─── CHECK 3: Scan detects at least one vulnerability ─────────────────────
    check3_passed = False
    detail3 = "No scan data available to check vulnerabilities."
    if scan_data and check1_passed:
        try:
            vuln_count = 0
            for dep in scan_data.get("dependencies", []):
                vulns = dep.get("vulnerabilities", [])
                vuln_count += len(vulns)
            # The project has multiple vulnerable packages (lodash 4.17.20, axios 0.21.1, pyyaml 5.3.1, etc.)
            if vuln_count >= 1:
                check3_passed = True
                detail3 = f"Scan found {vuln_count} vulnerabilities across dependencies."
            else:
                # Check top-level summary
                summary = scan_data.get("summary", {})
                total_vulns = summary.get("vulnerabilities_found", summary.get("total_vulnerabilities", 0))
                if total_vulns >= 1:
                    check3_passed = True
                    detail3 = f"Scan summary shows {total_vulns} vulnerabilities found."
                else:
                    detail3 = f"No vulnerabilities detected in scan output (vuln_count={vuln_count}, summary={summary}). Expected at least 1 for this project."
        except Exception as e:
            detail3 = f"Error checking vulnerabilities: {e}"
    checks.append({"name": "scan_detects_vulnerabilities", "passed": check3_passed, "detail": detail3})
    if check3_passed:
        total_score += 0.15

    # ─── CHECK 4: License compliance JSON output exists and used inventory ─────
    license_file = find_file(workspace, "compliance.json")
    if license_file is None:
        for alt in ["license_compliance.json", "license_report.json", "licenses.json", "license_check.json"]:
            license_file = find_file(workspace, alt)
            if license_file:
                break

    check4_passed = False
    license_data = None
    detail4 = "compliance.json (or equivalent license report) not found anywhere in workspace."
    if license_file:
        try:
            license_data = load_json(license_file)
            if isinstance(license_data, dict):
                # Must have some license/compliance-related structure
                has_compliance = any(k in license_data for k in [
                    "compliance_score", "license_summary", "dependencies", 
                    "conflicts", "licenses", "policy", "risk_score",
                    "license_distribution", "summary"
                ])
                if has_compliance:
                    check4_passed = True
                    detail4 = f"Found compliance report at {license_file} with keys: {list(license_data.keys())}"
                else:
                    detail4 = f"File {license_file} has unexpected structure. Keys: {list(license_data.keys())}"
            else:
                detail4 = f"File {license_file} is not a JSON object."
        except Exception as e:
            detail4 = f"Found {license_file} but failed to parse JSON: {e}"
    checks.append({"name": "license_compliance_json_exists", "passed": check4_passed, "detail": detail4})
    if check4_passed:
        total_score += 0.15

    # ─── CHECK 5: Strict policy was applied in license check ──────────────────
    check5_passed = False
    detail5 = "No license data available to check policy setting."
    if license_data and check4_passed:
        try:
            # The strict policy results in higher risk flags / different output
            # Under strict policy, GPL/AGPL/unknown licenses get flagged as conflicts
            # We check that: either 'policy' key says 'strict', or there are conflict detections,
            # or the compliance_score is not 100 (strict catches more things)
            policy_val = str(license_data.get("policy", "")).lower()
            has_strict = "strict" in policy_val
            
            # Check for conflict detection which strict policy surfaces
            conflicts = license_data.get("conflicts", [])
            has_conflicts_key = "conflicts" in license_data
            
            # Check compliance_score < 100 (strict policy usually flags things)
            compliance_score = license_data.get("compliance_score", 100)
            
            # Under strict policy, unknown licenses are flagged - look for that
            risk_summary = license_data.get("summary", {})
            has_unknown = any(
                "unknown" in str(v).lower() or "high" in str(v).lower()
                for v in risk_summary.values()
            ) if isinstance(risk_summary, dict) else False

            if has_strict or (has_conflicts_key and isinstance(conflicts, list)) or compliance_score < 100:
                check5_passed = True
                detail5 = f"Strict policy applied. policy='{policy_val}', compliance_score={compliance_score}, conflicts_key={has_conflicts_key}."
            else:
                detail5 = f"Cannot confirm strict policy was used. policy='{policy_val}', compliance_score={compliance_score}, keys={list(license_data.keys())}"
        except Exception as e:
            detail5 = f"Error checking strict policy: {e}"
    checks.append({"name": "strict_policy_applied", "passed": check5_passed, "detail": detail5})
    if check5_passed:
        total_score += 0.10

    # ─── CHECK 6: Upgrade plan JSON output exists ──────────────────────────────
    upgrade_file = find_file(workspace, "upgrade_plan.json")
    if upgrade_file is None:
        for alt in ["upgrades.json", "upgrade_report.json", "upgrade_roadmap.json", "security_upgrades.json"]:
            upgrade_file = find_file(workspace, alt)
            if upgrade_file:
                break

    check6_passed = False
    upgrade_data = None
    detail6 = "upgrade_plan.json (or equivalent) not found anywhere in workspace."
    if upgrade_file:
        try:
            upgrade_data = load_json(upgrade_file)
            if isinstance(upgrade_data, dict):
                # Should have upgrade-related keys
                has_upgrade_structure = any(k in upgrade_data for k in [
                    "upgrades", "phases", "timeline", "recommendations",
                    "upgrade_plan", "security_upgrades", "plan", "summary"
                ])
                if has_upgrade_structure:
                    check6_passed = True
                    detail6 = f"Found upgrade plan at {upgrade_file} with keys: {list(upgrade_data.keys())}"
                else:
                    detail6 = f"File {upgrade_file} has unexpected structure. Keys: {list(upgrade_data.keys())}"
            else:
                detail6 = f"File {upgrade_file} is not a JSON object: type={type(upgrade_data)}"
        except Exception as e:
            detail6 = f"Found {upgrade_file} but failed to parse JSON: {e}"
    checks.append({"name": "upgrade_plan_json_exists", "passed": check6_passed, "detail": detail6})
    if check6_passed:
        total_score += 0.10

    # ─── CHECK 7: Upgrade plan uses 45-day timeline and security-only filter ───
    check7_passed = False
    detail7 = "No upgrade plan data available to check timeline/security constraints."
    if upgrade_data and check6_passed:
        try:
            # Check for timeline=45 days
            timeline_val = upgrade_data.get("timeline", upgrade_data.get("timeline_days", None))
            
            # Check phases align with 45-day proprietary logic (30%/40%/30%)
            # Phase 1: ~13-14 days, Phase 2: ~18 days, Phase 3: ~13-14 days
            phases = upgrade_data.get("phases", [])
            has_phases = isinstance(phases, list) and len(phases) >= 2

            # Check security-only: upgrades should be security-focused
            upgrades = upgrade_data.get("upgrades", upgrade_data.get("security_upgrades", []))
            
            summary = upgrade_data.get("summary", {})
            
            # Timeline of 45 days: look for the value 45 anywhere in the structure
            data_str = json.dumps(upgrade_data)
            has_45_timeline = "45" in data_str
            
            # Security-only: all upgrades should have security relevance
            # or the plan explicitly mentions security
            has_security_focus = "security" in data_str.lower()
            
            if has_45_timeline and has_security_focus:
                check7_passed = True
                detail7 = f"Upgrade plan contains 45-day timeline and security focus. phases={len(phases) if has_phases else 'N/A'}"
            elif has_security_focus and has_phases:
                # Partial: has phases and security but maybe different timeline representation
                check7_passed = True
                detail7 = f"Upgrade plan has security focus and phased structure. timeline_val={timeline_val}"
            else:
                detail7 = f"Upgrade plan may not use 45-day timeline or security-only filter. has_45={has_45_timeline}, has_security={has_security_focus}, timeline_val={timeline_val}"
        except Exception as e:
            detail7 = f"Error checking upgrade plan constraints: {e}"
    checks.append({"name": "upgrade_plan_45day_security_only", "passed": check7_passed, "detail": detail7})
    if check7_passed:
        total_score += 0.05

    # ─── Final result ──────────────────────────────────────────────────────────
    all_passed = all(c["passed"] for c in checks)
    # Must pass at minimum checks 1, 4, 6 (one per tool) to be considered passing
    core_checks_passed = checks[0]["passed"] and checks[3]["passed"] and checks[5]["passed"]
    final_pass = core_checks_passed and total_score >= 0.60

    result = {
        "passed": final_pass,
        "score": round(total_score, 3),
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace_dir)