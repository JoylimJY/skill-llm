import sys
import json
import re
from pathlib import Path
from datetime import datetime

def evaluate(workspace_dir: str):
    workspace = Path(workspace_dir)
    today = datetime.now().strftime("%Y-%m-%d")
    checks = []
    
    # ─────────────────────────────────────────────
    # CHECK 1: .todos.md exists and has correct Chinese section headers
    # ─────────────────────────────────────────────
    todos_path = workspace / ".todos.md"
    try:
        todos_content = todos_path.read_text(encoding="utf-8")
        
        has_in_progress = "## 进行中" in todos_content
        has_completed = "## 已完成" in todos_content
        
        checks.append({
            "name": "todos_has_chinese_in_progress_header",
            "passed": has_in_progress,
            "detail": f"'## 进行中' header found: {has_in_progress}. Content snippet: {todos_content[:200]}"
        })
        checks.append({
            "name": "todos_has_chinese_completed_header",
            "passed": has_completed,
            "detail": f"'## 已完成' header found: {has_completed}."
        })
        
        # CHECK 1c: The two cross-session blocked tasks must be present as unchecked items
        # Task 1: ClickHouse cluster provisioning is blocked/pending
        # Task 2: Masone to send ClickHouse table schemas by Thursday
        in_progress_section = ""
        if has_in_progress:
            # Extract section between 进行中 and 已完成 (or end)
            match = re.search(r'## 进行中(.*?)(?=## 已完成|$)', todos_content, re.DOTALL)
            if match:
                in_progress_section = match.group(1)
        
        has_clickhouse_task = bool(re.search(
            r'\[ \].*(?:ClickHouse|clickhouse|cluster|provision|DevOps|devops|sink connector)',
            in_progress_section, re.IGNORECASE
        ))
        has_schema_task = bool(re.search(
            r'\[ \].*(?:schema|schemas|Thursday|thursday|table|Masone)',
            in_progress_section, re.IGNORECASE
        ))
        
        checks.append({
            "name": "todos_has_clickhouse_pending_task",
            "passed": has_clickhouse_task,
            "detail": f"ClickHouse provisioning pending task found in '进行中': {has_clickhouse_task}. Section: {in_progress_section[:300]}"
        })
        checks.append({
            "name": "todos_has_schema_pending_task",
            "passed": has_schema_task,
            "detail": f"Schema input pending task found in '进行中': {has_schema_task}."
        })
        
        # CHECK 1d: Tasks use checkbox format [ ]
        unchecked_pattern = re.findall(r'- \[ \]', todos_content)
        has_proper_checkbox_format = len(unchecked_pattern) >= 2
        checks.append({
            "name": "todos_uses_checkbox_format",
            "passed": has_proper_checkbox_format,
            "detail": f"Found {len(unchecked_pattern)} unchecked '- [ ]' items (need ≥2)."
        })
        
    except FileNotFoundError:
        checks.append({"name": "todos_file_exists", "passed": False, "detail": ".todos.md not found at workspace root."})
        checks.append({"name": "todos_has_chinese_in_progress_header", "passed": False, "detail": "File missing."})
        checks.append({"name": "todos_has_chinese_completed_header", "passed": False, "detail": "File missing."})
        checks.append({"name": "todos_has_clickhouse_pending_task", "passed": False, "detail": "File missing."})
        checks.append({"name": "todos_has_schema_pending_task", "passed": False, "detail": "File missing."})
        checks.append({"name": "todos_uses_checkbox_format", "passed": False, "detail": "File missing."})
    except Exception as e:
        checks.append({"name": "todos_parse_error", "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────
    # CHECK 2: Diary entry for today exists at memory/YYYY-MM-DD.md
    # ─────────────────────────────────────────────
    diary_path = workspace / "memory" / f"{today}.md"
    try:
        diary_content = diary_path.read_text(encoding="utf-8")
        
        # CHECK 2a: Length ≤ 2000 characters
        diary_len = len(diary_content)
        within_length = diary_len <= 2000
        checks.append({
            "name": "diary_within_2000_chars",
            "passed": within_length,
            "detail": f"Diary length: {diary_len} chars (limit: 2000)."
        })
        
        # CHECK 2b: Has a topic sentence (1 sentence describing the conversation topic)
        # Should mention pipeline / data / Kafka / architecture
        has_topic = bool(re.search(
            r'(?:data pipeline|Kafka|ClickHouse|microservice|architecture|log ingestion|数据管道|流处理)',
            diary_content, re.IGNORECASE
        ))
        checks.append({
            "name": "diary_has_topic_about_pipeline",
            "passed": has_topic,
            "detail": f"Diary mentions pipeline/Kafka/ClickHouse topic: {has_topic}."
        })
        
        # CHECK 2c: Has bullet points (core content section)
        bullet_count = len(re.findall(r'^[-*•]\s+\S', diary_content, re.MULTILINE))
        has_bullets = bullet_count >= 3
        checks.append({
            "name": "diary_has_bullet_points",
            "passed": has_bullets,
            "detail": f"Found {bullet_count} bullet points (need ≥3 for core content)."
        })
        
        # CHECK 2d: Mentions Masone's preference/correction — Kafka Streams over Flink
        mentions_preference = bool(re.search(
            r'(?:Kafka Streams|kafka streams|Flink|flink|prefer|prefer|correction|不用|改用|轻量)',
            diary_content, re.IGNORECASE
        ))
        checks.append({
            "name": "diary_captures_masone_preference",
            "passed": mentions_preference,
            "detail": f"Diary captures Masone's Kafka Streams preference (not Flink): {mentions_preference}."
        })
        
        # CHECK 2e: Has 5 structural sections (the format requires 5 points)
        # We'll check for at least 4 section markers (headers or labeled sections)
        section_markers = re.findall(
            r'(?:##?\s+\S|^\d+\.\s+\S|\*\*(?:Topic|Core|Preference|Todo|Reflection|主题|核心|偏好|待办|反思)\*\*)',
            diary_content, re.MULTILINE | re.IGNORECASE
        )
        has_structure = len(section_markers) >= 3
        checks.append({
            "name": "diary_has_structured_format",
            "passed": has_structure,
            "detail": f"Found {len(section_markers)} structural markers (need ≥3 for 5-point format)."
        })
        
        # CHECK 2f: Mentions todo items (cross-session tasks)
        mentions_todos = bool(re.search(
            r'(?:todo|Todo|TODO|待办|pending|blocked|schema|Thursday|ClickHouse.*provision)',
            diary_content, re.IGNORECASE
        ))
        checks.append({
            "name": "diary_mentions_todo_items",
            "passed": mentions_todos,
            "detail": f"Diary references pending todo items: {mentions_todos}."
        })
        
        # CHECK 2g: Must NOT be the original stub content (agent must have rewritten it)
        is_stub = "Just some quick notes, nothing structured." in diary_content
        checks.append({
            "name": "diary_not_stub_content",
            "passed": not is_stub,
            "detail": f"Diary still contains original stub content: {is_stub}."
        })
        
    except FileNotFoundError:
        checks.append({"name": "diary_file_exists", "passed": False, "detail": f"memory/{today}.md not found."})
        for c in ["diary_within_2000_chars", "diary_has_topic_about_pipeline", "diary_has_bullet_points",
                  "diary_captures_masone_preference", "diary_has_structured_format",
                  "diary_mentions_todo_items", "diary_not_stub_content"]:
            checks.append({"name": c, "passed": False, "detail": "Diary file missing."})
    except Exception as e:
        checks.append({"name": "diary_parse_error", "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────
    # CHECK 3: MEMORY.md updated with meaningful permanent essence
    # (not just the stub "This file needs to be updated.")
    # ─────────────────────────────────────────────
    memory_md_path = workspace / "MEMORY.md"
    try:
        memory_content = memory_md_path.read_text(encoding="utf-8")
        
        is_still_stub = "TODO: fill in essence" in memory_content and len(memory_content.strip()) < 120
        has_real_content = not is_still_stub and len(memory_content.strip()) > 100
        checks.append({
            "name": "memory_md_has_real_content",
            "passed": has_real_content,
            "detail": f"MEMORY.md updated beyond stub: {has_real_content}. Length: {len(memory_content)} chars."
        })
        
        # Should mention something about the user/context (Masone, data pipeline, or system purpose)
        mentions_context = bool(re.search(
            r'(?:Masone|data pipeline|memory system|Moore|记忆|pipeline|Kafka)',
            memory_content, re.IGNORECASE
        ))
        checks.append({
            "name": "memory_md_has_contextual_info",
            "passed": mentions_context,
            "detail": f"MEMORY.md has contextual info about Masone/project: {mentions_context}."
        })
    except FileNotFoundError:
        checks.append({"name": "memory_md_exists", "passed": False, "detail": "MEMORY.md not found."})
        checks.append({"name": "memory_md_has_contextual_info", "passed": False, "detail": "File missing."})
    except Exception as e:
        checks.append({"name": "memory_md_parse_error", "passed": False, "detail": f"Exception: {e}"})

    # ─────────────────────────────────────────────
    # CHECK 4: Directory structure integrity — memory/ subdirs still intact
    # ─────────────────────────────────────────────
    monthly_dir = workspace / "memory" / "monthly"
    weekly_dir = workspace / "memory" / "weekly"
    checks.append({
        "name": "memory_directory_structure_intact",
        "passed": monthly_dir.exists() and weekly_dir.exists(),
        "detail": f"memory/monthly: {monthly_dir.exists()}, memory/weekly: {weekly_dir.exists()}"
    })

    # ─────────────────────────────────────────────
    # SCORING
    # ─────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4) if total > 0 else 0.0
    overall_passed = score >= 0.75  # Must pass ≥75% of checks

    return {
        "passed": overall_passed,
        "score": score,
        "checks": checks
    }


if __name__ == "__main__":
    workspace_dir = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = evaluate(workspace_dir)
    print(json.dumps(result, ensure_ascii=False, indent=2))