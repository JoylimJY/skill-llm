import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── 1. Create the flash-thoughts skill directory with the real script ──────────
skills_dir = workspace / "skills" / "flash-thoughts"
scripts_dir = skills_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# Write the actual flash.py script as described in SKILL.md
flash_py_content = r'''#!/usr/bin/env python3
"""Flash Thoughts - 闪念记录"""
import sys
import os
from datetime import datetime
from pathlib import Path

FLASH_DIR = Path.home() / "notes" / "flash"

def get_today_file():
    FLASH_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    return FLASH_DIR / f"{today}.md"

def add_thought(content):
    filepath = get_today_file()
    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M")

    if not filepath.exists():
        # Create new file with header
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# {today} 闪念\n\n")
            f.write("---\n\n")
            f.write(f"## {time_str} - {content}\n\n")
            f.write(content + "\n")
    else:
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(f"\n---\n\n")
            f.write(f"## {time_str} - {content}\n\n")
            f.write(content + "\n")

    print(f"记好了！📝 写入了 `{filepath.name}`")

def search_thoughts(keyword):
    FLASH_DIR.mkdir(parents=True, exist_ok=True)
    results = []
    for md_file in sorted(FLASH_DIR.glob("*.md")):
        date = md_file.stem
        with open(md_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if keyword.lower() in line.lower():
                context = lines[i].strip()
                results.append(f"{date}: {context}")
    if results:
        print(f"找到了 {len(results)} 条包含 '{keyword}' 的闪念：")
        for r in results:
            print(f"  > {r}")
    else:
        print(f"没有找到包含 '{keyword}' 的闪念。")

def show_day(date_str):
    FLASH_DIR.mkdir(parents=True, exist_ok=True)
    filepath = FLASH_DIR / f"{date_str}.md"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print(f"没有找到 {date_str} 的闪念。")

def recent_days(n):
    FLASH_DIR.mkdir(parents=True, exist_ok=True)
    files = sorted(FLASH_DIR.glob("*.md"), reverse=True)[:int(n)]
    for f in files:
        print(f"\n{'='*40}")
        print(f.read_text(encoding="utf-8"))

def main():
    if len(sys.argv) < 2:
        print("用法: flash.py <add|search|show|recent> [参数]")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "add" and len(sys.argv) >= 3:
        add_thought(" ".join(sys.argv[2:]))
    elif cmd == "search" and len(sys.argv) >= 3:
        search_thoughts(" ".join(sys.argv[2:]))
    elif cmd == "show" and len(sys.argv) >= 3:
        show_day(sys.argv[2])
    elif cmd == "recent" and len(sys.argv) >= 3:
        recent_days(sys.argv[2])
    else:
        print("未知命令或参数不足")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''

(scripts_dir / "flash.py").write_text(flash_py_content, encoding="utf-8")

# ── 2. Create SKILL.md ────────────────────────────────────────────────────────
skill_md = """---
name: flash-thoughts
description: 随手记录灵感闪念。按日期存储，分隔线分隔每个想法，支持快速添加和搜索。
metadata: {"clawdbot":{"emoji":"💡","requires":{"bins":[]},"install":[]}}
---

# Flash Thoughts - 闪念记录

## 使用方法

### 添加闪念
```bash
python3 scripts/flash.py add "你的想法内容"
```

### 搜索闪念
```bash
python3 scripts/flash.py search "关键词"
python3 scripts/flash.py show 2026-03-20
python3 scripts/flash.py recent 7
```

### 配置存储路径
默认存储在 `~/notes/flash/`，可在脚本中修改 `FLASH_DIR` 变量。

## 文件结构
每个文件格式：
```markdown
# 2026-03-20 闪念

---

## 10:19 - 博客程序智能体技能

为各种博客程序写智能体技能...

---

## 14:32 - 闪念功能本身就是一个好想法

这个记录方式值得写成文章。
```
"""
(skills_dir / "SKILL.md").write_text(skill_md, encoding="utf-8")

# ── 3. Distractor directory structure ─────────────────────────────────────────
distractors = [
    ("projects/alpha/config.yaml", "project: alpha\nversion: 1.0\n"),
    ("projects/alpha/README_INTERNAL.txt", "Internal notes for alpha project.\n"),
    ("projects/beta/requirements.txt", "flask\nnumpy\n"),
    ("projects/beta/data/raw_data.csv", "id,value\n1,42\n2,99\n"),
    ("projects/beta/data/processed.json", '{"status": "ok", "count": 2}\n'),
    ("logs/system.log", "2026-01-01 INFO startup\n2026-01-02 WARN disk low\n"),
    ("logs/access.log", "GET /api/v1/health 200\nGET /api/v1/data 404\n"),
    ("notes/meeting_notes.txt", "Meeting on 2026-03-15:\n- Discuss roadmap\n- Budget review\n"),
    ("notes/todo.md", "# TODO\n- [ ] Fix bug #123\n- [ ] Deploy to staging\n"),
    ("archive/2025/q4_report.txt", "Q4 2025 Summary\nRevenue: $1.2M\n"),
    ("archive/2025/team_roster.csv", "name,role\nAlice,Engineer\nBob,Designer\n"),
    ("tmp/scratch.py", "# scratch work\nx = 1 + 1\nprint(x)\n"),
    ("tmp/notes_old.txt", "old ideas from last year - ignore\n"),
]

for rel_path, content in distractors:
    target = workspace / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")

# ── 4. Write task context file ────────────────────────────────────────────────
task_context = {
    "task": "flash-thoughts-workflow",
    "thoughts_to_add": [
        "quantum computing could optimize our protein folding pipeline",
        "we should integrate federated learning into the genomics project",
        "build a real-time anomaly detection system for lab sensor data"
    ],
    "search_keyword": "genomics",
    "expected_flash_dir": "~/notes/flash/"
}
(workspace / "task_context.json").write_text(
    json.dumps(task_context, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("Workspace generated successfully.")
print(f"Skill location: {skills_dir}")
print(f"Script location: {scripts_dir / 'flash.py'}")