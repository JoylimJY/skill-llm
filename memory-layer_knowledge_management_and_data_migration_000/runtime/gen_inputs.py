#!/usr/bin/env python3
"""
Generate a messy, realistic legacy workspace for a quant research firm.
The agent must migrate this into the three-layer memory system.
"""
import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)
WORKSPACE = Path("/workspace")

# ── 1. Legacy messy structure ──────────────────────────────────────────────────
dirs = [
    "old_memory/research",
    "old_memory/strategies",
    "old_memory/risk",
    "old_memory/raw_logs",
    "old_memory/misc",
    "archive/2024",
    "archive/2023",
    "scratch",
    "tmp_notes",
    "reports/weekly",
    "reports/monthly",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── 2. Legacy topic-like files (to be migrated to memory/topics/) ─────────────
topics = {
    "old_memory/research/alpha-momentum.md": """# Alpha Momentum Strategy
Created: 2025-01-15
Last review: 2026-03-20

## Overview
Cross-sectional momentum on A-share universe, 20-day lookback.
Sharpe: 1.82, Max DD: -12.4%

## Key Parameters
- Universe: CSI 500
- Rebalance: weekly
- Signal: 20d return z-score
- Position sizing: vol-parity

## Recent Changes
2026-03-20: Added turnover penalty to reduce transaction costs.
""",
    "old_memory/research/factor-valuation.md": """# Valuation Factor Research
Owner: quant-team
Status: production

## PB-ROE Composite
Uses 12-month trailing ROE with forward PB.
IC mean: 0.045, ICIR: 1.3

## Notes
- Avoid financials sector (distorted book value)
- Recompute monthly after earnings season
""",
    "old_memory/strategies/stat-arb.md": """# Statistical Arbitrage
Updated: 2026-02-10

## Pairs Trading
Cointegration-based on sector ETFs.
Entry z-score: 2.0, Exit: 0.5
Hold period: 3-7 days

## Risk Controls
- Max pairs: 20
- Correlation floor: 0.7
- Stop loss: 3% per pair
""",
    "old_memory/strategies/trend-following.md": """# Trend Following CTA
Updated: 2026-01-05

## System Parameters
Breakout on 60d high/low for futures.
ATR-based position sizing.
Markets: IF, IC, IH, TS, TF

## Performance
2025 return: +18.3%
2024 return: +7.1%
""",
    "old_memory/risk/var-model.md": """# Value at Risk Model
Maintained by: risk-team
Last updated: 2026-03-01

## Methodology
Historical simulation, 252-day window.
Confidence: 99%, Horizon: 1-day

## Limits
Portfolio VaR limit: 1.5% NAV/day
Stress VaR: 3x normal VaR
""",
    "old_memory/misc/infra-notes.md": """# Infrastructure Notes
Data vendor: Wind + Tushare
Execution: in-house OMS
Backtest engine: Zipline fork

## Servers
Prod: 10.0.1.10 (DO NOT store passwords here)
Dev: 10.0.1.20

## Contacts
Ops: ops-team@internal
""",
}
for path, content in topics.items():
    (WORKSPACE / path).write_text(content, encoding="utf-8")

# ── 3. Legacy raw log files (to be migrated to memory/transcripts/YYYY-MM/) ───
log_entries = [
    ("old_memory/raw_logs/session-2026-03-15.log",
     "2026-03-15",
     """[2026-03-15 09:12] Reviewed momentum alpha, added turnover filter.
[2026-03-15 10:45] Discussed VaR breach on 2026-03-14 with risk team.
[2026-03-15 14:00] Backtest run: stat-arb sharpe improved to 1.9 with new entry threshold.
"""),
    ("old_memory/raw_logs/session-2026-03-28.log",
     "2026-03-28",
     """[2026-03-28 08:30] Monthly factor review. Valuation IC declining in growth sectors.
[2026-03-28 11:00] CTA review: trend system hit stop on IC futures.
[2026-03-28 15:30] Infrastructure: Wind API latency spike, fallback to Tushare.
"""),
    ("old_memory/raw_logs/session-2026-04-01.log",
     "2026-04-01",
     """[2026-04-01 09:00] Q2 kickoff meeting. Priority: improve factor decay model.
[2026-04-01 13:00] Code review: OMS integration with new broker API.
"""),
    ("old_memory/raw_logs/session-2025-12-10.log",
     "2025-12-10",
     """[2025-12-10 10:00] Year-end review. Best strategy: momentum alpha +22%.
[2025-12-10 14:00] Risk framework update approved by CRO.
"""),
]
for path, date, content in log_entries:
    (WORKSPACE / path).write_text(content, encoding="utf-8")

# ── 4. Old flat MEMORY.md (not in index format, just chaotic notes) ───────────
old_memory_md = """# Memory Notes (OLD FORMAT)
DO NOT USE THIS FORMAT - needs migration

- alpha momentum strategy is in old_memory/research/alpha-momentum.md
- valuation factor notes somewhere in research folder
- stat arb and trend CTA in strategies/
- VaR model documentation in risk/
- raw session logs in raw_logs/

TODO: organize all this properly
Last touched: 2026-03-01
"""
(WORKSPACE / "MEMORY.md").write_text(old_memory_md, encoding="utf-8")

# ── 5. Distractor files ────────────────────────────────────────────────────────
distractors = {
    "scratch/tmp_analysis.py": "# TODO: clean up\nimport pandas as pd\n# placeholder\n",
    "scratch/ideas.txt": "ideas:\n- alternative data\n- NLP on earnings calls\n- satellite imagery\n",
    "tmp_notes/meeting-notes-jan.txt": "Jan 10: Discussed Q1 roadmap.\nJan 17: Budget review.\n",
    "tmp_notes/meeting-notes-feb.txt": "Feb 3: New hire onboarding.\nFeb 20: Strategy review.\n",
    "reports/weekly/wk13-2026.md": "# Week 13 Report\nPnL: +0.8%\nTop contributor: momentum\n",
    "reports/weekly/wk12-2026.md": "# Week 12 Report\nPnL: -0.3%\nTop contributor: CTA\n",
    "reports/monthly/march-2026.md": "# March 2026\nMonthly return: +2.1%\n",
    "archive/2024/old-strategy-v1.md": "# Legacy Strategy v1\nDecommissioned 2025-01.\n",
    "archive/2023/research-dump.md": "# 2023 Research\nArchived.\n",
    ".gitignore": "*.pyc\n__pycache__/\ntmp/\n",
    "requirements.txt": "pandas==2.1.0\nnumpy==1.26.0\n",
    "config/app.yaml": "env: production\nlog_level: INFO\n",
}
(WORKSPACE / "config").mkdir(exist_ok=True)
for path, content in distractors.items():
    p = WORKSPACE / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ── 6. SKILL.md reference files (the agent needs these) ───────────────────────
skill_dir = WORKSPACE / "skill"
skill_dir.mkdir(exist_ok=True)

(skill_dir / "SKILL.md").write_text("""---
name: memory-layer
description: 基于 Claude Code 记忆哲学的三层记忆管理系统。当需要以下操作时使用：(1) 设计 Index/Topic/Transcript 记忆架构，(2) 迁移现有记忆文件到分层结构，(3) 配置 autoDream 自动整理，(4) 优化上下文窗口使用率 70%+，(5) 实现基于重要性评分的记忆排序和检索。
---

# Memory Layer - 三层记忆系统

> 🧠 基于 Claude Code 记忆哲学，为 OpenClaw 设计

---

## 核心原则

| 原则 | 说明 |
|------|------|
| **分层加载** | Index 永远加载，Topic 按需，Transcript 仅 grep |
| **写纪律** | 先写 Topic，再更新 Index（防止膨胀） |
| **敏感数据不存储** | Transcript 是纯文本，禁止存储账号/密码/健康记录 |
| **自动化** | autoDream 夜间整理（默认禁用，需手动启用） |

---

## 架构

```
┌─────────────────────────────────────────┐
│   MEMORY.md (Index 层)                   │
│   - 仅指针，≤25KB                        │
│   - 始终加载到上下文                      │
└───────────────┬─────────────────────────┘
                │ 按需加载 (2-5 个文件)
                ▼
┌─────────────────────────────────────────┐
│   memory/topics/*.md (Topic 层)          │
│   - 结构化知识，≤50KB/文件               │
│   - 仅在相关时加载                        │
└───────────────┬─────────────────────────┘
                │ 永不加载，仅 grep
                ▼
┌─────────────────────────────────────────┐
│   memory/transcripts/*.log (Transcript 层)│
│   - 原始日志，仅追加                      │
│   - >90 天自动归档                        │
└─────────────────────────────────────────┘
```

---

## 如何使用

### 1. 创建目录结构

```bash
mkdir -p memory/topics memory/transcripts/$(date +%Y-%m)
```

### 2. 迁移现有记忆文件

```bash
# 备份（重要）
cp -r memory/ memory.backup.$(date +%Y%m%d)

# 迁移（根据你的目录结构调整）
cp memory/investments/*.md memory/topics/  # 示例
cp memory/projects/*.md memory/topics/     # 示例
cp memory/assets/*.md memory/topics/       # 示例
```

### 3. 重构 MEMORY.md

手动重写为 Index 格式（参考 references/index-spec.md）：

```markdown
# MEMORY.md - OpenClaw 记忆索引

## Topics
| 领域 | 主题 | 路径 | 更新 | 摘要 | 标签 | 重要性 |
|------|------|------|------|------|------|--------|
| 项目 | 内容工具 | memory/topics/project-tool.md | 2026-04-02 | 创作工具 | AI | 0.7 |
```

### 4. 启用 autoDream（可选）

```bash
# 默认配置已禁用，需手动启用
openclaw cron add "0 23 * * *" "memory-system auto-dream"
```

---

## 依赖

| 依赖 | 必需 | 说明 |
|------|------|------|
| OpenClaw CLI | ✅ | 唯一依赖 |
| OpenClaw Cron | ❌ | 仅 autoDream 需要 |

**无需额外工具**：本 Skill 是纯文档设计，`memory-system` 等工具不存在。

---

## 配置

**默认配置**：`config/default.json`（Skill 自带）

**自定义配置**：`~/.openclaw/memory-config.json`（可选）

```json
{
  "autoDream": {
    "enabled": false,
    "schedule": "23:00",
    "notifyOnComplete": false
  }
}
```

---

## 文档导航

| 文档 | 说明 |
|------|------|
| references/architecture.md | 完整架构设计 |
| references/index-spec.md | Index 层格式规范 |
| references/topic-spec.md | Topic 层格式规范 |
| references/transcript-spec.md | Transcript 层格式规范 |
| references/autodream.md | autoDream 算法详情 |
| references/config.md | 完整配置参数 |
| guides/MIGRATION.md | 迁移指南 |
| guides/EXAMPLES.md | 使用示例 |

---

*版本：2.0 | 最后更新：2026-04-03 | 代号：Memory Layer*
""", encoding="utf-8")

print("Workspace generated successfully.")
print("\nDirectory tree:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")