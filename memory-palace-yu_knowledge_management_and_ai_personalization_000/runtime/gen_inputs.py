import os
import random

random.seed(42)

workspace = "/workspace"

# ─── 1. Create distractor directory structure ───────────────────────────────

dirs = [
    "notes/old_projects",
    "notes/clients",
    "notes/methodology",
    "drafts/2025",
    "drafts/2026",
    "archive/consulting",
    "archive/research",
    "tools/scripts",
    "tools/templates",
    "exports/pdf_notes",
    "exports/word_docs",
    "personal/journal",
    "personal/goals",
    "temp/scratch",
]

for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ─── 2. Distractor files ─────────────────────────────────────────────────────

distractor_files = {
    "notes/old_projects/project_alpha.md": "# Project Alpha\n\nOld project notes from 2023.\n- Completed phase 1\n- Budget overrun",
    "notes/old_projects/project_beta.txt": "Project Beta - plain text notes\nClient: TechCorp\nStatus: Cancelled",
    "notes/clients/techcorp_notes.md": "# TechCorp\n\n- Enterprise client\n- Contact: Jane Doe\n- Annual contract",
    "notes/clients/startup_xyz.md": "# StartupXYZ\n\n- Seed stage\n- Founder: Alex\n- Needs: growth strategy",
    "notes/methodology/lean_notes.txt": "Lean methodology notes - not yet organized",
    "notes/methodology/agile_framework.md": "# Agile Notes\n\nSprint planning tips:\n1. Define backlog\n2. Estimate stories",
    "drafts/2025/q1_report_draft.md": "# Q1 2025 Draft Report\n\nRevenue growth: 12%\nNew clients: 3",
    "drafts/2026/strategy_draft.txt": "2026 strategy draft - work in progress\nFocus: digital transformation",
    "archive/consulting/old_methodology_v1.md": "# Old Methodology v1\n\nDeprecated. Do not use.",
    "archive/research/market_analysis_2024.md": "# Market Analysis 2024\n\nKey findings:\n- Market growing at 8% YoY",
    "tools/scripts/export_notes.sh": "#!/bin/bash\necho 'Exporting notes...'",
    "tools/templates/client_report.md": "# Client Report Template\n\n[CLIENT NAME]\n[DATE]\n\n## Summary\n\n[SUMMARY]",
    "exports/pdf_notes/README.txt": "PDF exports stored here",
    "personal/journal/2025-12-01.txt": "December 1st - busy day, three client calls",
    "personal/goals/2026_goals.md": "# 2026 Goals\n\n- Expand to 5 new markets\n- Launch training program",
    "temp/scratch/random_ideas.txt": "Random ideas:\n- AI-powered consulting\n- Automated reporting\n- Client portal",
}

for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ─── 3. The "raw messy inputs" the agent must PROCESS ────────────────────────
# These are the source notes that the agent needs to transform/organize
# into the memory palace structure

raw_identity_notes = """\
# 关于我的笔记 (Raw Identity Notes)

姓名: 张磊 (Zhang Lei)
职业: 战略咨询顾问 / Strategy Consultant
擅长: 数字化转型, 精益管理, 组织变革
工作风格: 直接, 数据驱动, 注重实践落地

性格特点:
- 喜欢用第一性原理思考问题
- 对模糊性有高容忍度
- 倾向于用系统思维看问题
- 不喜欢冗余, 追求简洁表达

核心方法论:
- 先诊断后方案: 不了解问题本质就不给建议
- 80/20法则: 找到最关键的20%发力
- 以终为始: 从期望结果倒推行动计划

这些是我的核心原则:
- 诚实比讨好重要
- 长期价值优于短期收益
- 实践检验真理
"""

raw_insights = """\
# 散乱洞察记录

## 关于数字化转型
大多数企业数字化失败不是技术问题, 是人的问题和流程问题.
技术是最后10%的事情.

## 关于咨询工作
客户最需要的不是答案, 是帮助他们想清楚问题.
顾问的价值在于结构化思考和外部视角.

## 关于学习
真正的学习必须产生行为改变.
读书不改变行动等于没读.

## 关于决策
大多数决策不需要完美信息.
70%信息时就要决策, 等待100%已经太晚.
"""

raw_daily_1 = """\
# 今天的记录

日期: 2026-03-20

重要会议: 与TechCorp讨论数字化路线图
决定: 建议他们先做流程梳理再上系统
洞察: 他们的问题根源是KPI设计问题, 不是工具问题

明天要做的事:
- 完成诊断报告初稿
- 给StartupXYZ发提案
"""

raw_daily_2 = """\
# 今天的记录

日期: 2026-03-22

完成了: 诊断报告, 客户反馈很好
新想法: 可以把这套方法做成培训课程
重要对话: 老朋友李明说AI工具改变了他的工作方式

洞察:
- 方法论比工具更重要
- 但好工具能让好方法论发挥10倍效果
"""

# Write these raw source files in temp/scratch for the agent to find and use
with open(os.path.join(workspace, "temp/scratch/my_identity_raw.md"), "w", encoding="utf-8") as f:
    f.write(raw_identity_notes)

with open(os.path.join(workspace, "temp/scratch/insights_raw.md"), "w", encoding="utf-8") as f:
    f.write(raw_insights)

with open(os.path.join(workspace, "temp/scratch/daily_notes_raw.md"), "w", encoding="utf-8") as f:
    f.write(raw_daily_1 + "\n---\n\n" + raw_daily_2)

# ─── 4. A partial/broken config attempt (distractor) ─────────────────────────
# Agent must NOT use this broken path - it points to wrong location
with open(os.path.join(workspace, "memory_config_old.txt"), "w") as f:
    f.write("OLD CONFIG - IGNORE\nmemory_location=/home/user/old_memory\n")

# ─── 5. A skill reference file that mentions memory palace ───────────────────
skill_ref = """\
# Available Skills

## memory-palace
Installed at: ~/.openclaw/workspace/skills/memory-palace
Trigger: 记忆宫 / memory palace
Config: .memory-path (optional, place in workspace root)

## code-helper
Trigger: code help

## web-search
Trigger: search
"""
os.makedirs(os.path.join(workspace, "tools"), exist_ok=True)
with open(os.path.join(workspace, "tools/installed_skills.md"), "w", encoding="utf-8") as f:
    f.write(skill_ref)

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_list, files in os.walk(workspace):
    level = root.replace(workspace, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f'{indent}{os.path.basename(root)}/')
    subindent = ' ' * 2 * (level + 1)
    for file in files:
        print(f'{subindent}{file}')