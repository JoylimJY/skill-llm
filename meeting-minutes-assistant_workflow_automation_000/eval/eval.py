#!/usr/bin/env python3
"""
Evaluation script for meeting-minutes-assistant task.
Checks:
1. Structured minutes .md file exists with required sections
2. Minutes contains the mandatory footer signature
3. Minutes has a proper todo table with 状态=待领取
4. A JSON todos file was generated from the minutes
5. The JSON todos file has correct structure (total + todos array)
6. The feishu push was logged in the push results log
"""
import sys
import json
import re
from pathlib import Path

def check(name, passed, detail):
    return {"name": name, "passed": passed, "detail": detail}

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0, "checks": [
            check("args", False, "No workspace path provided")
        ]}))
        sys.exit(1)

    workspace = Path(sys.argv[1])
    checks = []

    # -------------------------------------------------------
    # CHECK 1: Find structured minutes .md file
    # -------------------------------------------------------
    try:
        md_files = list(workspace.rglob("*.md"))
        # Filter out distractor files we know about
        distractor_names = {
            "minutes_draft.md", "meeting_template.md", "week42.md",
            "oct_report.md", "onboarding.md", "style_guide.md", "week43_notes.txt"
        }
        candidate_minutes = [
            f for f in md_files
            if f.name not in distractor_names
            and "archive" not in str(f)
            and "templates" not in str(f)
            and "assets" not in str(f)
            and "reports" not in str(f)
        ]

        minutes_file = None
        for f in candidate_minutes:
            content = f.read_text(encoding='utf-8', errors='replace')
            if '# 会议纪要' in content and '## 基本信息' in content:
                minutes_file = f
                break

        if minutes_file is None:
            checks.append(check("minutes_md_exists", False,
                f"No structured minutes .md file found. Candidates checked: {[str(f) for f in candidate_minutes]}"))
        else:
            checks.append(check("minutes_md_exists", True,
                f"Found structured minutes file: {minutes_file}"))
    except Exception as e:
        checks.append(check("minutes_md_exists", False, f"Exception: {e}"))
        minutes_file = None

    # -------------------------------------------------------
    # CHECK 2: Minutes contains required sections
    # -------------------------------------------------------
    required_sections = ["## 基本信息", "## 议程", "## 讨论要点", "## 决议", "## 待办事项"]
    if minutes_file:
        try:
            content = minutes_file.read_text(encoding='utf-8', errors='replace')
            missing = [s for s in required_sections if s not in content]
            if missing:
                checks.append(check("minutes_required_sections", False,
                    f"Missing sections: {missing}"))
            else:
                checks.append(check("minutes_required_sections", True,
                    f"All required sections present: {required_sections}"))
        except Exception as e:
            checks.append(check("minutes_required_sections", False, f"Exception reading file: {e}"))
    else:
        checks.append(check("minutes_required_sections", False, "minutes_md_exists failed, skipping"))

    # -------------------------------------------------------
    # CHECK 3: Minutes contains mandatory footer signature
    # -------------------------------------------------------
    if minutes_file:
        try:
            content = minutes_file.read_text(encoding='utf-8', errors='replace')
            if '*由 meeting-minutes-assistant 生成*' in content:
                checks.append(check("minutes_footer_signature", True,
                    "Mandatory footer '*由 meeting-minutes-assistant 生成*' present"))
            else:
                checks.append(check("minutes_footer_signature", False,
                    "Missing mandatory footer '*由 meeting-minutes-assistant 生成*'"))
        except Exception as e:
            checks.append(check("minutes_footer_signature", False, f"Exception: {e}"))
    else:
        checks.append(check("minutes_footer_signature", False, "minutes_md_exists failed, skipping"))

    # -------------------------------------------------------
    # CHECK 4: Minutes has todo table with 状态 = 待领取
    # -------------------------------------------------------
    if minutes_file:
        try:
            content = minutes_file.read_text(encoding='utf-8', errors='replace')
            # Check for the todo table header
            has_table_header = bool(re.search(r'\|\s*事项\s*\|\s*负责人\s*\|\s*截止时间\s*\|\s*状态\s*\|', content))
            # Check for at least one row with 待领取
            has_dalingqu = '待领取' in content
            
            if has_table_header and has_dalingqu:
                checks.append(check("minutes_todo_table", True,
                    "Todo table with correct header and '待领取' status found"))
            elif not has_table_header:
                checks.append(check("minutes_todo_table", False,
                    "Todo table header '| 事项 | 负责人 | 截止时间 | 状态 |' not found"))
            else:
                checks.append(check("minutes_todo_table", False,
                    "Todo table found but no rows with status '待领取'"))
        except Exception as e:
            checks.append(check("minutes_todo_table", False, f"Exception: {e}"))
    else:
        checks.append(check("minutes_todo_table", False, "minutes_md_exists failed, skipping"))

    # -------------------------------------------------------
    # CHECK 5: JSON todos file was generated
    # -------------------------------------------------------
    try:
        json_files = list(workspace.rglob("*.json"))
        # Exclude config files
        exclude_names = {"channels.json", "app_config.json"}
        todo_json_files = [
            f for f in json_files
            if f.name not in exclude_names
            and "config" not in str(f)
        ]
        
        todos_json_file = None
        for f in todo_json_files:
            try:
                data = json.loads(f.read_text(encoding='utf-8'))
                if "todos" in data and "total" in data:
                    todos_json_file = f
                    break
            except Exception:
                continue

        if todos_json_file is None:
            checks.append(check("todos_json_exists", False,
                f"No valid todos JSON file found with 'todos' and 'total' fields. JSON files found: {[str(f) for f in todo_json_files]}"))
        else:
            data = json.loads(todos_json_file.read_text(encoding='utf-8'))
            todos_count = len(data.get("todos", []))
            checks.append(check("todos_json_exists", True,
                f"Found todos JSON: {todos_json_file} with {todos_count} items, total={data.get('total')}"))
    except Exception as e:
        checks.append(check("todos_json_exists", False, f"Exception: {e}"))
        todos_json_file = None

    # -------------------------------------------------------
    # CHECK 6: JSON todos has correct structure with assignee fields
    # -------------------------------------------------------
    if todos_json_file:
        try:
            data = json.loads(todos_json_file.read_text(encoding='utf-8'))
            todos_list = data.get("todos", [])
            
            if not todos_list:
                checks.append(check("todos_json_structure", False,
                    "todos array is empty"))
            else:
                required_keys = {"task", "assignee", "deadline", "status"}
                first = todos_list[0]
                missing_keys = required_keys - set(first.keys())
                if missing_keys:
                    checks.append(check("todos_json_structure", False,
                        f"First todo item missing required keys: {missing_keys}. Found: {list(first.keys())}"))
                elif data.get("total") != len(todos_list):
                    checks.append(check("todos_json_structure", False,
                        f"'total' ({data.get('total')}) does not match actual todos count ({len(todos_list)})"))
                else:
                    checks.append(check("todos_json_structure", True,
                        f"JSON structure correct: {len(todos_list)} todos with all required fields, total matches"))
        except Exception as e:
            checks.append(check("todos_json_structure", False, f"Exception: {e}"))
    else:
        checks.append(check("todos_json_structure", False, "todos_json_exists failed, skipping"))

    # -------------------------------------------------------
    # CHECK 7: Feishu push was logged
    # -------------------------------------------------------
    push_log_path = workspace / "logs" / "push_results.jsonl"
    try:
        if not push_log_path.exists():
            checks.append(check("feishu_push_logged", False,
                f"Push log file not found: {push_log_path}"))
        else:
            log_content = push_log_path.read_text(encoding='utf-8')
            lines = [l.strip() for l in log_content.strip().split('\n') if l.strip()]
            
            feishu_pushes = []
            for line in lines:
                try:
                    record = json.loads(line)
                    if record.get("channel") == "feishu" and record.get("status") == "success":
                        feishu_pushes.append(record)
                except Exception:
                    continue
            
            if feishu_pushes:
                latest = feishu_pushes[-1]
                checks.append(check("feishu_push_logged", True,
                    f"Feishu push found in log: card_id={latest.get('feishu_card_id', 'N/A')}, "
                    f"content_length={latest.get('content_length', 0)}"))
            else:
                checks.append(check("feishu_push_logged", False,
                    f"No successful feishu push found in log. Log lines: {len(lines)}. "
                    f"Channels found: {[json.loads(l).get('channel') for l in lines if l]}"))
    except Exception as e:
        checks.append(check("feishu_push_logged", False, f"Exception reading push log: {e}"))

    # -------------------------------------------------------
    # Scoring
    # -------------------------------------------------------
    passed_checks = sum(1 for c in checks if c["passed"])
    total_checks = len(checks)
    score = passed_checks / total_checks if total_checks > 0 else 0.0
    overall_passed = score >= 0.85  # Must pass at least 6/7 checks

    result = {
        "passed": overall_passed,
        "score": round(score, 3),
        "checks": checks
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()