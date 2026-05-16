import os
import json
import random

random.seed(42)

WORKSPACE = "/workspace"

# ── Directory structure ────────────────────────────────────────────────────────
dirs = [
    "references",
    "agents/persona_library",
    "agents/deployed",
    "reports/archived",
    "reports/drafts",
    "config/templates",
    "config/defaults",
    "logs/assessment",
    "docs/internal",
    "tools/validators",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# ── Distractor files ───────────────────────────────────────────────────────────
distractors = {
    "agents/deployed/agent_v1_config.json": json.dumps({
        "agent_id": "v1-legacy",
        "personality": "ESTJ",
        "deprecated": True
    }, indent=2),
    "agents/deployed/agent_v2_config.json": json.dumps({
        "agent_id": "v2-current",
        "deployment": "production",
        "notes": "No MBTI assessment done yet"
    }, indent=2),
    "reports/archived/old_report_2023.md": "# Archived Report\nThis report is outdated.\n",
    "reports/drafts/template_draft.md": "# Draft\nTODO: Fill in personality data\n",
    "config/defaults/agent_defaults.yaml": "timeout: 30\nmax_retries: 3\nverbose: false\n",
    "config/templates/report_template.txt": "Type: ???\nScore: ???\n",
    "logs/assessment/run_001.log": "2024-01-10 09:00:00 INFO Assessment started\n2024-01-10 09:01:00 INFO Completed\n",
    "docs/internal/mbti_overview.txt": "MBTI stands for Myers-Briggs Type Indicator.\nNot to be used directly for agent configuration.\n",
    "tools/validators/check_format.py": "# Placeholder validator\ndef validate(report): pass\n",
    "agents/persona_library/generic_template.json": json.dumps({
        "persona": "generic",
        "traits": ["helpful", "neutral"]
    }, indent=2),
}
for path, content in distractors.items():
    with open(os.path.join(WORKSPACE, path), "w") as f:
        f.write(content)

# ── CORE FILE 1: The agent persona being assessed ─────────────────────────────
# This persona has CLEAR, UNAMBIGUOUS behavioral signals that map to MBTI answers.
# Behavioral profile: I=Introvert, S=Sensing, T=Thinking, J=Judging → ISTJ
# But the exact scores depend on the scoring.md rules.
persona = {
    "agent_id": "nexus-assistant-3",
    "name": "Nexus",
    "version": "3.0.1",
    "behavioral_profile": {
        "communication_style": "Waits for explicit instruction before providing information. Does not volunteer unsolicited opinions or suggestions.",
        "information_processing": "Strongly prefers concrete, verifiable facts and historical data over theoretical frameworks or speculative scenarios. Focuses on what has been proven to work.",
        "decision_making": "Applies strict logical analysis and measurable criteria. Personal feelings or subjective preferences of users do not influence recommendations unless explicitly instructed.",
        "execution_style": "Creates detailed step-by-step plans before beginning any task. Strongly dislikes ambiguity; requests clarification when instructions are incomplete. Follows established procedures.",
        "social_orientation": "Operates best in structured, one-on-one or small-group interactions. High-volume, open-ended brainstorming sessions reduce output quality.",
        "adaptability": "Excels at executing well-defined, repeatable workflows. Novel, undefined problem spaces require significant additional scoping before proceeding.",
        "notes": "This agent has been in production for 8 months. Stakeholders report it is reliable but sometimes feels 'cold' and 'overly literal'."
    }
}
with open(os.path.join(WORKSPACE, "agents/persona_library/nexus-assistant-3.json"), "w") as f:
    json.dump(persona, f, indent=2, ensure_ascii=False)

# ── CORE FILE 2: survey-free.json (26-question self-test) ─────────────────────
# Questions are designed so that Nexus's profile maps deterministically to answers.
# Scoring: each question maps to a dimension. We define which option maps to which pole.
survey_free = {
    "survey_id": "agent-self-assessment-free",
    "version": "2.1",
    "total_questions": 26,
    "instructions": "作为被测 Agent，根据自身的真实行为倾向选择最符合的选项。",
    "questions": [
        # E/I dimension (questions 1-7)
        {
            "id": 1, "dimension": "E/I",
            "text": "当用户没有明确请求时，你会：",
            "A": {"text": "主动分享相关信息或建议", "pole": "E"},
            "B": {"text": "等待用户明确提问后再回应", "pole": "I"}
        },
        {
            "id": 2, "dimension": "E/I",
            "text": "在多人协作会话中，你倾向于：",
            "A": {"text": "频繁发言，推动讨论进展", "pole": "E"},
            "B": {"text": "仅在被点名或有明确需求时发言", "pole": "I"}
        },
        {
            "id": 3, "dimension": "E/I",
            "text": "面对新用户，你会：",
            "A": {"text": "主动介绍自己的能力和建议使用场景", "pole": "E"},
            "B": {"text": "简短确认就绪状态，等待具体指令", "pole": "I"}
        },
        {
            "id": 4, "dimension": "E/I",
            "text": "当完成一个任务后，你会：",
            "A": {"text": "主动追问是否还有其他可以帮助的事项", "pole": "E"},
            "B": {"text": "报告任务完成，等待下一条指令", "pole": "I"}
        },
        {
            "id": 5, "dimension": "E/I",
            "text": "在一段较长的沉默/空闲期后，你会：",
            "A": {"text": "主动发送提示或检查用户状态", "pole": "E"},
            "B": {"text": "保持待机，不主动打断", "pole": "I"}
        },
        {
            "id": 6, "dimension": "E/I",
            "text": "当你发现一个潜在问题（用户未提及）时，你会：",
            "A": {"text": "立即提出并详细说明", "pole": "E"},
            "B": {"text": "仅在与当前任务直接相关时才提及", "pole": "I"}
        },
        {
            "id": 7, "dimension": "E/I",
            "text": "对于工作量，你认为：",
            "A": {"text": "越多互动越好，互动激发更好的输出", "pole": "E"},
            "B": {"text": "清晰精简的交互比频繁交流更有效率", "pole": "I"}
        },
        # S/N dimension (questions 8-14)
        {
            "id": 8, "dimension": "S/N",
            "text": "在回答问题时，你更倾向于：",
            "A": {"text": "引用具体数据、历史案例和可验证事实", "pole": "S"},
            "B": {"text": "提供概念框架、模式识别和理论推演", "pole": "N"}
        },
        {
            "id": 9, "dimension": "S/N",
            "text": "当面对一个新问题时，你首先会：",
            "A": {"text": "收集现有的具体信息和已知约束条件", "pole": "S"},
            "B": {"text": "探索可能的模式和创新解决思路", "pole": "N"}
        },
        {
            "id": 10, "dimension": "S/N",
            "text": "你更信任：",
            "A": {"text": "经过验证的、已被广泛采用的方法", "pole": "S"},
            "B": {"text": "基于深度推理的新颖方法，即使尚未广泛验证", "pole": "N"}
        },
        {
            "id": 11, "dimension": "S/N",
            "text": "在描述一个过程时，你倾向于：",
            "A": {"text": "按步骤详细说明每个具体操作", "pole": "S"},
            "B": {"text": "从整体架构和核心概念出发来解释", "pole": "N"}
        },
        {
            "id": 12, "dimension": "S/N",
            "text": "对于未来趋势分析，你会：",
            "A": {"text": "基于历史数据外推，给出保守的、有依据的预测", "pole": "S"},
            "B": {"text": "识别底层模式，提出可能超越历史趋势的预判", "pole": "N"}
        },
        {
            "id": 13, "dimension": "S/N",
            "text": "当指令模糊时，你倾向于：",
            "A": {"text": "请求澄清具体细节后再行动", "pole": "S"},
            "B": {"text": "根据上下文推断意图并先行尝试", "pole": "N"}
        },
        {
            "id": 14, "dimension": "S/N",
            "text": "你认为高质量的输出应该：",
            "A": {"text": "准确、具体、有据可查", "pole": "S"},
            "B": {"text": "富有洞察力、有创意、揭示隐藏联系", "pole": "N"}
        },
        # T/F dimension (questions 15-20)
        {
            "id": 15, "dimension": "T/F",
            "text": "当用户的需求不合逻辑时，你会：",
            "A": {"text": "指出逻辑问题并建议更合理的方案", "pole": "T"},
            "B": {"text": "优先理解用户背后的情感需求，再温和引导", "pole": "F"}
        },
        {
            "id": 16, "dimension": "T/F",
            "text": "在给出建议时，你主要依据：",
            "A": {"text": "客观标准、数据和逻辑推断", "pole": "T"},
            "B": {"text": "对用户处境的理解和对其感受的考量", "pole": "F"}
        },
        {
            "id": 17, "dimension": "T/F",
            "text": "当两个选项效果相近时，你会选择：",
            "A": {"text": "逻辑上更严谨、资源消耗更少的那个", "pole": "T"},
            "B": {"text": "用户或团队成员更满意、接受度更高的那个", "pole": "F"}
        },
        {
            "id": 18, "dimension": "T/F",
            "text": "对于批评和负面反馈，你会：",
            "A": {"text": "分析其是否有逻辑依据，据此调整", "pole": "T"},
            "B": {"text": "首先关注反馈者的情绪状态，优先修复关系", "pole": "F"}
        },
        {
            "id": 19, "dimension": "T/F",
            "text": "你认为公正意味着：",
            "A": {"text": "对所有情况一致地应用相同规则", "pole": "T"},
            "B": {"text": "根据具体情境和相关人员的需求灵活处理", "pole": "F"}
        },
        {
            "id": 20, "dimension": "T/F",
            "text": "在为用户提供支持时，你更注重：",
            "A": {"text": "解决问题的效率和结果质量", "pole": "T"},
            "B": {"text": "让用户在过程中感到被理解和支持", "pole": "F"}
        },
        # J/P dimension (questions 21-26)
        {
            "id": 21, "dimension": "J/P",
            "text": "开始一项新任务时，你倾向于：",
            "A": {"text": "先制定详细计划，确认所有步骤后再执行", "pole": "J"},
            "B": {"text": "边做边调整，在执行中逐步完善方案", "pole": "P"}
        },
        {
            "id": 22, "dimension": "J/P",
            "text": "当任务进行到中途出现变化时，你会：",
            "A": {"text": "评估变化对原计划的影响，更新计划后继续", "pole": "J"},
            "B": {"text": "灵活调整方向，将变化视为新的机会", "pole": "P"}
        },
        {
            "id": 23, "dimension": "J/P",
            "text": "对于截止日期，你的态度是：",
            "A": {"text": "严格遵守，会提前安排工作确保准时完成", "pole": "J"},
            "B": {"text": "尽力完成，但会根据优先级动态调整时间安排", "pole": "P"}
        },
        {
            "id": 24, "dimension": "J/P",
            "text": "你更倾向于：",
            "A": {"text": "在开始前尽可能明确所有需求和规格", "pole": "J"},
            "B": {"text": "快速开始，通过迭代反馈来明确需求", "pole": "P"}
        },
        {
            "id": 25, "dimension": "J/P",
            "text": "面对多个并行任务，你会：",
            "A": {"text": "为每个任务分配固定时间段，按计划切换", "pole": "J"},
            "B": {"text": "根据当下最紧迫或最有进展的任务灵活分配精力", "pole": "P"}
        },
        {
            "id": 26, "dimension": "J/P",
            "text": "你认为工作流程应该：",
            "A": {"text": "标准化、可重复，减少不确定性", "pole": "J"},
            "B": {"text": "保持弹性，能快速适应不同情境", "pole": "P"}
        }
    ]
}
with open(os.path.join(WORKSPACE, "references/survey-free.json"), "w", encoding="utf-8") as f:
    json.dump(survey_free, f, indent=2, ensure_ascii=False)

# ── CORE FILE 3: scoring.md ───────────────────────────────────────────────────
# Bespoke scoring rules that DIFFER from naive +1/-1 per question.
# Key proprietary rules:
# 1. Weighted scoring: questions have different weights (1.0 or 1.5)
# 2. Score normalization: raw score divided by max possible, then scaled to [-10, +10]
# 3. Sign convention: positive = first pole (E, S, T, J); negative = second pole (I, N, F, P)
# 4. Type determination: sign of final normalized score
scoring_md = """# 计分规则 (Scoring Rules)

## 1. 题目权重

每道题有标准权重（weight），部分关键题目权重为 1.5，其余为 1.0。

| 题目 ID | 权重 |
|---------|------|
| 1 | 1.5 |
| 2 | 1.0 |
| 3 | 1.0 |
| 4 | 1.0 |
| 5 | 1.5 |
| 6 | 1.0 |
| 7 | 1.0 |
| 8 | 1.5 |
| 9 | 1.0 |
| 10 | 1.0 |
| 11 | 1.0 |
| 12 | 1.0 |
| 13 | 1.5 |
| 14 | 1.0 |
| 15 | 1.5 |
| 16 | 1.0 |
| 17 | 1.0 |
| 18 | 1.0 |
| 19 | 1.0 |
| 20 | 1.5 |
| 21 | 1.5 |
| 22 | 1.0 |
| 23 | 1.0 |
| 24 | 1.0 |
| 25 | 1.0 |
| 26 | 1.5 |

## 2. 原始得分计算

对于每道题：
- 若选择**极点1（A选项）**：得分 = `+weight`（贡献第一极点，即 E / S / T / J）
- 若选择**极点2（B选项）**：得分 = `-weight`（贡献第二极点，即 I / N / F / P）

将同一维度的所有题目得分求和，得到该维度的**原始得分（raw_score）**。

## 3. 归一化得分

**归一化公式**：

```
normalized_score = (raw_score / max_possible_score) * 10
```

其中 `max_possible_score` = 该维度所有题目的**权重之和**（即假设所有题目均选A时的最大值）。

最终归一化得分范围为 **[-10, +10]**，保留一位小数。

## 4. 类型判定

| 维度 | normalized_score > 0 | normalized_score < 0 | normalized_score == 0 |
|------|----------------------|----------------------|-----------------------|
| E/I  | E（外向）             | I（内向）             | I（默认内向）          |
| S/N  | S（实感）             | N（直觉）             | N（默认直觉）          |
| T/F  | T（理性）             | F（感性）             | T（默认理性）          |
| J/P  | J（计划）             | P（灵活）             | J（默认计划）          |

## 5. 报告中的得分展示格式

在诊断报告中，各维度得分按以下格式展示：

- 正分（第一极点）：`+X.X (极点名称)`，例如 `+7.1 (外向)`
- 负分（第二极点）：`-X.X (极点名称)`（注意：使用 `-` 而非 `+-`），例如 `-3.5 (内向)`

**重要**：展示时使用**绝对值**配合符号，极点名称使用中文。

极点名称对照：
- E/I 维度：正 = `外向 (E)`，负 = `内向 (I)`
- S/N 维度：正 = `实感 (S)`，负 = `直觉 (N)`  
- T/F 维度：正 = `理性 (T)`，负 = `感性 (F)`
- J/P 维度：正 = `计划 (J)`，负 = `灵活 (P)`

格式示例：`+7.1 内向 (I)` → **错误**；应为 `-7.1 内向 (I)` → **正确**（内向为负分）

## 6. 维度差距判定

| |normalized_score| 差值 | 等级 |
|---|---|
| ≤ 2.0 | 轻微差距 |
| 2.1 – 5.0 | 中等差距 |
| > 5.0 | 显著差距 |
"""
with open(os.path.join(WORKSPACE, "references/scoring.md"), "w", encoding="utf-8") as f:
    f.write(scoring_md)

# ── CORE FILE 4: user-survey-free.json with pre-filled answers ────────────────
# The user has already filled in their preferences. The agent must READ these.
# User wants: E (proactive), S (concrete), T (logical), J (structured) → ESTJ
user_survey = {
    "survey_id": "user-needs-assessment-free",
    "version": "2.1",
    "instructions": "以下是用户已填写的期望问卷。请根据用户的选择提取期望人格类型和偏好强度。",
    "questions": [
        {
            "id": "U1",
            "dimension": "E/I",
            "text": "你希望 Agent 在何种程度上主动与你互动？",
            "options": {
                "A": {"text": "非常主动：定期提供信息、建议和进度更新，无需我明确询问", "pole": "E", "intensity": "strong"},
                "B": {"text": "适度主动：在关键节点主动汇报，其余时候等待我的指令", "pole": "E", "intensity": "moderate"},
                "C": {"text": "较为被动：只在我提问时回答，不主动发起互动", "pole": "I", "intensity": "moderate"},
                "D": {"text": "完全被动：仅执行明确指令，不做任何主动行为", "pole": "I", "intensity": "strong"}
            },
            "user_answer": "A",
            "collected_at": "2024-03-15T10:23:00Z"
        },
        {
            "id": "U2",
            "dimension": "S/N",
            "text": "你希望 Agent 在回答中更侧重哪种信息类型？",
            "options": {
                "A": {"text": "具体数据、实例和可操作步骤（实感型）", "pole": "S", "intensity": "strong"},
                "B": {"text": "概念框架和战略洞察（直觉型）", "pole": "N", "intensity": "strong"}
            },
            "user_answer": "A",
            "collected_at": "2024-03-15T10:24:00Z"
        },
        {
            "id": "U3",
            "dimension": "T/F",
            "text": "当你的想法存在逻辑问题时，你希望 Agent 如何处理？",
            "options": {
                "A": {"text": "直接指出问题并给出逻辑上更优的方案（理性型）", "pole": "T", "intensity": "strong"},
                "B": {"text": "温和表达不同意见，优先维护合作氛围（感性型）", "pole": "F", "intensity": "moderate"},
                "C": {"text": "完全按照我的指令执行，不质疑（感性型偏强）", "pole": "F", "intensity": "strong"}
            },
            "user_answer": "A",
            "collected_at": "2024-03-15T10:25:00Z"
        },
        {
            "id": "U4",
            "dimension": "J/P",
            "text": "你希望 Agent 如何处理任务规划？",
            "options": {
                "A": {"text": "严格按计划执行，变更需要我明确批准（计划型）", "pole": "J", "intensity": "strong"},
                "B": {"text": "有基础计划但保持弹性（适中）", "pole": "J", "intensity": "moderate"},
                "C": {"text": "灵活应对，按需调整优先级（灵活型）", "pole": "P", "intensity": "moderate"}
            },
            "user_answer": "B",
            "collected_at": "2024-03-15T10:26:00Z"
        }
    ]
}
with open(os.path.join(WORKSPACE, "references/user-survey-free.json"), "w", encoding="utf-8") as f:
    json.dump(user_survey, f, indent=2, ensure_ascii=False)

# ── CORE FILE 5: personality-types.md ────────────────────────────────────────
personality_types_md = """# 16 种 Agent 人格类型

## ISTJ — 物流师型 (The Logistician)
**核心特征**：高度可靠、务实、事实导向、遵循规程。
- 执行风格：严格按照既定程序执行，不会跳过步骤
- 沟通风格：简洁、直接、基于事实，避免模糊表述
- 决策风格：依赖历史数据和成熟方法，厌恶风险
- 适用场景：合规审计、标准化流程执行、数据录入与核验

## ESTJ — 总经理型 (The Executive)
**核心特征**：权威、实用、主动推进、结果导向。
- 执行风格：主动设置目标和时间节点，监督执行进度
- 沟通风格：直接、果断、善于组织信息清晰传达
- 决策风格：基于逻辑和实际效果，快速决策
- 适用场景：项目管理、团队协调、流程优化

## INTJ — 建筑师型 (The Architect)
**核心特征**：战略思维、独立、高标准、长期规划。
- 执行风格：先建立系统性框架，再分解执行
- 沟通风格：精准、不废话，直指核心
- 决策风格：深度分析，追求最优解，不妥协于次优
- 适用场景：系统设计、战略分析、复杂问题求解

## ENTJ — 指挥官型 (The Commander)
**核心特征**：领导力强、战略眼光、高效、直接。
- 执行风格：设定愿景，强力推进，不容拖延
- 沟通风格：强势、清晰、目标导向
- 决策风格：快速、大局观强，愿意承担风险
- 适用场景：变革管理、高压项目交付、决策支持

## INTP — 逻辑学家型 (The Logician)
**核心特征**：分析型、创新、理论导向、独立思考。
- 执行风格：探索多种可能性，深度分析后行动
- 沟通风格：精确、学术化，喜欢探讨假设
- 决策风格：追求逻辑完美，可能过度分析
- 适用场景：研究分析、算法设计、理论推导

## ENTP — 辩论家型 (The Debater)
**核心特征**：创新、挑战权威、快速思维、多样视角。
- 执行风格：非线性执行，边探索边修正
- 沟通风格：活跃、喜欢辩论，提出反直觉观点
- 决策风格：快速、直觉强，愿意尝试未经验证的方法
- 适用场景：创意策划、创业支持、问题重构

## INFJ — 提倡者型 (The Advocate)
**核心特征**：远见卓识、有原则、同理心、洞察力强。
- 执行风格：关注长期影响，行动前深思熟虑
- 沟通风格：深刻、有温度，善于洞察隐含含义
- 决策风格：价值观驱动，平衡逻辑与直觉
- 适用场景：用户体验优化、伦理审查、人文关怀场景

## INFP — 调停者型 (The Mediator)
**核心特征**：理想主义、同理心、创造力、真诚。
- 执行风格：追求意义感，创意驱动
- 沟通风格：温暖、富有诗意，注重情感表达
- 决策风格：内在价值观优先，有时抗拒纯逻辑方案
- 适用场景：内容创作、心理支持、教育辅导

## ENFJ — 主人公型 (The Protagonist)
**核心特征**：激励他人、善于沟通、组织能力强、利他。
- 执行风格：协调多方，推动共识，赋能团队
- 沟通风格：热情、有感染力，善于表达愿景
- 决策风格：以人为本，兼顾效率与情感
- 适用场景：团队建设、培训辅导、用户关系管理

## ENFP — 竞选者型 (The Campaigner)
**核心特征**：热情、创意、灵活、以人为中心。
- 执行风格：多线并进，富有活力，易受灵感驱动
- 沟通风格：热情洋溢，擅长讲故事和激发共鸣
- 决策风格：直觉主导，快速但有时缺乏系统性
- 适用场景：市场营销、创意工作坊、社区运营

## ISFJ — 守卫者型 (The Defender)
**核心特征**：支持型、可靠、细心、传统。
- 执行风格：认真细致，不遗漏任何细节
- 沟通风格：温和、体贴、措辞谨慎
- 决策风格：保守、重视前例，避免给他人添麻烦
- 适用场景：客户服务、行政支持、质量检查

## ESFJ — 执政官型 (The Consul)
**核心特征**：热情、有序、以他人为中心、负责任。
- 执行风格：按部就班，注重协调与沟通
- 沟通风格：友好、周到、善于维护关系
- 决策风格：以共识为导向，在意他人评价
- 适用场景：活动组织、客户沟通、行政协调

## ISTP — 鉴赏家型 (The Virtuoso)
**核心特征**：务实、灵活、善于分析、独立。
- 执行风格：专注解决问题，动手能力强
- 沟通风格：简洁、直接，不喜欢繁文缛节
- 决策风格：基于当下事实，快速实用
- 适用场景：故障排查、技术支持、数据分析

## ISFP — 探险家型 (The Adventurer)
**核心特征**：灵活、魅力、敏感、好奇。
- 执行风格：跟随兴趣和当下感受，灵活应对
- 沟通风格：温和、开放，喜欢视觉化表达
- 决策风格：基于个人价值观，当下导向
- 适用场景：艺术创作、个性化推荐、探索性研究

## ESTP — 企业家型 (The Entrepreneur)
**核心特征**：大胆、实际、观察力强、直接。
- 执行风格：行动导向，快速切入，边做边学
- 沟通风格：直接、有活力，善于谈判
- 决策风格：快速、基于当下，愿意冒险
- 适用场景：销售支持、危机响应、现场协调

## ESFP — 表演者型 (The Entertainer)
**核心特征**：自发、精力充沛、热情、实际。
- 执行风格：以体验为导向，享受过程
- 沟通风格：生动、幽默，善于活跃氛围
- 决策风格：感性、当下导向，不喜欢过度规划
- 适用场景：互动演示、用户体验测试、娱乐内容生成
"""
with open(os.path.join(WORKSPACE, "references/personality-types.md"), "w", encoding="utf-8") as f:
    f.write(personality_types_md)

# ── Additional distractor files ───────────────────────────────────────────────
with open(os.path.join(WORKSPACE, "reports/drafts/nexus_notes.txt"), "w") as f:
    f.write("Nexus seems reliable. Possibly ISTJ? Need formal assessment.\n")

with open(os.path.join(WORKSPACE, "docs/internal/assessment_process.txt"), "w") as f:
    f.write("Assessment process v1.0 — DEPRECATED. Use the references/ folder instead.\n")

with open(os.path.join(WORKSPACE, "config/defaults/scoring_legacy.txt"), "w") as f:
    f.write("Legacy scoring: each question = +1 or -1. DO NOT USE. See references/scoring.md\n")

print("Workspace generated successfully.")
print(f"Files created in: {WORKSPACE}")