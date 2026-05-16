import os
import json
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Create deeply nested distractor file structure ──────────────────────────

dirs = [
    "reports/daily/2026-01",
    "reports/daily/2026-02",
    "reports/weekly",
    "data/raw/margin",
    "data/raw/news",
    "data/processed",
    "config",
    "logs",
    "scripts/legacy",
    "tools/analysis",
    "tools/viz",
    "archive/2025",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "reports/daily/2026-01/summary_20260115.txt": "市场情绪偏弱，涨停家数52，跌停家数18。融资余额18420亿。",
    "reports/daily/2026-02/summary_20260228.txt": "赚钱效应指数42%，连板天梯最高6板。",
    "reports/weekly/week_08_2026.md": "# 第8周周报\n\n本周市场整体偏弱，主力资金净流出。",
    "data/raw/margin/margin_snapshot_20260201.json": json.dumps({
        "date": "2026-02-01",
        "rzye": 18200,
        "rqye": 980
    }, ensure_ascii=False),
    "data/raw/news/news_batch_001.jsonl": '{"t":"2026-02-28T09:30:00","cat":"宏观","title":"央行维持利率不变"}\n{"t":"2026-02-28T10:15:00","cat":"个股","title":"某科技公司发布业绩预告"}',
    "data/processed/themes_20260228.csv": "题材名,涨停数,净流入亿\n人工智能,12,8.5\n新能源,9,5.2\n半导体,7,3.8",
    "config/data_sources.yaml": "base_url: https://hhxg.top/static/data\ncache_dir: ~/.cache/hhxg-market\ntimeout: 15",
    "config/report_template.json": json.dumps({
        "version": "1.0",
        "sections": ["market", "margin", "calendar"],
        "output_format": "json"
    }, ensure_ascii=False),
    "logs/fetch_errors_20260228.log": "[2026-02-28 20:01:05] ERROR: timeout fetching sectors\n[2026-02-28 20:01:06] INFO: retry success",
    "scripts/legacy/old_fetch.py": "# DEPRECATED: use fetch_snapshot.py instead\nimport requests\ndef get_market():\n    pass  # no longer maintained",
    "tools/analysis/calc_momentum.py": "def momentum(prices, window=20):\n    return [prices[i]/prices[i-window]-1 for i in range(window, len(prices))]",
    "tools/viz/plot_margin.py": "# placeholder for margin visualization\n# requires matplotlib",
    "archive/2025/annual_summary_2025.txt": "2025年A股全年涨停总数约12500次，融资余额年末收于16800亿。",
}

for rel_path, content in distractor_files.items():
    fpath = workspace / rel_path
    fpath.write_text(content, encoding="utf-8")

# ── The actual task artifact requirement ──────────────────────────────────────
# Agent must create: morning_digest.json in the workspace root
# This file does NOT exist yet — agent must create it by running the skills

# Create a task specification file (business context, not instructions)
task_spec = {
    "task": "morning_digest_automation",
    "requested_by": "quant_team_lead",
    "output_file": "morning_digest.json",
    "description": (
        "每日开盘前需要一份结构化的摘要 JSON，供量化策略系统读取。"
        "该文件需要合并三个维度的数据："
        "1. 最近交易日市场情绪数据（含连板晋级率和可选的量化信号计数）"
        "2. 融资融券近7日净买入TOP5股票及7日总变化"
        "3. 全年期货/期权交割日列表"
    ),
    "note": "请直接生成 morning_digest.json，无需解释。"
}
(workspace / "task_spec.json").write_text(
    json.dumps(task_spec, ensure_ascii=False, indent=2), encoding="utf-8"
)

print("Workspace initialized with distractor files and task spec.")
print(f"Agent must create: {workspace}/morning_digest.json")