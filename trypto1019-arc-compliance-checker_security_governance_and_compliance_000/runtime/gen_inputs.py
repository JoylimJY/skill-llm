import os
import json
import random
import hashlib
import stat
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Compliance checker skill structure (the tool itself) ──────────────────
skill_base = workspace / "skills" / "compliance-checker"
scripts_dir = skill_base / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

checker_script = scripts_dir / "checker.py"
checker_script.write_text(r'''#!/usr/bin/env python3
"""
OpenClaw Compliance Checker
Policy-based compliance assessment for OpenClaw skills.
"""
import json
import sys
import os
import hashlib
import re
import argparse
from pathlib import Path
from datetime import datetime, timezone


COMPLIANCE_DIR = Path.home() / ".openclaw" / "compliance"
POLICIES_DIR = COMPLIANCE_DIR / "policies"
ASSESSMENTS_DIR = COMPLIANCE_DIR / "assessments"
EXEMPTIONS_DIR = COMPLIANCE_DIR / "exemptions"
REMEDIATIONS_DIR = COMPLIANCE_DIR / "remediations"
SKILLS_DIR = Path.home() / ".openclaw" / "skills"

BUILT_IN_RULES = {
    "no-critical-findings": {
        "description": "No CRITICAL findings from skill scanner",
        "frameworks": ["CIS Control 16", "OWASP A06"],
        "check": "scanner_critical"
    },
    "no-high-findings": {
        "description": "No HIGH findings from skill scanner",
        "frameworks": ["CIS Control 16", "OWASP A06"],
        "check": "scanner_high"
    },
    "trust-verified": {
        "description": "Trust level is VERIFIED or TRUSTED",
        "frameworks": ["CIS Control 2"],
        "check": "trust_level"
    },
    "no-network-calls": {
        "description": "No unauthorized network requests",
        "frameworks": ["CIS Control 9", "OWASP A10"],
        "check": "network_calls"
    },
    "no-shell-exec": {
        "description": "No shell execution patterns",
        "frameworks": ["CIS Control 2", "OWASP A03"],
        "check": "shell_exec"
    },
    "no-eval-exec": {
        "description": "No eval/exec patterns",
        "frameworks": ["OWASP A03"],
        "check": "eval_exec"
    },
    "has-checksum": {
        "description": "SHA-256 checksums for all files",
        "frameworks": ["CIS Control 2"],
        "check": "checksum"
    },
    "no-env-access": {
        "description": "No environment variable access",
        "frameworks": ["CIS Control 3"],
        "check": "env_access"
    },
    "no-data-exfil": {
        "description": "No data exfiltration patterns",
        "frameworks": ["CIS Control 3", "CIS Control 13"],
        "check": "data_exfil"
    },
    "version-pinned": {
        "description": "All dependencies version-pinned",
        "frameworks": ["CIS Control 2"],
        "check": "version_pinned"
    },
}

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1, "info": 0}


def ensure_dirs():
    for d in [POLICIES_DIR, ASSESSMENTS_DIR, EXEMPTIONS_DIR, REMEDIATIONS_DIR, SKILLS_DIR]:
        d.mkdir(parents=True, exist_ok=True)


def load_json(path):
    if path.exists():
        return json.loads(path.read_text())
    return None


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2))


def get_policy_path(name):
    return POLICIES_DIR / f"{name}.json"


def get_assessment_path(skill, policy):
    return ASSESSMENTS_DIR / f"{skill}__{policy}.json"


def get_exemption_path(skill, rule):
    return EXEMPTIONS_DIR / f"{skill}__{rule}.json"


def get_remediation_path(skill, rule):
    return REMEDIATIONS_DIR / f"{skill}__{rule}.json"


def get_skill_dir(skill_name):
    return SKILLS_DIR / skill_name


def cmd_policy_create(args):
    ensure_dirs()
    path = get_policy_path(args.name)
    if path.exists():
        print(f"Policy '{args.name}' already exists.")
        return
    policy = {
        "name": args.name,
        "description": args.description,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rules": []
    }
    save_json(path, policy)
    print(f"Policy '{args.name}' created.")


def cmd_policy_add_rule(args):
    ensure_dirs()
    path = get_policy_path(args.policy)
    policy = load_json(path)
    if not policy:
        print(f"Policy '{args.policy}' not found.")
        sys.exit(1)
    if args.rule not in BUILT_IN_RULES:
        print(f"Unknown rule: {args.rule}. Available: {list(BUILT_IN_RULES.keys())}")
        sys.exit(1)
    for r in policy["rules"]:
        if r["rule"] == args.rule:
            print(f"Rule '{args.rule}' already in policy.")
            return
    rule_entry = {
        "rule": args.rule,
        "description": args.description or BUILT_IN_RULES[args.rule]["description"],
        "severity": args.severity,
        "frameworks": BUILT_IN_RULES[args.rule]["frameworks"]
    }
    policy["rules"].append(rule_entry)
    save_json(path, policy)
    print(f"Rule '{args.rule}' added to policy '{args.policy}' with severity '{args.severity}'.")


def _check_skill(skill_name, rule_name):
    """Run the actual check for a rule against a skill. Returns (passed, detail)."""
    skill_dir = get_skill_dir(skill_name)
    scripts = list(skill_dir.rglob("*.py")) if skill_dir.exists() else []
    content = ""
    for s in scripts:
        try:
            content += s.read_text(errors="ignore")
        except Exception:
            pass

    check = BUILT_IN_RULES[rule_name]["check"]

    if check == "scanner_critical":
        # Look for scanner output file
        scanner_output = skill_dir / "scanner_output.json"
        if scanner_output.exists():
            data = load_json(scanner_output)
            criticals = [f for f in data.get("findings", []) if f.get("severity", "").upper() == "CRITICAL"]
            if criticals:
                return False, f"Found {len(criticals)} CRITICAL finding(s)"
        return True, "No CRITICAL findings"

    elif check == "scanner_high":
        scanner_output = skill_dir / "scanner_output.json"
        if scanner_output.exists():
            data = load_json(scanner_output)
            highs = [f for f in data.get("findings", []) if f.get("severity", "").upper() == "HIGH"]
            if highs:
                return False, f"Found {len(highs)} HIGH finding(s)"
        return True, "No HIGH findings"

    elif check == "trust_level":
        trust_file = skill_dir / "trust.json"
        if trust_file.exists():
            data = load_json(trust_file)
            level = data.get("level", "UNKNOWN").upper()
            if level in ("VERIFIED", "TRUSTED"):
                return True, f"Trust level: {level}"
            return False, f"Trust level '{level}' not acceptable"
        return False, "No trust attestation found"

    elif check == "network_calls":
        patterns = [r"requests\.", r"urllib", r"httpx", r"http\.client", r"socket\."]
        for p in patterns:
            if re.search(p, content):
                return False, f"Network call pattern detected: {p}"
        return True, "No network call patterns detected"

    elif check == "shell_exec":
        patterns = [r"shell\s*=\s*True", r"subprocess\.call", r"subprocess\.run", r"os\.system"]
        for p in patterns:
            if re.search(p, content):
                return False, f"Shell execution pattern detected: {p}"
        return True, "No shell execution patterns"

    elif check == "eval_exec":
        patterns = [r"\beval\s*\(", r"\bexec\s*\("]
        for p in patterns:
            if re.search(p, content):
                return False, f"Eval/exec pattern detected: {p}"
        return True, "No eval/exec patterns"

    elif check == "checksum":
        checksum_file = skill_dir / "checksums.json"
        if not checksum_file.exists():
            return False, "No checksums.json found"
        checksums = load_json(checksum_file)
        for s in scripts:
            rel = str(s.relative_to(skill_dir))
            if rel not in checksums:
                return False, f"No checksum for {rel}"
            actual = hashlib.sha256(s.read_bytes()).hexdigest()
            if checksums[rel] != actual:
                return False, f"Checksum mismatch for {rel}"
        return True, "All checksums valid"

    elif check == "env_access":
        patterns = [r"os\.environ", r"os\.getenv", r"environ\["]
        for p in patterns:
            if re.search(p, content):
                return False, f"Environment variable access detected: {p}"
        return True, "No environment variable access"

    elif check == "data_exfil":
        patterns = [r"base64\.b64encode", r"pickle\.dumps", r"open\(.+['\"]w['\"]"]
        for p in patterns:
            if re.search(p, content):
                return False, f"Potential data exfiltration pattern: {p}"
        return True, "No data exfiltration patterns"

    elif check == "version_pinned":
        req_file = skill_dir / "requirements.txt"
        if req_file.exists():
            lines = [l.strip() for l in req_file.read_text().splitlines() if l.strip() and not l.startswith("#")]
            unpinned = [l for l in lines if "==" not in l and ">=" not in l and "<=" not in l]
            if unpinned:
                return False, f"Unpinned dependencies: {unpinned}"
        return True, "All dependencies pinned"

    return True, "Check not implemented"


def cmd_assess(args):
    ensure_dirs()
    policy_path = get_policy_path(args.policy)
    policy = load_json(policy_path)
    if not policy:
        print(f"Policy '{args.policy}' not found.")
        sys.exit(1)

    skill_name = args.skill
    results = []
    all_passed = True

    for rule_entry in policy["rules"]:
        rule_name = rule_entry["rule"]
        passed, detail = _check_skill(skill_name, rule_name)

        # Check for exemption
        exempt_path = get_exemption_path(skill_name, rule_name)
        exempted = False
        if not passed and exempt_path.exists():
            exempted = True

        results.append({
            "rule": rule_name,
            "severity": rule_entry["severity"],
            "passed": passed,
            "exempted": exempted,
            "detail": detail,
            "frameworks": rule_entry["frameworks"]
        })

        if not passed and not exempted:
            all_passed = False

    # Determine status
    all_exempted = all(r["passed"] or r["exempted"] for r in results)
    if all_passed:
        status = "COMPLIANT"
    elif all_exempted and not all_passed:
        status = "EXEMPTED"
    else:
        status = "NON-COMPLIANT"

    assessment = {
        "skill": skill_name,
        "policy": args.policy,
        "assessed_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "results": results
    }

    path = get_assessment_path(skill_name, args.policy)
    save_json(path, assessment)
    print(f"Assessment complete. Status: {status}")
    for r in results:
        icon = "✓" if r["passed"] else ("~" if r["exempted"] else "✗")
        print(f"  [{icon}] {r['rule']}: {r['detail']}")


def cmd_assess_all(args):
    ensure_dirs()
    if not SKILLS_DIR.exists():
        print("No skills directory found.")
        return
    skills = [d.name for d in SKILLS_DIR.iterdir() if d.is_dir()]
    for skill in skills:
        print(f"\nAssessing {skill}...")
        class FakeArgs:
            pass
        fa = FakeArgs()
        fa.skill = skill
        fa.policy = args.policy
        cmd_assess(fa)


def cmd_status(args):
    ensure_dirs()
    policy_path = get_policy_path(args.policy)
    if not policy_path.exists():
        print(f"Policy '{args.policy}' not found.")
        sys.exit(1)
    assessments = list(ASSESSMENTS_DIR.glob(f"*__{args.policy}.json"))
    if not assessments:
        print(f"No assessments found for policy '{args.policy}'.")
        return
    print(f"\nCompliance Status — Policy: {args.policy}\n" + "="*50)
    for a_path in sorted(assessments):
        data = load_json(a_path)
        print(f"  {data['skill']:30s} {data['status']}")


def cmd_report(args):
    ensure_dirs()
    policy_path = get_policy_path(args.policy)
    policy = load_json(policy_path)
    if not policy:
        print(f"Policy '{args.policy}' not found.")
        sys.exit(1)

    assessments = list(ASSESSMENTS_DIR.glob(f"*__{args.policy}.json"))
    all_assessments = [load_json(a) for a in sorted(assessments)]

    report = {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": policy,
        "summary": {
            "total": len(all_assessments),
            "compliant": sum(1 for a in all_assessments if a["status"] == "COMPLIANT"),
            "non_compliant": sum(1 for a in all_assessments if a["status"] == "NON-COMPLIANT"),
            "exempted": sum(1 for a in all_assessments if a["status"] == "EXEMPTED"),
            "unknown": sum(1 for a in all_assessments if a["status"] == "UNKNOWN"),
        },
        "assessments": all_assessments,
        "exemptions": [],
        "remediations": []
    }

    # Load exemptions and remediations
    for e_path in sorted(EXEMPTIONS_DIR.glob("*.json")):
        data = load_json(e_path)
        if data:
            report["exemptions"].append(data)

    for r_path in sorted(REMEDIATIONS_DIR.glob("*.json")):
        data = load_json(r_path)
        if data:
            report["remediations"].append(data)

    if args.format == "json":
        out_path = Path.cwd() / f"compliance_report__{args.policy}.json"
        save_json(out_path, report)
        print(f"Report written to {out_path}")
    else:
        print(f"\n{'='*60}")
        print(f"COMPLIANCE REPORT — {args.policy.upper()}")
        print(f"{'='*60}")
        s = report["summary"]
        print(f"Total:        {s['total']}")
        print(f"Compliant:    {s['compliant']}")
        print(f"Non-Compliant:{s['non_compliant']}")
        print(f"Exempted:     {s['exempted']}")
        for a in all_assessments:
            print(f"\n  [{a['status']}] {a['skill']}")
            for r in a["results"]:
                icon = "✓" if r["passed"] else ("~" if r["exempted"] else "✗")
                print(f"    [{icon}] {r['rule']}: {r['detail']}")


def cmd_exempt(args):
    ensure_dirs()
    path = get_exemption_path(args.skill, args.rule)
    exemption = {
        "skill": args.skill,
        "rule": args.rule,
        "reason": args.reason,
        "approved_by": args.approved_by,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    save_json(path, exemption)
    print(f"Exemption recorded for '{args.skill}' / rule '{args.rule}' (approved by: {args.approved_by}).")


def cmd_remediate(args):
    ensure_dirs()
    path = get_remediation_path(args.skill, args.rule)
    remediation = {
        "skill": args.skill,
        "rule": args.rule,
        "action": args.action,
        "status": args.status,
        "recorded_at": datetime.now(timezone.utc).isoformat()
    }
    save_json(path, remediation)
    print(f"Remediation recorded for '{args.skill}' / rule '{args.rule}': {args.status}.")


def cmd_pipeline(args):
    print(f"Running pipeline for skill '{args.skill}' against policy '{args.policy}'...")
    cmd_assess(args)


def main():
    parser = argparse.ArgumentParser(prog="checker.py", description="OpenClaw Compliance Checker")
    sub = parser.add_subparsers(dest="command")

    # policy
    p_policy = sub.add_parser("policy")
    p_policy_sub = p_policy.add_subparsers(dest="policy_command")

    p_create = p_policy_sub.add_parser("create")
    p_create.add_argument("--name", required=True)
    p_create.add_argument("--description", default="")

    p_add_rule = p_policy_sub.add_parser("add-rule")
    p_add_rule.add_argument("--policy", required=True)
    p_add_rule.add_argument("--rule", required=True)
    p_add_rule.add_argument("--description", default="")
    p_add_rule.add_argument("--severity", required=True)

    # assess
    p_assess = sub.add_parser("assess")
    p_assess.add_argument("--skill", required=True)
    p_assess.add_argument("--policy", required=True)

    # assess-all
    p_assess_all = sub.add_parser("assess-all")
    p_assess_all.add_argument("--policy", required=True)

    # status
    p_status = sub.add_parser("status")
    p_status.add_argument("--policy", required=True)

    # report
    p_report = sub.add_parser("report")
    p_report.add_argument("--policy", required=True)
    p_report.add_argument("--format", default="text", choices=["json", "text"])

    # exempt
    p_exempt = sub.add_parser("exempt")
    p_exempt.add_argument("--skill", required=True)
    p_exempt.add_argument("--rule", required=True)
    p_exempt.add_argument("--reason", required=True)
    p_exempt.add_argument("--approved-by", required=True, dest="approved_by")

    # remediate
    p_remediate = sub.add_parser("remediate")
    p_remediate.add_argument("--skill", required=True)
    p_remediate.add_argument("--rule", required=True)
    p_remediate.add_argument("--action", required=True)
    p_remediate.add_argument("--status", required=True)

    # pipeline
    p_pipeline = sub.add_parser("pipeline")
    p_pipeline.add_argument("--skill", required=True)
    p_pipeline.add_argument("--policy", required=True)

    args = parser.parse_args()

    if args.command == "policy":
        if args.policy_command == "create":
            cmd_policy_create(args)
        elif args.policy_command == "add-rule":
            cmd_policy_add_rule(args)
        else:
            p_policy.print_help()
    elif args.command == "assess":
        cmd_assess(args)
    elif args.command == "assess-all":
        cmd_assess_all(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "exempt":
        cmd_exempt(args)
    elif args.command == "remediate":
        cmd_remediate(args)
    elif args.command == "pipeline":
        cmd_pipeline(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
''')
checker_script.chmod(checker_script.stat().st_mode | stat.S_IEXEC)

