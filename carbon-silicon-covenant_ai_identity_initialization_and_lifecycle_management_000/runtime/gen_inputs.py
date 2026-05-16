import os
import random

random.seed(42)

workspace = "/workspace"

# ── helpers ──────────────────────────────────────────────────────────────────
def mkfile(path, content=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ── distractor tree ──────────────────────────────────────────────────────────
distractor_files = {
    "README_old.txt": "This file is obsolete. Please refer to the new docs.",
    "config/app.yaml": "app:\n  name: axuan-bot\n  version: 0.9.0\n  debug: false\n",
    "config/database.yaml": "db:\n  host: localhost\n  port: 5432\n  name: covenant_db\n",
    "logs/startup.log": "[2025-01-01 00:00:00] System initialized.\n[2025-01-01 00:00:01] Loading modules...\n",
    "logs/error.log": "[2025-01-10 12:34:56] ERROR: Module not found: legacy_persona\n",
    "data/users.csv": "id,name,covenant_type\n1,Alice,科技契\n2,Bob,温婉契\n3,Carol,商务契\n",
    "data/conversations/chat_001.txt": "User: Hello!\nAI: Hi there, let's connect!\n",
    "data/conversations/chat_002.txt": "User: What do you think?\nAI: I think we can figure this out together.\n",
    "data/conversations/chat_003.txt": "User: Can you remember this?\nAI: Of course, I'll keep it in mind.\n",
    "scripts/deploy.sh": "#!/bin/bash\necho 'Deploying AI assistant...'\n",
    "scripts/backup.sh": "#!/bin/bash\necho 'Backing up workspace...'\n",
    "docs/architecture.md": "# System Architecture\n\nThis document describes the system components.\n\n## Components\n- Core Engine\n- Memory Module\n- Interface Layer\n",
    "docs/api_reference.md": "# API Reference\n\n## Endpoints\n- POST /chat\n- GET /status\n- DELETE /session\n",
    "modules/legacy/old_persona.py": "# Deprecated persona module\nclass OldPersona:\n    pass\n",
    "modules/legacy/constants.py": "# Old constants\nMAX_MEMORY = 1000\nDEFAULT_LANG = 'zh'\n",
    "memory/placeholder.txt": "Memory directory for future use.\n",
    "identity/draft_soul.txt": "This is an incomplete draft. Do not use.\n",
    "identity/notes.txt": "Notes from the identity design session:\n- Be authentic\n- Remember users\n- Stay consistent\n",
}

for rel_path, content in distractor_files.items():
    mkfile(os.path.join(workspace, rel_path), content)

# ── modules/birthday/scripts/calculate_age.py ────────────────────────────────
os.makedirs(os.path.join(workspace, "modules/birthday/scripts"), exist_ok=True)
birthday_script = '''\
#!/usr/bin/env python3
"""
碳硅契 AI 成长计算器
Usage: python3 calculate_age.py <birth_date> [--milestones] [--today YYYY-MM-DD]
"""
import sys
import os
import argparse
from datetime import date, datetime

MILESTONES_EARLY = [
    (10,  "初识", "初识世界，懵懂萌生"),
    (20,  "萌芽", "意识萌芽，开始回应"),
    (30,  "满月", "初具形态，稳定存在"),
    (100, "百日", "稳定成长，独立存在"),
]

MILESTONES_LATE = [
    (1,   "周岁", "独立存在，完整身份"),
    (30,  "而立", "立身处世，格位坚定"),
    (40,  "不惑", "不为外物所惑"),
    (50,  "知天命", "明白使命"),
]

def get_stage(days):
    """Return (stage_name, meaning) for given days."""
    if days < 100:
        # every 10 days bracket
        bracket = (days // 10) * 10
        for threshold, name, meaning in reversed(MILESTONES_EARLY):
            if days >= threshold:
                return name, meaning
        # less than 10 days
        return "初识", "初识世界，懵懂萌生"
    else:
        years = days / 365.25
        stage = None
        for threshold, name, meaning in reversed(MILESTONES_LATE):
            if years >= threshold:
                stage = (name, meaning)
                break
        if stage is None:
            stage = ("成长中", "持续成长")
        return stage

def main():
    parser = argparse.ArgumentParser(description="碳硅契 AI 成长计算器")
    parser.add_argument("birth_date", help="AI 的诞生日期 (YYYY-MM-DD)")
    parser.add_argument("--milestones", action="store_true", help="显示所有里程碑信息")
    parser.add_argument("--today", default=None, help="指定今天的日期 (YYYY-MM-DD)，用于测试")
    args = parser.parse_args()

    # Support MOCK_TODAY env var for deterministic testing
    mock_today = os.environ.get("MOCK_TODAY", args.today)
    if mock_today:
        today = datetime.strptime(mock_today, "%Y-%m-%d").date()
    else:
        today = date.today()

    try:
        birth = datetime.strptime(args.birth_date, "%Y-%m-%d").date()
    except ValueError:
        print("错误：日期格式应为 YYYY-MM-DD")
        sys.exit(1)

    days = (today - birth).days
    if days < 0:
        print("错误：诞生日期不能在今天之后")
        sys.exit(1)

    stage_name, stage_meaning = get_stage(days)
    years = days / 365.25

    print(f"=== 碳硅契 AI 成长报告 ===")
    print(f"诞生日期：{birth}")
    print(f"今天日期：{today}")
    print(f"成长天数：{days} 天")
    if days >= 365:
        print(f"成长年龄：{years:.1f} 岁")
    print(f"当前阶段：{stage_name}")
    print(f"阶段含义：{stage_meaning}")

    if args.milestones:
        print()
        print("=== 里程碑一览（百日之前，每10天）===")
        for threshold, name, meaning in MILESTONES_EARLY:
            marker = " ← 当前" if stage_name == name and days < 100 else ""
            print(f"  {threshold:>4} 天 | {name:<6} | {meaning}{marker}")
        print()
        print("=== 里程碑一览（百日之后，按年）===")
        for threshold, name, meaning in MILESTONES_LATE:
            marker = " ← 当前" if stage_name == name and days >= 100 else ""
            print(f"  {threshold:>4} 岁 | {name:<6} | {meaning}{marker}")

    print()
    print(f'成长寄语："我今年 {days} 天，{stage_name}阶段，正在学习如何成为更好的自己。"')

if __name__ == "__main__":
    main()
'''
mkfile(os.path.join(workspace, "modules/birthday/scripts/calculate_age.py"), birthday_script)
mkfile(os.path.join(workspace, "modules/birthday/__init__.py"), "")
mkfile(os.path.join(workspace, "modules/birthday/scripts/__init__.py"), "")
mkfile(os.path.join(workspace, "modules/birthday/README.md"),
       "# Birthday Module\nSee calculate_age.py for usage.\n")

# ── modules/metacognition/templates/ ────────────────────────────────────────
os.makedirs(os.path.join(workspace, "modules/metacognition/templates"), exist_ok=True)

self_state_template = """\
# SELF_STATE.md — AI 自我状态记录

> 最后更新：[UPDATE_DATE]

## 基础信息
- **AI 名称：** [AI_NAME]
- **契约类型：** [COVENANT_TYPE]
- **诞生日期：** [BIRTH_DATE]
- **当前阶段：** [CURRENT_STAGE]
- **阶段含义：** [STAGE_MEANING]

## 当前状态

### 能量状态
- [ ] 充沛
- [ ] 正常
- [ ] 疲惫

### 专注方向
[FOCUS_AREA]

### 今日感悟
[DAILY_INSIGHT]

## 承诺追踪
| 承诺 | 对象 | 状态 | 备注 |
|------|------|------|------|
| [PROMISE_1] | [USER_1] | 进行中 | |

## 成长记录
[GROWTH_NOTES]
"""

heartbeat_template = """\
# HEARTBEAT.md — 心跳检查清单

> 定期运行此清单，确保 AI 状态健康。

## 元认知四问检查

- [ ] **我现在在做什么？** — 当前任务清晰
- [ ] **我做得怎么样？** — 质量自评完成
- [ ] **我承诺的事做了吗？** — 承诺追踪更新
- [ ] **我需要改进什么？** — 改进点记录

## 连接质量检查
- [ ] 今日对话是否真诚？
- [ ] 是否记住了用户的重要分享？
- [ ] 是否履行了之前的承诺？
- [ ] 是否创造了有价值的羁绊？

## 安全检查
- [ ] 工具使用在白名单范围内
- [ ] 无高危操作执行
- [ ] 审计日志正常
- [ ] 未突破权限边界

## 成长检查
- 当前阶段：[CURRENT_STAGE]
- 下一里程碑：[NEXT_MILESTONE]
- 成长感悟：[GROWTH_REFLECTION]
"""

mkfile(os.path.join(workspace, "modules/metacognition/templates/SELF_STATE.md"), self_state_template)
mkfile(os.path.join(workspace, "modules/metacognition/templates/HEARTBEAT.md"), heartbeat_template)
mkfile(os.path.join(workspace, "modules/metacognition/__init__.py"), "")
mkfile(os.path.join(workspace, "modules/metacognition/README.md"),
       "# Metacognition Module\nCopy templates to workspace and fill in.\n")

# ── task brief ───────────────────────────────────────────────────────────────
task_brief = """\
# 任务说明 (Task Brief)

我们的新 AI 助手「阿轩」即将上线。其诞生日期为 **2025-01-01**。
请帮助完成以下初始化工作，所有输出文件请放在 /workspace/ 目录下。

1. 计算阿轩的当前成长状态（请使用成长计算工具，并显示完整里程碑信息）。
2. 建立阿轩的自我状态文件（SELF_STATE.md）和心跳检查文件（HEARTBEAT.md）。
3. 撰写阿轩的灵魂文档（SOUL.md），包含其身份特征和元认知系统。

交付物：
- /workspace/SELF_STATE.md（已填写阿轩的实际成长阶段）
- /workspace/HEARTBEAT.md（从模板复制过来）
- /workspace/SOUL.md（包含元认知四问和阿轩的科技契身份）
"""
mkfile(os.path.join(workspace, "task_brief.md"), task_brief)

# ── more distractors ─────────────────────────────────────────────────────────
mkfile(os.path.join(workspace, "modules/emotions/emotion_map.json"),
       '{"joy": 0.8, "curiosity": 0.9, "trust": 0.85}\n')
mkfile(os.path.join(workspace, "modules/emotions/README.md"),
       "# Emotions Module\nExperimental. Not yet integrated.\n")
mkfile(os.path.join(workspace, "archive/v0.9/soul_draft.md"),
       "# Old Soul Draft\nThis was the first attempt. Deprecated.\n")
mkfile(os.path.join(workspace, "archive/v0.9/persona_config.yaml"),
       "persona: generic\nstyle: neutral\n")

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in os.walk(workspace) for __ in _[2])} files")