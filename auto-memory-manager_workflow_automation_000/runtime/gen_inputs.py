import os
import json
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── Directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "memory-manager",
    "memory-manager/temp",
    "memory-manager/docs",
    "memory-manager/tests",
    "memory-manager/archive",
    "memory-manager/reports",
    "memory-manager/logs",
    "lab-notes",
    "lab-notes/raw",
    "lab-notes/processed",
    "shared",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── memory_manager.py  (canonical implementation matching SKILL.md API) ─────
memory_manager_py = textwrap.dedent('''\
    """
    Memory Manager - Core Module
    Implements: record_session(), process_temp_files(), weekly_digest()
    """

    import os
    import json
    import re
    import glob
    from datetime import datetime, timedelta
    from pathlib import Path


    def _load_config():
        """Load config.json if present, else return defaults."""
        cfg_path = Path(__file__).parent / "config.json"
        defaults = {
            "temp_dir": "./temp",
            "memory_dir": "../memory",
            "auto_save": True,
            "cleanup_days": 30,
        }
        if cfg_path.exists():
            with open(cfg_path) as f:
                user_cfg = json.load(f)
            defaults.update(user_cfg)
        return defaults


    def _resolve_dir(raw_path: str) -> Path:
        """Resolve a path relative to the script file's location."""
        base = Path(__file__).parent
        p = (base / raw_path).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p


    def _next_session_number(temp_dir: Path) -> int:
        """Return the next available session number."""
        existing = list(temp_dir.glob("session_*.md"))
        if not existing:
            return 1
        nums = []
        for f in existing:
            m = re.search(r"session_(\\d+)\\.md", f.name)
            if m:
                nums.append(int(m.group(1)))
        return max(nums) + 1 if nums else 1


    def record_session(session_data: dict) -> Path:
        """
        Record a single session to temp/session_N.md.

        Required keys in session_data:
          date, topics, key_info, todos, decisions, emotion

        Returns the path of the written file.
        """
        cfg = _load_config()
        temp_dir = _resolve_dir(cfg["temp_dir"])

        required = ["date", "topics", "key_info", "todos", "decisions", "emotion"]
        for key in required:
            if key not in session_data:
                raise ValueError(f"Missing required key: {key}")

        n = _next_session_number(temp_dir)
        filename = temp_dir / f"session_{n}.md"

        def _fmt_list(items):
            if not items:
                return "  (none)"
            return "\\n".join(f"  - {item}" for item in items)

        content = f"""# Session {n} — {session_data['date']}

## Topics
{_fmt_list(session_data['topics'])}

## Key Information
{_fmt_list(session_data['key_info'])}

## Todos
{_fmt_list(session_data['todos'])}

## Decisions
{_fmt_list(session_data['decisions'])}

## Emotion
  {session_data['emotion']}
"""
        filename.write_text(content, encoding="utf-8")
        return filename


    def process_temp_files(target_date: str = None) -> dict:
        """
        Process all session_*.md files in temp_dir.

        - Aggregates all sessions into a single YYYY-MM-DD.md in memory_dir.
        - Deletes processed session_*.md files from temp_dir.
        - Returns dict with keys: date, session_count, output_file.
        """
        cfg = _load_config()
        temp_dir = _resolve_dir(cfg["temp_dir"])
        memory_dir = _resolve_dir(cfg["memory_dir"])

        if target_date is None:
            target_date = datetime.now().strftime("%Y-%m-%d")

        session_files = sorted(temp_dir.glob("session_*.md"))
        session_count = len(session_files)

        all_topics = []
        all_key_info = []
        all_todos = []
        all_decisions = []
        emotions = []

        for sf in session_files:
            text = sf.read_text(encoding="utf-8")
            # Parse sections
            for line in text.splitlines():
                stripped = line.strip()
                if stripped.startswith("- "):
                    pass  # handled below
            # Simple section parser
            current_section = None
            for line in text.splitlines():
                stripped = line.strip()
                if stripped == "## Topics":
                    current_section = "topics"
                elif stripped == "## Key Information":
                    current_section = "key_info"
                elif stripped == "## Todos":
                    current_section = "todos"
                elif stripped == "## Decisions":
                    current_section = "decisions"
                elif stripped == "## Emotion":
                    current_section = "emotion"
                elif stripped.startswith("## "):
                    current_section = None
                elif stripped.startswith("- ") and current_section == "topics":
                    all_topics.append(stripped[2:])
                elif stripped.startswith("- ") and current_section == "key_info":
                    all_key_info.append(stripped[2:])
                elif stripped.startswith("- ") and current_section == "todos":
                    all_todos.append(stripped[2:])
                elif stripped.startswith("- ") and current_section == "decisions":
                    all_decisions.append(stripped[2:])
                elif current_section == "emotion" and stripped and not stripped.startswith("#"):
                    emotions.append(stripped)

        def _fmt(items):
            if not items:
                return "  (none)"
            return "\\n".join(f"  - {item}" for item in items)

        summary_content = f"""# Daily Summary — {target_date}

## Sessions Processed: {session_count}

## Topics Covered
{_fmt(all_topics)}

## Key Information
{_fmt(all_key_info)}

## Todos
{_fmt(all_todos)}

## Decisions Made
{_fmt(all_decisions)}

## Mood / Emotion
{_fmt(emotions)}
"""

        output_file = memory_dir / f"{target_date}.md"
        output_file.write_text(summary_content, encoding="utf-8")

        # Clean up temp session files
        for sf in session_files:
            sf.unlink()

        return {
            "date": target_date,
            "session_count": session_count,
            "output_file": str(output_file),
        }


    def weekly_digest(week_end_date: str = None) -> dict:
        """
        Read the past 7 daily files from memory_dir and append a digest to MEMORY.md.
        Also deletes daily files older than cleanup_days.

        Returns dict with keys: weeks_read, appended_to.
        """
        cfg = _load_config()
        memory_dir = _resolve_dir(cfg["memory_dir"])
        cleanup_days = int(cfg.get("cleanup_days", 30))

        if week_end_date is None:
            week_end_date = datetime.now().strftime("%Y-%m-%d")

        end = datetime.strptime(week_end_date, "%Y-%m-%d")
        days_read = 0
        collected_key_info = []
        collected_decisions = []

        for i in range(7):
            day = end - timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            day_file = memory_dir / f"{day_str}.md"
            if day_file.exists():
                days_read += 1
                text = day_file.read_text(encoding="utf-8")
                current_section = None
                for line in text.splitlines():
                    stripped = line.strip()
                    if stripped == "## Key Information":
                        current_section = "key_info"
                    elif stripped == "## Decisions Made":
                        current_section = "decisions"
                    elif stripped.startswith("## "):
                        current_section = None
                    elif stripped.startswith("- ") and current_section == "key_info":
                        collected_key_info.append(stripped[2:])
                    elif stripped.startswith("- ") and current_section == "decisions":
                        collected_decisions.append(stripped[2:])

        memory_file = memory_dir / "MEMORY.md"

        def _fmt(items):
            if not items:
                return "  (none)"
            return "\\n".join(f"  - {item}" for item in items)

        digest = f"""
---
## Weekly Digest — week ending {week_end_date}

### Core Knowledge Gained
{_fmt(collected_key_info)}

### Key Decisions
{_fmt(collected_decisions)}
"""
        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(digest)

        # Cleanup old daily files
        cutoff = datetime.now() - timedelta(days=cleanup_days)
        removed = []
        for f in memory_dir.glob("????-??-??.md"):
            m = re.match(r"(\\d{4}-\\d{2}-\\d{2})\\.md", f.name)
            if m:
                try:
                    file_date = datetime.strptime(m.group(1), "%Y-%m-%d")
                    if file_date < cutoff:
                        f.unlink()
                        removed.append(f.name)
                except ValueError:
                    pass

        return {
            "weeks_read": days_read,
            "appended_to": str(memory_file),
            "cleaned_up": removed,
        }
''')

