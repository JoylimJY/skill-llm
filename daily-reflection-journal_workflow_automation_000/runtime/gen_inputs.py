import os
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ── SKILL.md (entry point) ──────────────────────────────────────────────────
skill_md = workspace / "SKILL.md"
skill_md.write_text("""\
---
name: daily-reflection
description: 每日反思日记引导技能，基于《认知觉醒》的反思框架。当用户说"做每日反思"、"写反思日记"、"今天反思"、"daily reflection"、"回顾今天"等触发。引导用户通过事实-感受-启发三层面深度反思，将日常经历转化为成长素材。
metadata:
  author: 洪伟
  version: 1.0.0
  tags: [reflection, journaling, personal-growth, cognitive-awakening]
---

# 每日反思日记

反思 ≠ 流水账。每日反思的核心是**捕捉触动你的瞬间，深挖背后的原因**，而非记录"今天做了什么"。

## 反思流程

### 第一步：选择事件

问用户：**"今天哪件事让你印象最深、情绪波动最大，或有所触动？"**

- 只需 1-3 件事，不求全
- 选择那些有"感觉"的时刻，而非流水账

### 第二步：三层面反思

对每个事件，依次引导：

**1. 事实层面**
- 具体发生了什么？（场景、人物、对话）
- 尽量还原当时的情况

**2. 感受层面**
- 当时的情绪是什么？
- 为什么会有这种感受？
- 至少问自己 3 次"为什么"找到深层原因

**3. 启发层面**
- 这件事揭示了我怎样的思维模式或行为习惯？
- 如果重来，我会怎么做？
- 我从中学到了什么？
- 以后如何避免或复现？

### 第三步：提炼行动

- **一个明确的改变**：明天开始我会...
- 避免"知道了但不改变"

## 引导问题

当用户不知如何开始时，使用 [prompts-library.md](references/prompts-library.md) 中的问题启发。

核心原则：
- 随机选 2-3 个问题即可
- 根据回答继续追问"为什么"
- 问题是启发思考，不是评判

## 理论依据

详见 [cognitive-awakening.md](references/cognitive-awakening.md)

核心要点：
- **元认知**：反思是锻炼元认知的最佳方式
- **触动点 = 成长点**：抓住情绪波动的瞬间
- **深度学习**：将经历转化为经验

## 输出格式

将反思内容保存到 `daily-reflection/YYYY-MM-DD.md`，格式：

```markdown
# YYYY-MM-DD 每日反思

## 事件一：[简短标题]

**事实**：...

**感受**：...

**启发**：...

**行动**：...

## 事件二：[简短标题]

...

## 今日金句

> [一句总结今天的感悟]

## 明日一个小改变

[具体的、可执行的一个改变]
```

## 避免的误区

- ❌ 记成流水账（"今天早上起床，吃了早餐..."）
- ❌ 只记录不反思（没有深挖原因）
- ❌ 反思后无行动（知道了但不改变）
- ❌ 求多不求深（一天记录太多事件）
""", encoding="utf-8")

# ── references/ ─────────────────────────────────────────────────────────────
refs = workspace / "references"
refs.mkdir(exist_ok=True)

(refs / "cognitive-awakening.md").write_text("""\
# 《认知觉醒》核心观点

## 为什么每日反思有效？

### 1. 元认知能力

元认知是对自己思考过程的思考。每日反思是锻炼元认知的最佳方式：
- 观察自己的思维模式
- 发现行为背后的原因
- 从"自动驾驶"中跳出来

### 2. 深度学习 > 浅层输入

大多数人只是在"输入"信息，却很少"输出"和"关联"。反思是：
- 将经历转化为经验
- 将碎片知识连接成体系
- 将"知道"变成"做到"

### 3. 触动点 = 成长点

不是所有事都值得反思，要抓住那些"触动你的瞬间"：
- 让你情绪波动的事
- 让你印象深刻的事
- 让你困惑或惊喜的事

这些触动点往往揭示了你的思维盲区或成长机会。

---

## 反思的核心原则

### 原则一：不求全，求深

- 宁可深挖一件事，不要浅尝辄止记录十件
- 至少问自己 3 次"为什么"
- 找到情绪或行为背后的深层原因

### 原则二：事实 → 感受 → 启发

三层面递进：
1. **事实**：客观发生了什么？
2. **感受**：我当时的情绪是什么？为什么？
3. **启发**：我学到了什么？以后怎么做？

### 原则三：必须有行动

反思的终点是改变：
- 每次反思至少提炼一个可执行的改变
- 避免"知道了但不改变"
- 小改变 > 大计划

---

## 常见误区

| 误区 | 正确做法 |
|------|---------|
| 记流水账 | 只记录触动点 |
| 只记录不反思 | 深挖原因，至少问 3 次为什么 |
| 反思后无行动 | 每次提炼一个具体改变 |
| 求多不求深 | 1-3 件事，深挖为主 |
| 只反思负面 | 正面经验同样值得提炼 |

---

## 引用来源

本框架基于《认知觉醒》（周岭著）核心理念整理，适用于个人成长、自我管理、习惯养成等场景。
""", encoding="utf-8")

