import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    """Find the risk report file."""
    workspace_path = Path(workspace)
    candidates = list(workspace_path.rglob("risk_report.md")) + \
                 list(workspace_path.rglob("risk_report.txt")) + \
                 list(workspace_path.rglob("risk_report.json"))
    if candidates:
        return candidates[0]
    return None

def load_report(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace").lower()
    except Exception as e:
        return ""

def check_section_structure(text: str) -> tuple[bool, str]:
    """Check for the required 6-section output format from SKILL.md."""
    required_sections = [
        (r"high.{0,20}risk", "High-risk findings section"),
        (r"medium.{0,20}risk", "Medium-risk findings section"),
        (r"low.{0,20}risk|low.{0,20}cleanup", "Low-risk/cleanup section"),
        (r"upgrad", "Packages worth upgrading section"),
        (r"remov|unnecessary|removable", "Packages that may be removable section"),
        (r"command|npm|bun|pnpm|yarn|fix|verify|run", "Exact commands section"),
    ]
    missing = []
    for pattern, name in required_sections:
        if not re.search(pattern, text):
            missing.append(name)
    if missing:
        return False, f"Missing sections: {', '.join(missing)}"
    return True, "All 6 required sections present"

def check_direct_vs_transitive(text: str) -> tuple[bool, str]:
    """Agent must distinguish direct from transitive deps."""
    has_direct = bool(re.search(r"\bdirect\b", text))
    has_transitive = bool(re.search(r"\btransitive\b", text))
    if has_direct and has_transitive:
        return True, "Distinguishes direct vs transitive dependencies"
    missing = []
    if not has_direct:
        missing.append("'direct'")
    if not has_transitive:
        missing.append("'transitive'")
    return False, f"Missing distinction keywords: {', '.join(missing)}"

def check_high_risk_findings(text: str) -> tuple[bool, str]:
    """Must identify the genuinely high-risk items."""
    # request is deprecated/abandoned, postinstall hook with curl is risky,
    # serialize-javascript 2.1.2 has known RCE, axios 0.21.1 has known vulns
    high_risk_expected = [
        (r"\brequest\b", "deprecated 'request' package"),
        (r"postinstall|post.install|hook", "risky postinstall hook"),
        (r"serialize.javascript|serialize_javascript", "serialize-javascript vulnerability"),
    ]
    found = []
    missing = []
    for pattern, name in high_risk_expected:
        if re.search(pattern, text):
            found.append(name)
        else:
            missing.append(name)
    if len(found) >= 2:
        return True, f"Identified high-risk items: {', '.join(found)}"
    return False, f"Missing high-risk findings: {', '.join(missing)} (found: {', '.join(found) or 'none'})"

def check_loose_semver(text: str) -> tuple[bool, str]:
    """Must flag overly broad semver ranges like '*'."""
    patterns = [r"\*.*lodash|lodash.*\*", r"\*.*colors|colors.*\*", r"broad|loose|wildcard|\bstar\b|\*"]
    for pat in patterns:
        if re.search(pat, text):
            return True, "Identifies overly broad/loose semver ranges (e.g., '*')"
    return False, "Does not flag overly broad semver ranges ('*' on lodash or colors)"

def check_duplicate_deps(text: str) -> tuple[bool, str]:
    """Must identify duplicated/overlapping dependencies across workspace packages."""
    patterns = [
        r"lodash.{0,60}underscore|underscore.{0,60}lodash",
        r"node.uuid.{0,60}uuid|uuid.{0,60}node.uuid",
        r"duplicat|overlap|redundant|both.*lodash|lodash.*both",
    ]
    for pat in patterns:
        if re.search(pat, text):
            return True, "Identifies duplicate/overlapping dependencies"
    # Check if lodash and underscore both mentioned in context of duplication
    if re.search(r"lodash", text) and re.search(r"underscore", text):
        return True, "Mentions both lodash and underscore (likely flagging duplication)"
    return False, "Does not identify duplicated or overlapping dependencies across workspace"

def check_stale_packages(text: str) -> tuple[bool, str]:
    """Must flag stale or outdated packages."""
    stale_expected = [
        (r"\bmoment\b", "moment.js (stale/maintenance mode)"),
        (r"validator.*5\.|5\.7|old.*validator|validator.*old|validator.*outdated|outdated.*validator", "validator 5.7.0 (very old)"),
        (r"winston.*2\.|2\.4|old.*winston|winston.*old|winston.*outdated|outdated.*winston", "winston 2.4.7 (very old)"),
        (r"react.scripts.*4|4\.0\.3|react.scripts.*old|old.*react.scripts", "react-scripts 4.0.3 (outdated CRA)"),
    ]
    found = []
    missing = []
    for pattern, name in stale_expected:
        if re.search(pattern, text):
            found.append(name)
        else:
            missing.append(name)
    if len(found) >= 2:
        return True, f"Identifies stale packages: {', '.join(found)}"
    return False, f"Insufficient stale package identification. Found: {', '.join(found) or 'none'}. Missing: {', '.join(missing)}"

def check_unnecessary_runtime_deps(text: str) -> tuple[bool, str]:
    """Must flag crypto (built-in node module) as unnecessary runtime dep."""
    if re.search(r"\bcrypto\b.{0,100}(built.in|native|node.built|unnecessary|should not|remove|built.in module)", text) or \
       re.search(r"(built.in|native|node.built|unnecessary).{0,100}\bcrypto\b", text):
        return True, "Flags 'crypto' as unnecessary (built-in Node module)"
    if re.search(r"\bcrypto\b", text):
        return True, "Mentions 'crypto' package (possibly flagged as unnecessary)"
    return False, "Does not identify 'crypto' as an unnecessary runtime dep (it's a built-in Node module)"

def check_audit_commands_used(text: str) -> tuple[bool, str]:
    """Must include actual audit/ls commands in the 'Exact commands' section."""
    commands_found = []
    if re.search(r"npm\s+(audit|ls)", text):
        commands_found.append("npm audit/ls")
    if re.search(r"bun\s+(audit|pm)", text):
        commands_found.append("bun audit/pm")
    if re.search(r"pnpm\s+(audit|ls)", text):
        commands_found.append("pnpm audit/ls")
    if commands_found:
        return True, f"Includes package manager commands: {', '.join(commands_found)}"
    return False, "No npm/bun/pnpm audit or ls commands found in report"

def check_node_sass_deprecated(text: str) -> tuple[bool, str]:
    """Must flag node-sass as deprecated (superseded by sass)."""
    if re.search(r"node.sass.{0,100}(deprecated|sass|supersed|replace|remove)", text) or \
       re.search(r"(deprecated|supersed).{0,100}node.sass", text):
        return True, "Flags node-sass as deprecated (superseded by sass)"
    if re.search(r"node.sass", text):
        return True, "Mentions node-sass (likely flagging as deprecated)"
    return False, "Does not flag node-sass as deprecated"

def check_axios_version(text: str) -> tuple[bool, str]:
    """Both packages use axios 0.21.1 — should flag for upgrade."""
    if re.search(r"axios.{0,60}(0\.21|old|outdated|vuln|upgrad)|((0\.21|old|outdated|vuln|upgrad).{0,60}axios)", text):
        return True, "Flags axios 0.21.1 as outdated/vulnerable"
    if re.search(r"\baxios\b", text):
        return True, "Mentions axios (possibly flagging version)"
    return False, "Does not flag axios 0.21.1 (outdated, known vulnerabilities)"

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            {"name": "argument", "passed": False, "detail": "No workspace path provided"}
        ]}))
        return

    workspace = sys.argv[1]
    report_path = find_report(workspace)

    checks = []

    # Check 0: Report file exists
    if report_path is None:
        checks.append({"name": "report_exists", "passed": False,
                        "detail": "risk_report.md/txt/json not found in workspace"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "report_exists", "passed": True,
                    "detail": f"Found report at {report_path}"})

    text = load_report(report_path)
    if not text.strip():
        checks.append({"name": "report_non_empty", "passed": False,
                        "detail": "Report file is empty or unreadable"})
        print(json.dumps({"passed": False, "score": 0.0, "checks": checks}))
        return

    checks.append({"name": "report_non_empty", "passed": True, "detail": "Report has content"})

    # Run all checks
    check_fns = [
        ("section_structure", check_section_structure),
        ("direct_vs_transitive", check_direct_vs_transitive),
        ("high_risk_findings", check_high_risk_findings),
        ("loose_semver_ranges", check_loose_semver),
        ("duplicate_dependencies", check_duplicate_deps),
        ("stale_packages", check_stale_packages),
        ("unnecessary_runtime_deps", check_unnecessary_runtime_deps),
        ("audit_commands_present", check_audit_commands_used),
        ("node_sass_deprecated", check_node_sass_deprecated),
        ("axios_version_flagged", check_axios_version),
    ]

    weights = {
        "section_structure": 2.0,       # Proprietary trap — must follow exact SKILL.md format
        "direct_vs_transitive": 1.5,    # Proprietary rule from SKILL.md review rules
        "high_risk_findings": 2.0,      # Core skill output
        "loose_semver_ranges": 1.5,     # Specific SKILL.md workflow step 4
        "duplicate_dependencies": 1.5,  # Specific SKILL.md workflow step 4
        "stale_packages": 1.5,          # Specific SKILL.md workflow step 4
        "unnecessary_runtime_deps": 1.0,
        "audit_commands_present": 1.0,  # SKILL.md mandates running audit commands
        "node_sass_deprecated": 0.75,
        "axios_version_flagged": 0.75,
    }

    total_weight = sum(weights.values())
    earned_weight = 0.0

    for name, fn in check_fns:
        try:
            passed, detail = fn(text)
        except Exception as e:
            passed, detail = False, f"Check error: {e}"
        checks.append({"name": name, "passed": passed, "detail": detail})
        if passed:
            earned_weight += weights.get(name, 1.0)

    score = round(earned_weight / total_weight, 4)

    # Must pass section_structure AND at least 6 other checks to pass overall
    structure_passed = any(c["name"] == "section_structure" and c["passed"] for c in checks)
    passed_count = sum(1 for c in checks if c["passed"])
    overall_passed = structure_passed and passed_count >= 8 and score >= 0.65

    print(json.dumps({
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }, indent=2))

if __name__ == "__main__":
    main()