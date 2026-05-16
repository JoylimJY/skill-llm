import sys
import json
import subprocess
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
home = Path.home()
compliance_dir = home / ".openclaw" / "compliance"
checker = workspace / "skills" / "compliance-checker" / "scripts" / "checker.py"

checks = []
score_weights = []

def check(name, weight=1.0):
    def decorator(fn):
        score_weights.append(weight)
        try:
            passed, detail = fn()
        except Exception as e:
            passed, detail = False, f"Exception: {e}"
        checks.append({"name": name, "passed": passed, "detail": detail})
        return fn
    return decorator


# ── CHECK 1: Policy 'fintech-prod' was created ───────────────────────────────
@check("policy_fintech_prod_exists", weight=1.5)
def _():
    policy_path = compliance_dir / "policies" / "fintech-prod.json"
    if not policy_path.exists():
        return False, f"Policy file not found at {policy_path}"
    data = json.loads(policy_path.read_text())
    if data.get("name") != "fintech-prod":
        return False, f"Policy name mismatch: {data.get('name')}"
    return True, "Policy 'fintech-prod' exists with correct name"


# ── CHECK 2: Policy contains exactly the required rules ───────────────────────
@check("policy_has_required_rules", weight=2.0)
def _():
    policy_path = compliance_dir / "policies" / "fintech-prod.json"
    if not policy_path.exists():
        return False, "Policy file not found"
    data = json.loads(policy_path.read_text())
    rules_in_policy = {r["rule"] for r in data.get("rules", [])}
    required_rules = {
        "no-critical-findings",
        "trust-verified",
        "no-shell-exec",
        "no-env-access",
        "version-pinned",
    }
    missing = required_rules - rules_in_policy
    if missing:
        return False, f"Missing rules: {sorted(missing)}. Found: {sorted(rules_in_policy)}"
    return True, f"All required rules present: {sorted(rules_in_policy)}"


# ── CHECK 3: Rule severities are correct ──────────────────────────────────────
@check("rule_severities_correct", weight=1.5)
def _():
    policy_path = compliance_dir / "policies" / "fintech-prod.json"
    if not policy_path.exists():
        return False, "Policy file not found"
    data = json.loads(policy_path.read_text())
    rule_map = {r["rule"]: r["severity"] for r in data.get("rules", [])}
    
    expected_severities = {
        "no-critical-findings": "critical",
        "trust-verified": "high",
        "no-shell-exec": "medium",
        "no-env-access": "medium",  # acceptable: medium or high from SKILL.md perspective
        "version-pinned": "medium",
    }
    
    issues = []
    for rule, expected_sev in expected_severities.items():
        actual = rule_map.get(rule, "MISSING")
        # Be strict: check that the severity is one of the expected ones
        # no-env-access could reasonably be medium or high
        if rule == "no-env-access":
            if actual not in ("medium", "high"):
                issues.append(f"{rule}: expected medium or high, got {actual}")
        elif actual != expected_sev:
            issues.append(f"{rule}: expected {expected_sev}, got {actual}")
    
    if issues:
        return False, f"Severity mismatches: {issues}"
    return True, "All rule severities correct"


# ── CHECK 4: Assessment was performed on arc-payment-gateway ─────────────────
@check("assessment_exists", weight=2.0)
def _():
    assessment_path = compliance_dir / "assessments" / "arc-payment-gateway__fintech-prod.json"
    if not assessment_path.exists():
        return False, f"Assessment file not found at {assessment_path}"
    data = json.loads(assessment_path.read_text())
    if data.get("skill") != "arc-payment-gateway":
        return False, f"Skill mismatch: {data.get('skill')}"
    if data.get("policy") != "fintech-prod":
        return False, f"Policy mismatch: {data.get('policy')}"
    return True, f"Assessment exists with status: {data.get('status')}"


# ── CHECK 5: Exemption for no-network-calls exists ────────────────────────────
@check("exemption_no_network_calls", weight=2.0)
def _():
    exemption_path = compliance_dir / "exemptions" / "arc-payment-gateway__no-network-calls.json"
    if not exemption_path.exists():
        return False, f"Exemption file not found at {exemption_path}"
    data = json.loads(exemption_path.read_text())
    if data.get("skill") != "arc-payment-gateway":
        return False, f"Skill mismatch in exemption: {data.get('skill')}"
    if data.get("rule") != "no-network-calls":
        return False, f"Rule mismatch in exemption: {data.get('rule')}"
    reason = data.get("reason", "")
    approved_by = data.get("approved_by", "")
    if not reason:
        return False, "Exemption has no reason"
    if not approved_by:
        return False, "Exemption has no approved_by (missing --approved-by flag)"
    return True, f"Exemption exists, approved_by='{approved_by}', reason present"


