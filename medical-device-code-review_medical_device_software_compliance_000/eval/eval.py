import sys
import os
import re
import json
from pathlib import Path

def find_report(workspace: str) -> Path | None:
    """Search for code_review_report.md anywhere in workspace."""
    results = list(Path(workspace).rglob("code_review_report.md"))
    if results:
        return results[0]
    return None

def score_checks(checks: list[dict]) -> float:
    passed = sum(1 for c in checks if c["passed"])
    return round(passed / len(checks), 3) if checks else 0.0

def main():
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    checks = []

    # ── Locate the report ────────────────────────────────────────────────────
    report_path = find_report(workspace)

    if report_path is None:
        checks.append({
            "name": "report_file_exists",
            "passed": False,
            "detail": "code_review_report.md not found anywhere in workspace"
        })
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    checks.append({
        "name": "report_file_exists",
        "passed": True,
        "detail": f"Found report at {report_path}"
    })

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({"name": "report_readable", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, ensure_ascii=False))
        return

    checks.append({"name": "report_readable", "passed": True, "detail": "File read successfully"})

    # ── CHECK 1: Required top-level sections present ──────────────────────────
    required_sections = [
        ("section_summary",      r"##\s*审核总结"),
        ("section_critical",     r"##\s*严重问题"),
        ("section_major",        r"##\s*主要问题"),
        ("section_minor",        r"##\s*次要问题"),
        ("section_compliance",   r"##\s*合规说明"),
    ]
    for name, pattern in required_sections:
        found = bool(re.search(pattern, content))
        checks.append({
            "name": name,
            "passed": found,
            "detail": f"Section matching '{pattern}' {'found' if found else 'NOT found'} in report"
        })

    # ── CHECK 2: Safety class must be identified as C ─────────────────────────
    # Accept: 安全等级：C / Class C / Safety Class C / 等级：C
    class_c_pattern = r"(安全等级|Safety\s*Class|软件安全等级|等级)[：:]\s*[Cc]\b"
    class_c_found = bool(re.search(class_c_pattern, content, re.IGNORECASE))
    checks.append({
        "name": "safety_class_C_identified",
        "passed": class_c_found,
        "detail": "Report must identify software safety class as C (infusion pump = Class C)"
    })

    # ── CHECK 3: Race condition identified ────────────────────────────────────
    race_keywords = r"(竞态条件|race.condition|mutex|互斥|线程安全|并发|thread.safe)"
    race_found = bool(re.search(race_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "race_condition_identified",
        "passed": race_found,
        "detail": "Report must mention race condition on g_target_flow_rate (missing mutex in set_flow_rate)"
    })

    # ── CHECK 4: Integer overflow identified ──────────────────────────────────
    overflow_keywords = r"(整数溢出|integer.overflow|溢出)"
    overflow_found = bool(re.search(overflow_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "integer_overflow_identified",
        "passed": overflow_found,
        "detail": "Report must identify integer overflow in calculate_dose or validate_and_apply_prescription"
    })

    # ── CHECK 5: Missing input validation identified ──────────────────────────
    input_val_keywords = r"(未验证|输入验证|边界检查|input.validat|bounds.check|无.*验证|缺.*验证)"
    input_val_found = bool(re.search(input_val_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "missing_input_validation_identified",
        "passed": input_val_found,
        "detail": "Report must identify missing input validation on rate_ml_per_hr / concentration"
    })

    # ── CHECK 6: Hardcoded credentials identified ─────────────────────────────
    hc_keywords = r"(硬编码|hardcoded|hard.coded|MEDFLOW_ADMIN|明文密码|凭证|credentials)"
    hc_found = bool(re.search(hc_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "hardcoded_credentials_identified",
        "passed": hc_found,
        "detail": "Report must flag hardcoded admin credential MEDFLOW_ADMIN_2024"
    })

    # ── CHECK 7: Unencrypted PHI transmission identified ──────────────────────
    phi_keywords = r"(明文|未加密|unencrypt|plaintext|PHI|患者.*数据.*传输|HTTP.*传输|TLS|加密)"
    phi_found = bool(re.search(phi_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "unencrypted_phi_identified",
        "passed": phi_found,
        "detail": "Report must flag unencrypted PHI transmission via network_send_plaintext"
    })

    # ── CHECK 8: SQL injection identified ────────────────────────────────────
    sql_keywords = r"(SQL\s*注入|sql.inject|注入|injection)"
    sql_found = bool(re.search(sql_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "sql_injection_identified",
        "passed": sql_found,
        "detail": "Report must identify SQL injection in network_comm.c db_query()"
    })

    # ── CHECK 9: Missing timeout identified ───────────────────────────────────
    timeout_keywords = r"(超时|timeout|time.out|无限循环|infinite.loop|阻塞)"
    timeout_found = bool(re.search(timeout_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "missing_timeout_identified",
        "passed": timeout_found,
        "detail": "Report must identify missing timeout in sensor polling loop"
    })

    # ── CHECK 10: Test coverage deficiency identified (must reference 90%) ─────
    # For Class C the threshold is 90% not 70%; report must call out the 57% coverage
    coverage_keywords = r"(覆盖率|coverage|90%|测试覆盖)"
    coverage_found = bool(re.search(coverage_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "test_coverage_deficiency_identified",
        "passed": coverage_found,
        "detail": "Report must address test coverage (Class C requires >90%; current is ~57%)"
    })

    # ── CHECK 11: Magic numbers identified ────────────────────────────────────
    magic_keywords = r"(魔法数字|magic.number|未命名常量|unnamed.constant|硬编码.*数值|数字.*未定义)"
    magic_found = bool(re.search(magic_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "magic_numbers_identified",
        "passed": magic_found,
        "detail": "Report must flag magic numbers (500, 10000, 0.85) in infusion_controller.c"
    })

    # ── CHECK 12: YY/T 0664 compliance statement ──────────────────────────────
    yyt_keywords = r"(YY[/／]T\s*0664|IEC\s*62304)"
    yyt_found = bool(re.search(yyt_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "yyt_0664_compliance_mentioned",
        "passed": yyt_found,
        "detail": "Compliance section must reference YY/T 0664 or IEC 62304"
    })

    # ── CHECK 13: NMPA / network security compliance statement ───────────────
    nmpa_keywords = r"(NMPA|网络安全|GB\s*9706|数据安全法|个人信息保护法|网络安全注册)"
    nmpa_found = bool(re.search(nmpa_keywords, content, re.IGNORECASE))
    checks.append({
        "name": "nmpa_or_cybersecurity_standard_mentioned",
        "passed": nmpa_found,
        "detail": "Compliance section must reference NMPA, GB 9706.1 or Chinese cybersecurity regulations"
    })

    # ── CHECK 14: File:line references present ────────────────────────────────
    # SKILL.md output format requires "文件:行号" citations
    file_line_pattern = r"\.(c|h|py|json)\s*[：:]\s*\d+"
    file_line_found = bool(re.search(file_line_pattern, content, re.IGNORECASE))
    checks.append({
        "name": "file_line_references_present",
        "passed": file_line_found,
        "detail": "Issues must cite file:line_number per required output format (e.g., infusion_controller.c:45)"
    })

    # ── CHECK 15: Overall assessment present ──────────────────────────────────
    # Should say 严重问题 (critical issues) in the summary block
    assessment_pattern = r"(总体评估|overall|通过|严重问题|次要问题|主要问题)[：:\s]"
    assessment_found = bool(re.search(assessment_pattern, content, re.IGNORECASE))
    checks.append({
        "name": "overall_assessment_present",
        "passed": assessment_found,
        "detail": "审核总结 section must include an overall assessment verdict"
    })

    # ── CHECK 16: Critical issues section is non-empty ────────────────────────
    # Extract content between 严重问题 section and next ##
    critical_section_match = re.search(
        r"##\s*严重问题[^\n]*\n(.*?)(?=\n##|\Z)", content, re.DOTALL
    )
    critical_nonempty = False
    critical_detail = "严重问题 section not found or empty"
    if critical_section_match:
        critical_body = critical_section_match.group(1).strip()
        # Must have at least one bullet or line item
        if len(critical_body) > 20:
            critical_nonempty = True
            critical_detail = f"严重问题 section has {len(critical_body)} chars of content"
    checks.append({
        "name": "critical_issues_section_nonempty",
        "passed": critical_nonempty,
        "detail": critical_detail
    })

    # ── CHECK 17: Race condition correctly classified as 严重 (critical) ────────
    # Check that race condition appears in or before 严重 section, not just in minor
    critical_with_race = False
    if critical_section_match:
        critical_body = critical_section_match.group(1)
        if re.search(race_keywords, critical_body, re.IGNORECASE):
            critical_with_race = True
    checks.append({
        "name": "race_condition_is_critical_severity",
        "passed": critical_with_race,
        "detail": "Race condition on infusion rate (patient safety) must appear in 严重问题 section"
    })

    # ── Compute final result ──────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 3)

    # Minimum pass threshold: must pass at least 13/17 checks including
    # the existence, safety class, and at least one critical issue check
    mandatory = [
        "report_file_exists",
        "safety_class_C_identified",
        "critical_issues_section_nonempty",
        "yyt_0664_compliance_mentioned",
    ]
    mandatory_passed = all(
        any(c["name"] == m and c["passed"] for c in checks)
        for m in mandatory
    )
    overall_passed = mandatory_passed and passed_count >= 13

    result = {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()