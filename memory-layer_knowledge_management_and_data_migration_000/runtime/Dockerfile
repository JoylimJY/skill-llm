FROM python:3.11-slim

RUN sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list.d/debian.sources || sed -i 's/deb.debian.org/mirrors.tuna.tsinghua.edu.cn/g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    bash \
    coreutils \
    findutils \
    grep \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple \
    pathlib2

RUN cat > /gen_inputs_script.py << 'PYEOF'
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

# -- 1. Legacy messy structure
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

skill_dir = WORKSPACE / "skill"
skill_dir.mkdir(exist_ok=True)

(skill_dir / "SKILL.md").write_text("""---
name: memory-layer
description: Three-layer memory management system.
---

# Memory Layer

## Architecture

Index -> Topics -> Transcripts

""", encoding="utf-8")

print("Workspace generated successfully.")
print("\nDirectory tree:")
for p in sorted(WORKSPACE.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(WORKSPACE)}")
PYEOF

WORKDIR /workspace