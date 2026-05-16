import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    workspace = Path(workspace_dir)

    # --- Find the output IDP file ---
    # The prompt asks for a file named zhao_lei_idp.md
    target_files = list(workspace.rglob("zhao_lei_idp.md"))

    def add_check(name, passed, detail):
        checks.append({"name": name, "passed": passed, "detail": detail})

    if not target_files:
        add_check("file_exists", False, "zhao_lei_idp.md not found anywhere in workspace.")
        score = 0.0
        return {"passed": False, "score": score, "checks": checks}

    idp_path = target_files[0]
    add_check("file_exists", True, f"Found at {idp_path}")

    try:
        content = idp_path.read_text(encoding="utf-8")
    except Exception as e:
        add_check("file_readable", False, f"Could not read file: {e}")
        return {"passed": False, "score": 0.0, "checks": checks}

    add_check("file_readable", True, f"File read successfully ({len(content)} chars)")

    # ---- CHECK 1: Gap Analysis Table ----
    # Must contain a markdown table with the 5 required columns
    required_table_headers = ["能力维度", "当前水平", "目标要求", "差距", "紧迫度"]
    table_header_found = all(h in content for h in required_table_headers)
    add_check(
        "gap_table_headers",
        table_header_found,
        "All 5 required table columns present." if table_header_found
        else f"Missing columns. Required: {required_table_headers}"
    )

    # ---- CHECK 2: All 6 competencies appear in the table ----
    required_competencies = ["资金管理", "融资筹划", "预算管理", "财务分析", "税务管理", "内部控制"]
    missing_comp = [c for c in required_competencies if c not in content]
    comp_all_present = len(missing_comp) == 0
    add_check(
        "gap_table_all_competencies",
        comp_all_present,
        "All 6 competency dimensions found." if comp_all_present
        else f"Missing competencies: {missing_comp}"
    )

    # ---- CHECK 3: Urgency levels 高/中/低 are present ----
    has_high = "高" in content
    has_mid = "中" in content
    has_low = "低" in content
    urgency_present = has_high and (has_mid or has_low)
    add_check(
        "urgency_levels_present",
        urgency_present,
        "紧迫度 levels (高/中/低) correctly applied in table." if urgency_present
        else "Missing urgency level indicators (高/中/低) in gap table."
    )

    # ---- CHECK 4: Gap values are correct ----
    # 资金管理: 5-3=2, 融资筹划: 5-2=3, 预算管理: 5-4=1
    # 财务分析: 4-3=1, 税务管理: 4-2=2, 内部控制: 4-3=1
    gap_checks = [
        ("资金管理 gap=2", "资金管理", "2"),
        ("融资筹划 gap=3 (largest)", "融资筹划", "3"),
        ("预算管理 gap=1", "预算管理", "1"),
    ]
    # Check by finding table rows - look for the pattern competency...gap_value
    table_section = content
    gap_correct_count = 0
    gap_details = []
    for check_name, comp, expected_gap in gap_checks:
        # Find lines containing the competency and check if the gap value appears nearby
        lines = [l for l in content.split('\n') if comp in l]
        found = any(expected_gap in l for l in lines)
        if found:
            gap_correct_count += 1
            gap_details.append(f"{comp}:✓")
        else:
            gap_details.append(f"{comp}:✗(expected gap={expected_gap})")

    gap_pass = gap_correct_count >= 2
    add_check(
        "gap_values_correct",
        gap_pass,
        f"Gap calculation check: {', '.join(gap_details)}"
    )

    # ---- CHECK 5: SMART Goals section ----
    smart_section_present = "发展目标" in content and "SMART" in content
    add_check(
        "smart_goals_section",
        smart_section_present,
        "SMART 发展目标 section found." if smart_section_present
        else "Missing 发展目标(SMART原则) section."
    )

    # ---- CHECK 6: Employee and position info correct ----
    has_zhao_lei = "赵磊" in content
    has_current_pos = "预算主管" in content
    has_target_pos = "预算经理" in content
    identity_correct = has_zhao_lei and has_current_pos and has_target_pos
    add_check(
        "employee_identity_correct",
        identity_correct,
        f"Employee/position info: 赵磊={has_zhao_lei}, 预算主管={has_current_pos}, 预算经理={has_target_pos}"
    )

    # ---- CHECK 7: 在岗历练 section ----
    has_onthejob = "在岗历练" in content
    add_check(
        "section_onthejob_training",
        has_onthejob,
        "在岗历练 section present." if has_onthejob else "Missing 在岗历练 section."
    )

    # ---- CHECK 8: 导师辅导 section ----
    has_mentor = "导师辅导" in content
    add_check(
        "section_mentor_coaching",
        has_mentor,
        "导师辅导 section present." if has_mentor else "Missing 导师辅导 section."
    )

    # ---- CHECK 9: 培训/认证 or 培训认证 section ----
    has_training = "培训" in content and ("认证" in content or "证书" in content)
    add_check(
        "section_training_certification",
        has_training,
        "培训/认证 section present." if has_training else "Missing 培训/认证 section."
    )

    # ---- CHECK 10: 自我学习 section ----
    has_self_learn = "自我学习" in content
    add_check(
        "section_self_learning",
        has_self_learn,
        "自我学习 section present." if has_self_learn else "Missing 自我学习 section."
    )

    # ---- CHECK 11: 时间节点 section ----
    has_timeline = "时间节点" in content or "时间" in content and "评估" in content
    add_check(
        "section_timeline_evaluation",
        has_timeline,
        "时间节点与评估方式 section present." if has_timeline else "Missing 时间节点与评估方式 section."
    )

    # ---- CHECK 12: Strategy integration - overseas business mentioned ----
    overseas_keywords = ["海外", "东南亚", "跨境", "境外", "国际", "overseas"]
    strategy_integrated = any(kw in content for kw in overseas_keywords)
    add_check(
        "strategy_integration",
        strategy_integrated,
        "Strategic context (海外业务) integrated into recommendations." if strategy_integrated
        else "No reference to overseas/international business strategy found - strategy input was ignored."
    )

    # ---- CHECK 13: 融资筹划 marked as highest urgency ----
    # 融资筹划 has the largest gap (3) and should have 高 urgency
    lines_with_rongzi = [l for l in content.split('\n') if "融资筹划" in l]
    rongzi_high = any("高" in l for l in lines_with_rongzi)
    add_check(
        "融资筹划_highest_urgency",
        rongzi_high,
        "融资筹划 correctly marked as 高 urgency (largest gap=3)." if rongzi_high
        else "融资筹划 should be 高 urgency (gap=3, largest) but was not marked so."
    )

    # ---- Compute score ----
    passed_checks = [c for c in checks if c["passed"]]
    score = round(len(passed_checks) / len(checks), 4)

    # Overall pass requires all critical checks
    critical = [
        "gap_table_headers", "gap_table_all_competencies", "urgency_levels_present",
        "smart_goals_section", "section_onthejob_training", "section_mentor_coaching",
        "section_training_certification", "section_self_learning",
        "section_timeline_evaluation", "strategy_integration",
        "融资筹划_highest_urgency"
    ]
    critical_passed = all(
        next((c["passed"] for c in checks if c["name"] == cn), False)
        for cn in critical
    )
    overall_passed = critical_passed and score >= 0.85

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))