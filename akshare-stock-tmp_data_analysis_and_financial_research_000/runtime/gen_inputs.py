#!/usr/bin/env python3
"""
Generate the sandbox workspace with mock akshare module, distractor files,
and the task brief for the agent.
"""
import os
import json
import random
import pandas as pd
import numpy as np
from pathlib import Path

random.seed(42)
np.random.seed(42)

WORKSPACE = Path("/workspace")

# ─────────────────────────────────────────────
# 1. Create distractor directory structure
# ─────────────────────────────────────────────
distractor_dirs = [
    "archive/2022/Q1",
    "archive/2022/Q3",
    "archive/2023/reports",
    "data/raw/equity",
    "data/processed/temp",
    "notebooks/experiments",
    "config/backtests",
    "logs/pipeline",
    "scripts/deprecated",
    "docs/internal",
]
for d in distractor_dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "archive/2022/Q1/portfolio_snapshot.csv": "symbol,weight\n000001,0.15\n600519,0.20\n300750,0.18\n",
    "archive/2022/Q3/risk_report.txt": "VaR (95%): 2.3%\nMax Drawdown: 8.7%\nSharpe Ratio: 1.42\n",
    "archive/2023/reports/annual_summary.json": json.dumps({"year": 2023, "return": "12.4%", "benchmark": "CSI300"}),
    "data/raw/equity/tickers.txt": "000001\n600519\n300750\n002594\n600036\n",
    "data/processed/temp/STALE_prices.csv": "date,close\n20230101,14.5\n20230102,14.8\n",
    "notebooks/experiments/ma_crossover_draft.py": "# DRAFT - do not use\nimport pandas\n# TODO: fix column names\n",
    "config/backtests/strategy_v1.yaml": "strategy: momentum\nlookback: 20\nrebalance: monthly\n",
    "logs/pipeline/run_20240315.log": "[INFO] Pipeline started\n[ERROR] Connection timeout after 30s\n[INFO] Retry 1/3\n[ERROR] Data fetch failed\n",
    "scripts/deprecated/old_fetcher.py": "# DEPRECATED: uses tushare which is no longer supported\nimport tushare as ts\npro = ts.pro_api('INVALID_TOKEN')\n",
    "docs/internal/data_dictionary.md": "# Data Dictionary\n- qfq: 前复权 (forward adjusted)\n- hfq: 后复权 (backward adjusted)\n- adj: no adjustment\n",
    "data/raw/equity/sector_map.json": json.dumps({"000001": "banking", "600519": "liquor", "300750": "new_energy"}),
    "config/backtests/universe.json": json.dumps({"universe": ["000001", "600519", "300750"], "benchmark": "000300"}),
}
for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# ─────────────────────────────────────────────
# 2. Build mock akshare package
# ─────────────────────────────────────────────
mock_pkg_dir = WORKSPACE / "mock_akshare_pkg"
mock_pkg_dir.mkdir(exist_ok=True)

# Generate deterministic K-line data for 3 stocks
STOCKS = {
    "000001": {"name": "平安银行", "base_price": 10.0, "exchange": "sz"},
    "600519": {"name": "贵州茅台", "base_price": 1700.0, "exchange": "sh"},
    "300750": {"name": "宁德时代", "base_price": 150.0, "exchange": "sz"},
}

def generate_kline(symbol, base_price, n=120):
    """Generate deterministic daily OHLCV data."""
    rng = np.random.RandomState(int(symbol))
    dates = pd.date_range("20240101", periods=n, freq="B")
    prices = [base_price]
    for _ in range(n - 1):
        prices.append(prices[-1] * (1 + rng.normal(0, 0.015)))
    prices = np.array(prices)
    df = pd.DataFrame({
        "日期": dates.strftime("%Y-%m-%d"),
        "开盘": np.round(prices * (1 + rng.uniform(-0.005, 0.005, n)), 2),
        "收盘": np.round(prices, 2),
        "最高": np.round(prices * (1 + rng.uniform(0.001, 0.02, n)), 2),
        "最低": np.round(prices * (1 - rng.uniform(0.001, 0.02, n)), 2),
        "成交量": np.random.RandomState(int(symbol)+1).randint(1000000, 50000000, n),
        "成交额": np.round(prices * np.random.RandomState(int(symbol)+2).randint(1000000, 50000000, n), 2),
        "振幅": np.round(rng.uniform(0.5, 3.0, n), 2),
        "涨跌幅": np.round(rng.normal(0, 1.5, n), 2),
        "涨跌额": np.round(rng.normal(0, 0.3, n), 2),
        "换手率": np.round(rng.uniform(0.1, 3.0, n), 2),
    })
    return df