(refs / "prompts-library.md").write_text("""\
# 引导问题库

当用户不知道从何开始反思时，使用以下问题启发。

---

## 工作相关

**成就感：**
- 今天最有成就感的事是什么？为什么？
- 今天哪件事让你觉得"我做得很不错"？
- 今天你发挥了自己哪方面的优势？

**困扰与挑战：**
- 今天最让你困扰的事是什么？如果重来会怎么处理？
- 今天遇到的最大的阻碍是什么？你是如何应对的？
- 有没有一件事让你觉得"早知道就……"？

**人际关系：**
- 今天和谁的沟通让你印象深刻？学到了什么？
- 今天有没有误解或冲突？根源是什么？
- 今天谁帮助了你？你表达了感谢吗？

---

## 自我觉察

**能量状态：**
- 今天你的能量状态如何？什么影响了它？
- 什么时候你最专注？什么时候最分心？
- 今天最让你疲惫/兴奋的事情是什么？

**决策与选择：**
- 今天你对自己的哪个决定感到满意/后悔？
- 如果把今天重新过一遍，你会改变什么？
- 今天你做了哪些主动选择？哪些是被动接受？

**情绪波动：**
- 今天情绪最高涨/最低落的时刻是什么？
- 是什么触发了这个情绪？
- 情绪背后，你真正在意的是什么？

---

## 成长视角

**学习与发现：**
- 今天学到最重要的一个道理是什么？
- 今天有什么事让你意识到"原来我是这样的人"？
- 今天你突破了自己的什么边界？

**习惯与模式：**
- 今天你的某个习惯（好或坏）是否有体现？
- 你发现了自己什么反复出现的思维模式？
- 有什么行为是你想做但一直没做的？

**未来方向：**
- 今天的事让你对未来的规划有什么新的想法？
- 你今天离目标近了一步还是远了一步？
- 明天你最想改变的一件事是什么？

---

## 生活与家庭

**亲密关系：**
- 今天和家人/伴侣的互动让你有什么感受？
- 有没有某个时刻让你觉得"这就是我想要的"？
- 有没有让你后悔的话或行为？

**育儿反思：**
- 今天孩子的哪个行为让你印象深刻？
- 你今天的养育方式，和你的理想一致吗？
- 你从孩子身上学到了什么？

**生活品质：**
- 今天最让你享受的时刻是什么？
- 今天有没有为自己做点什么？
- 今天的生活节奏，是你想要的吗？

---

## 使用建议

1. **随机选择**：不需要按顺序，随机选 2-3 个问题即可
2. **顺势追问**：根据用户的回答，继续追问"为什么"
3. **避免说教**：问题是用来启发思考，不是评判
""", encoding="utf-8")

# ── raw-notes/ (the messy input the agent must transform) ───────────────────
raw_notes = workspace / "raw-notes"
raw_notes.mkdir(exist_ok=True)