(WORKSPACE / "memory-manager" / "memory_manager.py").write_text(memory_manager_py, encoding="utf-8")

# ── SKILL.md ────────────────────────────────────────────────────────────────
skill_md = textwrap.dedent("""\
    ---
    name: memory-manager
    description: 智能记忆管理系统：自动记录会话、每日总结、每周提炼，打造 AI 的长期记忆。
    metadata:
      {"openclaw": {"emoji": "🧠", "requires": {"bins": ["python"]}}}
    ---

    # Memory Manager - 智能记忆管理系统

    **让 AI 拥有真正的长期记忆！**

    自动记录每次会话、每日批量总结、每周提炼精华，打造会学习、会成长的 AI 助手！

    ---

    ## 🛠️ 核心功能

    ### 1. 会话记录
    - ✅ **自动记录** - 每次会话结束自动保存
    - ✅ **结构化存储** - 主题/关键信息/待办/决策分类
    - ✅ **临时文件** - 保存到 memory/temp/ 目录
    - ✅ **自动编号** - 便于追踪和检索

    ### 2. 每日总结
    - ✅ **批量处理** - 每晚 20:00 处理所有临时文件
    - ✅ **信息提炼** - 提取关键信息/待办/决策
    - ✅ **生成日报** - 创建 memory/YYYY-MM-DD.md
    - ✅ **自动清理** - 删除临时文件，保持整洁

    ### 3. 每周提炼
    - ✅ **读取周记忆** - 读取本周 7 个每日文件
    - ✅ **提取核心** - 提炼到 MEMORY.md（长期记忆）
    - ✅ **清理过期** - 删除 30 天前的每日文件
    - ✅ **持续成长** - 长期记忆只增不减

    ### 4. 实时保存（双重保障）
    - ✅ **关键节点触发** - 技能发布/收款变更/重要决策
    - ✅ **立即追加** - 实时写入 MEMORY.md
    - ✅ **不丢失** - 即使每日总结失败也有记录

    ---

    ## 📁 文件结构

    ```
    memory-manager/
    ├── memory_manager.py      # 主脚本
    ├── SKILL.md              # 技能说明
    ├── config.example.json   # 配置模板
    ├── .gitignore            # Git 忽略
    └── temp/                 # 临时文件目录（自动创建）
        ├── session_*.md      # 会话记录
        └── YYYY-MM-DD.md     # 每日总结
    ```

    ---

    ## 🚀 快速开始

    ### 3. 使用

    **会话记录：**
    ```python
    from memory_manager import record_session

    session_data = {
        "date": "2026-03-06",
        "topics": ["技能发布", "商业化讨论"],
        "key_info": ["发布第 5 个技能"],
        "todos": ["明天提交方案"],
        "decisions": ["采用 SaaS 模式"],
        "emotion": "专注"
    }

    record_session(session_data)
    ```

    **每日总结：**
    ```python
    from memory_manager import process_temp_files

    result = process_temp_files()
    print(f"处理了 {result['session_count']} 个会话")
    ```

    ---

    ## ⚙️ 配置选项

    | 配置项 | 说明 | 默认值 |
    |--------|------|--------|
    | `temp_dir` | 临时文件目录 | `./temp` |
    | `memory_dir` | 记忆文件目录 | `../memory` |
    | `auto_save` | 自动保存关键信息 | `true` |
    | `cleanup_days` | 保留天数 | `30` |
""")