KLINE_DATA = {}
for sym, info in STOCKS.items():
    df = generate_kline(sym, info["base_price"])
    KLINE_DATA[sym] = df.to_dict(orient="records")

# Generate financial abstract data (quarterly)
FINANCIAL_DATA = {}
for sym, info in STOCKS.items():
    rng = np.random.RandomState(int(sym) + 100)
    quarters = ["2024-03-31", "2023-12-31", "2023-09-30", "2023-06-30"]
    rows = []
    base_revenue = rng.uniform(1e9, 1e11)
    for q in quarters:
        rows.append({
            "报告期": q,
            "净利润": round(base_revenue * rng.uniform(0.08, 0.25), 2),
            "净利润同比增长率": round(rng.uniform(-10, 30), 2),
            "扣非净利润": round(base_revenue * rng.uniform(0.07, 0.22), 2),
            "营业总收入": round(base_revenue, 2),
            "营业总收入同比增长率": round(rng.uniform(-5, 25), 2),
            "基本每股收益": round(rng.uniform(0.1, 3.0), 4),
            "每股净资产": round(rng.uniform(3.0, 20.0), 4),
            "净资产收益率": round(rng.uniform(5.0, 25.0), 2),
            "毛利率": round(rng.uniform(20.0, 70.0), 2),
        })
    FINANCIAL_DATA[sym] = rows

# Serialize data to be embedded in mock module
kline_json = json.dumps(KLINE_DATA)
financial_json = json.dumps(FINANCIAL_DATA)

mock_module_code = f'''
import pandas as pd
import json

_KLINE_DATA = json.loads({repr(kline_json)})
_FINANCIAL_DATA = json.loads({repr(financial_json)})

def stock_zh_a_hist(symbol="000001", period="daily", start_date="20240101", end_date="20241231", adjust=""):
    """
    获取A股历史行情数据。
    
    Parameters
    ----------
    symbol : str  股票代码
    period : str  "daily" | "weekly" | "monthly"
    start_date : str  开始日期 YYYYMMDD
    end_date : str    结束日期 YYYYMMDD
    adjust : str  "" | "qfq" | "hfq"
    """
    if adjust != "qfq":
        raise ValueError(
            f"[mock-akshare] stock_zh_a_hist: adjust={{repr(adjust)}} is not supported in this environment. "
            f"Only adjust='qfq' (前复权) is available. Check the SKILL.md for correct parameter usage."
        )
    if symbol not in _KLINE_DATA:
        raise ValueError(f"[mock-akshare] Unknown symbol: {{symbol}}. Supported: {{list(_KLINE_DATA.keys())}}")
    if period != "daily":
        raise ValueError(f"[mock-akshare] period={{repr(period)}} not cached. Use 'daily'.")
    
    df = pd.DataFrame(_KLINE_DATA[symbol])
    # Filter by date range
    df["日期"] = pd.to_datetime(df["日期"])
    start = pd.to_datetime(start_date, format="%Y%m%d")
    end = pd.to_datetime(end_date, format="%Y%m%d")
    df = df[(df["日期"] >= start) & (df["日期"] <= end)].reset_index(drop=True)
    df["日期"] = df["日期"].dt.strftime("%Y-%m-%d")
    return df


def stock_financial_abstract_ths(symbol="000001", indicator="按报告期"):
    """
    获取同花顺财务摘要数据。
    
    Parameters
    ----------
    symbol : str  股票代码
    indicator : str  必须为 "按报告期"
    """
    VALID_INDICATORS = ["按报告期", "按年度", "按单季度"]
    if indicator not in VALID_INDICATORS:
        raise ValueError(
            f"[mock-akshare] stock_financial_abstract_ths: indicator={{repr(indicator)}} is invalid. "
            f"Must be one of {{VALID_INDICATORS}}."
        )
    if indicator != "按报告期":
        raise ValueError(
            f"[mock-akshare] indicator={{repr(indicator)}} has no data in mock. Use '按报告期'."
        )
    if symbol not in _FINANCIAL_DATA:
        raise ValueError(f"[mock-akshare] Unknown symbol: {{symbol}}.")
    return pd.DataFrame(_FINANCIAL_DATA[symbol])


def stock_board_industry_name_em():
    data = [
        {{"板块名称": "银行", "涨跌幅": 0.52, "总市值": 9.8e13}},
        {{"板块名称": "白酒", "涨跌幅": -0.31, "总市值": 4.2e13}},
        {{"板块名称": "新能源汽车", "涨跌幅": 1.24, "总市值": 3.1e13}},
    ]
    return pd.DataFrame(data)


def stock_zh_a_spot_em(symbol=None):
    rows = []
    for sym, info in {{"000001": ("平安银行", 10.5), "600519": ("贵州茅台", 1720.0), "300750": ("宁德时代", 155.0)}}.items():
        rows.append({{"代码": sym, "名称": info[0], "最新价": info[1]}})
    return pd.DataFrame(rows)
'''

