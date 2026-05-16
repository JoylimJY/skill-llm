import sys
import json
import re
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    """Search for dependency_health_report.md anywhere in workspace."""
    candidates = list(Path(workspace).rglob("dependency_health_report.md"))
    if candidates:
        return candidates[0]
    return None

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str) -> dict:
    checks = []

    # ── Locate report ────────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        checks.append(check("report_file_exists", False, "dependency_health_report.md not found anywhere in workspace"))
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append(check("report_file_exists", True, f"Found at {report_path}"))

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(check("report_readable", False, f"Could not read file: {e}"))
        return {"passed": False, "score": 0.0, "checks": checks}

    content_lower = content.lower()

    # ── CHECK 1: Both ecosystems covered ─────────────────────────────────────
    has_nodejs = any(kw in content_lower for kw in ["node.js", "nodejs", "npm", "api-gateway", "api gateway"])
    has_python = any(kw in content_lower for kw in ["python", "pip", "risk-scorer", "risk scorer"])
    checks.append(check(
        "covers_nodejs_ecosystem",
        has_nodejs,
        "Report mentions Node.js/npm ecosystem" if has_nodejs else "No mention of Node.js/npm ecosystem"
    ))
    checks.append(check(
        "covers_python_ecosystem",
        has_python,
        "Report mentions Python/pip ecosystem" if has_python else "No mention of Python/pip ecosystem"
    ))

    # ── CHECK 2: Security tier present (🔴 Critical) ──────────────────────────
    has_critical_tier = "🔴" in content or "critical" in content_lower
    checks.append(check(
        "critical_security_tier_present",
        has_critical_tier,
        "🔴 Critical security tier found" if has_critical_tier else "Missing 🔴 Critical security tier"
    ))

    # Specific known vulnerable packages mentioned
    has_lodash_vuln = "lodash" in content_lower
    has_crypto_vuln = "cryptography" in content_lower
    checks.append(check(
        "vulnerable_lodash_mentioned",
        has_lodash_vuln,
        "lodash vulnerability mentioned" if has_lodash_vuln else "lodash not mentioned in security section"
    ))
    checks.append(check(
        "vulnerable_cryptography_mentioned",
        has_crypto_vuln,
        "cryptography vulnerability mentioned" if has_crypto_vuln else "cryptography package not mentioned"
    ))

    # ── CHECK 3: High tier for major/breaking updates (🟠) ───────────────────
    has_high_tier = "🟠" in content or ("high" in content_lower and "breaking" in content_lower)
    checks.append(check(
        "high_breaking_updates_tier_present",
        has_high_tier,
        "🟠 High/breaking updates tier found" if has_high_tier else "Missing 🟠 High breaking-updates tier"
    ))

    # express major version or flask major version should appear here
    has_express_major = "express" in content_lower and any(
        v in content for v in ["5.0", "5.x"]
    )
    has_flask_major = "flask" in content_lower and any(
        v in content for v in ["3.0", "3.x"]
    )
    breaking_packages_ok = has_express_major or has_flask_major
    checks.append(check(
        "breaking_update_packages_identified",
        breaking_packages_ok,
        f"Major version updates identified (express@5.x={has_express_major}, flask@3.x={has_flask_major})"
        if breaking_packages_ok
        else "No major-version breaking updates (express@5 or flask@3) identified in high tier"
    ))

    # ── CHECK 4: Medium/Minor tier (🟡) ──────────────────────────────────────
    has_medium_tier = "🟡" in content or "minor" in content_lower or "patch" in content_lower
    checks.append(check(
        "medium_minor_updates_tier_present",
        has_medium_tier,
        "🟡 Medium/minor updates tier found" if has_medium_tier else "Missing 🟡 medium updates tier"
    ))

    # axios or numpy or scikit-learn or requests should appear as minor updates
    minor_packages = ["axios", "numpy", "scikit-learn", "sklearn", "requests"]
    found_minor = [p for p in minor_packages if p in content_lower]
    has_minor_packages = len(found_minor) >= 1
    checks.append(check(
        "minor_update_packages_listed",
        has_minor_packages,
        f"Minor update packages found: {found_minor}" if has_minor_packages else "No minor-update packages listed"
    ))

    # ── CHECK 5: Unused dependencies tier (🟢) ───────────────────────────────
    has_unused_tier = "🟢" in content or "unused" in content_lower
    checks.append(check(
        "unused_dependencies_tier_present",
        has_unused_tier,
        "🟢 Unused dependencies tier found" if has_unused_tier else "Missing 🟢 unused dependencies tier"
    ))

    # moment (Node) and/or pandas (Python) should be flagged as unused
    moment_unused = "moment" in content_lower and ("unused" in content_lower or "uninstall" in content_lower or "🟢" in content)
    pandas_unused = "pandas" in content_lower and ("unused" in content_lower or "uninstall" in content_lower or "🟢" in content)
    unused_packages_ok = moment_unused or pandas_unused
    checks.append(check(
        "specific_unused_packages_identified",
        unused_packages_ok,
        f"Unused packages identified (moment={moment_unused}, pandas={pandas_unused})"
        if unused_packages_ok
        else "Neither 'moment' nor 'pandas' identified as unused"
    ))

    # ── CHECK 6: Summary table ────────────────────────────────────────────────
    has_summary_table = (
        ("| category" in content_lower or "| count" in content_lower or
         ("---" in content and "|" in content and "security" in content_lower))
    )
    checks.append(check(
        "summary_table_present",
        has_summary_table,
        "Summary table with category/count columns found" if has_summary_table else "No summary table detected"
    ))

    # ── CHECK 7: Safe update commands provided ────────────────────────────────
    has_update_commands = any(cmd in content for cmd in [
        "npm audit fix", "npm update", "npm install", "pip install --upgrade",
        "pip install", "npm uninstall"
    ])
    checks.append(check(
        "safe_update_commands_provided",
        has_update_commands,
        "Copy-pasteable update commands found" if has_update_commands else "No update commands provided"
    ))

    # ── CHECK 8: Report quality — minimum length ──────────────────────────────
    word_count = len(content.split())
    sufficient_length = word_count >= 150
    checks.append(check(
        "report_minimum_length",
        sufficient_length,
        f"Report has {word_count} words (≥150 required)" if sufficient_length
        else f"Report too short: {word_count} words (<150)"
    ))

    # ── CHECK 9: Both fix versions mentioned (lodash fix + cryptography fix) ──
    lodash_fix = bool(re.search(r"lodash[^\n]*4\.17\.21|4\.17\.21[^\n]*lodash", content_lower))
    crypto_fix = bool(re.search(r"cryptography[^\n]*41\.|41\.[^\n]*cryptography", content_lower))
    fix_versions_ok = lodash_fix or crypto_fix
    checks.append(check(
        "fix_versions_specified",
        fix_versions_ok,
        f"Fix versions specified (lodash@4.17.21={lodash_fix}, cryptography@41.x={crypto_fix})"
        if fix_versions_ok
        else "No specific fix versions mentioned for vulnerable packages"
    ))

    # ── Score calculation ─────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])

    # Mandatory checks that must pass for overall pass
    mandatory = [
        "report_file_exists",
        "covers_nodejs_ecosystem",
        "covers_python_ecosystem",
        "critical_security_tier_present",
        "high_breaking_updates_tier_present",
        "unused_dependencies_tier_present",
        "specific_unused_packages_identified",
    ]
    mandatory_passed = all(
        c["passed"] for c in checks if c["name"] in mandatory
    )

    score = round(passed_count / total, 3)
    overall_passed = mandatory_passed and score >= 0.65

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))