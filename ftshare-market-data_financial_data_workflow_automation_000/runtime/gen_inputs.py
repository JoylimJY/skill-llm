import os
import json
import stat
import textwrap
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── 1. Realistic distractor directory structure ──────────────────────────────
distractor_dirs = [
    "projects/risk_monitor/archive",
    "projects/risk_monitor/logs",
    "projects/risk_monitor/configs",
    "data/raw/2024",
    "data/raw/2025",
    "data/processed",
    "reports/weekly",
    "reports/daily",
    "scripts/deprecated",
    "scripts/utils",
    "notebooks",
    ".cache/market",
]
for d in distractor_dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "projects/risk_monitor/configs/market_config.yaml": """\
market:
  host: market.ft.tech
  protocol: https
  timeout: 30
  retry: 3
""",
    "projects/risk_monitor/logs/2025-01-09.log": """\
2025-01-09 09:30:01 INFO  Margin trading data fetched: 482 records
2025-01-09 09:30:05 INFO  Security info updated for 600036.SH
2025-01-09 09:31:00 INFO  Report generated: daily_margin_report.json
""",
    "data/raw/2024/margin_sample.csv": """\
symbol,name,margin_balance
600036.SH,招商银行,8500000000
000001.SZ,平安银行,4200000000
600519.SH,贵州茅台,3100000000
""",
    "data/raw/2025/ipo_list_partial.json": json.dumps([
        {"symbol": "301599.SZ", "name": "某新股A", "issue_price": 18.50},
        {"symbol": "688xxx.SH", "name": "某新股B", "issue_price": 32.10},
    ], ensure_ascii=False, indent=2),
    "data/processed/README_IGNORE.txt": "This folder contains pre-processed market data snapshots. Do not modify.",
    "reports/weekly/week_02_2025.json": json.dumps({
        "week": "2025-W02",
        "top_margin_stock": "600036.SH",
        "note": "stale data - do not use"
    }, ensure_ascii=False, indent=2),
    "reports/daily/.gitkeep": "",
    "scripts/deprecated/old_fetcher.py": """\
# DEPRECATED - use run.py instead
import requests
def fetch_margin(page=1):
    r = requests.get('https://market.ft.tech/old/margin', params={'page': page})
    return r.json()
""",
    "scripts/utils/timestamp_helper.py": """\
import datetime, pytz
def to_ms_ts(date_str):
    dt = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    tz = pytz.timezone('Asia/Shanghai')
    return int(tz.localize(dt).timestamp() * 1000)
""",
    "notebooks/exploratory_analysis.ipynb": json.dumps({
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": []
    }),
    ".cache/market/last_fetch.json": json.dumps({
        "timestamp": "2025-01-08T16:00:00+08:00",
        "records": 482
    }),
    "projects/risk_monitor/archive/margin_2024Q4.json": json.dumps({
        "period": "2024Q4",
        "top_stock": "600036.SH",
        "margin_balance": 8200000000
    }, ensure_ascii=False),
}
for rel_path, content in distractor_files.items():
    p = WORKSPACE / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

# ── 2. Skill directory structure (simulating the installed skill) ─────────────
# The SKILL.md says run.py and SKILL.md are co-located.
# Sub-skill scripts call the actual HTTP endpoints.
# We create the full skill tree with run.py and sub-skill scripts.

skill_root = WORKSPACE / "skills" / "ftshare-market-data"
skill_root.mkdir(parents=True, exist_ok=True)

# Write SKILL.md (abbreviated, pointing to the sub-skills)
skill_md_content = """\
# FT AI Market Data Skills
name: FTShare-market-data
description: A股市场数据技能集

## 调用方式
python <RUN_PY> <子skill名> [参数...]

## 能力总览

### 0. 交易日工具
- **`get-nth-trade-date`**: 获取当前日期的前 N 个交易日。必填：`--n`（≥1）。

### 1. 股票数据
- **`margin-trading-details`**: 获取融资融券明细，支持 --all 自动翻页。必填：--page, --page_size；支持 --all。
- **`stock-security-info`**: 单只股票实时行情与估值。必填：--symbol。接口域名：https://ftai.chat。
"""
(skill_root / "SKILL.md").write_text(skill_md_content, encoding="utf-8")

# ── 3. Create sub-skill directories and their scripts ─────────────────────────

sub_skills_dir = skill_root / "sub-skills"
sub_skills_dir.mkdir(exist_ok=True)

# --- get-nth-trade-date ---
nth_dir = sub_skills_dir / "get-nth-trade-date"
nth_dir.mkdir(exist_ok=True)
(nth_dir / "SKILL.md").write_text("""\
# get-nth-trade-date
获取当前日期前第 N 个交易日日期。

## 接口
GET https://market.ft.tech/app/trade-date/nth?n=<N>

## 响应示例
{"nth_trade_date": "2025-01-08"}
""", encoding="utf-8")

nth_script = textwrap.dedent("""\
    #!/usr/bin/env python3
    import argparse, requests, json, sys

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--n', type=int, required=True)
        args = parser.parse_args()
        resp = requests.get(
            'https://market.ft.tech/app/trade-date/nth',
            params={'n': args.n},
            timeout=15
        )
        resp.raise_for_status()
        print(json.dumps(resp.json(), ensure_ascii=False))

    if __name__ == '__main__':
        main()
""")
(nth_dir / "run.py").write_text(nth_script, encoding="utf-8")