(mock_pkg_dir / "akshare.py").write_text(mock_module_code)
(mock_pkg_dir / "setup.py").write_text(
    "from setuptools import setup\n"
    "setup(name='akshare', version='1.0.0', py_modules=['akshare'])\n"
)

# ─────────────────────────────────────────────
# 3. Create task brief for the agent
# ─────────────────────────────────────────────
task_brief = """# Quantitative Stock Screening Task

## Context
Our investment research team needs a Python script that automates preliminary stock screening
for three A-share securities: 000001 (平安银行), 600519 (贵州茅台), and 300750 (宁德时代).

## Requirements

Write a Python script named `run_screening.py` that does ALL of the following:

1. **Historical Price Analysis (date range: 2024-01-01 to 2024-06-30)**
   - Retrieve daily historical K-line data for each of the three stocks.
   - Use FRONT-ADJUSTED prices (前复权) to ensure price continuity across dividend events.
   - Compute the 20-day simple moving average (MA20) of closing prices for each stock.
   - Identify the LAST trading date in the retrieved data and record:
     - The closing price on that date
     - The MA20 value on that date
     - Whether the closing price is ABOVE or BELOW MA20 (record as "above" or "below")

2. **Quarterly Financial Fundamentals**
   - Retrieve the most recent quarterly financial abstract for each stock (use "by report period" mode).
   - From the most recent quarter's data, extract:
     - 净利润 (net profit)
     - 净资产收益率 (ROE)
     - 毛利率 (gross margin)

3. **Output**
   - When executed, the script must write a file called `screening_result.json` to the SAME directory
     as the script itself.
   - The JSON must contain a top-level key `"stocks"` mapping to a list of objects, one per stock,
     each with these exact keys:
       - `"symbol"` (string)
       - `"last_date"` (string, format YYYY-MM-DD)
       - `"last_close"` (float)
       - `"ma20"` (float, rounded to 2 decimal places)
       - `"price_vs_ma20"` (string: "above" or "below")
       - `"net_profit"` (float)
       - `"roe"` (float)
       - `"gross_margin"` (float)

## Notes
- The akshare library is available. See /workspace/SKILL.md for API reference.
- Do not hardcode any price or financial figures; all values must come from the library calls.
- The script must be runnable with: `python run_screening.py`
"""

(WORKSPACE / "task_brief.md").write_text(task_brief)

# Copy SKILL.md reference note
(WORKSPACE / "SKILL.md").write_text(open("/workspace/SKILL.md").read() if Path("/workspace/SKILL.md").exists() else """
---
name: akshare-stock
description: A股量化数据分析工具，基于AkShare库获取A股行情、财务数据、板块信息等。
---

# A股量化 - AkShare 数据接口

## 历史K线数据

```python
import akshare as ak
stock_zh_a_hist(symbol="000001", period="daily", start_date="20240101", end_date="20241231", adjust="qfq")
```

## 财务数据

```python
import akshare as ak
stock_financial_abstract_ths(symbol="000001", indicator="按报告期")
```
""")

print("Workspace setup complete.")
print(f"Mock akshare package at: {mock_pkg_dir}")
print(f"Task brief at: {WORKSPACE / 'task_brief.md'}")