import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    total_score = 0.0

    # Find the review file
    review_file = None
    candidates = list(Path(workspace).rglob("code_review_report.md"))
    if candidates:
        review_file = candidates[0]

    # CHECK 0: File exists
    if not review_file or not review_file.exists():
        checks.append({"name": "review_file_exists", "passed": False, "detail": "code_review_report.md not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    try:
        content = review_file.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "review_file_readable", "passed": False, "detail": f"Could not read file: {e}"})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "review_file_exists", "passed": True, "detail": f"Found at {review_file}"})
    total_score += 0.05

    # CHECK 1: Correct top-level template structure (proprietary format from SKILL.md)
    # Must have "## Code Review Summary"
    has_summary_header = bool(re.search(r'##\s+Code Review Summary', content))
    checks.append({
        "name": "template_code_review_summary_header",
        "passed": has_summary_header,
        "detail": "Must contain '## Code Review Summary' header per the review template"
    })
    if has_summary_header:
        total_score += 0.05

    # CHECK 2: Must have Overall Assessment line in bold
    has_overall_assessment = bool(re.search(r'\*\*Overall Assessment\*\*\s*:', content))
    checks.append({
        "name": "template_overall_assessment",
        "passed": has_overall_assessment,
        "detail": "Must contain '**Overall Assessment**: [...]' line per the review template"
    })
    if has_overall_assessment:
        total_score += 0.05

    # CHECK 3: Must have 🔴 Critical Issues section
    has_critical = bool(re.search(r'###\s+🔴\s+Critical Issues', content))
    checks.append({
        "name": "template_critical_issues_section",
        "passed": has_critical,
        "detail": "Must contain '### 🔴 Critical Issues' section per the review template"
    })
    if has_critical:
        total_score += 0.05

    # CHECK 4: Must have 🟡 Improvements Suggested section
    has_improvements = bool(re.search(r'###\s+🟡\s+Improvements Suggested', content))
    checks.append({
        "name": "template_improvements_section",
        "passed": has_improvements,
        "detail": "Must contain '### 🟡 Improvements Suggested' section per the review template"
    })
    if has_improvements:
        total_score += 0.05

    # CHECK 5: Must have 🟢 Positive Aspects section
    has_positive = bool(re.search(r'###\s+🟢\s+Positive Aspects', content))
    checks.append({
        "name": "template_positive_aspects_section",
        "passed": has_positive,
        "detail": "Must contain '### 🟢 Positive Aspects' section per the review template"
    })
    if has_positive:
        total_score += 0.05

    # CHECK 6: Must have 📝 Additional Notes section
    has_notes = bool(re.search(r'###\s+📝\s+Additional Notes', content))
    checks.append({
        "name": "template_additional_notes_section",
        "passed": has_notes,
        "detail": "Must contain '### 📝 Additional Notes' section per the review template"
    })
    if has_notes:
        total_score += 0.05

    # ---- SECURITY CHECKS ----

    # CHECK 7: SQL injection identified (the f-string query pattern)
    sql_injection_mentioned = bool(re.search(
        r'sql\s*inject',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "security_sql_injection_identified",
        "passed": sql_injection_mentioned,
        "detail": "Must identify SQL injection vulnerabilities in user_controller.py"
    })
    if sql_injection_mentioned:
        total_score += 0.10

    # CHECK 8: user_controller.py mentioned with line reference for SQL issue
    user_ctrl_referenced = bool(re.search(r'user_controller\.py', content))
    checks.append({
        "name": "security_references_user_controller_file",
        "passed": user_ctrl_referenced,
        "detail": "Review must reference user_controller.py for security issues"
    })
    if user_ctrl_referenced:
        total_score += 0.05

    # CHECK 9: Hardcoded credentials identified (DB_PASSWORD, SECRET_KEY)
    hardcoded_creds = bool(re.search(
        r'(hardcoded|hard-coded|hardcoded credential|hard.coded.secret|secret.key|DB_PASSWORD|SECRET_KEY)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "security_hardcoded_credentials_identified",
        "passed": hardcoded_creds,
        "detail": "Must identify hardcoded credentials (DB_PASSWORD, SECRET_KEY) in user_controller.py"
    })
    if hardcoded_creds:
        total_score += 0.08

    # CHECK 10: Sensitive data logging identified (password logged in plain text)
    sensitive_logging = bool(re.search(
        r'(log(g(ing|ed)?)?.*password|password.*log(g(ing|ed)?)?|sensitive.*log|log.*sensitive)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "security_sensitive_data_logging_identified",
        "passed": sensitive_logging,
        "detail": "Must identify that passwords are being logged in plain text in update_user_password()"
    })
    if sensitive_logging:
        total_score += 0.07

    # ---- PERFORMANCE CHECKS ----

    # CHECK 11: N+1 query problem identified
    n_plus_one = bool(re.search(
        r'(n\+1|n \+ 1|n-plus-one|n\+1 query|query.*loop|loop.*quer)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "performance_n_plus_one_identified",
        "passed": n_plus_one,
        "detail": "Must identify N+1 query problem in get_transactions_for_user()"
    })
    if n_plus_one:
        total_score += 0.08

    # CHECK 12: String concatenation in loop identified (JS paymentService or Python)
    string_concat = bool(re.search(
        r'(string.concat(enat(e|ion))?.*loop|loop.*string.concat|inefficient.*string|O\(n.{0,5}2\)|quadratic)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "performance_string_concat_in_loop_identified",
        "passed": string_concat,
        "detail": "Must identify inefficient string concatenation in loops (buildTransactionReport or processRefunds in paymentService.js)"
    })
    if string_concat:
        total_score += 0.07

    # CHECK 13: paymentService.js referenced
    payment_svc_referenced = bool(re.search(r'paymentService\.js', content))
    checks.append({
        "name": "performance_references_payment_service_file",
        "passed": payment_svc_referenced,
        "detail": "Review must reference paymentService.js for performance/style issues"
    })
    if payment_svc_referenced:
        total_score += 0.05

    # ---- CODE STYLE CHECKS ----

    # CHECK 14: var usage identified (JS should use const/let)
    var_usage = bool(re.search(
        r'(var\s|use\s+const|use\s+let|avoid.*\bvar\b|\bvar\b.*avoid|const.*let.*instead|replace.*var)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "style_var_usage_identified",
        "passed": var_usage,
        "detail": "Must flag use of 'var' in paymentService.js - JS skill requires const/let"
    })
    if var_usage:
        total_score += 0.05

    # CHECK 15: Mutable default argument (items=[]) identified
    mutable_default = bool(re.search(
        r'(mutable.default|default.arg(ument)?.*list|list.*default.arg|mutable.*arg|\[\]\s*as\s*default|\[\]\s*default\s*param)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "style_mutable_default_argument_identified",
        "passed": mutable_default,
        "detail": "Must identify mutable default argument 'items=[]' in process_payment() - Python-specific anti-pattern"
    })
    if mutable_default:
        total_score += 0.05

    # CHECK 16: Callback hell / deep nesting identified in submitPayment
    callback_hell = bool(re.search(
        r'(callback.hell|deep.nest(ing)?|nest(ing|ed).callback|pyramid.of.doom|avoid.*callback)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "style_callback_hell_identified",
        "passed": callback_hell,
        "detail": "Must identify callback hell in submitPayment() in paymentService.js"
    })
    if callback_hell:
        total_score += 0.05

    # ---- TEST QUALITY CHECKS ----

    # CHECK 17: Poor test quality identified (meaningless tests, no assertions)
    test_quality = bool(re.search(
        r'(test.*meaningless|meaningless.*test|test.*not.*test(ing)?|poor.*test|test quality|test.*assertion|no.*assertion|weak.*test|test_1|test.*smoke)',
        content, re.IGNORECASE
    ))
    checks.append({
        "name": "testing_poor_test_quality_identified",
        "passed": test_quality,
        "detail": "Must flag poor test quality in test_user_controller.py (meaningless tests, no real assertions)"
    })
    if test_quality:
        total_score += 0.05

    # ---- IN CRITICAL SECTION ----
    # CHECK 18: At least 2 issues appear under the 🔴 Critical Issues section
    critical_section_match = re.search(
        r'###\s+🔴\s+Critical Issues(.*?)(?=###\s+🟡|###\s+🟢|###\s+📝|$)',
        content, re.DOTALL
    )
    critical_section_content = critical_section_match.group(1) if critical_section_match else ""
    # Count bullet points in critical section
    critical_bullets = re.findall(r'^\s*[-*]\s+.+', critical_section_content, re.MULTILINE)
    has_enough_critical = len(critical_bullets) >= 2
    checks.append({
        "name": "critical_section_has_multiple_issues",
        "passed": has_enough_critical,
        "detail": f"Critical Issues section must list at least 2 issues (found {len(critical_bullets)} bullet points)"
    })
    if has_enough_critical:
        total_score += 0.05

    # Final determination
    # Must pass: file exists, correct template structure, at least 1 security + 1 performance + overall structure
    mandatory_checks = [
        "review_file_exists",
        "template_code_review_summary_header",
        "template_critical_issues_section",
        "template_improvements_section",
        "security_sql_injection_identified",
        "security_hardcoded_credentials_identified",
        "performance_n_plus_one_identified",
    ]

    mandatory_results = {c["name"]: c["passed"] for c in checks}
    all_mandatory_pass = all(mandatory_results.get(name, False) for name in mandatory_checks)

    final_score = round(min(total_score, 1.0), 3)
    passed = all_mandatory_pass and final_score >= 0.55

    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2, ensure_ascii=False))