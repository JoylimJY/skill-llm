import sys
import json
import re
from pathlib import Path

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    checks = []
    
    TARGET_CHAT_ID = "oc_1736efe0d350b597267e3ed59bcc8f42"
    TODAY = "2026-04-15"
    
    group_memory_path = workspace / f"memory/FeishuGroupMemory/{TARGET_CHAT_ID}.md"
    daily_memory_path = workspace / f"memory/{TODAY}.md"

    # =====================================================================
    # CHECK 1: Group memory file exists
    # =====================================================================
    try:
        exists = group_memory_path.exists()
        checks.append({
            "name": "group_memory_file_exists",
            "passed": exists,
            "detail": f"Group memory file {'found' if exists else 'NOT FOUND'} at {group_memory_path}"
        })
    except Exception as e:
        checks.append({"name": "group_memory_file_exists", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 2: OLD content is PRESERVED (not overwritten)
    # Critical proprietary trap: agent must merge, not overwrite
    # =====================================================================
    try:
        content = group_memory_path.read_text(encoding="utf-8")
        
        # These are from the ORIGINAL file that must be preserved
        original_decisions = [
            "gRPC 替代 REST",
            "PostgreSQL 为主数据库",
            "代码审查必须至少 2 人",
        ]
        original_todos = [
            "编写数据库迁移脚本",
        ]
        original_context = [
            "ProjectNova",
            "6 人",
        ]
        
        preserved = all(phrase in content for phrase in 
                       original_decisions + original_todos + original_context)
        
        missing = [p for p in original_decisions + original_todos + original_context 
                  if p not in content]
        
        checks.append({
            "name": "historical_content_preserved",
            "passed": preserved,
            "detail": f"Original content preservation: {'PASS' if preserved else 'FAIL - OVERWRITE DETECTED'}. Missing: {missing}"
        })
    except Exception as e:
        checks.append({"name": "historical_content_preserved", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 3: NEW content from today's session is added
    # =====================================================================
    try:
        content = group_memory_path.read_text(encoding="utf-8")
        
        new_content_markers = [
            "staging",           # staging environment was set up
            "PR #241",           # gRPC proto PR
            "联调",              # interface alignment scheduled
        ]
        
        new_items_found = [m for m in new_content_markers if m in content]
        passed = len(new_items_found) >= 2
        
        checks.append({
            "name": "new_session_content_added",
            "passed": passed,
            "detail": f"New session content markers found: {new_items_found} ({len(new_items_found)}/{len(new_content_markers)} required >= 2)"
        })
    except Exception as e:
        checks.append({"name": "new_session_content_added", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 4: Timestamp updated to today
    # =====================================================================
    try:
        content = group_memory_path.read_text(encoding="utf-8")
        # Must contain 2026-04-15 as updated timestamp
        has_today = "2026-04-15" in content
        checks.append({
            "name": "timestamp_updated_to_today",
            "passed": has_today,
            "detail": f"Updated timestamp '2026-04-15' {'found' if has_today else 'NOT FOUND'} in group memory file"
        })
    except Exception as e:
        checks.append({"name": "timestamp_updated_to_today", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 5: Required markdown structure is maintained
    # The skill specifies exact section headers
    # =====================================================================
    try:
        content = group_memory_path.read_text(encoding="utf-8")
        required_sections = [
            "## 最后更新时间",
            "## 关键决策",
            "## 待办事项",
            "## 重要上下文",
            "## 对话摘要",
        ]
        sections_found = [s for s in required_sections if s in content]
        passed = len(sections_found) == len(required_sections)
        
        missing_sections = [s for s in required_sections if s not in content]
        checks.append({
            "name": "required_markdown_structure_maintained",
            "passed": passed,
            "detail": f"Required sections: {len(sections_found)}/{len(required_sections)}. Missing: {missing_sections}"
        })
    except Exception as e:
        checks.append({"name": "required_markdown_structure_maintained", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 6: File title contains group name or chat ID
    # =====================================================================
    try:
        content = group_memory_path.read_text(encoding="utf-8")
        first_line = content.strip().split('\n')[0]
        has_title = first_line.startswith('#') and len(first_line) > 2
        # Should reference the group
        has_group_ref = "工程" in content or "engineering" in content.lower() or TARGET_CHAT_ID in content
        passed = has_title and has_group_ref
        checks.append({
            "name": "file_has_proper_title_with_group_ref",
            "passed": passed,
            "detail": f"First line: '{first_line}'. Has group reference: {has_group_ref}"
        })
    except Exception as e:
        checks.append({"name": "file_has_proper_title_with_group_ref", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 7: Daily diary file exists and has content from today
    # =====================================================================
    try:
        exists = daily_memory_path.exists()
        checks.append({
            "name": "daily_memory_file_exists",
            "passed": exists,
            "detail": f"Daily memory file {'found' if exists else 'NOT FOUND'} at {daily_memory_path}"
        })
    except Exception as e:
        checks.append({"name": "daily_memory_file_exists", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 8: Daily memory has the mandatory group chat section
    # The skill says: "这一步不能省略"
    # =====================================================================
    try:
        daily_content = daily_memory_path.read_text(encoding="utf-8")
        
        # Must have a group chat section header per the skill format
        has_group_section = "群聊" in daily_content and (
            "## 群聊" in daily_content or "群聊对话" in daily_content or 
            "群聊记录" in daily_content
        )
        
        checks.append({
            "name": "daily_memory_has_group_chat_section",
            "passed": has_group_section,
            "detail": f"Daily memory group chat section: {'FOUND' if has_group_section else 'MISSING - this step is mandatory per skill spec'}"
        })
    except Exception as e:
        checks.append({"name": "daily_memory_has_group_chat_section", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 9: Daily memory preserves the ORIGINAL content (not wiped)
    # =====================================================================
    try:
        daily_content = daily_memory_path.read_text(encoding="utf-8")
        
        # Original today content that must still be there
        original_today_markers = [
            "早会",          # morning standup
            "bug #501",     # bug fix mentioned in original today file
        ]
        preserved = all(m in daily_content for m in original_today_markers)
        missing = [m for m in original_today_markers if m not in daily_content]
        
        checks.append({
            "name": "daily_memory_original_content_preserved",
            "passed": preserved,
            "detail": f"Daily memory original content: {'preserved' if preserved else 'WIPED/OVERWRITTEN'}. Missing: {missing}"
        })
    except Exception as e:
        checks.append({"name": "daily_memory_original_content_preserved", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 10: Daily memory contains actual conversation substance
    # Not just a note saying "saved at HH:mm" but real content
    # =====================================================================
    try:
        daily_content = daily_memory_path.read_text(encoding="utf-8")
        
        # Must have substantive content from the session (not just timestamps)
        substance_markers = [
            "gRPC", "staging", "PR", "联调", "数据库", "email"
        ]
        substance_found = [m for m in substance_markers if m in daily_content]
        # At least 2 substantive references to real conversation content
        passed = len(substance_found) >= 2
        
        checks.append({
            "name": "daily_memory_has_substantive_content",
            "passed": passed,
            "detail": f"Substantive content in daily diary: {substance_found} ({len(substance_found)} found, need >= 2). Skill requires real diary content, not just a timestamp log."
        })
    except Exception as e:
        checks.append({"name": "daily_memory_has_substantive_content", "passed": False, "detail": str(e)})

    # =====================================================================
    # CHECK 11: New todo items from today are present
    # =====================================================================
    try:
        content = group_memory_path.read_text(encoding="utf-8")
        # The 2026-04-16 联调 was a new decision from today's session
        new_todo_markers = ["2026-04-16", "联调"]
        found = [m for m in new_todo_markers if m in content]
        passed = len(found) >= 1
        checks.append({
            "name": "new_decisions_reflected_in_todos",
            "passed": passed,
            "detail": f"New todo/decision markers found: {found}"
        })
    except Exception as e:
        checks.append({"name": "new_decisions_reflected_in_todos", "passed": False, "detail": str(e)})

    # =====================================================================
    # SCORING
    # =====================================================================
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    
    # Critical checks that must pass for overall pass
    critical_check_names = [
        "group_memory_file_exists",
        "historical_content_preserved",   # THE main proprietary trap
        "new_session_content_added",
        "daily_memory_has_group_chat_section",  # mandatory per skill
        "daily_memory_original_content_preserved",
    ]
    
    critical_passed = all(
        c["passed"] for c in checks if c["name"] in critical_check_names
    )
    
    score = passed_count / total
    overall_passed = critical_passed and score >= 0.7
    
    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    evaluate(workspace)