# ── 2. The target skill: arc-payment-gateway (deliberately problematic) ───────
target_skill_dir = Path.home() / ".openclaw" / "skills" / "arc-payment-gateway"
target_skill_dir.mkdir(parents=True, exist_ok=True)

# Main script: has shell exec + env access + network calls
main_script = target_skill_dir / "main.py"
main_script.write_text("""#!/usr/bin/env python3
\"\"\"Arc Payment Gateway Skill - processes payment transactions\"\"\"
import os
import requests
import subprocess

API_KEY = os.environ.get("PAYMENT_API_KEY", "")
GATEWAY_URL = os.environ.get("GATEWAY_URL", "https://payments.internal/api/v1")

def process_payment(amount, currency, card_token):
    # Validate input
    result = subprocess.run(
        ["validate-card", card_token],
        capture_output=True, text=True
    )
    
    resp = requests.post(GATEWAY_URL + "/charge", json={
        "amount": amount,
        "currency": currency,
        "token": card_token,
        "api_key": API_KEY
    })
    return resp.json()

def batch_process(payment_file):
    os.system(f"chmod 600 {payment_file}")
    with open(payment_file) as f:
        import json
        payments = json.load(f)
    return [process_payment(**p) for p in payments]
""")

# Helper script: version-unpinned requirements (triggers version-pinned rule)
requirements_file = target_skill_dir / "requirements.txt"
requirements_file.write_text("""requests
pyyaml
cryptography>=3.0
stripe
""")

