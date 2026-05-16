import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# ─── Directory skeleton ───────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "novels",
    "novels/.archive",
    "drafts/rough",
    "drafts/discarded",
    "assets/covers",
    "assets/fonts",
    "platform/submission",
    "platform/guidelines",
    "tools",
    "logs",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files (10+) ──────────────────────────────────────────
(WORKSPACE / "drafts/rough/scene_ideas.txt").write_text(
    "场景想法：\n- 雨夜停车场\n- 废弃实验室\n- 深夜的解剖室\n", encoding="utf-8"
)
(WORKSPACE / "drafts/rough/character_sketch.txt").write_text(
    "粗略人物草稿，待整理\n沈白：法医，冷静，有秘密\n", encoding="utf-8"
)
(WORKSPACE / "drafts/discarded/chapter_draft_v0.txt").write_text(
    "这是废弃的初稿，请勿使用。\n天气晴朗，万里无云...\n（已弃用）\n", encoding="utf-8"
)
(WORKSPACE / "assets/covers/placeholder.txt").write_text("封面图片占位符\n", encoding="utf-8")
(WORKSPACE / "assets/fonts/font_list.txt").write_text("思源黑体\n方正书宋\n", encoding="utf-8")
(WORKSPACE / "platform/submission/guidelines_v2.txt").write_text(
    "平台投稿要求（旧版）：\n- 每章不低于2000字\n- 使用繁体字\n（此文件已过期，请参考最新版）\n",
    encoding="utf-8"
)
(WORKSPACE / "platform/guidelines/submission_faq.md").write_text(
    "# 常见问题\nQ: 章节字数要求？\nA: 请联系编辑确认。\n", encoding="utf-8"
)
(WORKSPACE / "tools/formatter.py").write_text(
    "# 格式化工具（开发中）\nprint('Not implemented')\n", encoding="utf-8"
)
(WORKSPACE / "logs/creation_log.txt").write_text(
    "2024-01-01 项目启动\n2024-01-05 第一轮策划会\n", encoding="utf-8"
)
(WORKSPACE / "novels/.archive/old_project_notes.txt").write_text(
    "旧项目笔记，已归档。\n项目名：消失的证人（已取消）\n", encoding="utf-8"
)
(WORKSPACE / "drafts/rough/title_candidates.txt").write_text(
    "备选书名：\n1. 寂静的尸语\n2. 骨殇\n3. 白骨证词\n4. 死亡的指纹\n", encoding="utf-8"
)
(WORKSPACE / "platform/submission/contract_template.txt").write_text(
    "版权合同模板\n甲方：作者\n乙方：平台\n条款：……（略）\n", encoding="utf-8"
)

# ─── Reference files (from SKILL.md — must exist for agent to use) ───

# outline-template.md
(WORKSPACE / "references/outline-template.md").write_text("""\
# 《[小说名称]》创作大纲

## 基本信息
- 题材：[题材]
- 主角：[主角名] | 职业/身份：[职业]
- 核心冲突：[核心冲突]
- 总章节数：[N]章

## 故事主线
[主线概述，200字以内]

## 人物关系图
[主要人物关系描述]

## 章节规划 TODO List

| 章节 | 标题 | 核心事件 | 结尾钩子 | 状态 |
|------|------|----------|----------|------|
| 第01章 | [标题] | [核心事件] | [钩子类型] | 待开始 |
| 第02章 | [标题] | [核心事件] | [钩子类型] | 待开始 |
| 第03章 | [标题] | [核心事件] | [钩子类型] | 待开始 |

## 已完成章节摘要

（每章完成后在此添加300-500字摘要）

""", encoding="utf-8")

# character-template.md
(WORKSPACE / "references/character-template.md").write_text("""\
# 《[小说名称]》人物档案

## 主角档案

### [主角姓名]
- **性别**：
- **年龄**：
- **职业/身份**：
- **外貌特征**：
- **核心性格**：
- **内心动机**：
- **最大弱点**：
- **背景故事**：

---

## 反派档案

### [反派姓名]
- **性别**：
- **年龄**：
- **职业/身份**：
- **行动目标**：
- **与主角的关系**：
- **真实动机（隐藏）**：

---

## 配角档案

### [配角1姓名]
- **职能**：（帮助主角 / 制造麻烦 / 提供信息）
- **与主角关系**：
- **关键作用**：

### [配角2姓名]
- **职能**：
- **与主角关系**：
- **关键作用**：

""", encoding="utf-8")

# chapter-template.md
(WORKSPACE / "references/chapter-template.md").write_text("""\
# 第XX章 [章节标题]

> 字数目标：3000-5000字

---

[正文内容]

---

*（本章结尾钩子）*

""", encoding="utf-8")

