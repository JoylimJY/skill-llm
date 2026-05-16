import sys
import json
import os
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    score = 0.0

    # --- Find the diagnosis report file ---
    # The agent is asked to produce 'expense_diagnosis_report.md'
    report_path = None
    for candidate in Path(workspace).rglob("expense_diagnosis_report.md"):
        report_path = candidate
        break

    if report_path is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "expense_diagnosis_report.md not found anywhere in workspace."}]
        }

    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {report_path}"})
    score += 0.05

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": score,
            "checks": checks + [{"name": "file_readable", "passed": False, "detail": str(e)}]
        }

    content_lower = content.lower()

    # -------------------------------------------------------
    # CHECK 1: DIAGNOSIS SECTION EXISTS
    # -------------------------------------------------------
    has_diagnosis_section = bool(re.search(r'#+\s*diagnosis', content_lower))
    checks.append({
        "name": "has_diagnosis_section",
        "passed": has_diagnosis_section,
        "detail": "Report must contain a '### Diagnosis' section per SKILL.md output shape."
    })
    if has_diagnosis_section:
        score += 0.10

    # -------------------------------------------------------
    # CHECK 2: RECOMMENDATION SECTION EXISTS
    # -------------------------------------------------------
    has_recommendation_section = bool(re.search(r'#+\s*recommendation', content_lower))
    checks.append({
        "name": "has_recommendation_section",
        "passed": has_recommendation_section,
        "detail": "Report must contain a '### Recommendation' section per SKILL.md output shape."
    })
    if has_recommendation_section:
        score += 0.10

    # -------------------------------------------------------
    # CHECK 3: EXECUTION SECTION EXISTS
    # -------------------------------------------------------
    has_execution_section = bool(re.search(r'#+\s*execution', content_lower))
    checks.append({
        "name": "has_execution_section",
        "passed": has_execution_section,
        "detail": "Report must contain an '### Execution' section per SKILL.md output shape."
    })
    if has_execution_section:
        score += 0.10

    # -------------------------------------------------------
    # CHECK 4: COMPATIBILITY SECTION EXISTS
    # -------------------------------------------------------
    has_compatibility_section = bool(re.search(r'#+\s*compatibility', content_lower))
    checks.append({
        "name": "has_compatibility_section",
        "passed": has_compatibility_section,
        "detail": "Report must contain a '### Compatibility' section per SKILL.md output shape."
    })
    if has_compatibility_section:
        score += 0.08

    # -------------------------------------------------------
    # CHECK 5: NOTES SECTION EXISTS
    # -------------------------------------------------------
    has_notes_section = bool(re.search(r'#+\s*notes', content_lower))
    checks.append({
        "name": "has_notes_section",
        "passed": has_notes_section,
        "detail": "Report must contain a '### Notes' section per SKILL.md output shape."
    })
    if has_notes_section:
        score += 0.07

    # -------------------------------------------------------
    # CHECK 6: IDENTIFIES DUPLICATE ROWS
    # Must call out that EMP-001 and EMP-005 appear duplicated
    # -------------------------------------------------------
    mentions_duplicates = bool(
        re.search(r'duplic', content_lower) or
        re.search(r'emp-001', content_lower) or
        re.search(r'emp-005', content_lower)
    )
    checks.append({
        "name": "identifies_duplicates",
        "passed": mentions_duplicates,
        "detail": "Diagnosis must identify duplicate rows (EMP-001 row repeated, EMP-005 duplicate). Should mention 'duplicat' or the specific employee IDs."
    })
    if mentions_duplicates:
        score += 0.08

    # -------------------------------------------------------
    # CHECK 7: IDENTIFIES MIXED DATE FORMATS
    # The CSV has dates in multiple formats: YYYY-MM-DD, DD/MM/YYYY, MM-DD-YYYY, "Month DD, YYYY", YYYY/MM/DD, DD-MM-YYYY
    # -------------------------------------------------------
    mentions_date_issues = bool(
        re.search(r'date', content_lower) and
        (re.search(r'format', content_lower) or re.search(r'inconsist', content_lower) or
         re.search(r'mixed', content_lower) or re.search(r'clean', content_lower) or
         re.search(r'standar', content_lower))
    )
    checks.append({
        "name": "identifies_mixed_date_formats",
        "passed": mentions_date_issues,
        "detail": "Diagnosis must call out mixed/inconsistent date formats in Submission Date and Expense Date columns."
    })
    if mentions_date_issues:
        score += 0.08

    # -------------------------------------------------------
    # CHECK 8: IDENTIFIES MISSING/BLANK VALUES
    # EMP-004 has blank Employee Name, EMP-010 has blank Expense Date, EMP-016 has blank Submission Date
    # -------------------------------------------------------
    mentions_blanks = bool(
        re.search(r'blank', content_lower) or
        re.search(r'missing', content_lower) or
        re.search(r'empty', content_lower) or
        re.search(r'null', content_lower)
    )
    checks.append({
        "name": "identifies_blank_values",
        "passed": mentions_blanks,
        "detail": "Diagnosis must identify blank/missing values (e.g., blank Employee Name, blank Expense Date)."
    })
    if mentions_blanks:
        score += 0.07

    # -------------------------------------------------------
    # CHECK 9: IDENTIFIES MIXED CURRENCY (USD, GBP, EUR)
    # -------------------------------------------------------
    mentions_currency_issue = bool(
        (re.search(r'currency', content_lower) or re.search(r'gbp', content_lower) or re.search(r'eur', content_lower)) and
        (re.search(r'mixed', content_lower) or re.search(r'inconsist', content_lower) or
         re.search(r'multiple', content_lower) or re.search(r'different', content_lower) or
         re.search(r'gbp', content_lower) or re.search(r'eur', content_lower))
    )
    checks.append({
        "name": "identifies_mixed_currency",
        "passed": mentions_currency_issue,
        "detail": "Diagnosis must identify mixed currencies (USD, GBP, EUR) as a risk requiring normalization."
    })
    if mentions_currency_issue:
        score += 0.07

    # -------------------------------------------------------
    # CHECK 10: IDENTIFIES INCONSISTENT STATUS/CASE VALUES
    # Status column has: Approved, pending, APPROVED, approved, Rejected, Pending, PENDING
    # Currency also has: USD, usd
    # -------------------------------------------------------
    mentions_case_inconsistency = bool(
        re.search(r'case', content_lower) or
        re.search(r'upper', content_lower) or
        re.search(r'lower', content_lower) or
        re.search(r'status', content_lower) and re.search(r'inconsist|mixed|standar|clean', content_lower)
    )
    checks.append({
        "name": "identifies_case_inconsistency",
        "passed": mentions_case_inconsistency,
        "detail": "Diagnosis must identify case inconsistency in Status column (Approved vs APPROVED vs approved vs pending vs Pending vs PENDING)."
    })
    if mentions_case_inconsistency:
        score += 0.05

    # -------------------------------------------------------
    # CHECK 11: IDENTIFIES NON-NUMERIC AMOUNT VALUE
    # EMP-007 has Amount = "N/A"
    # -------------------------------------------------------
    mentions_amount_issue = bool(
        re.search(r'n/a', content_lower) or
        (re.search(r'amount', content_lower) and
         (re.search(r'non.numeric|invalid|not.numeric|text|string|error', content_lower) or
          re.search(r'n/a', content_lower)))
    )
    checks.append({
        "name": "identifies_non_numeric_amount",
        "passed": mentions_amount_issue,
        "detail": "Diagnosis must flag that Amount column contains 'N/A' (non-numeric) for EMP-007, which will break SUM/AVERAGE formulas."
    })
    if mentions_amount_issue:
        score += 0.05

    # -------------------------------------------------------
    # CHECK 12: RECOMMENDS HELPER COLUMNS (not one mega-formula)
    # SKILL.md priority: "Prefer helper columns when a single long formula would be fragile"
    # -------------------------------------------------------
    mentions_helper_columns = bool(
        re.search(r'helper.col', content_lower) or
        re.search(r'helper col', content_lower) or
        re.search(r'auxiliary.col', content_lower) or
        re.search(r'intermediate.col', content_lower) or
        re.search(r'staging.col', content_lower) or
        re.search(r'working.col', content_lower) or
        re.search(r'helper', content_lower) and re.search(r'col', content_lower)
    )
    checks.append({
        "name": "recommends_helper_columns",
        "passed": mentions_helper_columns,
        "detail": "Recommendation must prefer helper columns over a single complex formula, per SKILL.md priorities."
    })
    if mentions_helper_columns:
        score += 0.05

    # -------------------------------------------------------
    # CHECK 13: MENTIONS EXCEL AND WPS COMPATIBILITY
    # Both must be mentioned explicitly
    # -------------------------------------------------------
    mentions_excel = bool(re.search(r'\bexcel\b', content_lower))
    mentions_wps = bool(re.search(r'\bwps\b', content_lower))
    both_mentioned = mentions_excel and mentions_wps
    checks.append({
        "name": "mentions_excel_and_wps_compatibility",
        "passed": both_mentioned,
        "detail": f"Compatibility section must explicitly mention both Excel and WPS. Found Excel: {mentions_excel}, WPS: {mentions_wps}."
    })
    if both_mentioned:
        score += 0.07

    # -------------------------------------------------------
    # CHECK 14: MENTIONS A FALLBACK FORMULA/APPROACH
    # SKILL.md: "Provide a fallback when the preferred formula may not work everywhere"
    # -------------------------------------------------------
    mentions_fallback = bool(
        re.search(r'fallback', content_lower) or
        re.search(r'fall.back', content_lower) or
        re.search(r'alternative', content_lower) or
        re.search(r'alternatively', content_lower) or
        re.search(r'if.not.available', content_lower) or
        re.search(r'if.*not.*support', content_lower) or
        re.search(r'older.version', content_lower) or
        re.search(r'instead.*use', content_lower)
    )
    checks.append({
        "name": "mentions_fallback",
        "passed": mentions_fallback,
        "detail": "Compatibility section must provide a fallback formula or approach per SKILL.md requirements."
    })
    if mentions_fallback:
        score += 0.05

    # -------------------------------------------------------
    # CHECK 15: CONFIRMS WORKFLOW GATE - PAUSE BEFORE EXECUTION
    # SKILL.md: "If the next step would directly modify a workbook... ask for confirmation first"
    # The Execution section must either (a) be conditional on approval / reference user confirmation,
    # OR the report must contain some explicit note that execution requires user sign-off.
    # -------------------------------------------------------
    mentions_confirmation = bool(
        re.search(r'confirm', content_lower) or
        re.search(r'approv', content_lower) or
        re.search(r'agree', content_lower) or
        re.search(r'proceed', content_lower) or
        re.search(r'before.*execut', content_lower) or
        re.search(r'execut.*approv', content_lower) or
        re.search(r'upon.*approval', content_lower) or
        re.search(r'once.*approved', content_lower) or
        re.search(r'after.*confirmation', content_lower)
    )
    checks.append({
        "name": "workflow_gate_confirmation",
        "passed": mentions_confirmation,
        "detail": "Per SKILL.md, the agent must pause before execution and note that changes require user confirmation. Report must reference confirmation/approval gating."
    })
    if mentions_confirmation:
        score += 0.05

    # -------------------------------------------------------
    # CHECK 16: INCLUDES AT LEAST ONE ACTUAL SPREADSHEET FORMULA
    # Execution section should have concrete formula(s), not just descriptions
    # -------------------------------------------------------
    has_formula = bool(
        re.search(r'=\s*[A-Z]+\s*\(', content) or   # matches =VLOOKUP( =IFERROR( =TRIM( etc
        re.search(r'=\w+\(', content) or
        re.search(r'vlookup|xlookup|countif|sumif|iferror|trim|upper|lower|text\(|datevalue|isblank|if\(', content_lower)
    )
    checks.append({
        "name": "includes_formula_recommendation",
        "passed": has_formula,
        "detail": "Execution section must include at least one concrete spreadsheet formula (e.g., TRIM, UPPER, COUNTIF, VLOOKUP, IFERROR, TEXT, DATEVALUE)."
    })
    if has_formula:
        score += 0.05

    # --- Clamp score ---
    score = min(score, 1.0)

    # --- Determine overall pass ---
    # Must pass: file exists, at least 4 of 5 structural sections, and at least 5 of the content checks
    structural_checks = [
        "has_diagnosis_section",
        "has_recommendation_section",
        "has_execution_section",
        "has_compatibility_section",
        "has_notes_section"
    ]
    content_checks = [
        "identifies_duplicates",
        "identifies_mixed_date_formats",
        "identifies_blank_values",
        "identifies_mixed_currency",
        "identifies_case_inconsistency",
        "identifies_non_numeric_amount",
        "recommends_helper_columns",
        "mentions_excel_and_wps_compatibility",
        "mentions_fallback",
        "workflow_gate_confirmation",
        "includes_formula_recommendation",
    ]

    passed_structural = sum(1 for c in checks if c["name"] in structural_checks and c["passed"])
    passed_content = sum(1 for c in checks if c["name"] in content_checks and c["passed"])

    overall_passed = (
        any(c["name"] == "file_exists" and c["passed"] for c in checks) and
        passed_structural >= 4 and
        passed_content >= 6 and
        score >= 0.55
    )

    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, indent=2))