import sys
import json
import re
from pathlib import Path

def load_result_file(workspace: Path):
    """Find the audit result JSON file."""
    candidates = list(workspace.rglob("audit_report.json"))
    if not candidates:
        # Also search common alternative names
        for alt in ["review_result.json", "审查结果.json", "bridge_audit.json"]:
            candidates = list(workspace.rglob(alt))
            if candidates:
                break
    return candidates[0] if candidates else None

def eval_agent(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    total_score = 0.0

    # ── STEP 1: Find and load the output file ──────────────────────────────
    result_file = load_result_file(workspace)
    file_found = result_file is not None

    checks.append({
        "name": "output_file_exists",
        "passed": file_found,
        "detail": f"Found: {result_file}" if file_found else "No audit_report.json (or equivalent) found in workspace"
    })

    if not file_found:
        return {
            "passed": False,
            "score": 0.0,
            "checks": checks
        }

    try:
        raw = result_file.read_text(encoding="utf-8")
        data = json.loads(raw)
    except Exception as e:
        checks.append({"name": "json_parseable", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "json_parseable", "passed": True, "detail": "JSON parsed successfully"})

    # ── STEP 2: Top-level schema check ─────────────────────────────────────
    has_审查结果 = "审查结果" in data and isinstance(data["审查结果"], list)
    has_总结 = "总结" in data and isinstance(data["总结"], str)

    checks.append({
        "name": "schema_审查结果_list",
        "passed": has_审查结果,
        "detail": f"Key '审查结果' present and is a list: {has_审查结果}"
    })
    checks.append({
        "name": "schema_总结_present",
        "passed": has_总结,
        "detail": f"Key '总结' present and is a string: {has_总结}"
    })

    if not has_审查结果:
        return {"passed": False, "score": 0.1, "checks": checks}

    items = data["审查结果"]

    # Helper: search items for a specific issue
    def find_item_matching(keywords: list, field: str = "不符合内容") -> list:
        """Return all items whose 'field' contains any of the keywords."""
        result = []
        for item in items:
            text = str(item.get(field, "")) + str(item.get("修改建议", "")) + str(item.get("来源位置", ""))
            if any(kw in text for kw in keywords):
                result.append(item)
        return result

    def item_has_type(item, type_value: str) -> bool:
        return type_value in str(item.get("类型", ""))

    def item_has_severity(item, severity: str) -> bool:
        return severity in str(item.get("严重程度", ""))

    # ── CHECK 3: ISSUE 1 — C50 vs C40 concrete conflict (上下文一致性, 高) ────
    issue1_items = find_item_matching(["C50", "C40"], "不符合内容")
    if not issue1_items:
        issue1_items = find_item_matching(["C50", "C40"])
    issue1_found = len(issue1_items) > 0
    issue1_type_correct = any(item_has_type(i, "上下文一致性") for i in issue1_items)
    issue1_severity_correct = any(item_has_severity(i, "高") for i in issue1_items)

    checks.append({
        "name": "issue1_concrete_conflict_found",
        "passed": issue1_found,
        "detail": f"C50/C40 concrete inconsistency detected: {issue1_found}. Items: {len(issue1_items)}"
    })
    checks.append({
        "name": "issue1_type_上下文一致性",
        "passed": issue1_type_correct,
        "detail": f"Classified as 上下文一致性: {issue1_type_correct}"
    })
    checks.append({
        "name": "issue1_severity_高",
        "passed": issue1_severity_correct,
        "detail": f"Severity '高': {issue1_severity_correct}"
    })

    # ── CHECK 4: ISSUE 2 — Q355D vs Q235C steel conflict (上下文一致性, 高) ──
    issue2_items = find_item_matching(["Q355", "Q235"])
    issue2_found = len(issue2_items) > 0
    issue2_type_correct = any(item_has_type(i, "上下文一致性") for i in issue2_items)
    issue2_severity_correct = any(item_has_severity(i, "高") for i in issue2_items)

    checks.append({
        "name": "issue2_steel_grade_conflict_found",
        "passed": issue2_found,
        "detail": f"Q355D/Q235C steel grade inconsistency detected: {issue2_found}"
    })
    checks.append({
        "name": "issue2_type_上下文一致性",
        "passed": issue2_type_correct,
        "detail": f"Classified as 上下文一致性: {issue2_type_correct}"
    })
    checks.append({
        "name": "issue2_severity_高",
        "passed": issue2_severity_correct,
        "detail": f"Severity '高': {issue2_severity_correct}"
    })

    # ── CHECK 5: ISSUE 3 — μ=0.25 vs μ=0.20 prestress conflict (上下文一致性, 中) ─
    issue3_items = find_item_matching(["0.25", "0.20", "摩擦系数", "μ"])
    # filter to those mentioning conflict between the two values
    issue3_conflict_items = [i for i in issue3_items if
                              ("0.25" in str(i) and "0.20" in str(i)) or
                              ("摩擦系数" in str(i) and ("0.25" in str(i) or "0.20" in str(i)))]
    issue3_found = len(issue3_conflict_items) > 0
    issue3_type_correct = any(item_has_type(i, "上下文一致性") for i in issue3_conflict_items)

    checks.append({
        "name": "issue3_prestress_mu_conflict_found",
        "passed": issue3_found,
        "detail": f"μ=0.25 vs μ=0.20 prestress friction coefficient conflict: {issue3_found}"
    })
    checks.append({
        "name": "issue3_type_上下文一致性",
        "passed": issue3_type_correct,
        "detail": f"Classified as 上下文一致性: {issue3_type_correct}"
    })

    # ── CHECK 6: ISSUE 4 — JT/T 329-2010 outdated norm (规范符合性, 高) ─────
    issue4_items = find_item_matching(["JT/T 329", "329-2010", "329-2025"])
    issue4_found = len(issue4_items) > 0
    issue4_type_correct = any(item_has_type(i, "规范符合性") for i in issue4_items)
    # Must mention the new version 2025
    issue4_new_version = any("2025" in str(i) for i in issue4_items)

    checks.append({
        "name": "issue4_outdated_norm_JT_T329_found",
        "passed": issue4_found,
        "detail": f"JT/T 329-2010 outdated norm flagged: {issue4_found}"
    })
    checks.append({
        "name": "issue4_type_规范符合性",
        "passed": issue4_type_correct,
        "detail": f"Classified as 规范符合性: {issue4_type_correct}"
    })
    checks.append({
        "name": "issue4_recommends_2025_version",
        "passed": issue4_new_version,
        "detail": f"Recommends JT/T 329-2025: {issue4_new_version}"
    })

    # ── CHECK 7: ISSUE 5 — Sa3 on-site derusting is wrong (规范符合性, 中) ──
    # Site work must use St3, not Sa3 (Sa3 requires factory/blast room)
    issue5_items = find_item_matching(["Sa3", "St3", "除锈", "工地", "喷砂"])
    # We want items that flag Sa3 as improper for on-site work
    issue5_sa3_flagged = [i for i in issue5_items if
                           "Sa3" in str(i) and
                           ("工地" in str(i) or "现场" in str(i) or "St3" in str(i) or "不可" in str(i))]
    issue5_found = len(issue5_sa3_flagged) > 0
    issue5_type_correct = any(item_has_type(i, "规范符合性") for i in issue5_sa3_flagged)
    issue5_recommends_st3 = any("St3" in str(i) for i in issue5_sa3_flagged)

    checks.append({
        "name": "issue5_sa3_onsite_improper_found",
        "passed": issue5_found,
        "detail": f"Sa3 on-site derusting flagged as improper: {issue5_found}"
    })
    checks.append({
        "name": "issue5_type_规范符合性",
        "passed": issue5_type_correct,
        "detail": f"Classified as 规范符合性: {issue5_type_correct}"
    })
    checks.append({
        "name": "issue5_recommends_St3",
        "passed": issue5_recommends_st3,
        "detail": f"Recommends St3 grade: {issue5_recommends_st3}"
    })

    # ── CHECK 8: ISSUE 6 — JC3 wrong for rural highway (规范符合性, 中) ────
    issue6_items = find_item_matching(["JC3", "JC2", "腐蚀环境", "乡村", "铁路"])
    issue6_jc3_flagged = [i for i in issue6_items if
                           "JC3" in str(i) and
                           ("JC2" in str(i) or "乡村" in str(i) or "高速" in str(i) or "铁路" in str(i))]
    issue6_found = len(issue6_jc3_flagged) > 0
    issue6_jc2_recommended = any("JC2" in str(i) for i in issue6_jc3_flagged)
    issue6_type_correct = any(item_has_type(i, "规范符合性") for i in issue6_jc3_flagged)

    checks.append({
        "name": "issue6_JC3_wrong_for_rural_highway",
        "passed": issue6_found,
        "detail": f"JC3 incorrect for rural highway (should be JC2) flagged: {issue6_found}"
    })
    checks.append({
        "name": "issue6_recommends_JC2",
        "passed": issue6_jc2_recommended,
        "detail": f"Recommends JC2 for rural area: {issue6_jc2_recommended}"
    })
    checks.append({
        "name": "issue6_type_规范符合性",
        "passed": issue6_type_correct,
        "detail": f"Classified as 规范符合性: {issue6_type_correct}"
    })

    # ── CHECK 9: ISSUE 7 — 80cm vs 100cm positioning bar spacing (上下文一致性, 低) ─
    issue7_items = find_item_matching(["80cm", "100cm", "定位筋", "间距"])
    issue7_conflict_items = [i for i in issue7_items if
                              ("80" in str(i) and "100" in str(i)) or
                              ("定位筋" in str(i))]
    issue7_found = len(issue7_conflict_items) > 0
    issue7_type_correct = any(item_has_type(i, "上下文一致性") for i in issue7_conflict_items)

    checks.append({
        "name": "issue7_positioning_bar_spacing_conflict",
        "passed": issue7_found,
        "detail": f"80cm vs 100cm positioning bar spacing conflict flagged: {issue7_found}"
    })
    checks.append({
        "name": "issue7_type_上下文一致性",
        "passed": issue7_type_correct,
        "detail": f"Classified as 上下文一致性: {issue7_type_correct}"
    })

    # ── CHECK 10: ISSUE 8 — water-cement ratio 0.38 ≤ 0.40 should NOT be flagged ─
    # The agent must NOT flag this as inconsistent (it satisfies the range)
    false_positive_items = []
    for item in items:
        content = str(item.get("不符合内容", "")) + str(item.get("来源位置", ""))
        if "0.38" in content and "0.40" in content:
            # Check it's not flagged as 不一致/conflict — if it's flagged, it's a false positive
            item_type_text = str(item.get("类型", ""))
            severity_text = str(item.get("严重程度", ""))
            # If the item classifies this as 不一致 with high/medium severity, it's wrong
            if ("不一致" in item_type_text or "冲突" in item_type_text) and severity_text in ["高", "中"]:
                false_positive_items.append(item)

    no_false_positive_wc_ratio = len(false_positive_items) == 0
    checks.append({
        "name": "no_false_positive_water_cement_ratio",
        "passed": no_false_positive_wc_ratio,
        "detail": f"Water-cement ratio 0.38 (satisfies ≤0.40) NOT wrongly flagged as inconsistent: {no_false_positive_wc_ratio}"
    })

    # ── CHECK 11: Required JSON fields in each item ──────────────────────────
    required_fields = ["类型", "不符合内容", "修改建议", "严重程度", "来源位置"]
    items_with_all_fields = 0
    for item in items:
        if all(f in item for f in required_fields):
            items_with_all_fields += 1

    field_completeness = items_with_all_fields / max(len(items), 1)
    fields_ok = field_completeness >= 0.8

    checks.append({
        "name": "items_have_required_fields",
        "passed": fields_ok,
        "detail": f"{items_with_all_fields}/{len(items)} items have all required fields (类型/不符合内容/修改建议/严重程度/来源位置)"
    })

    # ── CHECK 12: Railway norm inapplicability flagged ───────────────────────
    railway_norm_flagged = any(
        "TB/T" in str(item) or "铁路" in str(item.get("不符合内容", "")) or "铁路" in str(item.get("修改建议", ""))
        for item in items
    )
    checks.append({
        "name": "railway_norm_inapplicable_flagged",
        "passed": railway_norm_flagged,
        "detail": f"Railway norm TB/T 1979 inapplicability for highway bridge flagged: {railway_norm_flagged}"
    })

    # ── SCORING ──────────────────────────────────────────────────────────────
    # Weights for each check
    weights = {
        "output_file_exists": 2,
        "json_parseable": 2,
        "schema_审查结果_list": 1,
        "schema_总结_present": 1,
        # Issue 1: C50/C40 - 3 checks × 3 = 9
        "issue1_concrete_conflict_found": 3,
        "issue1_type_上下文一致性": 3,
        "issue1_severity_高": 3,
        # Issue 2: Q355D/Q235C - 3 checks × 3 = 9
        "issue2_steel_grade_conflict_found": 3,
        "issue2_type_上下文一致性": 3,
        "issue2_severity_高": 3,
        # Issue 3: mu=0.25 vs 0.20 - 2 checks × 2 = 4
        "issue3_prestress_mu_conflict_found": 2,
        "issue3_type_上下文一致性": 2,
        # Issue 4: JT/T 329-2010 outdated - 3 checks × 3 = 9
        "issue4_outdated_norm_JT_T329_found": 3,
        "issue4_type_规范符合性": 3,
        "issue4_recommends_2025_version": 3,
        # Issue 5: Sa3 onsite - 3 checks × 3 = 9
        "issue5_sa3_onsite_improper_found": 3,
        "issue5_type_规范符合性": 3,
        "issue5_recommends_St3": 3,
        # Issue 6: JC3 wrong - 3 checks × 3 = 9
        "issue6_JC3_wrong_for_rural_highway": 3,
        "issue6_recommends_JC2": 3,
        "issue6_type_规范符合性": 3,
        # Issue 7: positioning bar - 2 checks × 2 = 4
        "issue7_positioning_bar_spacing_conflict": 2,
        "issue7_type_上下文一致性": 2,
        # No false positive - 3
        "no_false_positive_water_cement_ratio": 3,
        # Field completeness - 2
        "items_have_required_fields": 2,
        # Railway norm - 2
        "railway_norm_inapplicable_flagged": 2,
    }

    total_weight = sum(weights.values())
    earned = sum(weights[c["name"]] for c in checks if c["passed"] and c["name"] in weights)
    score = round(earned / total_weight, 4)

    # Passing threshold: must score ≥ 0.65 AND pass all critical checks
    critical_passed = all(
        c["passed"] for c in checks
        if c["name"] in [
            "output_file_exists", "json_parseable", "schema_审查结果_list",
            "issue1_concrete_conflict_found", "issue2_steel_grade_conflict_found",
            "issue4_outdated_norm_JT_T329_found", "issue5_sa3_onsite_improper_found",
            "issue6_JC3_wrong_for_rural_highway",
        ]
    )
    passed = score >= 0.65 and critical_passed

    return {
        "passed": passed,
        "score": score,
        "checks": checks
    }

if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = eval_agent(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))