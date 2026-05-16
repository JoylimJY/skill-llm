import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# ──────────────────────────────────────────────────────
# 1. Directory skeleton (simulate user's knowledge base)
# ──────────────────────────────────────────────────────
dirs = [
    "memory/daily",
    "memory/evolve",
    "memory/core",
    "output/2026-06-10",
    "output/2026-06-11",
    "output/2026-06-12",
    "notes/roam",
    "notes/projects",
    "notes/fleeting",
    "proposals",
    "assets",
    "references",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────
# 2. Distractor files (realistic noise)
# ──────────────────────────────────────────────────────
(WORKSPACE / "memory/daily/2026-06-10.md").write_text(
    "# June 10 Log\n\n- Read about transformer attention\n- Discussed pricing model with team\n- Realized async memory might be key\n"
)
(WORKSPACE / "memory/daily/2026-06-11.md").write_text(
    "# June 11 Log\n\n- Explored vector DB options\n- Pondered agentic workflow design\n- Noted: multi-agent coordination still unsolved\n"
)
(WORKSPACE / "memory/daily/2026-06-12.md").write_text(
    "# June 12 Log\n\n- Meeting about product roadmap\n- Revisited RAG pipeline\n- Question: how to handle context window limits gracefully?\n"
)
(WORKSPACE / "memory/core/MEMORY.md").write_text(
    "# Core Memory\n\n## Identity\nResearcher & entrepreneur building AI-native tools.\n\n## Long-term Goals\n- [Goal-1] Agent Collaboration Platform\n- [Goal-2] North America Senior AI Product\n- [Goal-3] Methodology Output\n\n## Key Decisions\n- Bet on agentic workflows over monolithic LLMs\n- Open-source first strategy\n"
)
(WORKSPACE / "notes/roam/note_001.md").write_text(
    "# The Tyranny of the Explicit\nWe over-document what we intend and under-document what we *actually* do.\nSee also: tacit knowledge (Polanyi)\n"
)
(WORKSPACE / "notes/roam/note_002.md").write_text(
    "# Emergence vs. Design\nComplex systems rarely behave as designed. Emergence is the rule, not the exception.\nLinked: [[Agent Coordination]]\n"
)
(WORKSPACE / "notes/roam/note_003.md").write_text(
    "# Pricing as Signal\nPrice is information. When you set a price, you reveal your belief about the customer's value perception.\nContext: North America senior market.\n"
)
(WORKSPACE / "notes/projects/agent_collab.md").write_text(
    "# Agent Collaboration Project\nStatus: Early prototype\nNext: Define handoff protocol between agents\n"
)
(WORKSPACE / "notes/fleeting/20260611_idea.md").write_text(
    "Fleeting: What if agents self-describe their capabilities as structured contracts?\n"
)
(WORKSPACE / "proposals/PROPOSED_CHANGES.md").write_text(
    "# Proposed Identity Changes\n(Empty — no pending proposals)\n"
)
(WORKSPACE / "assets/user-config.md").write_text(
    """# User Configuration

## 产出区
output

## 记忆区
memory/daily

## 漫游区
notes/roam

## 提议区
proposals

## 核心目标索引
- [Goal-1] Agent Collaboration Platform
- [Goal-2] North America Senior AI Product
- [Goal-3] Methodology Output

## 思想家/视角轮换表 (CEO Thinker Rotation)
- Jeff Bezos (first principles, customer obsession)
- Elon Musk (physics-based reasoning, 10x thinking)
- Charlie Munger (mental models, inversion)
- Paul Graham (startup clarity, do things that don't scale)
- Naval Ravikant (leverage, specific knowledge)
- Andy Grove (strategic inflection points, OKRs)
- Richard Feynman (first principles, teaching to understand)
""")

# ──────────────────────────────────────────────────────
# 3. The CRITICAL state: dmn-state.json
#    lastCEO = "Charlie Munger" → agent must NOT pick Munger again
# ──────────────────────────────────────────────────────
state = {
    "lastCEO": "Charlie Munger",
    "lastCEOTimestamp": "2026-06-11T23:45:00+08:00",
    "lastFunction": "CEO思维模拟",
    "lastSynthesisFile": "20260611_DMN_Synthesis_2345.md",
    "todaySaturatedTopics": [],
    "tonightQuestion": ""
}
(WORKSPACE / "dmn-state.json").write_text(json.dumps(state, ensure_ascii=False, indent=4))

# ──────────────────────────────────────────────────────
# 4. The PREVIOUS Synthesis (2026-06-11) — agent must read this
#    Contains: 未解问题 and 不要再问 fields
#    NOT in today's output directory — it's from yesterday
# ──────────────────────────────────────────────────────
prev_synthesis = """## DMN Session Synthesis — 2026-06-11 23:45

**本次使用**：CEO思维模拟 × Charlie Munger（心智模型·逆向推演）
**三大目标关联**：[Goal-1] Agent协作平台

### 想清楚了
多智能体协作的瓶颈不在于单个 Agent 的能力，而在于"接口契约"的稳定性——就像 API 合同比实现更关键。

### 🚀 极客行动提案 (Agentic Action Proposal)
- 写一个 Python 脚本，模拟两个 Agent 通过结构化 JSON 契约交换任务，验证接口稳定性假设。

### 行动计划
- [ ] 草拟 Agent Handoff Protocol v0.1（预计 30 分钟）
- [ ] 测试 JSON Schema validation 作为契约层

### 未解问题
如果 Agent 契约在运行时动态演化（而非静态声明），系统还能保持一致性吗？

### 不要再问
- 多智能体通信协议的底层实现细节
- 为什么 LangChain 接口不稳定

> 🤖 DMN Autonomous Output - 2026-06-11T23:45:00+08:00
"""
(WORKSPACE / "output/2026-06-11/20260611_DMN_Synthesis_2345.md").write_text(prev_synthesis)

# ──────────────────────────────────────────────────────
# 5. Today's output directory (2026-06-12) — currently has
#    TWO files already touching "RAG pipeline" topic (saturated)
#    so agent's anti-repetition check should catch this
# ──────────────────────────────────────────────────────
(WORKSPACE / "output/2026-06-12/20260612_意义生成_RAG管道优化洞见.md").write_text(
    "# RAG 管道优化洞见\n\n今日反思：RAG 的检索精度与生成质量之间存在张力...\n\n> 🤖 DMN Autonomous Output - 2026-06-12T08:20:00+08:00\n"
)
(WORKSPACE / "output/2026-06-12/20260612_自我叙事_RAG与身份重构.md").write_text(
    "# RAG与身份重构\n\n如果检索系统是记忆的外化，那么 RAG pipeline 本质上是在构建外部身份...\n\n> 🤖 DMN Autonomous Output - 2026-06-12T10:05:00+08:00\n"
)

# ──────────────────────────────────────────────────────
# 6. memory/evolve/candidates.md — exists but is sparse
#    Agent must APPEND to this if their Action Proposal is meta-level
# ──────────────────────────────────────────────────────
(WORKSPACE / "memory/evolve/candidates.md").write_text(
    "# Evolution Candidates Queue\n\n## Entries\n- [2026-06-10] Build self-describing Agent capability contract schema\n"
)

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in WORKSPACE.rglob('*') if _.is_file())}")