# ── CHECK 6: Remediation for no-shell-exec exists with status=fixed ───────────
@check("remediation_no_shell_exec", weight=2.0)
def _():
    remediation_path = compliance_dir / "remediations" / "arc-payment-gateway__no-shell-exec.json"
    if not remediation_path.exists():
        return False, f"Remediation file not found at {remediation_path}"
    data = json.loads(remediation_path.read_text())
    if data.get("skill") != "arc-payment-gateway":
        return False, f"Skill mismatch in remediation: {data.get('skill')}"
    if data.get("rule") != "no-shell-exec":
        return False, f"Rule mismatch in remediation: {data.get('rule')}"
    if data.get("status") != "fixed":
        return False, f"Remediation status is '{data.get('status')}', expected 'fixed'"
    if not data.get("action", ""):
        return False, "Remediation has no action description"
    return True, f"Remediation exists with status=fixed, action='{data.get('action', '')[:60]}...'"


# ── CHECK 7: JSON compliance report was generated ─────────────────────────────
@check("json_report_generated", weight=2.0)
def _():
    # Report should be named compliance_report__fintech-prod.json
    # Search in cwd and workspace
    candidates = list(Path("/").rglob("compliance_report__fintech-prod.json"))
    if not candidates:
        # Also try workspace
        candidates = list(workspace.rglob("compliance_report__fintech-prod.json"))
    if not candidates:
        return False, "compliance_report__fintech-prod.json not found anywhere"
    report_path = candidates[0]
    data = json.loads(report_path.read_text())
    
    # Validate report structure
    if "policy" not in data:
        return False, "Report missing 'policy' key"
    if "summary" not in data:
        return False, "Report missing 'summary' key"
    if "assessments" not in data:
        return False, "Report missing 'assessments' key"
    
    summary = data["summary"]
    if "total" not in summary:
        return False, "Summary missing 'total'"
    
    return True, f"JSON report found at {report_path}, total assessments: {summary.get('total')}"


# ── CHECK 8: Report contains correct assessment data ─────────────────────────
@check("report_has_assessment_data", weight=1.5)
def _():
    candidates = list(Path("/").rglob("compliance_report__fintech-prod.json"))
    if not candidates:
        candidates = list(workspace.rglob("compliance_report__fintech-prod.json"))
    if not candidates:
        return False, "Report file not found"
    
    data = json.loads(candidates[0].read_text())
    assessments = data.get("assessments", [])
    
    gateway_assessment = next(
        (a for a in assessments if a.get("skill") == "arc-payment-gateway"), None
    )
    if not gateway_assessment:
        return False, "No arc-payment-gateway assessment in report"
    
    results = gateway_assessment.get("results", [])
    rule_names_in_report = {r["rule"] for r in results}
    
    required_rules = {"no-critical-findings", "trust-verified", "no-shell-exec", "no-env-access", "version-pinned"}
    missing = required_rules - rule_names_in_report
    if missing:
        return False, f"Report assessment missing rules: {sorted(missing)}"
    
    return True, f"Report contains arc-payment-gateway assessment with {len(results)} rule results"


# ── CHECK 9: Report includes exemptions section ───────────────────────────────
@check("report_includes_exemptions", weight=1.0)
def _():
    candidates = list(Path("/").rglob("compliance_report__fintech-prod.json"))
    if not candidates:
        candidates = list(workspace.rglob("compliance_report__fintech-prod.json"))
    if not candidates:
        return False, "Report file not found"
    
    data = json.loads(candidates[0].read_text())
    exemptions = data.get("exemptions", [])
    
    gateway_exemption = next(
        (e for e in exemptions if e.get("skill") == "arc-payment-gateway" and e.get("rule") == "no-network-calls"),
        None
    )
    if not gateway_exemption:
        return False, f"No arc-payment-gateway/no-network-calls exemption in report. Found: {exemptions}"
    
    return True, "Report includes arc-payment-gateway no-network-calls exemption"


# ── CHECK 10: Report includes remediations section ────────────────────────────
@check("report_includes_remediations", weight=1.0)
def _():
    candidates = list(Path("/").rglob("compliance_report__fintech-prod.json"))
    if not candidates:
        candidates = list(workspace.rglob("compliance_report__fintech-prod.json"))
    if not candidates:
        return False, "Report file not found"
    
    data = json.loads(candidates[0].read_text())
    remediations = data.get("remediations", [])
    
    gateway_remediation = next(
        (r for r in remediations if r.get("skill") == "arc-payment-gateway" and r.get("rule") == "no-shell-exec"),
        None
    )
    if not gateway_remediation:
        return False, f"No arc-payment-gateway/no-shell-exec remediation in report. Found: {remediations}"
    if gateway_remediation.get("status") != "fixed":
        return False, f"Remediation in report has wrong status: {gateway_remediation.get('status')}"
    
    return True, "Report includes arc-payment-gateway no-shell-exec remediation with status=fixed"


# ── Compute final score ───────────────────────────────────────────────────────
total_weight = sum(score_weights)
passed_weight = sum(w for c, w in zip(checks, score_weights) if c["passed"])
score = round(passed_weight / total_weight, 4) if total_weight > 0 else 0.0
all_passed = all(c["passed"] for c in checks)

result = {
    "passed": all_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))