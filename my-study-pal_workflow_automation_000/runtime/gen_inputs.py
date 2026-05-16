import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── USER.md ──────────────────────────────────────────────────────────────────
user_md = workspace / "USER.md"
user_md.write_text("""# 用户信息

姓名：李明
职业方向：产品经理（互联网行业，3年经验）
年龄：28岁
学习目标：提升数据分析能力，能独立看懂数据报表并提出业务洞察
可用学习时间：工作日晚上 21:00，每次约30分钟
""", encoding="utf-8")

# ── memory/user-profile.md ───────────────────────────────────────────────────
memory_dir = workspace / "mystudy"
memory_dir.mkdir(parents=True, exist_ok=True)

profile_md = memory_dir / "user-profile.md"
profile_md.write_text("""# 学习画像

更新时间：2026-01-10

## 偏好风格
- 喜欢结合工作场景的案例
- 倾向干货 + 小故事结合
- 不喜欢太学术的语言
- 期望语气：轻松幽默

## 历史学习
- 暂无记录

## 其他备注
- 对Excel有基础，但从未接触过SQL或Python
- 希望能在季度汇报中用数据说话
""", encoding="utf-8")

# ── Distractor files to increase realism ────────────────────────────────────
# Old incomplete attempt at a study folder (wrong naming, incomplete)
old_study = workspace / "mystudy" / "数据分析_旧版"
old_study.mkdir(parents=True, exist_ok=True)
(old_study / "notes.txt").write_text("第一次尝试学数据分析，没坚持下去...", encoding="utf-8")
(old_study / "todo.md").write_text("- [ ] 学Excel\n- [ ] 学SQL\n", encoding="utf-8")

# Unrelated project files
projects_dir = workspace / "projects"
projects_dir.mkdir(parents=True, exist_ok=True)
(projects_dir / "q1_report.xlsx.bak").write_text("backup of q1 report", encoding="utf-8")
(projects_dir / "meeting_notes_2026-03-01.txt").write_text(
    "会议记录：讨论Q1数据复盘，需要产品提供用户留存数据...", encoding="utf-8"
)

# Config-like distractor
config_dir = workspace / "config"
config_dir.mkdir(parents=True, exist_ok=True)
(config_dir / "settings.yaml").write_text("theme: dark\nlanguage: zh-CN\n", encoding="utf-8")
(config_dir / "shortcuts.json").write_text('{"study": "Ctrl+S", "review": "Ctrl+R"}', encoding="utf-8")

# Old cron-like file (wrong format, distractor)
(workspace / "reminders.txt").write_text(
    "记得每天晚上21点学习！\n（这只是备忘，不是真正的cron）\n", encoding="utf-8"
)

# A partial roadmap with wrong structure (distractor)
partial_dir = workspace / "drafts"
partial_dir.mkdir(parents=True, exist_ok=True)
(partial_dir / "roadmap_draft.md").write_text("""# 草稿：数据分析路线图

第一章：数据的概念
  - 1.1 什么是大数据
  - 1.2 数据类型介绍
  - 1.3 数据采集方法
（未完成...）
""", encoding="utf-8")

# Fake session file in wrong location
(workspace / "session_notes.txt").write_text(
    "今天学了一点点均值和方差的概念，感觉懵懵的", encoding="utf-8"
)

# Another distractor: an exercises file not in proper path
(workspace / "练习题_随手记.md").write_text("""## 随手记的几道题
1. 平均值和中位数哪个更能代表收入水平？
2. 什么是标准差？
""", encoding="utf-8")

# MEMORY.md (referenced in skill but currently empty to simulate fresh start)
(workspace / "MEMORY.md").write_text("""# 全局记忆

（暂无记录）
""", encoding="utf-8")

print("Workspace generated successfully.")
print("\nDirectory structure:")
for p in sorted(workspace.rglob("*")):
    indent = "  " * (len(p.relative_to(workspace).parts) - 1)
    print(f"{indent}{p.name}{'/' if p.is_dir() else ''}")