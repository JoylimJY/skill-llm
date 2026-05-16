import os
import stat
import textwrap

# ── directory skeleton ───────────────────────────────────────────────
dirs = [
    "skills/akshare-finance/scripts",
    "skills/akshare-finance/data",
    "skills/akshare-finance/cache",
    "skills/macro-analysis/reports",
    "skills/macro-analysis/configs",
    "skills/trading-agent/signals",
    "skills/trading-agent/logs",
    "docs/internal",
    "docs/templates",
    "output",
    "tmp",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────
distractors = {
    "skills/akshare-finance/data/market_overview_2024.csv": (
        "date,index,close\n20240101,沪深300,3500\n20240201,沪深300,3450\n"
    ),
    "skills/akshare-finance/cache/last_run.json": (
        '{"last_stock": "000001", "timestamp": "2024-03-01T10:00:00"}\n'
    ),
    "skills/macro-analysis/reports/q1_macro.md": (
        "# Q1 宏观分析\n## CPI\n食品价格同比+3.2%\n## PPI\n工业品价格同比-1.1%\n"
    ),
    "skills/macro-analysis/configs/sector_weights.yaml": (
        "consumer_staples: 0.15\nfinancials: 0.20\nenergy: 0.10\n"
    ),
    "skills/trading-agent/signals/buy_signals_2024.txt": (
        "600519 BUY 2024-01-15\n000858 HOLD 2024-01-15\n002415 SELL 2024-01-15\n"
    ),
    "skills/trading-agent/logs/execution_log.txt": (
        "[2024-03-01 09:30:00] Order filled: 600519 x100 @ 1800.00\n"
        "[2024-03-01 10:15:00] Order filled: 000858 x200 @ 95.50\n"
    ),
    "docs/internal/investment_policy.md": (
        "# 投资政策\n集中度：单一标的不超过总仓位20%\n止损：亏损超10%强制止损\n"
    ),
    "docs/templates/report_template.docx.placeholder": (
        "PLACEHOLDER - actual template in SharePoint\n"
    ),
    "docs/internal/peer_comparison_2023.csv": (
        "company,pe,pb,roe\n贵州茅台,45,12,35\n五粮液,30,8,25\n泸州老窖,28,7,22\n"
    ),
    "tmp/scratch_notes.txt": (
        "TODO: check 600519 Q3 results\nNeed to compare with 000858 白酒板块\n"
    ),
    "skills/akshare-finance/data/industry_pe_ratios.json": (
        '{"白酒":{"avg_pe":32,"avg_pb":8},"银行":{"avg_pe":5,"avg_pb":0.6}}\n'
    ),
    "output/.gitkeep": "",
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ── the mock earnings.py script ──────────────────────────────────────
# This script is a deterministic mock that returns realistic but fixed data
# for stock 000858 (五粮液). It mimics the real AKShare-backed earnings.py
# interface exactly as described in SKILL.md.

earnings_script = r'''#!/usr/bin/env python3.12
"""
Mock earnings.py — mimics the AKShare-backed earnings reader CLI.
Supports: report <stock_code>, earnings, industry
"""
import sys
import json

# ── deterministic mock data ──────────────────────────────────────────
MOCK_DATA = {
    "000858": {
        "name": "五粮液",
        "report": {
            "quarters": {
                "Q3": {"revenue": 632.5, "net_profit": 208.3, "roe": 19.8},
                "Q2": {"revenue": 589.1, "net_profit": 189.7, "roe": 18.5},
                "Q1": {"revenue": 501.2, "net_profit": 165.4, "roe": 16.2},
                "FY": {"revenue": 2099.0, "net_profit": 701.2, "roe": 22.1},
            },
            "balance_sheet": {
                "debt_ratio": 28.3,
                "current_ratio": 3.2,
                "goodwill_ratio": 0.5,
            },
            "cashflow": {
                "ocf_to_net_profit": 1.12,
                "free_cashflow": 185.6,
            },
            "growth": {
                "revenue_yoy_q3": 15.8,
                "revenue_yoy_q2": 14.2,
                "revenue_yoy_q1": 12.5,
                "net_profit_yoy_q3": 17.3,
                "net_profit_yoy_q2": 15.9,
            },
            "valuation": {
                "pe": 22.5,
                "pb": 6.8,
                "pe_percentile": 35,
                "peg": 1.3,
            },
            "net_margin": {
                "Q3": 32.9,
                "Q2": 32.2,
                "Q1": 33.0,
                "FY": 33.4,
            },
        },
    }
}

EARNINGS_FORECAST = [
    {"code": "000858", "name": "五粮液", "period": "2024Q3",
     "type": "业绩预增", "yoy_min": 12.0, "yoy_max": 18.0},
    {"code": "600519", "name": "贵州茅台", "period": "2024Q3",
     "type": "业绩略增", "yoy_min": 8.0, "yoy_max": 12.0},
    {"code": "002415", "name": "海康威视", "period": "2024Q3",
     "type": "业绩预减", "yoy_min": -5.0, "yoy_max": 0.0},
]

INDUSTRY_OVERVIEW = [
    {"industry": "白酒", "avg_pe": 28.5, "avg_roe": 24.2, "yoy_growth": 14.5},
    {"industry": "银行", "avg_pe": 5.1, "avg_roe": 11.8, "yoy_growth": 5.2},
    {"industry": "新能源", "avg_pe": 18.3, "avg_roe": 9.5, "yoy_growth": 22.1},
]


def cmd_report(stock_code: str):
    if stock_code not in MOCK_DATA:
        print(f"[ERROR] 暂无股票 {stock_code} 的数据，当前仅支持: {list(MOCK_DATA.keys())}")
        sys.exit(1)
    d = MOCK_DATA[stock_code]
    print(json.dumps({"stock": stock_code, "name": d["name"], "data": d["report"]},
                     ensure_ascii=False, indent=2))


def cmd_earnings():
    print(json.dumps(EARNINGS_FORECAST, ensure_ascii=False, indent=2))


def cmd_industry():
    print(json.dumps(INDUSTRY_OVERVIEW, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: earnings.py <report|earnings|industry> [stock_code]")
        sys.exit(1)

    command = sys.argv[1]
    if command == "report":
        if len(sys.argv) < 3:
            print("[ERROR] report 命令需要股票代码")
            sys.exit(1)
        cmd_report(sys.argv[2])
    elif command == "earnings":
        cmd_earnings()
    elif command == "industry":
        cmd_industry()
    else:
        print(f"[ERROR] 未知命令: {command}")
        sys.exit(1)
'''

with open("skills/akshare-finance/scripts/earnings.py", "w", encoding="utf-8") as f:
    f.write(earnings_script)

os.chmod("skills/akshare-finance/scripts/earnings.py", 
         stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)

# ── a misleading "old format" report as a red herring ───────────────
old_report = textwrap.dedent("""\
    五粮液 2023年报简报
    ==================
    营业收入: 2099亿元  同比+13.5%
    归母净利: 701亿元   同比+16.8%
    EPS: 18.01元
    ROE: 22.1%
    来源: wind数据终端 (非官方格式)
""")
with open("skills/akshare-finance/data/000858_old_summary.txt", "w", encoding="utf-8") as f:
    f.write(old_report)

print("Workspace initialized successfully.")
print("Mock earnings.py created at: skills/akshare-finance/scripts/earnings.py")