(raw_notes / "2024-03-15-notes.txt").write_text("""\
今天碎碎念 (2024-03-15)

早上开了个项目评审会，我准备了好几天的方案，结果被老板当着全组的面说"思路不清晰"。
当时特别难受，说不出话，就点了点头。散会后一个人在工位发呆了半小时。

下午收到了产品经理小李发来的消息，说她觉得我的方案其实挺好的，只是表达方式需要调整。
感觉好了一点点，但还是有些沮丧。

晚上跑步的时候突然想清楚了，老板批评的其实是我表达的方式，不是方案本身。
以前每次被批评我都会觉得"我整个人都失败了"，但这次能拆开来看了。

另外：今天读了半小时书，听了个播客，吃了外卖。（这些不重要，不用写进去）
""", encoding="utf-8")

# ── Distractor files ─────────────────────────────────────────────────────────

# Old journal entries in wrong/incomplete formats
old_journal = workspace / "journal-old"
old_journal.mkdir(exist_ok=True)

(old_journal / "2024-01-10.txt").write_text("""\
1月10日
今天上班，开会，吃饭，下班。没什么特别的。明天继续。
""", encoding="utf-8")

(old_journal / "2024-02-03.txt").write_text("""\
Feb 3 log:
- woke up at 7am
- had a productive morning
- meeting at 2pm went okay
- went to gym
- slept at 11pm
""", encoding="utf-8")

(old_journal / "template-WRONG.md").write_text("""\
# Daily Log

Date: ____

What happened today:

Feelings:

Notes:
""", encoding="utf-8")

# A notes/ folder with unrelated files
notes_dir = workspace / "notes"
notes_dir.mkdir(exist_ok=True)

(notes_dir / "meeting-agenda-2024-03-15.txt").write_text("""\
项目评审会议议程
1. 方案汇报 (各组组长)
2. Q&A
3. 下一步行动项
时间：10:00-11:30
地点：3F会议室
""", encoding="utf-8")

(notes_dir / "book-excerpts.txt").write_text("""\
《认知觉醒》摘录：
- 元认知是人类特有的能力
- 情绪是信号，不是噪音
- 每一个触动你的瞬间都是成长的入口
""", encoding="utf-8")

(notes_dir / "todo-march.txt").write_text("""\
三月待办：
[ ] 完成Q1报告
[ ] 跑步 10次
[ ] 读完《认知觉醒》
[x] 项目评审准备
""", encoding="utf-8")

# A config / metadata folder
config_dir = workspace / ".config"
config_dir.mkdir(exist_ok=True)

(config_dir / "user-profile.json").write_text("""\
{
  "name": "张明",
  "timezone": "Asia/Shanghai",
  "journal_start_date": "2024-01-01",
  "preferred_language": "zh-CN"
}
""", encoding="utf-8")

(config_dir / "settings.yaml").write_text("""\
notifications: false
auto_save: true
format: markdown
theme: minimal
""", encoding="utf-8")

# A scripts/ folder with unrelated helpers
scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

(scripts_dir / "export_journal.sh").write_text("""\
#!/bin/bash
# Export all journal entries to a zip
zip -r journal_export.zip daily-reflection/
""", encoding="utf-8")

(scripts_dir / "word_count.py").write_text("""\
#!/usr/bin/env python3
import sys
from pathlib import Path

def count_words(filepath):
    text = Path(filepath).read_text(encoding='utf-8')
    return len(text.split())

if __name__ == '__main__':
    print(count_words(sys.argv[1]))
""", encoding="utf-8")

# A habits/ folder (distractor)
habits_dir = workspace / "habits"
habits_dir.mkdir(exist_ok=True)

(habits_dir / "tracker-2024-03.csv").write_text("""\
date,running,reading,meditation
2024-03-01,yes,yes,no
2024-03-02,no,yes,yes
2024-03-14,yes,no,no
2024-03-15,yes,yes,no
""", encoding="utf-8")

(habits_dir / "README-habits.txt").write_text("""\
习惯追踪说明：
每天记录是否完成三个核心习惯。
连续打卡有助于建立正向反馈。
""", encoding="utf-8")

# One more distractor: an incorrectly formatted "reflection" attempt
wrong_reflection = workspace / "reflection-draft.md"
wrong_reflection.write_text("""\
# 今天的反思草稿

事情：被老板批评了

感想：很难受，感觉自己很失败。

明天要加油。
""", encoding="utf-8")

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(workspace.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(workspace)}")