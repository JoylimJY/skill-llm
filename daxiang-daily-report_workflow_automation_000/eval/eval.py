import json
import re
import sys
from pathlib import Path

def evaluate(workspace: str):
    checks = []
    
    # === FIND THE REPORT FILE ===
    target_date = "2026-03-12"
    expected_filename = f"daxiang_{target_date}_v1.md"
    
    found_files = list(Path(workspace).rglob(expected_filename))
    
    # Exclude archive/old files in archive directory
    found_files = [f for f in found_files if "archive" not in str(f)]
    
    if not found_files:
        checks.append({
            "name": "report_file_exists",
            "passed": False,
            "detail": f"File '{expected_filename}' not found in workspace. Agent must generate this file."
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    report_path = found_files[0]
    checks.append({
        "name": "report_file_exists",
        "passed": True,
        "detail": f"Found report at: {report_path}"
    })
    
    try:
        content = report_path.read_text(encoding="utf-8")
    except Exception as e:
        checks.append({
            "name": "report_readable",
            "passed": False,
            "detail": f"Could not read file: {e}"
        })
        return {"passed": False, "score": 0.0, "checks": checks}
    
    checks.append({
        "name": "report_readable",
        "passed": True,
        "detail": f"File readable, {len(content)} characters."
    })

    # === CHECK 1: CORRECT DATE IN TITLE ===
    date_in_title = "2026-03-12" in content
    checks.append({
        "name": "correct_date_in_report",
        "passed": date_in_title,
        "detail": "Report title contains '2026-03-12'" if date_in_title else "Date '2026-03-12' not found in report"
    })

    # === CHECK 2: ALL 6 SECTIONS PRESENT ===
    section_patterns = [
        (r"一[、.].*数据概览|📈.*一[、、]|一、今日数据概览", "Section 1: 数据概览"),
        (r"二[、.].*时间|⏰.*二[、、]|二、时间精力分布", "Section 2: 时间精力分布"),
        (r"三[、.].*单人|🗣.*三[、、]|三、单人沟通分析", "Section 3: 单人沟通分析"),
        (r"四[、.].*群聊|💬.*四[、、]|四、群聊汇总", "Section 4: 群聊汇总"),
        (r"五[、.].*洞察|💡.*五[、、]|五、整体洞察", "Section 5: 整体洞察"),
        (r"六[、.].*todo|✅.*六[、、]|六、todo清单", "Section 6: todo清单"),
    ]
    
    all_sections_present = True
    for pattern, name in section_patterns:
        found = bool(re.search(pattern, content, re.IGNORECASE))
        if not found:
            all_sections_present = False
        checks.append({
            "name": f"section_present_{name}",
            "passed": found,
            "detail": f"{name} {'found' if found else 'NOT FOUND'} in report"
        })

    # === CHECK 3: DATA OVERVIEW TABLE - correct counts ===
    # personal: 5 contacts (张伟, 李娜, 王强, 陈敏, 刘洋)
    # groups: 3 (产品研发同步群, 技术部全员群, 运营技术协同群)
    # system notifications: 5
    # total messages: shuffled but count is fixed
    
    # Check personal contact count (should be 5)
    personal_5 = bool(re.search(r'个人对话.*?5\s*人|5\s*人.*?个人对话', content, re.DOTALL))
    checks.append({
        "name": "data_overview_personal_count",
        "passed": personal_5,
        "detail": "Personal contact count shows 5" if personal_5 else "Personal contact count does not show 5 (expected 5 unique contacts)"
    })

    # Check group count (should be 3)
    group_3 = bool(re.search(r'活跃群聊.*?3\b|3\b.*?活跃群聊|群聊.*?\|\s*3\b', content, re.DOTALL))
    checks.append({
        "name": "data_overview_group_count",
        "passed": group_3,
        "detail": "Active group count shows 3" if group_3 else "Active group count does not show 3 (expected 3 groups)"
    })
    
    # Check system notification count (should be 5)
    sys_5 = bool(re.search(r'系统通知.*?5\b|5\b.*?系统通知', content, re.DOTALL))
    checks.append({
        "name": "data_overview_system_count",
        "passed": sys_5,
        "detail": "System notification count shows 5" if sys_5 else "System notification count does not show 5 (expected 5)"
    })

    # === CHECK 4: TIME SEGMENTS - all 4 present ===
    time_segments = ["上午", "下午", "晚间", "凌晨"]
    for seg in time_segments:
        found = seg in content
        checks.append({
            "name": f"time_segment_{seg}",
            "passed": found,
            "detail": f"Time segment '{seg}' {'found' if found else 'NOT FOUND'}"
        })

    # === CHECK 5: ALL 5 PERSONAL CONTACTS ANALYZED ===
    contacts = ["张伟", "李娜", "王强", "陈敏", "刘洋"]
    for contact in contacts:
        found = contact in content
        checks.append({
            "name": f"contact_analyzed_{contact}",
            "passed": found,
            "detail": f"Contact '{contact}' {'found' if found else 'NOT FOUND'} in report"
        })

    # === CHECK 6: COMPLETE CONVERSATION TABLE for personal contacts ===
    # The key proprietary requirement: 完整沟通内容表格 with columns 时间|说话人|具体内容
    table_header_pattern = r'时间\s*\|.*?说话人\s*\|.*?具体内容|时间.*?说话人.*?具体内容'
    has_conversation_table = bool(re.search(table_header_pattern, content, re.DOTALL))
    checks.append({
        "name": "complete_conversation_table_present",
        "passed": has_conversation_table,
        "detail": "完整沟通内容表格 with 时间|说话人|具体内容 columns found" if has_conversation_table else "MISSING: 完整沟通内容表格 (时间|说话人|具体内容) not found - this is a required proprietary format"
    })
    
    # Check that actual message content appears verbatim in the table (not just summarized)
    key_messages = [
        "今天的版本发布计划确认了吗",
        "索引没有及时刷新",
        "上午处理",
    ]
    verbatim_count = 0
    for msg in key_messages:
        if msg in content:
            verbatim_count += 1
    
    verbatim_ok = verbatim_count >= 2
    checks.append({
        "name": "verbatim_messages_in_table",
        "passed": verbatim_ok,
        "detail": f"Found {verbatim_count}/{len(key_messages)} verbatim message contents in report (need >= 2). This tests that messages are NOT truncated/summarized."
    })

    # === CHECK 7: STAR RATINGS in Section 3 ===
    has_star_rating = bool(re.search(r'[⭐★]{1,5}', content))
    checks.append({
        "name": "star_ratings_present",
        "passed": has_star_rating,
        "detail": "Star ratings (⭐ or ★) found in individual contact analysis" if has_star_rating else "MISSING: Star ratings not found in contact analysis"
    })

    # === CHECK 8: GROUP ANALYSIS - all 3 groups present ===
    groups = ["产品研发同步群", "技术部全员群", "运营技术协同群"]
    for group in groups:
        found = group in content
        checks.append({
            "name": f"group_analyzed_{group}",
            "passed": found,
            "detail": f"Group '{group}' {'found' if found else 'NOT FOUND'} in group analysis"
        })

    # === CHECK 9: @ME MENTIONS TRACKED ===
    # 产品研发同步群: 2 @me, 技术部全员群: 1 @me, 运营技术协同群: 1 @me
    at_me_tracked = bool(re.search(r'@我.*?[1-4]\s*次|[1-4]\s*次.*?@我|at_me|@我的', content, re.DOTALL))
    checks.append({
        "name": "at_me_mentions_tracked",
        "passed": at_me_tracked,
        "detail": "@我 mention counts tracked in group analysis" if at_me_tracked else "MISSING: @我 mention tracking not found in group analysis"
    })

    # === CHECK 10: TODO LIST ITEMS ===
    # Expected todos from conversations:
    # - 确认发布计划 (from 张伟)
    # - review产品文档 (from 张伟)
    # - 通知测试上测试环境 (from 李娜)
    # - 评估运营活动需求 (from 王强)
    # - 配置新同学权限 (from 陈敏)
    # - 准备技术分享PPT (from 刘洋)
    
    todo_keywords = ["发布", "review", "需求", "权限", "分享", "PPT", "排期", "评估", "文档"]
    todo_found_count = sum(1 for kw in todo_keywords if kw in content)
    has_todos = todo_found_count >= 3
    checks.append({
        "name": "todo_list_populated",
        "passed": has_todos,
        "detail": f"Todo list contains relevant items ({todo_found_count}/{len(todo_keywords)} keywords found)" if has_todos else f"MISSING: Todo list appears empty or incomplete (only {todo_found_count}/{len(todo_keywords)} keywords found)"
    })

    # === CHECK 11: SECTION 5 INSIGHTS ===
    insight_keywords = ["沟通重心", "协同", "时间投入", "待办"]
    insight_count = sum(1 for kw in insight_keywords if kw in content)
    has_insights = insight_count >= 2
    checks.append({
        "name": "section5_insights",
        "passed": has_insights,
        "detail": f"Section 5 insights found ({insight_count}/4 keywords)" if has_insights else f"Section 5 insights insufficient ({insight_count}/4 keywords found)"
    })

    # === CHECK 12: SYSTEM NOTIFICATIONS FILTERED FROM PERSONAL/GROUP COUNTS ===
    # Verify system messages are counted separately, not mixed into personal chats
    # The overview table should NOT show system contacts as personal chats
    system_as_personal = bool(re.search(r'个人对话.*?[6-9]\s*人|[6-9]\s*人.*?个人对话', content, re.DOTALL))
    # If it shows 6+ personal contacts, system msgs weren't filtered
    system_filtered = not system_as_personal
    checks.append({
        "name": "system_notifications_filtered",
        "passed": system_filtered,
        "detail": "System notifications correctly excluded from personal contact count" if system_filtered else "System notifications NOT filtered: personal count appears inflated (>= 6, expected 5)"
    })

    # === COMPUTE SCORE ===
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    
    # Must pass critical checks to overall pass
    critical_checks = [
        "report_file_exists",
        "correct_date_in_report",
        "complete_conversation_table_present",
        "verbatim_messages_in_table",
        "star_ratings_present",
        "todo_list_populated",
    ]
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_checks
    )
    
    overall_passed = critical_passed and score >= 0.70
    
    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace)
    print(json.dumps(result, ensure_ascii=False, indent=2))