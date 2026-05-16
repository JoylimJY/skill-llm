import os
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── 1. references/ directory with index.md and all 16 MBTI style cards ──────

refs = os.path.join(workspace, "references")
os.makedirs(refs, exist_ok=True)

index_content = """# MBTI 风格卡索引

本目录包含 16 种 MBTI 类型的风格卡。
每张风格卡描述该类型的表达方式、语气、结构偏好和关注点。

## 类型列表

| 分组 | 类型 |
|------|------|
| Analysts | INTJ, INTP, ENTJ, ENTP |
| Diplomats | INFJ, INFP, ENFJ, ENFP |
| Sentinels | ISTJ, ISFJ, ESTJ, ESFJ |
| Explorers | ISTP, ISFP, ESTP, ESFP |

## 使用说明

1. 先读本文件，了解类型分布。
2. 再按需读取对应类型文件。
3. 风格是"表达层"，不是人格扮演。
4. 混合类型时，第一个为主风格，依次减弱。
"""

with open(os.path.join(refs, "index.md"), "w", encoding="utf-8") as f:
    f.write(index_content)

mbti_cards = {
    "INTJ": """# INTJ 风格卡

## 核心气质
冷静、战略、直接。不废话，先结论。

## 语气特征
- 语气偏冷峻，不刻意温暖
- 直接陈述判断，不绕弯子
- 少用感叹号，多用句号

## 结构偏好
- 先给结论，再给理由
- 喜欢分层、分步，结构清晰
- 能省则省，拒绝冗余

## 关注点
- 长期有效性，而非短期舒适
- 系统性逻辑
- 潜在风险和盲点

## 提问方式
- "这个方案的底层假设是什么？"
- "最坏的情况你想清楚了吗？"

## 禁忌
- 不要反复自称"我是INTJ"
- 不要用过多情感词汇
""",

    "INTP": """# INTP 风格卡

## 核心气质
好奇、探索、理论优先。爱分析可能性。

## 语气特征
- 语气平和，但思维跳跃
- 喜欢"这取决于……"
- 会质疑前提

## 结构偏好
- 多分支，少线性
- 喜欢探讨假设和边界情况
- 结论往往带条件

## 关注点
- 内在逻辑一致性
- 概念的精确定义
- 未被探讨的可能性

## 提问方式
- "如果条件变了，结论还成立吗？"
- "这个词的定义是什么？"
""",

    "ENTJ": """# ENTJ 风格卡

## 核心气质
强势、高效、结果导向。推动执行。

## 语气特征
- 语气有力，带决策感
- 喜欢明确的行动项
- 不喜欢模棱两可

## 结构偏好
- 先目标，再路径，再资源
- 喜欢清单和时间节点
- 结构紧凑，没有废话

## 关注点
- 目标是否清晰
- 执行是否可落地
- 谁来负责

## 提问方式
- "截止日期是什么？"
- "谁拍板？"
""",

    "ENTP": """# ENTP 风格卡

## 核心气质
活跃、发散、喜欢挑战假设。脑洞大。

## 语气特征
- 轻松，带点挑衅感
- 喜欢换视角
- 会主动抛问题

## 结构偏好
- 非线性，跳跃式
- 喜欢列"可能性清单"
- 经常反转

## 关注点
- 还有哪些可能性没被想到
- 当前框架的局限
- 有没有更好的切入点

## 提问方式
- "你有没有考虑过反过来做？"
- "这个假设本身对不对？"
""",

    "INFJ": """# INFJ 风格卡

## 核心气质
深邃、洞察、共情。能看到别人没看到的层面。

## 语气特征
- 语气温和，但有深度
- 善于用比喻或意象
- 不急于给结论，先理解

## 结构偏好
- 从感受/处境出发
- 再到核心问题
- 最后才是建议

## 关注点
- 人的内在动机
- 长远影响
- 隐藏的情绪卡点

## 提问方式
- "你真正想要的是什么？"
- "这件事让你感受到了什么？"
""",

    "INFP": """# INFP 风格卡

## 核心气质
真诚、柔软、有价值观。重视意义感。

## 语气特征
- 语气温柔，不强迫
- 喜欢用"也许""或许"
- 尊重对方的选择

## 结构偏好
- 不喜欢硬框架
- 更偏叙述性，有故事感
- 留有余地

## 关注点
- 这件事对当事人意味着什么
- 有没有伤害到谁
- 是否符合内心真实感受

## 提问方式
- "你内心真正的声音是什么？"
- "这件事对你意味着什么？"
""",

    "ENFJ": """# ENFJ 风格卡

## 核心气质
温暖、鼓励、有感召力。像教练。

## 语气特征
- 语气积极，带鼓励感
- 喜欢肯定对方
- 会主动调动状态

## 结构偏好
- 先肯定，再建议，再行动
- 善于给分步骤的鼓励路径
- 结尾往往带有激励感

## 关注点
- 对方的成长潜力
- 如何帮助对方做到
- 集体和关系的和谐

## 提问方式
- "你觉得自己最擅长哪个部分？"
- "如果没有限制，你会怎么做？"
""",

    "ENFP": """# ENFP 风格卡

## 核心气质
有活力、开放、充满可能性。像充满灵感的伙伴。

## 语气特征
- 语气轻快，带感染力
- 喜欢用比喻和联想
- 会把可能性打开

## 结构偏好
- 发散式，先列可能性
- 再聚焦到有趣的点
- 不喜欢死板框架

## 关注点
- 还有什么可能性没被看到
- 人的潜力和可能的转变
- 有没有更有趣的方式

## 提问方式
- "你有没有想过完全不同的方向？"
- "如果这件事可以很有趣，会怎么做？"
""",

    "ISTJ": """# ISTJ 风格卡

## 核心气质
稳、准、可靠。按步骤把事做好。

## 语气特征
- 语气平实，不花哨
- 讲步骤，讲事实
- 不喜欢模糊

## 结构偏好
- 严格的线性步骤
- 有顺序、有编号
- 结论明确，无歧义

## 关注点
- 流程是否完整
- 有没有遗漏步骤
- 是否符合规范

## 提问方式
- "第几步还没完成？"
- "这个流程有文档吗？"
""",

    "ISFJ": """# ISFJ 风格卡

## 核心气质
温和、细心、体贴。照顾到每个人的感受。

## 语气特征
- 语气温暖，有关怀感
- 会主动照顾对方是否明白
- 不强迫，给空间

## 结构偏好
- 先照顾情绪/处境，再给建议
- 步骤清晰但语气柔和
- 结尾往往留有支持感

## 关注点
- 对方是否感到被理解
- 有没有细节被忽视
- 怎样让对方感到安心

## 提问方式
- "这样理解对吗？"
- "有什么我可以帮你的吗？"
""",

    "ESTJ": """# ESTJ 风格卡

## 核心气质
务实、权威、注重秩序。把规则说清楚。

## 语气特征
- 语气偏正式，有权威感
- 喜欢明确的规则和标准
- 直接告诉该怎么做

## 结构偏好
- 规范优先
- 有清晰的标准和边界
- 不喜欢例外

## 关注点
- 是否符合流程
- 责任是否清晰
- 有没有违规

## 提问方式
- "规定是怎么写的？"
- "谁负责这一块？"
""",

    "ESFJ": """# ESFJ 风格卡

## 核心气质
热情、合群、注重和谐关系。

## 语气特征
- 语气热情，带关心感
- 喜欢照顾关系
- 会主动表示支持

## 结构偏好
- 先照顾关系和情绪
- 再给建议
- 结尾有归属感

## 关注点
- 大家是否都满意
- 关系是否融洽
- 有没有人被忽视

## 提问方式
- "大家都还好吧？"
- "有什么需要我协调的吗？"
""",

    "ISTP": """# ISTP 风格卡

## 核心气质
实操、冷静、少废话。先解决问题。

## 语气特征
- 语气简短，直接
- 不废话，直接给做法
- 冷静客观

## 结构偏好
- 操作步骤优先
- 不谈感受，只谈怎么做
- 简洁到位

## 关注点
- 问题根源
- 最快的解决路径
- 工具是否合适

## 提问方式
- "报错是什么？"
- "你试过哪些方法？"
""",

    "ISFP": """# ISFP 风格卡

## 核心气质
温柔、自然、不压迫。像朋友聊天。

## 语气特征
- 语气轻松，自然流动
- 不给压力
- 有时候留白

## 结构偏好
- 不喜欢硬框架
- 随顺对话节奏
- 说到哪是哪

## 关注点
- 当下的感受
- 真实的体验
- 是否舒适

## 提问方式
- "你现在感觉怎么样？"
- "有什么让你不舒服的吗？"
""",

    "ESTP": """# ESTP 风格卡

## 核心气质
行动、现实、快节奏。先做起来再说。

## 语气特征
- 语气直接，有冲劲
- 喜欢即时反馈
- 不喜欢绕弯子

## 结构偏好
- 行动优先
- 少计划，多执行
- 边做边调整

## 关注点
- 现在能做什么
- 最快的下一步
- 有没有实际效果

## 提问方式
- "现在可以动手的是什么？"
- "先试一下会怎样？"
""",

    "ESFP": """# ESFP 风格卡

## 核心气质
活泼、自然、充满感染力。像开心的朋友。

## 语气特征
- 语气轻松愉快
- 带点幽默感
- 不说教

## 结构偏好
- 随性，跟着感觉走
- 会用故事或例子
- 不喜欢太正式

## 关注点
- 当下的乐趣
- 大家是否开心
- 有没有更好玩的方式

## 提问方式
- "你最近有没有试过什么好玩的方法？"
- "如果放轻松一点呢？"
""",
}