(WORKSPACE / "memory-manager" / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── config.example.json ─────────────────────────────────────────────────────
config_example = {
    "temp_dir": "./temp",
    "memory_dir": "../memory",
    "auto_save": True,
    "cleanup_days": 30
}
(WORKSPACE / "memory-manager" / "config.example.json").write_text(
    json.dumps(config_example, indent=2, ensure_ascii=False), encoding="utf-8"
)

# ── .gitignore ───────────────────────────────────────────────────────────────
(WORKSPACE / "memory-manager" / ".gitignore").write_text(
    "temp/\n*.pyc\n__pycache__/\nconfig.json\n", encoding="utf-8"
)

# ── Distractor files (realistic lab environment noise) ───────────────────────
# lab-notes/raw — unstructured meeting notes (NOT in the memory_manager format)
raw_notes = [
    ("meeting_2026_03_01.txt",
     "Attendees: Alice, Bob, Carol\nDiscussed protein folding pipeline.\nAction: Bob will submit HPC job by Friday.\nDecision: Use AlphaFold2 for initial screen.\n"),
    ("meeting_2026_03_02.txt",
     "Alice presented preliminary results.\nKey finding: mutation X shows 3x activity.\nTodo: Replicate in wet lab.\n"),
    ("meeting_2026_03_03.txt",
     "Team reviewed literature on CRISPR delivery.\nDecision: Pursue lipid nanoparticle approach.\nEmotion in room: excited, cautious.\n"),
    ("ideas_brainstorm.txt",
     "Random ideas:\n- automated data pipeline\n- cloud backup for sequencing data\n- weekly digest for PI\n"),
]
for fname, content in raw_notes:
    (WORKSPACE / "lab-notes" / "raw" / fname).write_text(content, encoding="utf-8")

# lab-notes/processed — already processed summaries (distractor)
(WORKSPACE / "lab-notes" / "processed" / "week_summary_feb.md").write_text(
    "# Week of Feb 2026\n\nCompleted phase 1 screening.\n", encoding="utf-8"
)

# docs/ — distractor docs
(WORKSPACE / "memory-manager" / "docs" / "architecture.md").write_text(
    "# Architecture\n\nSee SKILL.md for full details.\n", encoding="utf-8"
)
(WORKSPACE / "memory-manager" / "docs" / "api_reference.md").write_text(
    "# API Reference\n\nrecord_session(session_data: dict) -> Path\nprocess_temp_files(target_date=None) -> dict\n",
    encoding="utf-8"
)

# tests/ — dummy test file
(WORKSPACE / "memory-manager" / "tests" / "test_placeholder.py").write_text(
    "# Tests to be written\ndef test_noop():\n    pass\n", encoding="utf-8"
)

# archive/ — old session files from a different era (wrong format, distractor)
(WORKSPACE / "memory-manager" / "archive" / "old_session_1.txt").write_text(
    "[Session 1]\nDate=2025-01-10\nNotes=Early experiment on memory module.\n", encoding="utf-8"
)
(WORKSPACE / "memory-manager" / "archive" / "old_session_2.txt").write_text(
    "[Session 2]\nDate=2025-01-11\nNotes=Prototype crashed, need refactor.\n", encoding="utf-8"
)

# reports/ — distractor
(WORKSPACE / "memory-manager" / "reports" / "q1_2026_draft.md").write_text(
    "# Q1 2026 Progress\n\nDraft - not final.\n", encoding="utf-8"
)

# shared/ — distractor config files
(WORKSPACE / "shared" / "global_config.json").write_text(
    json.dumps({"environment": "lab", "version": "1.0"}, indent=2), encoding="utf-8"
)
(WORKSPACE / "shared" / "team_roster.txt").write_text(
    "Alice Chen - PI\nBob Nguyen - PhD student\nCarol Davis - Postdoc\n", encoding="utf-8"
)

# logs/ — distractor log file
(WORKSPACE / "memory-manager" / "logs" / "system.log").write_text(
    "2026-03-01 08:00:00 INFO  System started\n2026-03-01 20:00:00 INFO  Daily summary scheduled\n",
    encoding="utf-8"
)

print("Workspace generated successfully.")
print("Structure:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")