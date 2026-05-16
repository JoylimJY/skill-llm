import sys
import json
import re
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # Find the output file
    target_files = list(Path(workspace).rglob("loan_testcases.md"))
    
    if not target_files:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_exists", "passed": False, "detail": "loan_testcases.md not found anywhere in workspace"}]
        }
    
    target_file = target_files[0]
    
    try:
        content = target_file.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "passed": False,
            "score": 0.0,
            "checks": [{"name": "file_readable", "passed": False, "detail": f"Cannot read file: {e}"}]
        }
    
    # ---- CHECK 1: File exists ----
    checks.append({"name": "file_exists", "passed": True, "detail": f"Found at {target_file}"})
    
    # ---- CHECK 2: Correct 7-column table header ----
    required_headers = ["用例编号", "模块/功能点", "用例类型", "前置条件", "测试步骤", "预期结果", "优先级"]
    header_found = all(h in content for h in required_headers)
    checks.append({
        "name": "correct_table_headers",
        "passed": header_found,
        "detail": f"All 7 required headers present: {header_found}. Missing: {[h for h in required_headers if h not in content]}"
    })
    
    # ---- CHECK 3: TC-XXX numbering format ----
    tc_pattern = re.compile(r'TC-\d{3}')
    tc_matches = tc_pattern.findall(content)
    has_tc_numbering = len(tc_matches) >= 5
    checks.append({
        "name": "tc_numbering_format",
        "passed": has_tc_numbering,
        "detail": f"Found {len(tc_matches)} TC-XXX numbered cases. Need at least 5."
    })
    
    # ---- CHECK 4: Priority labels P0/P1/P2/P3 only ----
    priority_pattern = re.compile(r'\|\s*(P[0-9])\s*\|')
    priorities_found = set(priority_pattern.findall(content))
    valid_priorities = {"P0", "P1", "P2", "P3"}
    invalid_priorities = priorities_found - valid_priorities
    has_valid_priorities = len(priorities_found) > 0 and len(invalid_priorities) == 0
    checks.append({
        "name": "valid_priority_labels",
        "passed": has_valid_priorities,
        "detail": f"Priorities found: {priorities_found}. Invalid: {invalid_priorities}"
    })
    
    # ---- CHECK 5: P0 cases exist (core flow) ----
    has_p0 = "P0" in content
    checks.append({
        "name": "p0_cases_present",
        "passed": has_p0,
        "detail": "P0 priority cases must exist for core main flow"
    })
    
    # ---- CHECK 6: Specific field names in test steps (not vague) ----
    specific_fields = ["申请人姓名", "贷款金额", "身份证号", "联系电话", "企业营业执照编号"]
    fields_mentioned = [f for f in specific_fields if f in content]
    has_specific_fields = len(fields_mentioned) >= 3
    checks.append({
        "name": "specific_field_names_in_steps",
        "passed": has_specific_fields,
        "detail": f"Specific field names found: {fields_mentioned}. Need at least 3."
    })
    
    # ---- CHECK 7: Specific button/action names ----
    specific_actions = ["提交审批", "保存草稿", "同意", "驳回", "确认驳回"]
    actions_mentioned = [a for a in specific_actions if a in content]
    has_specific_actions = len(actions_mentioned) >= 3
    checks.append({
        "name": "specific_button_names_in_steps",
        "passed": has_specific_actions,
        "detail": f"Specific button/action names found: {actions_mentioned}. Need at least 3."
    })
    
    # ---- CHECK 8: No vague expected results ----
    vague_phrases = ["操作成功", "提交成功", "审批通过了", "系统正常"]
    vague_found = [p for p in vague_phrases if p in content]
    no_vague_results = len(vague_found) == 0
    checks.append({
        "name": "no_vague_expected_results",
        "passed": no_vague_results,
        "detail": f"Vague phrases found (should be 0): {vague_found}"
    })
    
    # ---- CHECK 9: Boundary value testing for field lengths ----
    # Applicant name: 2~10 chars boundary
    # Remark field: 500 chars
    # Rejection comment: 1~200 chars
    boundary_indicators = ["500", "200", "2~10", "50", "10个", "边界", "最大", "最小", "字符"]
    boundary_mentioned = [b for b in boundary_indicators if b in content]
    has_boundary_tests = len(boundary_mentioned) >= 3
    checks.append({
        "name": "boundary_value_tests",
        "passed": has_boundary_tests,
        "detail": f"Boundary value indicators found: {boundary_mentioned}"
    })
    
    # ---- CHECK 10: State machine coverage ----
    states = ["草稿", "待审批", "支行经理", "风控", "审批通过", "驳回", "撤回"]
    states_covered = [s for s in states if s in content]
    has_state_coverage = len(states_covered) >= 5
    checks.append({
        "name": "state_machine_coverage",
        "passed": has_state_coverage,
        "detail": f"States covered: {states_covered}. Need at least 5."
    })
    
    # ---- CHECK 11: Role/permission tests ----
    roles = ["申请人", "支行经理", "风控专员", "CFO"]
    roles_covered = [r for r in roles if r in content]
    has_role_tests = len(roles_covered) >= 3
    checks.append({
        "name": "role_permission_tests",
        "passed": has_role_tests,
        "detail": f"Roles covered: {roles_covered}. Need at least 3."
    })
    
    # ---- CHECK 12: Amount-based branch test (<=500万 vs >500万) ----
    amount_branch = any(kw in content for kw in ["500万", "5000000", "CFO审批", "CFO节点"])
    checks.append({
        "name": "amount_branch_condition_tested",
        "passed": amount_branch,
        "detail": "Test cases must cover the >500万 branch triggering CFO review"
    })
    
    # ---- CHECK 13: Conditional mandatory field (抵押物描述 > 100万) ----
    conditional_field = "抵押物描述" in content and ("100万" in content or "1000000" in content)
    checks.append({
        "name": "conditional_required_field_tested",
        "passed": conditional_field,
        "detail": "抵押物描述 must-fill condition (>100万) should be tested"
    })
    
    # ---- CHECK 14: 需求确认建议 section ----
    has_confirmation_section = "需求确认建议" in content or "疑问点" in content
    checks.append({
        "name": "requirement_confirmation_section",
        "passed": has_confirmation_section,
        "detail": "Must include 需求确认建议(疑问点) section for ambiguous/conflicting rules in PRD"
    })
    
    # ---- CHECK 15: Specific ambiguities flagged ----
    # PRD has 3 conflicts: 风控驳回返回节点, 同时在途申请数量, 备注字段长度
    ambiguity_indicators = [
        ("风控驳回", "风控专员驳回后的返回节点冲突"),
        ("在途申请", "同时在途申请数量冲突"),
        ("备注", "备注字段长度冲突"),
    ]
    ambiguities_found = []
    for keyword, desc in ambiguity_indicators:
        if keyword in content:
            ambiguities_found.append(desc)
    
    has_ambiguity_flags = len(ambiguities_found) >= 2
    checks.append({
        "name": "conflicts_flagged_in_prd",
        "passed": has_ambiguity_flags,
        "detail": f"PRD conflicts flagged: {ambiguities_found}. Need at least 2."
    })
    
    # ---- CHECK 16: Permission isolation - ID number masking for risk officer ----
    has_id_masking_test = ("身份证" in content and ("风控" in content) and 
                           any(kw in content for kw in ["脱敏", "****", "隐藏", "不可见", "前6位", "后4位", "掩码"]))
    checks.append({
        "name": "id_masking_permission_test",
        "passed": has_id_masking_test,
        "detail": "Must test that RiskOfficer sees masked ID card number"
    })
    
    # ---- CHECK 17: Duplicate submission protection ----
    has_duplicate_protection = any(kw in content for kw in ["重复点击", "禁用", "防重", "灰色", "不可用", "重复提交"])
    checks.append({
        "name": "duplicate_submission_protection",
        "passed": has_duplicate_protection,
        "detail": "Must test button disable after first click (duplicate submit protection)"
    })
    
    # ---- CHECK 18: Minimum number of test cases ----
    # Count table rows (lines that start with | and contain TC-)
    tc_rows = [line for line in content.split('\n') if re.search(r'\|\s*TC-\d+', line)]
    has_minimum_cases = len(tc_rows) >= 15
    checks.append({
        "name": "minimum_test_case_count",
        "passed": has_minimum_cases,
        "detail": f"Found {len(tc_rows)} test case rows. Need at least 15 for adequate coverage."
    })
    
    # ---- CHECK 19: Case types variety ----
    case_types = ["正向", "逆向", "边界", "权限", "流程", "UI", "数据校验"]
    types_found = [t for t in case_types if t in content]
    has_type_variety = len(types_found) >= 4
    checks.append({
        "name": "case_type_variety",
        "passed": has_type_variety,
        "detail": f"Case types found: {types_found}. Need at least 4 different types."
    })
    
    # ---- CHECK 20: Specific Toast / UI feedback in expected results ----
    has_specific_ui_feedback = any(kw in content for kw in [
        "Toast", "弹出", "提示", "跳转", "列表首行", "红色", "灰色", "禁用", "状态列"
    ])
    checks.append({
        "name": "specific_ui_feedback_in_expected_results",
        "passed": has_specific_ui_feedback,
        "detail": "Expected results must specify concrete UI feedback (Toast, page jump, color, state label etc.)"
    })
    
    # Calculate score
    passed_checks = [c for c in checks if c["passed"]]
    score = len(passed_checks) / len(checks)
    
    # Overall pass: must pass critical checks
    critical_checks = [
        "file_exists",
        "correct_table_headers",
        "tc_numbering_format",
        "valid_priority_labels",
        "p0_cases_present",
        "state_machine_coverage",
        "requirement_confirmation_section",
        "minimum_test_case_count",
    ]
    critical_passed = all(
        any(c["name"] == name and c["passed"] for c in checks)
        for name in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))