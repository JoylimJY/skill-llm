import sys
import json
import re
from pathlib import Path

workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")

checks = []

def make_check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

# --- Find the two expected output files ---
# Report 1: Bugcrowd IDOR report
bugcrowd_report_path = list(workspace.rglob("bugcrowd_idor_report.md"))
# Report 2: HackerOne SQLi report
hackerone_report_path = list(workspace.rglob("hackerone_sqli_report.md"))

# Check 1: Bugcrowd IDOR report file exists
bugcrowd_file = bugcrowd_report_path[0] if bugcrowd_report_path else None
checks.append(make_check(
    "bugcrowd_idor_report_exists",
    bool(bugcrowd_file),
    f"Found at {bugcrowd_file}" if bugcrowd_file else "File bugcrowd_idor_report.md not found anywhere in workspace"
))

# Check 2: HackerOne SQLi report file exists
hackerone_file = hackerone_report_path[0] if hackerone_report_path else None
checks.append(make_check(
    "hackerone_sqli_report_exists",
    bool(hackerone_file),
    f"Found at {hackerone_file}" if hackerone_file else "File hackerone_sqli_report.md not found anywhere in workspace"
))

# ---- Parse and validate Bugcrowd IDOR report ----
bugcrowd_content = ""
if bugcrowd_file:
    try:
        bugcrowd_content = bugcrowd_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(make_check("bugcrowd_report_readable", False, f"Could not read file: {e}"))
        bugcrowd_content = ""

# Check 3: Bugcrowd report mentions 'bugcrowd' (platform-specific formatting)
bc_platform = bool(re.search(r'bugcrowd', bugcrowd_content, re.IGNORECASE))
checks.append(make_check(
    "bugcrowd_report_platform_marker",
    bc_platform,
    "Report contains 'bugcrowd' platform identifier" if bc_platform else "No 'bugcrowd' marker found in report"
))

# Check 4: Bugcrowd report has CWE reference (IDOR -> CWE-639 or CWE-284 or similar)
bc_cwe = bool(re.search(r'CWE-\d+', bugcrowd_content, re.IGNORECASE))
checks.append(make_check(
    "bugcrowd_report_cwe_mapping",
    bc_cwe,
    f"CWE reference found in bugcrowd report" if bc_cwe else "No CWE-XXX reference found in bugcrowd IDOR report — auto-mapping may not have triggered"
))

# Check 5: Bugcrowd report has Steps to Reproduce section
bc_steps = bool(re.search(r'steps?\s+to\s+reproduce', bugcrowd_content, re.IGNORECASE))
checks.append(make_check(
    "bugcrowd_report_has_repro_steps",
    bc_steps,
    "Steps to Reproduce section found" if bc_steps else "Missing 'Steps to Reproduce' section in bugcrowd report"
))

# Check 6: Bugcrowd report has Impact section
bc_impact = bool(re.search(r'##?\s*impact', bugcrowd_content, re.IGNORECASE))
checks.append(make_check(
    "bugcrowd_report_has_impact",
    bc_impact,
    "Impact section found" if bc_impact else "Missing 'Impact' section in bugcrowd report"
))

# Check 7: Bugcrowd report severity is 'high'
bc_severity = bool(re.search(r'high', bugcrowd_content, re.IGNORECASE))
checks.append(make_check(
    "bugcrowd_report_severity_high",
    bc_severity,
    "Severity 'high' referenced in bugcrowd report" if bc_severity else "Severity 'high' not found in bugcrowd report"
))

# Check 8: Bugcrowd report target domain
bc_target = bool(re.search(r'payments\.fintech-corp\.io', bugcrowd_content, re.IGNORECASE))
checks.append(make_check(
    "bugcrowd_report_target_domain",
    bc_target,
    "Target domain 'payments.fintech-corp.io' found in bugcrowd report" if bc_target else "Target domain not found in bugcrowd report"
))

# ---- Parse and validate HackerOne SQLi report ----
hackerone_content = ""
if hackerone_file:
    try:
        hackerone_content = hackerone_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append(make_check("hackerone_report_readable", False, f"Could not read file: {e}"))
        hackerone_content = ""

# Check 9: HackerOne report mentions 'hackerone' (platform-specific formatting)
h1_platform = bool(re.search(r'hackerone', hackerone_content, re.IGNORECASE))
checks.append(make_check(
    "hackerone_report_platform_marker",
    h1_platform,
    "Report contains 'hackerone' platform identifier" if h1_platform else "No 'hackerone' marker found in report"
))

# Check 10: HackerOne report has CWE reference (SQLi -> CWE-89)
h1_cwe = bool(re.search(r'CWE-\d+', hackerone_content, re.IGNORECASE))
checks.append(make_check(
    "hackerone_report_cwe_mapping",
    h1_cwe,
    "CWE reference found in HackerOne report" if h1_cwe else "No CWE-XXX reference found in HackerOne SQLi report — auto-mapping may not have triggered"
))

# Check 11: HackerOne report has Steps to Reproduce section
h1_steps = bool(re.search(r'steps?\s+to\s+reproduce', hackerone_content, re.IGNORECASE))
checks.append(make_check(
    "hackerone_report_has_repro_steps",
    h1_steps,
    "Steps to Reproduce section found" if h1_steps else "Missing 'Steps to Reproduce' section in HackerOne report"
))

# Check 12: HackerOne report has Remediation section
h1_remediation = bool(re.search(r'##?\s*remediation', hackerone_content, re.IGNORECASE))
checks.append(make_check(
    "hackerone_report_has_remediation",
    h1_remediation,
    "Remediation section found" if h1_remediation else "Missing 'Remediation' section in HackerOne report"
))

# Check 13: HackerOne report severity is 'critical'
h1_severity = bool(re.search(r'critical', hackerone_content, re.IGNORECASE))
checks.append(make_check(
    "hackerone_report_severity_critical",
    h1_severity,
    "Severity 'critical' referenced in HackerOne report" if h1_severity else "Severity 'critical' not found in HackerOne report"
))

# Check 14: HackerOne report target domain
h1_target = bool(re.search(r'api\.fintech-corp\.io', hackerone_content, re.IGNORECASE))
checks.append(make_check(
    "hackerone_report_target_domain",
    h1_target,
    "Target domain 'api.fintech-corp.io' found in HackerOne report" if h1_target else "Target domain not found in HackerOne report"
))

# Check 15: HackerOne report has a title containing sql or injection (from --title flag)
h1_title = bool(re.search(r'sql\s*inject|sql injection|sqli', hackerone_content, re.IGNORECASE))
checks.append(make_check(
    "hackerone_report_title_mentions_sqli",
    h1_title,
    "Title/content references SQL injection" if h1_title else "Report does not appear to reference SQL Injection in title/content"
))

# --- Compute score ---
total = len(checks)
passed_count = sum(1 for c in checks if c["passed"])
score = round(passed_count / total, 4) if total > 0 else 0.0
overall_passed = passed_count >= int(total * 0.85)  # 85% threshold

result = {
    "passed": overall_passed,
    "score": score,
    "checks": checks
}

print(json.dumps(result, indent=2))