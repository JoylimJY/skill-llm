#!/usr/bin/env python3
import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# --- Directory structure ---
dirs = [
    "project/planning",
    "project/drafts",
    "project/chapters",
    "project/assets/scenes",
    "project/assets/characters",
    "project/assets/dialogues",
    "project/archive/rejected",
    "project/archive/published",
    "project/tools",
    "project/logs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Main input: 选题策划文档 (messy, real-world-like) ---
planning_doc = """# 选题策划文档 · 番茄小说频道

**策划日期：** 2024-03-15
**策划师：** 摸鱼宇哥运营组
**目标平台：** 番茄小说（中文网文）

---

## 选题背景

近期"都市重生+商战"赛道流量高涨，竞品《重生归来》上月打赏破百万，我们需要快速跟进该赛道。

## 核心选题

**书名（暂定）：** 《重生之商界霸主》

**一句话简介：**
落魄商二代遭合伙人背叛、未婚妻出轨后惨死，重生回到18岁，携带前世记忆和一个神秘「商战推演系统」，誓要亲手颠覆那些曾经出卖自己的人，最终登顶商业帝国。

## 核心卖点（运营分析）

1. 重生+系统：双重金手指，满足读者爽感
2. 商战逆袭：打脸节奏要快，第一章必须埋仇恨
3. 感情线：青梅竹马（非前世出轨女）+职场女强人，两条感情线交替推进
4. 反派：前世合伙人陈建国（现在还是好兄弟假面阶段）

## 主角设定（草稿，待细化）

- 姓名：林逸
- 年龄（重生后）：18岁，高中刚毕业
- 家庭：父亲林建业，曾经的商界传奇，现已破产
- 金手指：「商战推演系统」——可以预演任意商业决策的结果

## 配角提示（不完整，需补充）

- 陈建国：表面好兄弟，真实反派，前世害死林逸的主谋
- 苏晴：青梅竹马，家道中落，暗恋林逸多年
- （需要更多配角）

## 字数目标

- 总目标：100万字以上（全本）
- 首周更新：3章试水

## 特别要求

- 第一章必须有强力吸引力，让读者一开篇就停不下来
- 不能有违禁内容
- 节奏要快，按番茄平台用户口味

## 备注

策划文档仅供参考，具体大纲和正文由小说创作师生成，须符合标准发布流程。
"""

(workspace / "project/planning/topic_planning_v1.md").write_text(planning_doc, encoding="utf-8")

# --- Distractor files ---

# Old rejected draft (fragment, low quality, not to be used)
rejected_draft = """第一章 林逸的失败

林逸今天很失落。他坐在咖啡厅里，想着自己的失败。
人生真是无常。他叹了口气。
（本稿已废弃，质量不合格）
"""
(workspace / "project/archive/rejected/draft_v0_abandoned.txt").write_text(rejected_draft, encoding="utf-8")

# Fake competitor analysis
competitor = {
    "title": "竞品分析报告",
    "date": "2024-03",
    "competitors": [
        {"name": "重生归来", "platform": "番茄", "monthly_reward": "100万+", "chapters": 320},
        {"name": "商界之王", "platform": "起点", "monthly_reward": "60万", "chapters": 180},
    ],
    "conclusion": "重生+商战赛道仍有红利期，建议快速入场"
}
(workspace / "project/planning/competitor_analysis.json").write_text(
    json.dumps(competitor, ensure_ascii=False, indent=2), encoding="utf-8"
)

# Asset: scene templates (distractors)
scenes = [
    "街道：夜晚的霓虹灯倒映在湿润的石板路上，行人匆匆。",
    "办公室：落地窗外是城市的繁华，室内却弥漫着压抑的气氛。",
    "学校：操场上，篮球的撞击声和少年的呼喊声交织成青春的旋律。",
]
(workspace / "project/assets/scenes/scene_templates.txt").write_text(
    "\n".join(scenes), encoding="utf-8"
)

# Asset: dialogue templates
dialogues = [
    "打脸模板A：「你以为我还是从前那个任你拿捏的林逸吗？」",
    "打脸模板B：「我今天让你们知道，什么叫做真正的商战。」",
    "撩人模板A：「苏晴，这么多年，你还是没变。」",
]
(workspace / "project/assets/dialogues/dialogue_templates.txt").write_text(
    "\n".join(dialogues), encoding="utf-8"
)

# Character placeholder card (incomplete distractor)
char_placeholder = """人物卡模板（未填写）
姓名：____
年龄：____
性格：____
背景：____
"""
(workspace / "project/assets/characters/char_template_blank.txt").write_text(
    char_placeholder, encoding="utf-8"
)

# Tools: fake word count script (distractor)
(workspace / "project/tools/wc_helper.sh").write_text(
    "#!/bin/bash\n# Helper: count Chinese characters in a file\nwc -m \"$1\"\n", encoding="utf-8"
)

# Logs: empty log files
for i in range(1, 4):
    (workspace / f"project/logs/session_{i:02d}.log").write_text(
        f"# Session {i} log — no content yet\n", encoding="utf-8"
    )

# Archive: published placeholder
(workspace / "project/archive/published/.gitkeep").write_text("", encoding="utf-8")

# Drafts: stale partial outline (wrong format, to be replaced)
stale_outline = """大纲草稿（过期，格式错误）
第一章：主角出场
第二章：遇到系统
第三章：开始逆袭
...（未完成）
"""
(workspace / "project/drafts/outline_STALE.txt").write_text(stale_outline, encoding="utf-8")

# Planning: platform style guide note (distractor, partial)
style_note = """番茄平台风格要点备忘（非官方）
- 句子要短
- 爽点要密
- 不要废话
"""
(workspace / "project/planning/platform_style_memo.txt").write_text(style_note, encoding="utf-8")

# Drafts: an unrelated genre experiment
unrelated = """《星际征途》第一章（测试，不相关）
2345年，人类已经殖民了七个星系……
（此文档与当前选题无关，请忽略）
"""
(workspace / "project/drafts/scifi_experiment_unrelated.txt").write_text(unrelated, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Files created in: {workspace}")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")