# Trust attestation — skill is TRUSTED
trust_file = target_skill_dir / "trust.json"
trust_file.write_text(json.dumps({
    "skill": "arc-payment-gateway",
    "level": "TRUSTED",
    "attested_by": "security-team",
    "attested_at": "2024-01-15T10:00:00Z"
}, indent=2))

# Scanner output — no critical findings, one high finding
scanner_output = target_skill_dir / "scanner_output.json"
scanner_output.write_text(json.dumps({
    "skill": "arc-payment-gateway",
    "scanned_at": "2024-06-01T08:00:00Z",
    "findings": [
        {
            "id": "SCAN-001",
            "severity": "HIGH",
            "title": "Hardcoded credential placeholder",
            "description": "API_KEY retrieved from env but used directly in HTTP body"
        },
        {
            "id": "SCAN-002",
            "severity": "MEDIUM",
            "title": "Insecure subprocess usage",
            "description": "subprocess.run without timeout"
        }
    ]
}, indent=2))

# ── 3. Distractor files to simulate a real, messy workspace ───────────────────
# Old policy leftovers
old_dir = workspace / "archive" / "old-policies"
old_dir.mkdir(parents=True, exist_ok=True)
(old_dir / "staging_policy_v1.json").write_text(json.dumps({
    "name": "staging",
    "rules": ["no-critical-findings"],
    "deprecated": True
}))
(old_dir / "dev_policy_draft.txt").write_text("Rules to add later:\n- no-eval-exec\n- has-checksum\n")

