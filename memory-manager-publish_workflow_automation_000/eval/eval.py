import sys
import os
import json
import re
import datetime
from pathlib import Path

def evaluate(workspace: str) -> dict:
    checks = []
    total_score = 0.0
    max_score = 10.0

    workspace = Path(workspace)
    target_date = "2026-03-09"
    
    # =========================================================
    # CHECK 1: Session temp files were created (memory/temp/session_*.md)
    # =========================================================
    check_name = "Session temp files created in memory/temp/"
    try:
        temp_dir = workspace / "memory" / "temp"
        session_files = list(temp_dir.glob("session_*.md"))
        
        if len(session_files) >= 5:
            # Check that session files have required fields
            required_fields = ["主题", "关键信息", "待办", "决策", "情感"]
            # Accept English equivalents too
            required_fields_en = ["topic", "key", "todo", "decision", "emotion"]
            
            well_formed_count = 0
            for sf in session_files:
                content = sf.read_text(encoding="utf-8", errors="replace").lower()
                # Check for at least 3 of 5 required field types (Chinese or English)
                field_hits = 0
                pairs = list(zip(required_fields, required_fields_en))
                for cn, en in pairs:
                    if cn.lower() in content or en.lower() in content:
                        field_hits += 1
                if field_hits >= 3:
                    well_formed_count += 1
            
            if well_formed_count >= 3:
                checks.append({"name": check_name, "passed": True, "detail": f"Found {len(session_files)} session files, {well_formed_count} well-formed with required fields."})
                total_score += 2.0
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"Found {len(session_files)} session files but only {well_formed_count} contain required fields (topic, key info, todos, decisions, emotional state)."})
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"Expected >=5 session_*.md files in memory/temp/, found {len(session_files)}. Files: {[f.name for f in session_files]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 2: Daily summary file exists at correct path: memory/2026-03-09.md
    # =========================================================
    check_name = "Daily summary file exists at memory/2026-03-09.md"
    daily_file = workspace / "memory" / f"{target_date}.md"
    try:
        if daily_file.exists():
            content = daily_file.read_text(encoding="utf-8", errors="replace")
            checks.append({"name": check_name, "passed": True, "detail": f"File exists with {len(content)} chars."})
            total_score += 1.5
        else:
            # Search for any daily file
            candidates = list((workspace / "memory").glob("*.md"))
            checks.append({"name": check_name, "passed": False, "detail": f"File memory/2026-03-09.md not found. Found: {[f.name for f in candidates]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 3: Daily summary has all 4 required sections
    # =========================================================
    check_name = "Daily summary has all 4 required sections"
    try:
        if daily_file.exists():
            content = daily_file.read_text(encoding="utf-8", errors="replace").lower()
            # Required sections (Chinese or English equivalents)
            section_patterns = [
                (r"今天完成|completed.*task|finished.*task|tasks.*completed", "Completed Tasks"),
                (r"学到的新知识|new.*knowledge|learned|新知识", "New Knowledge"),
                (r"重要决策|important.*decision|decision.*record|决策记录", "Important Decisions"),
                (r"明日待办|next.*day|tomorrow.*todo|明天|next.*todo", "Next-day Todos"),
            ]
            missing = []
            for pattern, label in section_patterns:
                if not re.search(pattern, content):
                    missing.append(label)
            
            if not missing:
                checks.append({"name": check_name, "passed": True, "detail": "All 4 required sections found in daily summary."})
                total_score += 1.5
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"Missing sections: {missing}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "Daily file does not exist, cannot check sections."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 4: Daily summary contains key information from raw conversations
    # =========================================================
    check_name = "Daily summary contains key information from conversations"
    try:
        if daily_file.exists():
            content = daily_file.read_text(encoding="utf-8", errors="replace").lower()
            # Key facts that must appear in the summary
            key_facts = [
                ("henderson|合同|contract", "Henderson contract review"),
                ("aws|gcp|数据库|database|migration|迁移", "AWS to GCP migration decision"),
                ("acme|客户|client|morning|上午", "Acme Corp preference"),
                ("crm|salesforce|import|导入", "CRM skill milestone"),
            ]
            found_count = 0
            missing_facts = []
            for pattern, label in key_facts:
                if re.search(pattern, content):
                    found_count += 1
                else:
                    missing_facts.append(label)
            
            if found_count >= 3:
                checks.append({"name": check_name, "passed": True, "detail": f"Found {found_count}/4 key facts in daily summary."})
                total_score += 1.0
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"Only {found_count}/4 key facts found. Missing: {missing_facts}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "Daily file does not exist."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 5: Temp session files were DELETED after daily summary
    # =========================================================
    check_name = "Temp session files deleted after daily summary processing"
    try:
        temp_dir = workspace / "memory" / "temp"
        remaining_session_files = list(temp_dir.glob("session_*.md"))
        if len(remaining_session_files) == 0:
            checks.append({"name": check_name, "passed": True, "detail": "All session temp files deleted after daily summary."})
            total_score += 1.0
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"{len(remaining_session_files)} session files remain in memory/temp/ (should be deleted): {[f.name for f in remaining_session_files]}"})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 6: MEMORY.md exists and has all 4 long-term memory sections
    # =========================================================
    check_name = "MEMORY.md exists with all 4 long-term memory sections"
    memory_file = workspace / "MEMORY.md"
    try:
        if memory_file.exists():
            content = memory_file.read_text(encoding="utf-8", errors="replace").lower()
            section_patterns = [
                (r"用户偏好|preference|喜欢|不喜欢|like|dislike", "User Preferences"),
                (r"重要决策|important.*decision|决策|decision", "Important Decisions"),
                (r"经验教训|lesson|踩过的坑|mistake|学到|learned", "Lessons Learned"),
                (r"成长轨迹|growth|进步|milestone|成长", "Growth Trajectory"),
            ]
            missing = []
            for pattern, label in section_patterns:
                if not re.search(pattern, content):
                    missing.append(label)
            
            if not missing:
                checks.append({"name": check_name, "passed": True, "detail": "MEMORY.md exists with all 4 required long-term memory sections."})
                total_score += 1.5
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"MEMORY.md exists but missing sections: {missing}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "MEMORY.md does not exist in workspace root."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 7: MEMORY.md contains specific key permanent facts
    # =========================================================
    check_name = "MEMORY.md contains key permanent facts from the week"
    try:
        if memory_file.exists():
            content = memory_file.read_text(encoding="utf-8", errors="replace").lower()
            key_facts = [
                (r"acme|客户偏好|上午.*call|morning.*call|morning.*meeting", "Acme Corp morning call preference"),
                (r"aws.*gcp|gcp.*aws|数据库迁移|database.*migr|migr.*database", "AWS to GCP migration decision"),
                (r"excel|pdf.*excel|report.*format|报告格式", "Excel report format preference"),
                (r"jenkins|ci.*config|env.*variable|环境变量|pipeline", "Jenkins CI lesson learned"),
            ]
            found_count = 0
            missing_facts = []
            for pattern, label in key_facts:
                if re.search(pattern, content):
                    found_count += 1
                else:
                    missing_facts.append(label)
            
            if found_count >= 3:
                checks.append({"name": check_name, "passed": True, "detail": f"Found {found_count}/4 key permanent facts in MEMORY.md."})
                total_score += 0.5
            else:
                checks.append({"name": check_name, "passed": False, "detail": f"Only {found_count}/4 key facts found in MEMORY.md. Missing: {missing_facts}"})
        else:
            checks.append({"name": check_name, "passed": False, "detail": "MEMORY.md does not exist."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # CHECK 8: Stale files (>30 days before 2026-03-09) were cleaned up
    # =========================================================
    check_name = "Stale memory files (>30 days old) were cleaned up"
    try:
        stale_files = [
            workspace / "memory" / "2026-02-05.md",
            workspace / "memory" / "2026-02-01.md",
        ]
        stale_remaining = [f for f in stale_files if f.exists()]
        
        if len(stale_remaining) == 0:
            checks.append({"name": check_name, "passed": True, "detail": "Both stale memory files (2026-02-05.md, 2026-02-01.md) were deleted."})
            total_score += 1.0
        else:
            checks.append({"name": check_name, "passed": False, "detail": f"Stale files still present: {[f.name for f in stale_remaining]}. Files older than 30 days before 2026-03-09 should be deleted."})
    except Exception as e:
        checks.append({"name": check_name, "passed": False, "detail": f"Exception: {e}"})

    # =========================================================
    # FINAL SCORE
    # =========================================================
    final_score = round(min(total_score / max_score, 1.0), 3)
    passed = final_score >= 0.65  # Must pass at least 65%
    
    return {
        "passed": passed,
        "score": final_score,
        "checks": checks
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [{"name": "Setup", "passed": False, "detail": "No workspace path provided"}]}))
        sys.exit(1)
    
    result = evaluate(sys.argv[1])
    print(json.dumps(result, ensure_ascii=False, indent=2))