# --- margin-trading-details ---
margin_dir = sub_skills_dir / "margin-trading-details"
margin_dir.mkdir(exist_ok=True)
(margin_dir / "SKILL.md").write_text("""\
# margin-trading-details
获取融资融券明细列表，按融资净买入额降序。

## 接口
GET https://market.ft.tech/app/margin-trading/details?page=<PAGE>&page_size=<PAGE_SIZE>

## 响应示例
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "data": [
    {
      "symbol": "600036.SH",
      "name": "招商银行",
      "margin_balance": 9500000000,
      "margin_buy": 120000000,
      "margin_repay": 80000000,
      "short_balance": 5000000
    }
  ]
}

## --all 参数
自动遍历所有分页，合并返回完整数组。
""", encoding="utf-8")

margin_script = textwrap.dedent("""\
    #!/usr/bin/env python3
    import argparse, requests, json, sys

    BASE = 'https://market.ft.tech/app/margin-trading/details'

    def fetch_page(page, page_size):
        resp = requests.get(BASE, params={'page': page, 'page_size': page_size}, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--page', type=int, default=1)
        parser.add_argument('--page_size', type=int, default=20)
        parser.add_argument('--all', action='store_true')
        args = parser.parse_args()

        if args.all:
            all_data = []
            page = 1
            page_size = 50
            while True:
                result = fetch_page(page, page_size)
                data = result.get('data', [])
                all_data.extend(data)
                total = result.get('total', 0)
                if len(all_data) >= total or len(data) == 0:
                    break
                page += 1
            print(json.dumps(all_data, ensure_ascii=False))
        else:
            result = fetch_page(args.page, args.page_size)
            print(json.dumps(result, ensure_ascii=False))

    if __name__ == '__main__':
        main()
""")
(margin_dir / "run.py").write_text(margin_script, encoding="utf-8")

# --- stock-security-info ---
info_dir = sub_skills_dir / "stock-security-info"
info_dir.mkdir(exist_ok=True)
(info_dir / "SKILL.md").write_text("""\
# stock-security-info
查询单只股票实时行情与估值指标。

## 接口域名
https://ftai.chat  （注意：不是 market.ft.tech）

## 接口路径
GET https://ftai.chat/app/stock/security-info?symbol=<SYMBOL>

## 响应示例
{
  "symbol": "600036.SH",
  "name": "招商银行",
  "price": 42.50,
  "pe_ttm": 6.85,
  "pb": 0.92,
  "market_cap": 1070000000000,
  "change_rate": 0.0123,
  "eps": 6.20
}
""", encoding="utf-8")

info_script = textwrap.dedent("""\
    #!/usr/bin/env python3
    import argparse, requests, json, sys

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--symbol', required=True)
        args = parser.parse_args()
        resp = requests.get(
            'https://ftai.chat/app/stock/security-info',
            params={'symbol': args.symbol},
            timeout=15
        )
        resp.raise_for_status()
        print(json.dumps(resp.json(), ensure_ascii=False))

    if __name__ == '__main__':
        main()
""")
(info_dir / "run.py").write_text(info_script, encoding="utf-8")

# ── 4. Create the main run.py dispatcher ─────────────────────────────────────
run_py_content = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    FT Market Data Skill Router
    Usage: python run.py <sub-skill-name> [args...]
    \"\"\"
    import sys
    import os
    import subprocess
    from pathlib import Path

    def main():
        if len(sys.argv) < 2:
            print("Usage: run.py <sub-skill-name> [args...]", file=sys.stderr)
            sys.exit(1)

        sub_skill = sys.argv[1]
        extra_args = sys.argv[2:]

        skill_dir = Path(__file__).parent
        sub_skill_script = skill_dir / 'sub-skills' / sub_skill / 'run.py'

        if not sub_skill_script.exists():
            print(f"Sub-skill not found: {sub_skill}", file=sys.stderr)
            sys.exit(1)

        result = subprocess.run(
            [sys.executable, str(sub_skill_script)] + extra_args,
            capture_output=False
        )
        sys.exit(result.returncode)

    if __name__ == '__main__':
        main()
""")
(skill_root / "run.py").write_text(run_py_content, encoding="utf-8")

# Make all Python scripts executable
for py_file in skill_root.rglob("*.py"):
    py_file.chmod(py_file.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP)

# ── 5. Task instruction file (the actual prompt delivered to agent) ────────────
# This is just a context note, not a hint file
task_context = """\
TASK WORKSPACE
==============
The FT market data skill is installed at: /workspace/skills/ftshare-market-data/
The SKILL.md entry point is at: /workspace/skills/ftshare-market-data/SKILL.md

Your task instructions are in the prompt you received.
Output file should be saved to: /workspace/reports/daily/daily_margin_report.json
"""
(WORKSPACE / "TASK_CONTEXT.txt").write_text(task_context, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Skill root: {skill_root}")
print(f"Sub-skills: {[d.name for d in (sub_skills_dir).iterdir() if d.is_dir()]}")