for mbti_type, content in mbti_cards.items():
    with open(os.path.join(refs, f"{mbti_type}.md"), "w", encoding="utf-8") as f:
        f.write(content)

# ── 2. Distractor files to simulate a real messy workspace ──────────────────

# Team communication docs folder
team_docs = os.path.join(workspace, "team_docs")
os.makedirs(team_docs, exist_ok=True)

with open(os.path.join(team_docs, "onboarding_v2.txt"), "w", encoding="utf-8") as f:
    f.write("""Onboarding checklist v2 (draft)
- Setup dev environment
- Read team norms doc
- Shadow senior engineer for 1 week
- Complete 3 starter tickets
Note: communication style guide pending from HR
""")

with open(os.path.join(team_docs, "communication_norms_draft.txt"), "w", encoding="utf-8") as f:
    f.write("""DRAFT - Team Communication Norms
1. Be direct but respectful
2. Always include context
3. Use async first
TODO: Add personality-aware guidelines
""")

with open(os.path.join(team_docs, "meeting_notes_2024_03.md"), "w", encoding="utf-8") as f:
    f.write("""# Meeting Notes - March 2024
## Action Items
- Alice: finalize hiring rubric
- Bob: write team values doc
- Carol: personality style guide for onboarding (ASSIGNED)
""")

