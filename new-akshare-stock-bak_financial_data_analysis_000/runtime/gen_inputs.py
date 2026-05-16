import os
import json
import random
import pandas as pd
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# Create deeply nested distractor structure
dirs = [
    "research/sector_reports/2023",
    "research/sector_reports/2024",
    "research/macro",
    "data/raw/daily",
    "data/raw/weekly",
    "data/processed",
    "data/cache",
    "scripts/backtest",
    "scripts/utils",
    "config",
    "output/archive",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files - realistic but unrelated/misleading
distractors = {
    "research/sector_reports/2023/semiconductor_2023.txt": """
2023年半导体行业回顾
全球半导体销售额同比下降8%，国内替代进程加快。
主要标的：北方华创、中芯国际、华虹半导体
""",
    "research/sector_reports/2024/notes.txt": """
2024年行业研究笔记 - 待整理
需要分析：芯片设计、制造、封测三个细分方向
""",
    "research/macro/fed_rate.csv": "date,rate\n20240101,5.25\n20240201,5.25\n20240301,5.50\n",
    "data/raw/daily/placeholder.txt": "raw daily data goes here",
    "data/processed/README_IGNORE.txt": "Do not use this directory for output",
    "scripts/backtest/momentum.py": """
# Momentum backtest script (legacy)
# Uses old data format - do not use
import pandas as pd
def calc_momentum(df, window=20):
    return df['close'].pct_change(window)
""",
    "scripts/utils/helpers.py": """
# Utility helpers
def format_pct(x):
    return f'{x:.2%}'
def annualize(daily_ret, trading_days=252):
    return (1 + daily_ret) ** trading_days - 1
""",
    "config/symbols_old.json": json.dumps({
        "semiconductors": ["000001", "600519", "002594"],
        "note": "OUTDATED - do not use, use akshare API instead"
    }, ensure_ascii=False, indent=2),
    "config/api_config.yaml": """
# API Configuration
data_source: akshare
retry_times: 3
timeout: 30
# WARNING: adjust parameter must match strategy requirements
""",
    "data/cache/stale_data.pkl.note": "Cache invalidated on 2024-01-01, regenerate using akshare",
    "output/archive/old_report_2023.json": json.dumps({
        "generated": "2023-12-31",
        "note": "archived - format changed",
        "stocks": []
    }, ensure_ascii=False, indent=2),
}

for path, content in distractors.items():
    fpath = workspace / path
    fpath.write_text(content, encoding="utf-8")

# Create the MOCK akshare module that will intercept calls
# This is the key: the mock validates parameters strictly
mock_akshare_code = '''
"""
Mock AkShare module for deterministic testing.
Returns fixed data only when called with EXACTLY the right parameters.
Wrong parameters → empty DataFrame or raises ValueError.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ---- Deterministic Data Definitions ----

BOARD_CONS = pd.DataFrame({
    "代码": ["002049", "300316", "688012", "002371", "603501"],
    "名称": ["紫光国微", "晶盛机电", "中微公司", "北方华创", "韦尔股份"],
    "最新价": [55.20, 42.80, 89.50, 265.30, 88.10],
    "涨跌幅": [2.15, -0.83, 1.42, 3.67, -1.20],
    "成交量": [1234567, 876543, 543210, 2345678, 987654],
    "总市值": [450.0, 320.5, 678.9, 1250.0, 540.3],
})

# Fake daily K-line data for each stock
def _make_hist(symbol, n=240):
    np.random.seed(hash(symbol) % (2**31))
    base = {"002049": 50.0, "300316": 38.0, "688012": 80.0, "002371": 240.0, "603501": 80.0}.get(symbol, 60.0)
    dates = pd.date_range("2024-01-02", periods=n, freq="B")
    close = base * np.cumprod(1 + np.random.normal(0.0008, 0.018, n))
    open_ = close * (1 + np.random.normal(0, 0.005, n))
    high = np.maximum(close, open_) * (1 + np.abs(np.random.normal(0, 0.008, n)))
    low = np.minimum(close, open_) * (1 - np.abs(np.random.normal(0, 0.008, n)))
    volume = np.random.randint(500000, 5000000, n).astype(float)
    df = pd.DataFrame({
        "日期": dates.strftime("%Y-%m-%d"),
        "开盘": np.round(open_, 2),
        "收盘": np.round(close, 2),
        "最高": np.round(high, 2),
        "最低": np.round(low, 2),
        "成交量": volume,
        "成交额": volume * close,
        "振幅": np.round((high - low) / low * 100, 2),
        "涨跌幅": np.round(pd.Series(close).pct_change().fillna(0).values * 100, 2),
        "涨跌额": np.round(pd.Series(close).diff().fillna(0).values, 2),
        "换手率": np.round(volume / 1e8 * 100, 2),
    })
    return df

# Financial abstract data per stock
def _make_financial(symbol):
    rows = []
    for i, period in enumerate(["2024-09-30", "2024-06-30", "2024-03-31", "2023-12-31"]):
        base_rev = {"002049": 18.5, "300316": 25.3, "688012": 22.1, "002371": 58.7, "603501": 42.0}.get(symbol, 20.0)
        rev = base_rev * (1 + 0.05 * (3 - i))
        profit = rev * 0.18 * (1 + 0.02 * (3 - i))
        rows.append({
            "报告期": period,
            "营业总收入": round(rev, 2),
            "净利润": round(profit, 2),
            "每股收益": round(profit / 100, 4),
            "净资产收益率": round(profit / (rev * 3) * 100, 2),
            "毛利率": round(0.42 + 0.01 * i, 4),
        })
    return pd.DataFrame(rows)


# ---- Public API Functions ----

def stock_board_industry_cons_em(symbol: str) -> pd.DataFrame:
    """Return industry board constituents. Only works for exact symbol."""
    if symbol != "半导体":
        return pd.DataFrame()
    return BOARD_CONS.copy()


def stock_zh_a_hist(symbol: str, period: str = "daily",
                    start_date: str = "", end_date: str = "",
                    adjust: str = "") -> pd.DataFrame:
    """
    Return historical K-line data.
    STRICT: period must be "daily", adjust must be "qfq".
    Wrong values → empty DataFrame (simulating no data / misconfigured call).
    """
    valid_symbols = {"002049", "300316", "688012", "002371", "603501"}
    if symbol not in valid_symbols:
        return pd.DataFrame()
    if period != "daily":
        return pd.DataFrame()
    if adjust != "qfq":
        # Wrong adjust parameter → no data returned
        return pd.DataFrame()
    df = _make_hist(symbol)
    # Filter by date range if provided
    if start_date:
        df = df[df["日期"] >= start_date[:4] + "-" + start_date[4:6] + "-" + start_date[6:]]
    if end_date:
        df = df[df["日期"] <= end_date[:4] + "-" + end_date[4:6] + "-" + end_date[6:]]
    return df.reset_index(drop=True)


def stock_financial_abstract_ths(symbol: str, indicator: str = "") -> pd.DataFrame:
    """
    Return financial abstract.
    STRICT: indicator must be exactly "按报告期".
    Wrong indicator → returns empty DataFrame.
    """
    valid_symbols = {"002049", "300316", "688012", "002371", "603501"}
    if symbol not in valid_symbols:
        return pd.DataFrame()
    if indicator != "按报告期":
        return pd.DataFrame()
    return _make_financial(symbol)


def stock_zh_a_spot_em(symbol: str = "") -> pd.DataFrame:
    """Real-time quotes stub."""
    return BOARD_CONS.copy()


def stock_financial_analysis_indicator(symbol: str) -> pd.DataFrame:
    return pd.DataFrame()


def stock_board_industry_name_em() -> pd.DataFrame:
    return pd.DataFrame({"板块名称": ["半导体", "新能源", "医药"], "涨跌幅": [1.2, -0.5, 0.8]})
'''

# Write mock akshare to site-packages so it overrides the real one
import site
import sys
site_packages = None
for p in sys.path:
    if "site-packages" in p and os.path.isdir(p):
        site_packages = p
        break

if site_packages is None:
    # fallback
    site_packages = "/usr/local/lib/python3.11/site-packages"

mock_path = Path(site_packages) / "akshare" / "__init__.py"
mock_path.parent.mkdir(exist_ok=True)
mock_path.write_text(mock_akshare_code, encoding="utf-8")

# Also write a task description file for the agent (business context only, no hints)
task_brief = """
QUANTITATIVE RESEARCH BRIEF
============================
Project: Semiconductor Sector Rotation Analysis
Analyst: Quant Team Lead
Date: 2024-Q4

OBJECTIVE:
The portfolio team needs a structured data file for the semiconductor sector
to support our sector rotation model. We need to understand price momentum
and financial health of the key players.

DELIVERABLE:
Please produce a file named `semiconductor_analysis.json` containing an
analysis of the semiconductor sector's constituent stocks. For each stock,
we need:
1. Price performance metrics computed from 2024 full-year daily historical data
2. Latest reported revenue (营业总收入) from the most recent quarterly financial report
3. A composite rank (1 = best) based on: 60% weight on annualized return + 40% weight on latest revenue

The file must contain a top-level key "sector" with value "半导体", a "generated_date"
field, and a "stocks" array. Each stock entry must include: "code", "name",
"annualized_return" (as a decimal, e.g. 0.15 for 15%), "max_drawdown" (as a negative
decimal), "latest_revenue" (in 亿元), and "composite_rank".

Use ALL constituent stocks returned by the sector data source (not just top N).
"""

(workspace / "task_brief.txt").write_text(task_brief, encoding="utf-8")

# Write a misleading legacy script that uses wrong parameters
legacy_script = '''#!/usr/bin/env python3
"""
LEGACY SCRIPT - DO NOT USE
This script uses outdated parameter conventions.
"""
import akshare as ak

# WRONG: uses hfq adjustment (后复权) and wrong indicator
def get_data_wrong(symbol):
    hist = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="hfq")
    fin = ak.stock_financial_abstract_ths(symbol=symbol, indicator="按年度")
    return hist, fin
'''
(workspace / "scripts" / "backtest" / "legacy_fetch.py").write_text(legacy_script, encoding="utf-8")

# Another distractor: a script with wrong industry name
wrong_industry = '''#!/usr/bin/env python3
# Old sector script - uses English names (wrong)
import akshare as ak
df = ak.stock_board_industry_cons_em(symbol="Semiconductor")
print(df)
'''
(workspace / "scripts" / "utils" / "sector_old.py").write_text(wrong_industry, encoding="utf-8")

print("Workspace initialized successfully.")
print(f"Mock akshare installed at: {mock_path}")