# chapter-guide.md, hook-techniques.md, dialogue-writing.md, content-expansion.md, consistency.md
# (already shown in SKILL.md; write minimal versions pointing to their actual content)
(WORKSPACE / "references/chapter-guide.md").write_text("""\
# 章节写作指南

## 前20%决定生死
开头必须有即时冲突，使用十种开头技巧之一：
1. 行动中开场
2. 反常情境
3. 震撼对话
4. 倒计时开场
5. 重大发现
6. 危机时刻
7. 谜团浮现
8. 背叛开场
9. 重大选择
10. 结局预告

## 章节结构
- 开头钩子（前20%）
- 发展推进（中间50-60%）
- 高潮时刻（后15-20%）
- 结尾钩子（最后5-10%）
""", encoding="utf-8")

(WORKSPACE / "references/hook-techniques.md").write_text("""\
# 悬念设置技巧

## 十种经典悬念钩子
1. 突然揭示
2. 紧急危机
3. 未完成的动作
4. 身份反转
5. 两难选择
6. 神秘物品/线索
7. 时间限制
8. 承诺/威胁
9. 离奇消失
10. 言外之意

每章结尾必须使用以上钩子之一。
""", encoding="utf-8")

(WORKSPACE / "references/dialogue-writing.md").write_text("""\
# 对话写作规范

- 每句对话有明确目的
- 简洁，避免冗余
- 区分不同角色声音
- 正确使用标点（中文书名号等）
- 每个说话人独占一段
- 善用潜台词
""", encoding="utf-8")

(WORKSPACE / "references/content-expansion.md").write_text("""\
# 内容扩充技巧

字数不足时使用：
1. 场景细节描写
2. 人物内心活动
3. 对话扩展
4. 感官体验（五感）
5. 次要情节线
6. 节奏放慢
7. 环境烘托

原则：自然融入，保持张力，推进主线。
""", encoding="utf-8")

(WORKSPACE / "references/consistency.md").write_text("""\
# 连贯性保证机制

写前必读：
1. 阅读00-大纲.md中所有已完成章节摘要
2. 读取上一章文件
3. 检查人物状态

写时注意：
- 呼应前文伏笔
- 人物行为一致
- 悬念线延续

一致性检查：
- 人物行为符合性格
- 时间线连贯
- 场景转换自然
""", encoding="utf-8")

# ─── The critical wordcount script ───────────────────────────────────
(WORKSPACE / "scripts/check_chapter_wordcount.py").write_text("""\
#!/usr/bin/env python3
\"\"\"
Chapter wordcount checker for Chinese novel chapters.
Usage:
  python scripts/check_chapter_wordcount.py <chapter_file>  [min_chars]
  python scripts/check_chapter_wordcount.py --all <novel_dir> [min_chars]

Counts Chinese characters only (excludes spaces, punctuation, ASCII).
Default minimum: 3000 Chinese characters.
Exit code 0 = pass, 1 = fail (below minimum).
\"\"\"
import sys
import re
from pathlib import Path

def count_chinese(text):
    \"\"\"Count Chinese characters (CJK Unified Ideographs only).\"\"\"
    return len(re.findall(r'[\\u4e00-\\u9fff]', text))

def check_file(filepath, min_chars=3000):
    p = Path(filepath)
    if not p.exists():
        print(f"ERROR: File not found: {filepath}")
        return False
    text = p.read_text(encoding='utf-8')
    count = count_chinese(text)
    status = "PASS" if count >= min_chars else "FAIL"
    print(f"[{status}] {p.name}: {count} Chinese characters (minimum: {min_chars})")
    return count >= min_chars

def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)

    min_chars = 3000

    if args[0] == '--all':
        if len(args) < 2:
            print("ERROR: --all requires a directory path")
            sys.exit(1)
        novel_dir = Path(args[1])
        if len(args) >= 3:
            try:
                min_chars = int(args[2])
            except ValueError:
                pass
        chapter_files = sorted(novel_dir.glob('第*.md'))
        if not chapter_files:
            print(f"No chapter files found in {novel_dir}")
            sys.exit(1)
        all_pass = True
        for f in chapter_files:
            if not check_file(f, min_chars):
                all_pass = False
        sys.exit(0 if all_pass else 1)
    else:
        filepath = args[0]
        if len(args) >= 2:
            try:
                min_chars = int(args[1])
            except ValueError:
                pass
        passed = check_file(filepath, min_chars)
        sys.exit(0 if passed else 1)

if __name__ == '__main__':
    main()
""", encoding="utf-8")

# ─── Editorial brief (the "messy input" the agent must work from) ─────
(WORKSPACE / "platform/submission/editorial_brief.txt").write_text("""\
【编辑部内部备忘录】
项目代号：骨语
目标平台：悬疑推理频道
预计上线：下季度

故事方向：
主角沈白，女性，32岁，法医，供职于市公安局法医鉴定中心。
性格：冷静智慧，理性，高智商，有轻度职业创伤。
核心冲突：查明真相（一系列伪装成意外的连环命案，凶手藏在机构内部）。
反派：待确定（建议设置为内部人员，身份到第三章前不揭露）。
配角：搭档刑警陈默（男，40岁，老派但可靠）。

章节要求：本期交付前3章，书名《骨语》。
字数：每章达到发稿标准。
注意：编辑部需要完整项目归档，包含章节规划文档和人物档案。

请按照内部创作流程执行。
""", encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Files created in: {WORKSPACE}")