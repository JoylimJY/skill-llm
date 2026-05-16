import os
import random
import sys

random.seed(42)

workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"

# ── Directory structure ──────────────────────────────────────────────────────
dirs = [
    ".learnings",
    "output",
    "scripts",
    "drafts",
    "drafts/archive",
    "drafts/ideas",
    "references/tropes",
    "references/worldbuilding",
    "config",
    "tmp",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ─────────────────────────────────────────────────────────
distractor_files = {
    "drafts/archive/old_idea_1.txt": "一个关于时间旅行的故事想法，主角是个失业程序员。",
    "drafts/archive/old_idea_2.txt": "末日背景，最后一个人类文明在月球基地求生。",
    "drafts/ideas/brainstorm.txt": "题材方向：修仙 / 都市 / 末世 / 系统流 / 重生\n待定，需要进一步讨论。",
    "references/tropes/xianxia_tropes.txt": "常见修仙梗：神秘传承、废材逆袭、天才身份揭露、宝物认主",
    "references/tropes/urban_tropes.txt": "常见都市梗：商战逆袭、豪门身份揭秘、技术天才隐居",
    "references/worldbuilding/cultivation_ranks.txt": "炼气、筑基、金丹、元婴、化神、大乘、渡劫",
    "references/worldbuilding/power_systems.txt": "灵根品质、功法等级、法宝品阶、境界突破条件",
    "config/settings.json": '{"language": "zh-CN", "default_chapter_length": 2500, "style": "xianxia"}',
    "tmp/scratch.txt": "临时笔记：第一章节奏要快，开篇抓人。",
    "drafts/ideas/character_sketch.txt": "男主：外表普通，内心坚韧，有一个不为人知的秘密身份。",
    "references/tropes/system_tropes.txt": "系统流常见元素：签到系统、任务奖励、属性面板、商城兑换",
    "config/novel_config_template.txt": "小说名：\n题材：\n主角名：\n金手指：",
}
for path, content in distractor_files.items():
    full_path = os.path.join(workspace, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# ── .learnings/ template headers (empty but with minimal stub) ──────────────
# These exist as empty stubs to simulate an initialized but unused workspace.
# The agent must POPULATE them after generating chapters.
learnings_stubs = {
    "CHARACTERS.md": "# 角色档案\n\n<!-- 在此记录每章新出现或状态变化的角色 -->\n",
    "LOCATIONS.md": "# 地点档案\n\n<!-- 在此记录已出现的地点 -->\n",
    "PLOT_POINTS.md": "# 关键情节\n\n<!-- 在此记录关键情节转折 -->\n",
    "STORY_BIBLE.md": "# 世界观设定\n\n<!-- 在此记录世界观规则和设定 -->\n",
    "ERRORS.md": "# 生成失败记录\n\n<!-- 在此记录生成失败或质量问题 -->\n",
}
for filename, stub_content in learnings_stubs.items():
    full_path = os.path.join(workspace, ".learnings", filename)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(stub_content)

# ── init-novel.sh script (referenced in SKILL.md as already existing) ────────
init_script = """#!/bin/bash
# Novel workspace initializer
NOVEL_NAME="${1:-未命名小说}"
echo "初始化小说工作区：$NOVEL_NAME"
mkdir -p output
mkdir -p .learnings
echo "工作区创建完成。"
"""
script_path = os.path.join(workspace, "scripts", "init-novel.sh")
with open(script_path, "w", encoding="utf-8") as f:
    f.write(init_script)
os.chmod(script_path, 0o755)

# ── User direction file (the raw input the agent should work from) ───────────
direction_file = """# 小说创作需求

## 创作方向
题材：修仙 + 系统流
方向：一个被逐出宗门的废柴弟子，偶然获得一个"鉴定系统"，能鉴定万物价值并获得属性加成。
主角从最底层开始，凭借系统一步步打脸宗门、震惊修仙界。

## 关键要求
- 主角名：陈晨
- 宗门：青云宗
- 反派（初期）：同门师兄 张浩
- 女配角（至少一名）：同门师姐 苏璃
- 起点：被逐出宗门当天获得系统
- 目标：至少规划20章的完整大纲

请基于以上方向，启动完整的小说创作准备工作。
"""
direction_path = os.path.join(workspace, "创作需求.md")
with open(direction_path, "w", encoding="utf-8") as f:
    f.write(direction_file)

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")