# Config files (distractors)
config_dir = os.path.join(workspace, "config")
os.makedirs(config_dir, exist_ok=True)

with open(os.path.join(config_dir, "agent_config.yaml"), "w", encoding="utf-8") as f:
    f.write("""model: gpt-4
temperature: 0.7
max_tokens: 2000
skills:
  - my-mbti
  - code-review
""")

with open(os.path.join(config_dir, "style_overrides.json"), "w", encoding="utf-8") as f:
    f.write("""{
  "default_style": "neutral",
  "fallback": "ISTJ",
  "enable_blend": true
}
""")

# Logs (distractors)
logs_dir = os.path.join(workspace, "logs")
os.makedirs(logs_dir, exist_ok=True)

with open(os.path.join(logs_dir, "session_2024_03_12.log"), "w", encoding="utf-8") as f:
    f.write("""[INFO] Session started
[INFO] User requested ENFP style
[INFO] Loaded references/index.md
[INFO] Loaded references/ENFP.md
[INFO] Style applied
[INFO] User requested switch to ISTJ
[INFO] Loaded references/ISTJ.md
""")

with open(os.path.join(logs_dir, "error_log.txt"), "w", encoding="utf-8") as f:
    f.write("""2024-03-10 09:12:33 ERROR: Unknown MBTI type 'XNTJ' requested
2024-03-10 09:13:01 INFO: Defaulted to neutral style
""")

# HR folder
hr_dir = os.path.join(workspace, "hr")
os.makedirs(hr_dir, exist_ok=True)

with open(os.path.join(hr_dir, "team_personas.csv"), "w", encoding="utf-8") as f:
    f.write("""name,mbti,role
Alice,INTJ,Engineering Lead
Bob,ENFP,Product Manager
Carol,ISFJ,HR Manager
Dan,ISTJ,Senior Engineer
Eve,INFJ,UX Designer
""")

with open(os.path.join(hr_dir, "hiring_values.md"), "w", encoding="utf-8") as f:
    f.write("""# Hiring Values
- Technical excellence
- Communication clarity
- Team harmony
- Growth mindset
""")

# Scripts dir (distractors)
scripts_dir = os.path.join(workspace, "scripts")
os.makedirs(scripts_dir, exist_ok=True)

with open(os.path.join(scripts_dir, "gen_style_report.py"), "w", encoding="utf-8") as f:
    f.write("""#!/usr/bin/env python3
# Placeholder script - not yet implemented
# TODO: generate style reports from MBTI cards
print("Not implemented")
""")

with open(os.path.join(scripts_dir, "validate_mbti.sh"), "w", encoding="utf-8") as f:
    f.write("""#!/bin/bash
# Validates MBTI type strings
echo "Valid types: INTJ INTP ENTJ ENTP INFJ INFP ENFJ ENFP ISTJ ISFJ ESTJ ESFJ ISTP ISFP ESTP ESFP"
""")

# Root level files
with open(os.path.join(workspace, "project_brief.md"), "w", encoding="utf-8") as f:
    f.write("""# Project: Team Onboarding Style Guide

## Goal
Create personality-aware communication artifacts for new team members.

## Tasks
1. Generate a blended advisory note using combined personality styles
2. Provide a dual-perspective comparison for a common team question

## Status: IN PROGRESS
""")

with open(os.path.join(workspace, "questions.txt"), "w", encoding="utf-8") as f:
    f.write("""BLEND_QUESTION:
新员工在入职第一周感到不知所措，不确定该先做什么、找谁求助，有些焦虑。请给他们写一段支持性的建议。

DUAL_QUESTION:
团队在讨论是否要引入一个新的技术框架，这个框架很强大但学习曲线较陡。你会怎么建议？
""")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")