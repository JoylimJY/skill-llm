import sys
import os
import json
import re
from pathlib import Path

def find_report(workspace):
    """Search for the dependency health report file."""
    candidates = list(Path(workspace).rglob("dependency_health_report.md"))
    if not candidates:
        return None
    # Prefer root-level
    for c in candidates:
        if c.parent == Path(workspace):
            return c
    return candidates[0]

def check_section(content, pattern, name):
    found = bool(re.search(pattern, content, re.IGNORECASE))
    return found

def run_eval(workspace):
    checks = []
    score = 0.0

    # ---- Check 1: Report file exists ----
    report_path = find_report(workspace)
    file_exists = report_path is not None
    checks.append({
        "name": "Report file 'dependency_health_report.md' exists",
        "passed": file_exists,
        "detail": str(report_path) if file_exists else "File not found anywhere in workspace"
    })

    if not file_exists:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        content = report_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        checks.append({"name": "Report file readable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "Report file readable", "passed": True, "detail": f"Read {len(content)} chars"})

    # ---- Check 2: Both ecosystems covered ----
    has_node = bool(re.search(r'(node\.?js|npm|finpay-api)', content, re.IGNORECASE))
    has_python = bool(re.search(r'(python|pip|requirements)', content, re.IGNORECASE))

    checks.append({
        "name": "Covers Node.js ecosystem",
        "passed": has_node,
        "detail": "Found Node.js/npm reference in report" if has_node else "No Node.js ecosystem mention found"
    })
    checks.append({
        "name": "Covers Python ecosystem",
        "passed": has_python,
        "detail": "Found Python/pip reference in report" if has_python else "No Python ecosystem mention found"
    })

    # ---- Check 3: Priority tier emojis/sections present ----
    has_critical_red = bool(re.search(r'🔴', content))
    has_high_orange = bool(re.search(r'🟠', content))
    has_medium_yellow = bool(re.search(r'🟡', content))
    has_low_green = bool(re.search(r'🟢', content))

    checks.append({
        "name": "🔴 Critical/Security tier present",
        "passed": has_critical_red,
        "detail": "Found 🔴 emoji in report" if has_critical_red else "Missing 🔴 Critical tier"
    })
    checks.append({
        "name": "🟠 High/Breaking tier present",
        "passed": has_high_orange,
        "detail": "Found 🟠 emoji in report" if has_high_orange else "Missing 🟠 High tier"
    })
    checks.append({
        "name": "🟡 Medium/Minor-Patch tier present",
        "passed": has_medium_yellow,
        "detail": "Found 🟡 emoji in report" if has_medium_yellow else "Missing 🟡 Medium tier"
    })
    checks.append({
        "name": "🟢 Low/Unused tier present",
        "passed": has_low_green,
        "detail": "Found 🟢 emoji in report" if has_low_green else "Missing 🟢 Low/Unused tier"
    })

    # ---- Check 4: Security vulnerabilities section mentions specific vulnerable packages ----
    # lodash 4.17.19, requests 2.20.0, pillow 8.0.0, or cryptography 2.8 are all vulnerable
    known_vuln_packages = ["lodash", "requests", "pillow", "cryptography", "axios", "jsonwebtoken", "pyyaml"]
    vuln_mentioned = [pkg for pkg in known_vuln_packages if re.search(pkg, content, re.IGNORECASE)]
    has_vuln_packages = len(vuln_mentioned) >= 1

    checks.append({
        "name": "Security section mentions at least one known vulnerable package",
        "passed": has_vuln_packages,
        "detail": f"Found vulnerable packages: {vuln_mentioned}" if has_vuln_packages else "No known vulnerable packages mentioned in security section"
    })

    # ---- Check 5: Unused dependencies identified ----
    # moment (Node.js) and/or flask/pillow (Python) should appear as unused
    unused_candidates = ["moment", "flask", "pillow"]
    unused_mentioned = [pkg for pkg in unused_candidates if re.search(pkg, content, re.IGNORECASE)]
    has_unused = len(unused_mentioned) >= 1

    checks.append({
        "name": "Unused dependencies section identifies at least one unused package",
        "passed": has_unused,
        "detail": f"Found unused packages mentioned: {unused_mentioned}" if has_unused else "No unused packages (moment/flask/pillow) mentioned"
    })

    # ---- Check 6: Update/fix commands provided ----
    # Should have copy-pasteable commands
    has_commands = bool(re.search(r'`(npm|pip|pip3)\s+(install|audit|update|uninstall)', content))
    checks.append({
        "name": "Actionable update/fix commands provided",
        "passed": has_commands,
        "detail": "Found copy-pasteable npm/pip commands" if has_commands else "No actionable commands found"
    })

    # ---- Check 7: Summary table with counts ----
    # Must have the summary table with category/count columns
    has_summary_table = bool(re.search(
        r'\|\s*(category|Category|🔴|Security|vulnerabilities).*\|.*\n.*\|[-\s|]+\|.*\n.*\|\s*\S',
        content, re.IGNORECASE | re.MULTILINE
    ))
    # Looser check: any table with "count" or numeric values near category keywords
    has_summary_loose = bool(re.search(
        r'(Security vulnerabilities|Major updates|Minor.*updates|Unused|Up-to-date)',
        content, re.IGNORECASE
    ))
    has_summary = has_summary_table or has_summary_loose

    checks.append({
        "name": "Output summary table with category counts present",
        "passed": has_summary,
        "detail": "Found summary table with categories" if has_summary else "No summary table with category/count structure found"
    })

    # ---- Check 8: Outdated packages section ----
    has_outdated = bool(re.search(
        r'(outdated|latest|current|update available)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "Outdated packages section present",
        "passed": has_outdated,
        "detail": "Found outdated package references" if has_outdated else "No outdated package information found"
    })

    # ---- Check 9: Report header / project name ----
    has_header = bool(re.search(
        r'(Dependency Health Report|dependency.*health|health.*report)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "Report has a proper header/title",
        "passed": has_header,
        "detail": "Found report header" if has_header else "No report header/title found"
    })

    # ---- Check 10: Safe update commands section ----
    has_safe_cmds = bool(re.search(
        r'(npm audit fix|pip install --upgrade|pip3 install --upgrade)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "Safe bulk update commands present (npm audit fix / pip install --upgrade)",
        "passed": has_safe_cmds,
        "detail": "Found safe batch update commands" if has_safe_cmds else "Missing safe update commands like 'npm audit fix' or 'pip install --upgrade'"
    })

    # ---- Scoring ----
    # Weights: critical checks get higher weight
    weights = {
        0: 0.05,   # file exists
        1: 0.02,   # readable
        2: 0.08,   # node coverage
        3: 0.08,   # python coverage
        4: 0.10,   # 🔴 tier
        5: 0.08,   # 🟠 tier
        6: 0.08,   # 🟡 tier
        7: 0.10,   # 🟢 tier (unused)
        8: 0.08,   # vuln packages
        9: 0.10,   # unused packages
        10: 0.05,  # commands
        11: 0.05,  # summary table
        12: 0.05,  # outdated
        13: 0.03,  # header
        14: 0.05,  # safe cmds
    }

    total_score = 0.0
    for i, check in enumerate(checks):
        w = weights.get(i, 0.0)
        if check["passed"]:
            total_score += w

    # Must pass minimum critical checks
    critical_passed = all(
        checks[i]["passed"] for i in [0, 1, 2, 3, 4, 7, 9]
    )

    return {
        "passed": critical_passed and total_score >= 0.65,
        "score": round(total_score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))