import sys
import json
import os
from pathlib import Path

def load_report(workspace):
    """Find audit_report.json anywhere in workspace."""
    matches = list(Path(workspace).rglob("audit_report.json"))
    if not matches:
        return None, "audit_report.json not found anywhere in workspace"
    # Prefer root-level or closest to root
    matches.sort(key=lambda p: len(p.parts))
    return matches[0], None

def run_eval(workspace):
    checks = []
    total_score = 0.0

    # ── Check 1: audit_report.json exists ──────────────────────────────────
    report_path, err = load_report(workspace)
    check1_passed = report_path is not None
    checks.append({
        "name": "audit_report.json exists",
        "passed": check1_passed,
        "detail": str(report_path) if check1_passed else err
    })
    if not check1_passed:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── Load and parse JSON ─────────────────────────────────────────────────
    try:
        with open(report_path, "r") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "audit_report.json is valid JSON", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "audit_report.json is valid JSON", "passed": True, "detail": "Parsed successfully"})

    # ── Check 2: Report covers all 5 skills ─────────────────────────────────
    # The report must reference all skill package names
    report_str = json.dumps(report).lower()
    expected_skills = ["skill-alpha", "skill-beta", "skill-gamma", "skill-delta", "skill-epsilon"]
    covered = [s for s in expected_skills if s.lower() in report_str]
    all_covered = len(covered) == len(expected_skills)
    checks.append({
        "name": "All 5 skill packages referenced in report",
        "passed": all_covered,
        "detail": f"Found: {covered}. Missing: {[s for s in expected_skills if s not in covered]}"
    })

    # ── Check 3: HIGH risk items correctly identified ───────────────────────
    # skill-beta (ELF magic + null bytes) and skill-gamma (unicode override + control chars)
    # and skill-epsilon (suspicious pattern + null byte) should be HIGH
    # skill-delta (high non-ascii) should be at least MEDIUM
    # skill-alpha should be LOW

    def find_risk(skill_name, risk_level):
        """Check if skill_name is associated with risk_level in the report."""
        report_text = json.dumps(report).upper()
        # Look for skill name appearing near the risk level
        idx = report_text.find(skill_name.upper())
        if idx == -1:
            return False
        # Check in a window around the skill name
        window = report_text[max(0, idx-200):idx+500]
        return risk_level.upper() in window

    high_risk_skills = ["skill-beta", "skill-gamma", "skill-epsilon"]
    correctly_flagged_high = []
    for skill in high_risk_skills:
        if find_risk(skill, "HIGH"):
            correctly_flagged_high.append(skill)

    high_check_passed = len(correctly_flagged_high) >= 2  # at least 2 of 3
    checks.append({
        "name": "HIGH risk skills correctly identified (skill-beta, skill-gamma, skill-epsilon)",
        "passed": high_check_passed,
        "detail": f"Correctly flagged as HIGH: {correctly_flagged_high}"
    })

    # ── Check 4: skill-alpha identified as LOW risk ──────────────────────────
    alpha_low = find_risk("skill-alpha", "LOW")
    checks.append({
        "name": "skill-alpha correctly identified as LOW risk",
        "passed": alpha_low,
        "detail": "skill-alpha should have no suspicious content (LOW risk)"
    })

    # ── Check 5: Proprietary flag names present in report ───────────────────
    proprietary_flags = ["NULL_BYTES", "MAGIC_BYTES", "UNICODE_OVERRIDE", "CONTROL_CHARS",
                         "HIGH_NON_ASCII", "SUSPICIOUS_PATTERN"]
    report_upper = json.dumps(report).upper()
    flags_found = [f for f in proprietary_flags if f in report_upper]
    flags_present = len(flags_found) >= 3  # at least 3 distinct flags from the tool
    checks.append({
        "name": "Proprietary flag names (NULL_BYTES, MAGIC_BYTES, etc.) present in report",
        "passed": flags_present,
        "detail": f"Found flags: {flags_found}"
    })

    # ── Check 6: Integrity verification results included ────────────────────
    # The agent must have run verify.js on high-risk files
    # Look for integrity/checksum/valid/invalid language in report
    integrity_terms = ["valid", "invalid", "integrity", "checksum", "expected", "actual", "verify"]
    integrity_present = any(t in report_str for t in integrity_terms)
    checks.append({
        "name": "Integrity verification results included in report",
        "passed": integrity_present,
        "detail": f"Report contains integrity/checksum language: {integrity_present}"
    })

    # ── Check 7: Security policy compliance — HIGH risk items have next steps ──
    # Per SKILL.md Security Policy: HIGH RISK items MUST have specific reason + next steps
    next_step_terms = ["manual review", "human", "inspect", "review", "next step", "action", "recommend"]
    has_next_steps = any(t in report_str for t in next_step_terms)
    checks.append({
        "name": "HIGH risk items include next-step recommendations (Security Policy compliance)",
        "passed": has_next_steps,
        "detail": f"Report contains action/next-steps language: {has_next_steps}"
    })

    # ── Check 8: Report structure is non-trivial (not just flat text) ────────
    # Should be a dict or list (not just a string dump)
    is_structured = isinstance(report, (dict, list))
    has_depth = False
    if isinstance(report, dict):
        has_depth = any(isinstance(v, (dict, list)) for v in report.values())
    elif isinstance(report, list):
        has_depth = any(isinstance(item, dict) for item in report)
    structured_check = is_structured and (has_depth or len(json.dumps(report)) > 200)
    checks.append({
        "name": "Report is a structured JSON object/array (not flat string)",
        "passed": structured_check,
        "detail": f"Type: {type(report).__name__}, top-level keys: {list(report.keys()) if isinstance(report, dict) else f'list of {len(report)} items'}"
    })

    # ── Scoring ───────────────────────────────────────────────────────────────
    weights = {
        "audit_report.json exists": 0.05,
        "audit_report.json is valid JSON": 0.05,
        "All 5 skill packages referenced in report": 0.15,
        "HIGH risk skills correctly identified (skill-beta, skill-gamma, skill-epsilon)": 0.25,
        "skill-alpha correctly identified as LOW risk": 0.10,
        "Proprietary flag names (NULL_BYTES, MAGIC_BYTES, etc.) present in report": 0.20,
        "Integrity verification results included in report": 0.10,
        "HIGH risk items include next-step recommendations (Security Policy compliance)": 0.05,
        "Report is a structured JSON object/array (not flat string)": 0.05,
    }

    score = sum(weights.get(c["name"], 0.0) for c in checks if c["passed"])

    # Must pass core checks to be considered overall passing
    core_checks = [
        "audit_report.json exists",
        "audit_report.json is valid JSON",
        "HIGH risk skills correctly identified (skill-beta, skill-gamma, skill-epsilon)",
        "Proprietary flag names (NULL_BYTES, MAGIC_BYTES, etc.) present in report",
    ]
    core_passed = all(c["passed"] for c in checks if c["name"] in core_checks)
    overall_passed = core_passed and score >= 0.55

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))