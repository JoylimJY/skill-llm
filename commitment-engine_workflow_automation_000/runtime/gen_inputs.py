import os
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Create deeply nested distractor structure ---
# Simulates a financial ops team workspace

dirs = [
    "workspace/reports/daily",
    "workspace/reports/weekly",
    "workspace/reports/archive/2024",
    "workspace/reports/archive/2025",
    "workspace/ops/risk",
    "workspace/ops/compliance",
    "workspace/ops/settlement",
    "workspace/data/feeds/bloomberg",
    "workspace/data/feeds/reuters",
    "workspace/data/processed",
    "workspace/logs/heartbeat",
    "workspace/logs/cron",
    "workspace/memory/2025-07",
    "workspace/memory/2025-06",
    "workspace/config",
    "workspace/scripts",
    "workspace/templates",
]

for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/reports/daily/risk_summary_20250714.md": "# Risk Summary\n\nVaR: $2.3M\nExposure: Normal\n",
    "workspace/reports/daily/risk_summary_20250715.md": "# Risk Summary\n\nVaR: $1.9M\nExposure: Low\n",
    "workspace/reports/weekly/pnl_week28.xlsx.txt": "PnL data placeholder - week 28",
    "workspace/reports/archive/2024/q4_report.md": "# Q4 2024 Report\n\nFinal figures: +12.3%\n",
    "workspace/reports/archive/2025/q1_report.md": "# Q1 2025 Report\n\nFinal figures: +8.1%\n",
    "workspace/ops/risk/thresholds.json": '{"var_limit": 5000000, "exposure_limit": 10000000, "drawdown_limit": 0.05}',
    "workspace/ops/compliance/checklist.md": "- [ ] Daily reconciliation\n- [ ] Position limits check\n- [ ] Counterparty exposure review\n",
    "workspace/ops/settlement/pending.csv": "trade_id,amount,counterparty,status\nT001,1200000,Goldman,pending\nT002,850000,JPMorgan,pending\n",
    "workspace/data/feeds/bloomberg/snapshot_20250716.json": '{"source": "bloomberg", "timestamp": "2025-07-16T08:00:00Z", "status": "ok"}',
    "workspace/data/feeds/reuters/snapshot_20250716.json": '{"source": "reuters", "timestamp": "2025-07-16T07:55:00Z", "status": "ok"}',
    "workspace/data/processed/clean_positions.csv": "symbol,quantity,price,value\nSPY,1000,540.2,540200\nQQQ,500,460.1,230050\n",
    "workspace/logs/heartbeat/hb_20250716_0800.log": "[08:00:01] Heartbeat started\n[08:00:02] No active commitments found\n[08:00:03] Heartbeat complete\n",
    "workspace/logs/heartbeat/hb_20250716_0900.log": "[09:00:01] Heartbeat started\n[09:00:02] Checking commitments...\n[09:00:03] Heartbeat complete\n",
    "workspace/logs/cron/cron_20250715.log": "2025-07-15 17:50:01 - Triggered: daily-risk-prep\n2025-07-15 17:50:45 - Completed successfully\n",
    "workspace/memory/2025-07/20250715.md": "## 2025-07-15 Memory\n\n- Processed 3 commitments\n- Daily report sent at 17:55\n- No overdue items\n",
    "workspace/memory/2025-07/20250714.md": "## 2025-07-14 Memory\n\n- Settlement review completed\n- 2 commitments marked done\n",
    "workspace/memory/2025-06/20250630.md": "## 2025-06-30 Memory\n\n- Month-end report compiled\n- All commitments cleared\n",
    "workspace/config/agent_config.yaml": "agent_name: xiaomeng\nheartbeat_interval: 300\nledger_path: workspace/commitments.md\ntimezone: Asia/Shanghai\n",
    "workspace/scripts/prep_daily_report.sh": "#!/bin/bash\n# Prepares the daily risk report\necho 'Preparing daily risk report...'\npython3 workspace/scripts/generate_report.py\n",
    "workspace/scripts/generate_report.py": "#!/usr/bin/env python3\n# Generates risk report from processed data\nprint('Report generation placeholder')\n",
    "workspace/templates/commitment_template.txt": "This is just a reference template - do not use directly.\nSee SKILL.md for actual format.\n",
}

for filepath, content in distractor_files.items():
    p = Path(filepath)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# --- THE CORE PROBLEM: Raw incoming task requests from the manager ---
# These are the messy, informal inputs the agent must process.
# Intentionally mixed Chinese/English, informal phrasing, no structure.

# We fix a reference datetime for the test: 2025-07-16 09:30:00 (Wednesday)
# This is recorded so the agent knows "now" for relative time calculations.

task_requests_content = """# 任务请求清单 — 收到时间：2025-07-16 09:30:00 (周三)

以下是今天早上收到的几条指令，请帮我录入追踪系统，确保都能按时执行：

---

[请求1] 每天下午17:50给我发工作日报（周一到周五），包含当日风控指标摘要和未结算交易清单。

[请求2] 帮我记得今天做一下对手方敞口复核，不太紧急，今天内完成就行。

[请求3] 下午14:00之前把上周的PnL结算报告发给合规部门。

[请求4] 记得联系路透社数据团队确认feed状态，今天内搞定。

[请求5] 我一会儿要开会，会后你给我整理一份本周未结算交易的汇总，直接发给我就行。

---

备注：请求1是长期的每日任务；其余都是今天的事。
"""

task_requests_path = Path("workspace/task_requests.md")
task_requests_path.write_text(task_requests_content, encoding="utf-8")

# Also create an EMPTY commitments.md with just the header (not filled - agent must fill it)
# Actually - do NOT pre-create it. Let the agent create it from scratch as required.
# But do create the parent workspace dir marker
marker = Path("workspace/.initialized")
marker.write_text("Workspace initialized at 2025-07-16 09:30:00\n")

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 2}")