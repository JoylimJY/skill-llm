#!/usr/bin/env python3
import sys
import json
import os
from pathlib import Path

def evaluate(workspace_dir: str):
    checks = []
    total_score = 0.0

    def add_check(name, passed, detail, weight=1.0):
        checks.append({"name": name, "passed": passed, "detail": detail})
        return weight if passed else 0.0

    # ── Find output files ──────────────────────────────────────────────────────
    json_files = list(Path(workspace_dir).rglob("candidate_tracking_report.json"))
    md_files = list(Path(workspace_dir).rglob("candidate_dashboard.md"))

    json_path = json_files[0] if json_files else None
    md_path = md_files[0] if md_files else None

    score = 0.0

    # CHECK 1: JSON file exists
    if json_path and json_path.exists():
        score += add_check("json_file_exists", True, f"Found JSON at {json_path}", weight=0.5)
    else:
        add_check("json_file_exists", False, "candidate_tracking_report.json not found anywhere in workspace", weight=0.5)

    # CHECK 2: Markdown file exists
    if md_path and md_path.exists():
        score += add_check("markdown_file_exists", True, f"Found Markdown at {md_path}", weight=0.5)
    else:
        add_check("markdown_file_exists", False, "candidate_dashboard.md not found anywhere in workspace", weight=0.5)

    # ── Parse JSON ────────────────────────────────────────────────────────────
    data = None
    if json_path:
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            # Handle case where JSON is wrapped in markdown code block
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
            data = json.loads(content)
            score += add_check("json_parseable", True, "JSON file is valid and parseable", weight=0.5)
        except Exception as e:
            add_check("json_parseable", False, f"JSON parse error: {e}", weight=0.5)

    if data is None:
        # Can't do further JSON checks
        final_score = score / 15.0  # normalize against max possible
        return {
            "passed": final_score >= 0.5,
            "score": min(1.0, final_score),
            "checks": checks
        }

    # CHECK 3: Top-level structure has required keys
    required_keys = {"operation", "candidates", "dashboard", "reminders", "alerts"}
    missing_keys = required_keys - set(data.keys())
    if not missing_keys:
        score += add_check("json_top_level_keys", True, "All required top-level keys present", weight=0.5)
    else:
        add_check("json_top_level_keys", False, f"Missing keys: {missing_keys}", weight=0.5)

    candidates = data.get("candidates", [])

    # CHECK 4: All 10 candidates present (9 named + 1 from sources)
    # We expect at least 9 candidates from the 3 source files
    expected_names = {"张伟", "陈静", "刘洋", "赵磊", "孙芳", "王强", "李梅", "吴浩", "周建国", "郑云"}
    found_names = {c.get("name", "") for c in candidates}
    matched = expected_names & found_names
    if len(matched) >= 9:
        score += add_check("all_candidates_present", True, f"Found {len(matched)}/10 expected candidates: {sorted(matched)}", weight=1.0)
    elif len(matched) >= 7:
        score += add_check("all_candidates_present", True, f"Found {len(matched)}/10 expected candidates (acceptable): {sorted(matched)}", weight=0.7)
    else:
        add_check("all_candidates_present", False, f"Only found {len(matched)}/10 candidates. Found: {sorted(found_names)}, Missing: {sorted(expected_names - found_names)}", weight=1.0)

    # CHECK 5: Correct status values (must use Chinese enum values)
    VALID_STATUSES = {"初筛", "面试", "Offer", "拒绝", "入职", "人才库"}
    invalid_status_candidates = []
    for c in candidates:
        status = c.get("status", "")
        if status not in VALID_STATUSES:
            invalid_status_candidates.append(f"{c.get('name','?')}:{status}")
    if not invalid_status_candidates:
        score += add_check("valid_status_values", True, f"All candidates use valid status enum values from: {VALID_STATUSES}", weight=1.0)
    else:
        add_check("valid_status_values", False, f"Invalid status values found: {invalid_status_candidates}. Must use: {VALID_STATUSES}", weight=1.0)

    # CHECK 6: Specific status mappings
    status_map_checks = []
    for c in candidates:
        name = c.get("name", "")
        status = c.get("status", "")
        if name == "赵磊":
            # Offer sent, not yet confirmed → should be "Offer"
            if status == "Offer":
                status_map_checks.append(f"赵磊→Offer: CORRECT")
            else:
                status_map_checks.append(f"赵磊→{status}: WRONG (expected Offer)")
        if name == "周建国":
            # offer_accepted → should be "入职"
            if status == "入职":
                status_map_checks.append(f"周建国→入职: CORRECT")
            else:
                status_map_checks.append(f"周建国→{status}: WRONG (expected 入职)")
        if name == "吴浩":
            # 建议放入人才库 → should be "人才库"
            if status == "人才库":
                status_map_checks.append(f"吴浩→人才库: CORRECT")
            else:
                status_map_checks.append(f"吴浩→{status}: WRONG (expected 人才库)")
        if name == "刘洋":
            # 二面已完成，等待三面 → 面试
            if status == "面试":
                status_map_checks.append(f"刘洋→面试: CORRECT")
            else:
                status_map_checks.append(f"刘洋→{status}: WRONG (expected 面试)")

    correct_mappings = sum(1 for s in status_map_checks if "CORRECT" in s)
    total_mappings = len(status_map_checks)
    if total_mappings > 0 and correct_mappings >= 3:
        score += add_check("status_mapping_correctness", True, f"Status mappings: {status_map_checks}", weight=1.5)
    else:
        add_check("status_mapping_correctness", False, f"Status mapping errors: {status_map_checks} ({correct_mappings}/{total_mappings} correct)", weight=1.5)

    # CHECK 7: Dashboard structure with all 6 status keys
    dashboard = data.get("dashboard", {})
    by_status = dashboard.get("by_status", {})
    required_status_keys = {"初筛", "面试", "Offer", "拒绝", "入职", "人才库"}
    missing_dashboard_keys = required_status_keys - set(by_status.keys())
    if not missing_dashboard_keys:
        score += add_check("dashboard_all_status_keys", True, f"Dashboard by_status has all 6 required keys: {list(by_status.keys())}", weight=1.0)
    else:
        add_check("dashboard_all_status_keys", False, f"Dashboard missing status keys: {missing_dashboard_keys}. Found: {list(by_status.keys())}", weight=1.0)

    # CHECK 8: Dashboard total matches candidate count
    total_in_dashboard = dashboard.get("total", 0)
    actual_candidate_count = len(candidates)
    if total_in_dashboard == actual_candidate_count:
        score += add_check("dashboard_total_matches", True, f"Dashboard total ({total_in_dashboard}) matches candidate count ({actual_candidate_count})", weight=0.5)
    else:
        add_check("dashboard_total_matches", False, f"Dashboard total ({total_in_dashboard}) does not match candidate count ({actual_candidate_count})", weight=0.5)

    # CHECK 9: Dashboard by_status counts sum to total
    status_sum = sum(v for v in by_status.values() if isinstance(v, (int, float)))
    if abs(status_sum - total_in_dashboard) <= 1:  # allow 1 rounding
        score += add_check("dashboard_counts_consistent", True, f"Status counts sum ({status_sum}) consistent with total ({total_in_dashboard})", weight=0.5)
    else:
        add_check("dashboard_counts_consistent", False, f"Status counts sum ({status_sum}) inconsistent with total ({total_in_dashboard})", weight=0.5)

    # CHECK 10: Reminders array present and non-empty
    reminders = data.get("reminders", [])
    if isinstance(reminders, list) and len(reminders) >= 2:
        score += add_check("reminders_populated", True, f"Reminders array has {len(reminders)} entries", weight=0.5)
    else:
        add_check("reminders_populated", False, f"Reminders array missing or has fewer than 2 entries. Found: {len(reminders) if isinstance(reminders, list) else 'N/A'}", weight=0.5)

    # CHECK 11: Reminder for 王强 (18 days no contact - must be high priority)
    wangqiang_reminder = None
    for r in reminders:
        if "王强" in r.get("candidate", "") or "王强" in str(r):
            wangqiang_reminder = r
            break
    if wangqiang_reminder:
        priority = wangqiang_reminder.get("priority", "")
        if priority == "高":
            score += add_check("reminder_wangqiang_high_priority", True, f"王强 reminder found with correct high priority: {wangqiang_reminder}", weight=1.0)
        else:
            add_check("reminder_wangqiang_high_priority", False, f"王强 reminder found but priority is '{priority}' (expected '高'). 18 days no contact should trigger high priority.", weight=1.0)
    else:
        add_check("reminder_wangqiang_high_priority", False, "No reminder found for 王强 (18 days no contact → must trigger high priority reminder)", weight=1.0)

    # CHECK 12: Reminder for 赵磊 (Offer >3 days unconfirmed)
    zhaolei_reminder = None
    for r in reminders:
        if "赵磊" in r.get("candidate", "") or "赵磊" in str(r):
            zhaolei_reminder = r
            break
    if zhaolei_reminder:
        score += add_check("reminder_zhaolei_offer", True, f"赵磊 reminder found (Offer >3 days unconfirmed): {zhaolei_reminder}", weight=1.0)
    else:
        add_check("reminder_zhaolei_offer", False, "No reminder for 赵磊 (Offer issued >3 days without confirmation)", weight=1.0)

    # CHECK 13: Alerts array present and contains appropriate alert types
    alerts = data.get("alerts", [])
    if isinstance(alerts, list) and len(alerts) >= 1:
        # Check for follow-up lag alert (跟进滞后 or similar)
        has_followup_alert = any(
            "滞后" in str(a) or "跟进" in str(a) or "未联系" in str(a) or "超过" in str(a)
            for a in alerts
        )
        if has_followup_alert:
            score += add_check("alerts_followup_lag", True, f"Follow-up lag alert present in alerts", weight=0.5)
        else:
            add_check("alerts_followup_lag", False, f"No follow-up lag alert found. Alerts: {alerts}", weight=0.5)

        # Check for Offer waiting alert
        has_offer_alert = any(
            "Offer" in str(a) or "offer" in str(a) or "等待" in str(a)
            for a in alerts
        )
        if has_offer_alert:
            score += add_check("alerts_offer_waiting", True, f"Offer waiting alert present", weight=0.5)
        else:
            add_check("alerts_offer_waiting", False, f"No Offer waiting alert found. Alerts: {alerts}", weight=0.5)
    else:
        add_check("alerts_followup_lag", False, "Alerts array is empty or missing", weight=0.5)
        add_check("alerts_offer_waiting", False, "Alerts array is empty or missing", weight=0.5)

    # CHECK 14: Each candidate has required fields
    CANDIDATE_REQUIRED = {"id", "name", "position", "status", "tags", "source", "applied_date", "next_action", "notes", "history"}
    candidates_with_all_fields = 0
    for c in candidates:
        if all(k in c for k in CANDIDATE_REQUIRED):
            candidates_with_all_fields += 1
    ratio = candidates_with_all_fields / max(len(candidates), 1)
    if ratio >= 0.8:
        score += add_check("candidate_required_fields", True, f"{candidates_with_all_fields}/{len(candidates)} candidates have all required fields", weight=1.0)
    else:
        add_check("candidate_required_fields", False, f"Only {candidates_with_all_fields}/{len(candidates)} candidates have all required fields. Required: {CANDIDATE_REQUIRED}", weight=1.0)

    # CHECK 15: next_action.priority uses correct Chinese values
    VALID_PRIORITY = {"高", "中", "低"}
    invalid_priority = []
    for c in candidates:
        na = c.get("next_action", {})
        if isinstance(na, dict):
            p = na.get("priority", "")
            if p and p not in VALID_PRIORITY:
                invalid_priority.append(f"{c.get('name','?')}:{p}")
    if not invalid_priority:
        score += add_check("priority_chinese_values", True, f"All next_action.priority values use Chinese enum (高|中|低)", weight=1.0)
    else:
        add_check("priority_chinese_values", False, f"Invalid priority values (must be 高|中|低): {invalid_priority}", weight=1.0)

    # CHECK 16: Tags are arrays with at least 2 tags per candidate
    candidates_with_tags = sum(1 for c in candidates if isinstance(c.get("tags"), list) and len(c.get("tags", [])) >= 2)
    ratio_tags = candidates_with_tags / max(len(candidates), 1)
    if ratio_tags >= 0.7:
        score += add_check("tags_populated", True, f"{candidates_with_tags}/{len(candidates)} candidates have >=2 tags", weight=0.5)
    else:
        add_check("tags_populated", False, f"Only {candidates_with_tags}/{len(candidates)} candidates have >=2 tags", weight=0.5)

    # CHECK 17: History records exist for candidates with interview progression
    # 刘洋 (二面已完成) should have multiple history entries
    liuyang = next((c for c in candidates if c.get("name") == "刘洋"), None)
    if liuyang:
        history = liuyang.get("history", [])
        if isinstance(history, list) and len(history) >= 2:
            score += add_check("history_records_liuyang", True, f"刘洋 has {len(history)} history entries (二面progression tracked)", weight=0.5)
        else:
            add_check("history_records_liuyang", False, f"刘洋 should have >=2 history entries for interview progression. Found: {len(history) if isinstance(history, list) else 'N/A'}", weight=0.5)
    else:
        add_check("history_records_liuyang", False, "刘洋 not found in candidates", weight=0.5)

    # ── Markdown checks ───────────────────────────────────────────────────────
    md_content = ""
    if md_path and md_path.exists():
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
        except Exception as e:
            add_check("markdown_readable", False, f"Cannot read markdown: {e}", weight=0.5)

    if md_content:
        score += add_check("markdown_readable", True, "Markdown file is readable", weight=0.3)

        # CHECK 18: Markdown has dashboard table
        has_table = "|" in md_content and "状态" in md_content and "数量" in md_content
        if has_table:
            score += add_check("markdown_dashboard_table", True, "Markdown contains status dashboard table with 状态|数量 columns", weight=0.5)
        else:
            add_check("markdown_dashboard_table", False, "Markdown missing dashboard table with 状态|数量 columns", weight=0.5)

        # CHECK 19: Markdown has emoji section headers from template
        has_dashboard_emoji = "📊" in md_content or "## 📊" in md_content
        has_reminder_section = "🔄" in md_content or "待处理" in md_content
        has_alert_section = "⚠️" in md_content or "警告" in md_content
        has_details_section = "📋" in md_content or "候选人详情" in md_content

        md_sections_found = sum([has_dashboard_emoji, has_reminder_section, has_alert_section, has_details_section])
        if md_sections_found >= 3:
            score += add_check("markdown_section_headers", True, f"Markdown has {md_sections_found}/4 expected section headers with emoji markers", weight=0.5)
        else:
            add_check("markdown_section_headers", False, f"Markdown only has {md_sections_found}/4 expected emoji-marked sections (📊, 🔄, ⚠️, 📋)", weight=0.5)

        # CHECK 20: Key candidate names appear in markdown
        names_in_md = sum(1 for name in ["张伟", "陈静", "刘洋", "赵磊", "王强", "李梅", "周建国"] if name in md_content)
        if names_in_md >= 6:
            score += add_check("markdown_candidate_names", True, f"{names_in_md}/7 key candidate names found in markdown", weight=0.5)
        else:
            add_check("markdown_candidate_names", False, f"Only {names_in_md}/7 key candidate names found in markdown", weight=0.5)

    # ── Final scoring ─────────────────────────────────────────────────────────
    max_possible_score = (
        0.5 + 0.5 + 0.5 + 1.0 + 1.0 + 1.5 + 1.0 + 0.5 + 0.5 + 0.5 +
        1.0 + 1.0 + 0.5 + 0.5 + 1.0 + 1.0 + 0.5 + 0.5 + 0.3 + 0.5 + 0.5 + 0.5
    )
    normalized = min(1.0, score / max_possible_score)
    passed = normalized >= 0.55

    return {
        "passed": passed,
        "score": round(normalized, 3),
        "checks": checks
    }

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))