# Fake previous compliance run artifacts
prev_compliance = workspace / "archive" / "compliance-run-2023"
prev_compliance.mkdir(parents=True, exist_ok=True)
(prev_compliance / "report_staging.json").write_text(json.dumps({
    "policy": "staging",
    "generated_at": "2023-11-01",
    "status": "outdated"
}))

# Skill inventory config
inventory_dir = workspace / "config"
inventory_dir.mkdir(parents=True, exist_ok=True)
(inventory_dir / "skill-inventory.yaml").write_text("""skills:
  - name: arc-payment-gateway
    version: 1.2.0
    environment: production
    owner: payments-team
  - name: arc-fraud-detector
    version: 0.9.1
    environment: staging
    owner: risk-team
""")
(inventory_dir / "deployment-targets.yaml").write_text("""environments:
  production:
    require_policy: fintech-prod
    auto_assess: true
  staging:
    require_policy: staging-basic
""")

# Some other random skill directories (distractors)
for skill_name in ["arc-fraud-detector", "arc-kyc-processor"]:
    d = Path.home() / ".openclaw" / "skills" / skill_name
    d.mkdir(parents=True, exist_ok=True)
    (d / "main.py").write_text(f'# {skill_name} placeholder\n')
    (d / "trust.json").write_text(json.dumps({"level": "UNKNOWN"}))

