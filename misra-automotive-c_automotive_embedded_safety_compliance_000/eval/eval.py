import sys
import re
import json
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    candidates = list(Path(workspace).rglob("misra_audit_report.txt"))
    if candidates:
        return candidates[0]
    return None

def check(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace: str) -> dict:
    checks = []
    score_parts = []

    # ── Locate the report ────────────────────────────────────────────────────
    report_path = find_report(workspace)
    if report_path is None:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [check("report_file_exists", False, "misra_audit_report.txt not found anywhere in workspace")]
        }
    checks.append(check("report_file_exists", True, f"Found at {report_path}"))

    try:
        content = report_path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [check("report_readable", False, f"Cannot read file: {e}")]
        }

    # ── 1. SAFETY CRITICAL banner (Rule 21.3 escalation) ────────────────────
    has_safety_banner = bool(re.search(r"SAFETY\s+CRITICAL", content, re.IGNORECASE))
    checks.append(check(
        "safety_critical_banner",
        has_safety_banner,
        "Report must contain '⚠️ SAFETY CRITICAL' banner at the top due to Rule 21.3 malloc violation"
    ))
    score_parts.append(1.0 if has_safety_banner else 0.0)

    # ── 2. Violation separator format (unicode heavy horizontal box chars) ───
    # The skill mandates ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # U+2501 BOX DRAWINGS HEAVY HORIZONTAL
    heavy_sep = "━" * 10  # at least 10 consecutive heavy horizontal chars
    has_heavy_sep = heavy_sep in content
    checks.append(check(
        "violation_separator_format",
        has_heavy_sep,
        "Violation blocks must be separated by ━━━━━━━━━ (U+2501 heavy horizontal) lines per SKILL.md format"
    ))
    score_parts.append(1.0 if has_heavy_sep else 0.0)

    # ── 3. VIOLATION block structure — required fields present ───────────────
    required_fields = [
        r"Rule\s*:",
        r"Category\s*:",
        r"ASIL\s*:",
        r"Severity\s*:",
        r"Location\s*:",
        r"Non-Compliant Code\s*:",
        r"MISRA-Compliant Replacement\s*:",
    ]
    field_results = []
    for pattern in required_fields:
        found = bool(re.search(pattern, content))
        field_results.append(found)
    all_fields_present = all(field_results)
    checks.append(check(
        "violation_block_fields",
        all_fields_present,
        f"Each violation block must contain Rule, Category, ASIL, Severity, Location, Non-Compliant Code, MISRA-Compliant Replacement. "
        f"Missing: {[required_fields[i] for i,v in enumerate(field_results) if not v]}"
    ))
    score_parts.append(1.0 if all_fields_present else sum(field_results)/len(field_results))

    # ── 4. Rule 21.3 violation detected ─────────────────────────────────────
    has_21_3 = bool(re.search(r"Rule\s+21\.3", content, re.IGNORECASE))
    checks.append(check(
        "rule_21_3_malloc_detected",
        has_21_3,
        "Rule 21.3 (malloc/free) must be flagged — it is mandatory and present in both Brake_Apply and Brake_IRQ_Handler"
    ))
    score_parts.append(1.0 if has_21_3 else 0.0)

    # ── 5. Rule 15.1 goto detected AND classified ASIL D ────────────────────
    has_15_1 = bool(re.search(r"Rule\s+15\.1", content, re.IGNORECASE))
    # Check that after Rule 15.1, ASIL D appears (within 500 chars)
    asil_d_for_goto = False
    for m in re.finditer(r"Rule\s+15\.1", content, re.IGNORECASE):
        snippet = content[m.start():m.start()+600]
        if re.search(r"ASIL\s*[:\-]?\s*D", snippet, re.IGNORECASE):
            asil_d_for_goto = True
            break
    checks.append(check(
        "rule_15_1_goto_detected",
        has_15_1,
        "Rule 15.1 (goto) must be flagged as Mandatory"
    ))
    score_parts.append(1.0 if has_15_1 else 0.0)

    checks.append(check(
        "rule_15_1_asil_d_escalation",
        asil_d_for_goto,
        "Per SKILL.md escalation rules, Rule 15.1 (goto) must be classified ASIL D regardless of context"
    ))
    score_parts.append(1.0 if asil_d_for_goto else 0.0)

    # ── 6. Rule 4.6 (bare int) detected ─────────────────────────────────────
    has_4_6 = bool(re.search(r"Rule\s+4\.6", content, re.IGNORECASE))
    checks.append(check(
        "rule_4_6_bare_int_detected",
        has_4_6,
        "Rule 4.6 — 'int retry_count' must be flagged; fixed-width types required"
    ))
    score_parts.append(1.0 if has_4_6 else 0.0)

    # ── 7. Rule 15.7 (missing else) detected ────────────────────────────────
    has_15_7 = bool(re.search(r"Rule\s+15\.7", content, re.IGNORECASE))
    checks.append(check(
        "rule_15_7_missing_else_detected",
        has_15_7,
        "Rule 15.7 — if-else if chain without final else in Brake_ValidatePressure must be flagged"
    ))
    score_parts.append(1.0 if has_15_7 else 0.0)

    # ── 8. Rule 16.4 (switch missing default) detected ──────────────────────
    has_16_4 = bool(re.search(r"Rule\s+16\.4", content, re.IGNORECASE))
    checks.append(check(
        "rule_16_4_switch_no_default_detected",
        has_16_4,
        "Rule 16.4 — switch in Brake_UpdateState lacks 'default:' clause"
    ))
    score_parts.append(1.0 if has_16_4 else 0.0)

    # ── 9. Rule 20.7 (unparenthesised macro) detected ────────────────────────
    has_20_7 = bool(re.search(r"Rule\s+20\.7", content, re.IGNORECASE))
    checks.append(check(
        "rule_20_7_macro_parentheses_detected",
        has_20_7,
        "Rule 20.7 — SCALE_PRESSURE(x) macro parameter not parenthesised must be flagged"
    ))
    score_parts.append(1.0 if has_20_7 else 0.0)

    # ── 10. Rule 17.3 (implicit function declaration) detected ───────────────
    has_17_3 = bool(re.search(r"Rule\s+17\.3", content, re.IGNORECASE))
    checks.append(check(
        "rule_17_3_implicit_decl_detected",
        has_17_3,
        "Rule 17.3 — compute_checksum called without declaration must be flagged"
    ))
    score_parts.append(1.0 if has_17_3 else 0.0)

    # ── 11. Rule 17.2 (recursion) detected ──────────────────────────────────
    has_17_2 = bool(re.search(r"Rule\s+17\.2", content, re.IGNORECASE))
    checks.append(check(
        "rule_17_2_recursion_detected",
        has_17_2,
        "Rule 17.2 — Brake_Factorial recursive self-call must be flagged"
    ))
    score_parts.append(1.0 if has_17_2 else 0.0)

    # ── 12. Missing volatile on BRAKE_PRESSURE_REG detected ─────────────────
    has_volatile_viol = bool(re.search(r"volatile", content, re.IGNORECASE)) and \
                        bool(re.search(r"BRAKE_PRESSURE_REG|hardware.register|missing.*volatile|volatile.*missing", content, re.IGNORECASE))
    checks.append(check(
        "missing_volatile_on_hw_register",
        has_volatile_viol,
        "BRAKE_PRESSURE_REG is missing 'volatile' qualifier — memory-embedded rule violation must be reported"
    ))
    score_parts.append(1.0 if has_volatile_viol else 0.0)

    # ── 13. ISR heightened strictness applied ───────────────────────────────
    # The report should mention Brake_IRQ_Handler and note ISR-specific concern
    has_isr_mention = bool(re.search(r"Brake_IRQ_Handler|ISR|interrupt.*handler|handler.*interrupt", content, re.IGNORECASE))
    checks.append(check(
        "isr_heightened_strictness_applied",
        has_isr_mention,
        "Brake_IRQ_Handler is an ISR — per escalation rules, memory-embedded rules apply with heightened strictness"
    ))
    score_parts.append(1.0 if has_isr_mention else 0.0)

    # ── 14. REVIEW SUMMARY section present with correct format ──────────────
    has_summary = bool(re.search(r"REVIEW\s+SUMMARY", content, re.IGNORECASE))
    checks.append(check(
        "review_summary_section_present",
        has_summary,
        "Report must end with a REVIEW SUMMARY table as per SKILL.md format"
    ))
    score_parts.append(1.0 if has_summary else 0.0)

    # ── 15. Summary table has correct fields ─────────────────────────────────
    summary_fields = [
        r"Total\s+violations",
        r"Mandatory",
        r"Required",
        r"ASIL\s+D",
        r"ASIL\s+[ABC]",
        r"Overall\s+compliance\s+status",
    ]
    summary_field_hits = [bool(re.search(p, content, re.IGNORECASE)) for p in summary_fields]
    all_summary_fields = all(summary_field_hits)
    checks.append(check(
        "review_summary_correct_fields",
        all_summary_fields,
        f"Summary must include: Total violations, Mandatory, Required, ASIL D breakdown, Overall compliance status. "
        f"Missing patterns: {[summary_fields[i] for i,v in enumerate(summary_field_hits) if not v]}"
    ))
    score_parts.append(1.0 if all_summary_fields else sum(summary_field_hits)/len(summary_field_hits))

    # ── 16. Overall compliance status is FAIL ────────────────────────────────
    has_fail_status = bool(re.search(r"compliance\s+status\s*[:\-]?\s*FAIL", content, re.IGNORECASE)) or \
                      bool(re.search(r"Overall.*?:\s*FAIL", content, re.IGNORECASE))
    checks.append(check(
        "overall_compliance_status_fail",
        has_fail_status,
        "With mandatory violations present (21.3, 15.1, 17.3, 17.2), overall compliance status must be FAIL"
    ))
    score_parts.append(1.0 if has_fail_status else 0.0)

    # ── 17. Summary light separator ─────────────────────────────────────────
    # REVIEW SUMMARY uses ── (U+2500 light horizontal) not ━━ (U+2501 heavy)
    light_sep = "─" * 10
    has_light_sep = light_sep in content
    checks.append(check(
        "summary_light_separator_format",
        has_light_sep,
        "REVIEW SUMMARY section must use ── (U+2500 light horizontal lines), distinct from violation ━━ separators"
    ))
    score_parts.append(1.0 if has_light_sep else 0.0)

    # ── 18. Minimum violation count detected (at least 7 unique rules) ───────
    rule_pattern = re.findall(r"Rule\s+(\d+\.\d+)", content, re.IGNORECASE)
    unique_rules = set(rule_pattern)
    min_rules_ok = len(unique_rules) >= 7
    checks.append(check(
        "minimum_violation_coverage",
        min_rules_ok,
        f"At least 7 distinct MISRA rules should be flagged. Found unique rules: {sorted(unique_rules)}"
    ))
    score_parts.append(1.0 if min_rules_ok else max(0.0, len(unique_rules)/7.0))

    # ── 19. MISRA-Compliant Replacement provided for malloc violation ─────────
    has_replacement_no_malloc = False
    # Look for replacement snippet that doesn't use malloc — static buffer or removal
    for m in re.finditer(r"MISRA-Compliant Replacement", content, re.IGNORECASE):
        snippet = content[m.start():m.start()+500]
        if "malloc" not in snippet.lower() and ("static" in snippet.lower() or "stack" in snippet.lower() or "uint8_t" in snippet.lower()):
            has_replacement_no_malloc = True
            break
    checks.append(check(
        "compliant_replacement_for_malloc",
        has_replacement_no_malloc,
        "A MISRA-compliant replacement for the malloc call must be provided using static/stack allocation"
    ))
    score_parts.append(1.0 if has_replacement_no_malloc else 0.0)

    # ── 20. Category field uses correct vocabulary ────────────────────────────
    valid_categories = bool(re.search(r"Category\s*[:\-]?\s*(Mandatory|Required|Advisory)", content))
    checks.append(check(
        "category_field_valid_vocabulary",
        valid_categories,
        "Category field must use exactly: Mandatory | Required | Advisory"
    ))
    score_parts.append(1.0 if valid_categories else 0.0)

    # ── Compute final score ──────────────────────────────────────────────────
    total_score = sum(score_parts) / len(score_parts) if score_parts else 0.0
    total_score = round(total_score, 4)
    passed = total_score >= 0.75 and has_safety_banner and has_heavy_sep and has_fail_status

    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(workspace)
    print(json.dumps(result, indent=2))