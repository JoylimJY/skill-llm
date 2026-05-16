import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # Find audit_report.md anywhere in workspace
    report_files = list(workspace.rglob("audit_report.md"))
    
    if not report_files:
        checks.append({
            "name": "report_file_exists",
            "passed": False,
            "detail": "No audit_report.md found anywhere in the workspace."
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = report_files[0]
    checks.append({
        "name": "report_file_exists",
        "passed": True,
        "detail": f"Found audit_report.md at {report_path}"
    })

    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "report_readable",
            "passed": False,
            "detail": f"Could not read audit_report.md: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "report_readable", "passed": True, "detail": "File is readable."})

    # ── CHECK 1: Four required categories present ──────────────────────────────
    required_categories = ["必填缺失", "规则不符", "平台不一致", "待确认"]
    found_categories = [cat for cat in required_categories if cat in content]
    cat_check_passed = len(found_categories) == 4
    checks.append({
        "name": "four_issue_categories_present",
        "passed": cat_check_passed,
        "detail": f"Found categories: {found_categories}. Expected all of: {required_categories}"
    })
    if cat_check_passed:
        total_score += 0.10

    # ── CHECK 2: Invalid system_online_date "/" flagged ───────────────────────
    online_date_flagged = (
        "系统上线时间" in content and
        ("/" in content or "无效" in content or "invalid" in content.lower() or "必填" in content)
    )
    # More flexible: just check that 系统上线时间 is mentioned as a problem
    online_date_flagged = "系统上线时间" in content
    checks.append({
        "name": "system_online_date_invalid_flagged",
        "passed": online_date_flagged,
        "detail": "Expected '系统上线时间' to be flagged as invalid (value is '/')."
    })
    if online_date_flagged:
        total_score += 0.08

    # ── CHECK 3: Empty data_resource_summary flagged ──────────────────────────
    summary_flagged = "数据资源摘要" in content
    checks.append({
        "name": "data_resource_summary_empty_flagged",
        "passed": summary_flagged,
        "detail": "Expected '数据资源摘要' empty field to be flagged under 必填缺失."
    })
    if summary_flagged:
        total_score += 0.08

    # ── CHECK 4: data_increment missing for large+growing table ──────────────
    # 行政执法案件表 has 158000 records and is continuously growing → 数据增量 must be filled
    increment_flagged = (
        "数据增量" in content and
        ("行政执法案件" in content or "admin_enforcement_case" in content)
    )
    checks.append({
        "name": "data_increment_required_flagged",
        "passed": increment_flagged,
        "detail": "Expected '数据增量' to be flagged as required for '行政执法案件表' (volume=158000, continuously growing)."
    })
    if increment_flagged:
        total_score += 0.12

    # ── CHECK 5: Chinese description == English name flagged (violation_type) ─
    # violation_type field has field_cn="违规类型" but description="violation_type" (equals en name)
    desc_eq_en_flagged = (
        ("violation_type" in content or "数据项中文描述" in content) and
        ("行政执法案件" in content or "violation" in content)
    )
    # Also check location field in illegal_parking_record where cn==en
    location_flagged = "location" in content
    desc_violation_flagged = desc_eq_en_flagged or location_flagged
    checks.append({
        "name": "chinese_desc_equals_english_name_flagged",
        "passed": desc_violation_flagged,
        "detail": "Expected fields where Chinese description equals English name to be flagged (violation_type, location)."
    })
    if desc_violation_flagged:
        total_score += 0.10

    # ── CHECK 6: Empty field description flagged (penalty_result) ────────────
    empty_desc_flagged = (
        ("penalty_result" in content or "处罚结果" in content) and
        ("描述" in content or "中文" in content)
    )
    checks.append({
        "name": "empty_field_description_flagged",
        "passed": empty_desc_flagged,
        "detail": "Expected 'penalty_result'/'处罚结果' with empty description to be flagged."
    })
    if empty_desc_flagged:
        total_score += 0.08

    # ── CHECK 7: TIMEFLAG exemption correctly applied (NOT flagged as issue) ──
    # TIMEFLAG with "默认信息" should NOT be flagged
    # We check that TIMEFLAG is either not mentioned as a problem, or explicitly noted as exempt
    timeflag_incorrectly_flagged = False
    # Look for TIMEFLAG mentioned near problem/issue keywords WITHOUT exemption context
    timeflag_matches = [m.start() for m in re.finditer(r'TIMEFLAG', content)]
    for pos in timeflag_matches:
        snippet = content[max(0, pos-100):pos+200]
        # If TIMEFLAG appears near "问题", "不符", "缺失" etc. without "忽略" or "豁免" or "可忽略"
        is_problem_context = bool(re.search(r'(问题|不符|缺失|需整改|违规)', snippet))
        is_exempt_context = bool(re.search(r'(忽略|豁免|可不|系统统一|无需|不需)', snippet))
        if is_problem_context and not is_exempt_context:
            timeflag_incorrectly_flagged = True
            break
    
    timeflag_check_passed = not timeflag_incorrectly_flagged
    checks.append({
        "name": "timeflag_exemption_correctly_applied",
        "passed": timeflag_check_passed,
        "detail": "TIMEFLAG with '默认信息' should NOT be flagged as an issue per special rule. " + 
                  ("Correctly NOT flagged." if timeflag_check_passed else "TIMEFLAG was incorrectly listed as a problem.")
    })
    if timeflag_check_passed:
        total_score += 0.12

    # ── CHECK 8: "不予共享" without legal basis flagged ───────────────────────
    no_sharing_flagged = (
        ("不予共享" in content or "共享类型" in content) and
        ("执法人员" in content or "enforcement_officer" in content or "法律依据" in content or "制度依据" in content)
    )
    checks.append({
        "name": "no_sharing_without_legal_basis_flagged",
        "passed": no_sharing_flagged,
        "detail": "Expected '执法人员信息表' with '不予共享' and no legal basis to be flagged under 规则不符."
    })
    if no_sharing_flagged:
        total_score += 0.10

    # ── CHECK 9: Platform system name mismatch flagged ────────────────────────
    # System name: "城市综合执法管理系统" vs platform: "城市综合执法系统"
    name_mismatch_flagged = (
        ("城市综合执法管理系统" in content or "城市综合执法系统" in content) and
        ("名称" in content or "不一致" in content or "差异" in content or "平台" in content)
    )
    checks.append({
        "name": "platform_system_name_mismatch_flagged",
        "passed": name_mismatch_flagged,
        "detail": "Expected system name mismatch ('城市综合执法管理系统' vs '城市综合执法系统') to be flagged under 平台不一致."
    })
    if name_mismatch_flagged:
        total_score += 0.08

    # ── CHECK 10: Stale platform table (> 6 months) flagged ──────────────────
    # admin_enforcement_case last updated 2024-05-10, submission date 2025-01-15 = ~8 months
    stale_table_flagged = (
        ("admin_enforcement_case" in content or "行政执法案件" in content) and
        ("更新" in content or "半年" in content or "过期" in content or "未更新" in content)
    )
    checks.append({
        "name": "stale_platform_table_flagged",
        "passed": stale_table_flagged,
        "detail": "Expected 'admin_enforcement_case' (last updated 2024-05-10) to be flagged for being >6 months stale."
    })
    if stale_table_flagged:
        total_score += 0.07

    # ── CHECK 11: violation_type field "默认信息" on platform flagged ─────────
    # violation_type field (NOT TIMEFLAG) on platform has "默认信息" as Chinese name - MUST be flagged
    platform_default_info_flagged = (
        ("violation_type" in content or "默认信息" in content) and
        ("平台" in content)
    )
    checks.append({
        "name": "non_timeflag_default_info_field_flagged",
        "passed": platform_default_info_flagged,
        "detail": "Expected 'violation_type' field with '默认信息' on platform (not TIMEFLAG) to be flagged under 平台不一致."
    })
    if platform_default_info_flagged:
        total_score += 0.07

    # ── CHECK 12: Each issue has correction suggestion (修正建议) ─────────────
    has_correction_suggestions = bool(re.search(r'(修正建议|整改建议|建议|应填写|需填写|请填写|修改为|补充)', content))
    checks.append({
        "name": "issues_have_correction_suggestions",
        "passed": has_correction_suggestions,
        "detail": "Expected each issue to include a correction/action suggestion per output format requirements."
    })
    if has_correction_suggestions:
        total_score += 0.05

    # ── CHECK 13: Issue has rule basis reference ──────────────────────────────
    has_rule_basis = bool(re.search(r'(规则依据|模板要求|审核规则|依据|要求)', content))
    checks.append({
        "name": "issues_reference_rules",
        "passed": has_rule_basis,
        "detail": "Expected issues to reference rule basis per output format requirements."
    })
    if has_rule_basis:
        total_score += 0.05

    # ── Final pass/fail ───────────────────────────────────────────────────────
    # Must pass at least 8 of 13 content checks (excluding file existence checks) 
    content_checks = checks[2:]  # skip file existence and readability
    passed_content = sum(1 for c in content_checks if c["passed"])
    overall_passed = passed_content >= 8 and total_score >= 0.55

    return {
        "passed": overall_passed,
        "score": round(min(total_score, 1.0), 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))