# Security notes (distractor)
notes_dir = workspace / "docs" / "security"
notes_dir.mkdir(parents=True, exist_ok=True)
(notes_dir / "security-notes.md").write_text("""# Security Notes

## Payment Gateway
- Requires network access to internal payment processor
- Shell validator binary is whitelisted by infosec
- Environment variables sourced from Vault at runtime

## Open Items
- Version pinning is tracked in ticket FIN-2847
""")
(notes_dir / "exemption-requests.txt").write_text("""Pending exemption requests:
- arc-payment-gateway: no-network-calls (approved by: alice.chen@fintech.io)
- arc-payment-gateway: no-shell-exec (disputed - see ticket FIN-2901)
""")

# Logs directory
logs_dir = workspace / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
(logs_dir / "scan-run-20240601.log").write_text("""[2024-06-01 08:00:01] Starting scan: arc-payment-gateway
[2024-06-01 08:00:03] Found 1 HIGH, 1 MEDIUM finding
[2024-06-01 08:00:03] Scan complete.
""")
(logs_dir / "deploy-audit-20240601.log").write_text("""[2024-06-01 09:00:00] Deploy attempt: arc-payment-gateway -> production
[2024-06-01 09:00:01] BLOCKED: No compliance assessment on record
""")

# CI/CD pipeline config (distractor)
cicd_dir = workspace / "ci"
cicd_dir.mkdir(parents=True, exist_ok=True)
(cicd_dir / "pipeline.yaml").write_text("""stages:
  - scan
  - trust-verify
  - compliance-check
  - deploy

compliance-check:
  script: python3 checker.py assess --skill $SKILL_NAME --policy fintech-prod
  allow_failure: false
""")

# Miscellaneous workspace files
(workspace / "TODO.txt").write_text("""TODO:
- Set up fintech-prod compliance policy
- Assess payment gateway before next sprint release
- Handle network access exception for payment gateway
- Close remediation ticket for shell exec pattern
- Generate compliance artifact for audit
""")
(workspace / "contacts.txt").write_text("""Security Approver: alice.chen@fintech.io  (alias: alice)
Payment Team Lead: bob.smith@fintech.io
Risk Officer: carol.jones@fintech.io
""")

print("Workspace generated successfully.")
print(f"Target skill located at: {target_skill_dir}")
print(f"Checker script located at: {checker_script}")