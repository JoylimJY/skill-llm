#!/usr/bin/env python3
"""
Generate a realistic, messy sandbox workspace for the A-share stock analysis task.
"""
import os
import random
import json
import csv
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Create deep distractor directory structure ---
dirs = [
    "project/legacy_code",
    "project/legacy_code/v1",
    "project/legacy_code/v2",
    "project/reports/drafts",
    "project/reports/final",
    "project/data/raw",
    "project/data/processed",
    "project/notebooks",
    "project/config",
    "tools/scrapers",
    "tools/cleaners",
    "archive/2023",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "project/legacy_code/v1/fetch_data.py": """\
# Old baostock-based fetcher (deprecated)
import baostock as bs

def get_hist(code):
    lg = bs.login()
    rs = bs.query_history_k_data_plus(code, 'date,close', start_date='20230101')
    data = []
    while rs.next():
        data.append(rs.get_row_data())
    bs.logout()
    return data
""",
    "project/legacy_code/v2/fetch_v2.py": """\
# Attempt to use tushare - abandoned
import tushare as ts

def get_stock(code):
    pro = ts.pro_api('INVALID_TOKEN')
    df = pro.daily(ts_code=code)
    return df
""",
    "project/legacy_code/v2/utils.py": """\
def clean_price(x):
    try:
        return float(str(x).replace(',',''))
    except:
        return None
""",
    "project/reports/drafts/sector_note.txt": """\
NOTE: Need to analyze semiconductor sector stocks.
Pending: get forward-adjusted daily prices for top holdings.
Pending: pull financial summary per reporting period.
Pending: cross-reference with board constituents.
Status: BLOCKED - no working data pipeline yet.
""",
    "project/reports/drafts/template.json": json.dumps({
        "report_date": "TBD",
        "sector": "半导体",
        "stocks": [],
        "note": "template only - not final"
    }, ensure_ascii=False, indent=2),
    "project/reports/final/.gitkeep": "",
    "project/data/raw/manual_tickers.csv": """\
symbol,name,note
300750,宁德时代,manually verified
688981,中芯国际,manually verified
002371,北方华创,manually verified
""",
    "project/data/processed/README_BROKEN.txt": """\
This folder should contain processed price data.
Processing script is missing / broken.
""",
    "project/notebooks/analysis_draft.ipynb": json.dumps({
        "nbformat": 4,
        "nbformat_minor": 5,
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# Draft analysis\n", "TODO: fill in with real data"]},
            {"cell_type": "code", "metadata": {}, "source": ["# placeholder\nimport pandas as pd\n"], "outputs": [], "execution_count": None}
        ],
        "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}
    }, indent=2),
    "project/config/settings.yaml": """\
data_source: akshare
sector: 半导体
date_range:
  start: "20240101"
  end: "20241231"
adjust_mode: ??  # TODO: figure out correct value
financial_indicator: ??  # TODO: figure out correct value
output_dir: project/reports/final
""",
    "tools/scrapers/old_scraper.py": """\
# Abandoned web scraper
import requests
from bs4 import BeautifulSoup

def scrape_board():
    # This no longer works
    url = 'http://old.finance.example.com/board'
    resp = requests.get(url, timeout=5)
    soup = BeautifulSoup(resp.text, 'html.parser')
    return soup.find_all('tr')
""",
    "tools/cleaners/normalize.py": """\
def normalize_symbol(s):
    return str(s).zfill(6)
""",
    "archive/2023/old_report.json": json.dumps({
        "year": 2023,
        "sector": "半导体",
        "stocks_analyzed": 5,
        "note": "outdated - use new pipeline"
    }, ensure_ascii=False, indent=2),
    "project/config/stock_list_old.txt": """\
# Old static list - do not use
000001 平安银行
600519 贵州茅台
300750 宁德时代
""",
}

for rel_path, content in distractor_files.items():
    fp = WORKSPACE / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content, encoding="utf-8")

# --- Create mock AkShare data files ---
# These simulate what AkShare functions would return for the semiconductor sector

mock_data_dir = WORKSPACE / "mock_akshare_data"
mock_data_dir.mkdir(exist_ok=True)

# 1. Board constituents for 半导体 (semiconductor)
board_cons_rows = [
    ["代码", "名称", "最新价", "涨跌幅", "涨跌额", "成交量", "成交额", "振幅", "最高", "最低", "今开", "昨收"],
    ["300750", "宁德时代", "148.50", "1.23", "1.80", "1234567", "18345678901", "2.1", "149.80", "146.20", "147.00", "146.70"],
    ["688981", "中芯国际", "58.30", "-0.51", "-0.30", "987654", "5756789012", "1.8", "58.90", "57.80", "58.60", "58.60"],
    ["002371", "北方华创", "289.00", "2.11", "5.97", "345678", "9987654321", "3.2", "291.50", "282.00", "284.00", "283.03"],
    ["603501", "韦尔股份", "95.40", "0.85", "0.80", "456789", "4356789012", "2.0", "96.20", "94.10", "94.50", "94.60"],
    ["002049", "紫光国微", "62.10", "-1.27", "-0.80", "234567", "1456789012", "2.5", "63.20", "61.50", "62.80", "62.90"],
]

with open(mock_data_dir / "board_cons_semiconductor.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(board_cons_rows)

# 2. Historical K-line data for each stock (daily, qfq adjusted, 2024)
import datetime

stocks = [
    ("300750", 148.50),
    ("688981", 58.30),
    ("002371", 289.00),
    ("603501", 95.40),
    ("002049", 62.10),
]

hist_cols = ["日期", "开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]

for sym, base_price in stocks:
    rows = [hist_cols]
    price = base_price
    d = datetime.date(2024, 1, 2)
    end = datetime.date(2024, 12, 31)
    rng = random.Random(int(sym) + 42)
    while d <= end:
        if d.weekday() < 5:  # weekdays only
            chg_pct = rng.uniform(-0.05, 0.05)
            open_p = round(price * (1 + rng.uniform(-0.01, 0.01)), 2)
            close_p = round(price * (1 + chg_pct), 2)
            high_p = round(max(open_p, close_p) * (1 + rng.uniform(0, 0.01)), 2)
            low_p = round(min(open_p, close_p) * (1 - rng.uniform(0, 0.01)), 2)
            volume = rng.randint(100000, 5000000)
            amount = round(volume * close_p, 2)
            amplitude = round((high_p - low_p) / price * 100, 2)
            chg_amount = round(close_p - price, 2)
            chg_rate = round(chg_pct * 100, 2)
            turnover = round(rng.uniform(0.1, 3.0), 2)
            rows.append([
                d.strftime("%Y-%m-%d"),
                open_p, close_p, high_p, low_p,
                volume, amount, amplitude, chg_rate, chg_amount, turnover
            ])
            price = close_p
        d += datetime.timedelta(days=1)

    with open(mock_data_dir / f"hist_daily_qfq_{sym}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# 3. Financial abstract data for each stock (按报告期)
fin_cols = [
    "报告期", "净利润", "净利润同比增长率", "扣非净利润", "营业总收入",
    "营业总收入同比增长率", "基本每股收益", "每股净资产", "净资产收益率",
    "销售毛利率", "资产负债率", "每股经营现金流量"
]

fin_periods = ["2024-09-30", "2024-06-30", "2024-03-31", "2023-12-31", "2023-09-30", "2023-06-30"]

for sym, base_price in stocks:
    rows = [fin_cols]
    rng = random.Random(int(sym) + 99)
    for period in fin_periods:
        net_profit = round(rng.uniform(1e8, 1e10), 2)
        rows.append([
            period,
            net_profit,
            round(rng.uniform(-20, 50), 2),
            round(net_profit * rng.uniform(0.85, 0.99), 2),
            round(rng.uniform(5e9, 5e10), 2),
            round(rng.uniform(-10, 40), 2),
            round(rng.uniform(0.5, 5.0), 2),
            round(rng.uniform(10, 80), 2),
            round(rng.uniform(5, 25), 2),
            round(rng.uniform(20, 60), 2),
            round(rng.uniform(30, 70), 2),
            round(rng.uniform(1, 8), 2),
        ])
    with open(mock_data_dir / f"financial_abstract_{sym}.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

# 4. A mock akshare module that serves the above data
# This will be placed so that `import akshare as ak` uses it IF the agent uses it
# We place a fake akshare.py in mock_akshare_data for reference by the setup script

mock_ak_code = '''\
"""
Mock AkShare module - serves pre-seeded data from /workspace/mock_akshare_data/
This is a test harness. The function signatures match the real AkShare API.
"""
import pandas as pd
from pathlib import Path

_DATA_DIR = Path("/workspace/mock_akshare_data")


def stock_board_industry_cons_em(symbol: str) -> pd.DataFrame:
    """Returns constituent stocks for an industry board."""
    if "半导体" in symbol:
        df = pd.read_csv(_DATA_DIR / "board_cons_semiconductor.csv")
        return df
    raise ValueError(f"No mock data for symbol: {symbol}")


def stock_zh_a_hist(
    symbol: str,
    period: str = "daily",
    start_date: str = "20240101",
    end_date: str = "20241231",
    adjust: str = ""
) -> pd.DataFrame:
    """Returns historical K-line data for a stock."""
    fname = _DATA_DIR / f"hist_{period}_{adjust}_{symbol}.csv"
    if not fname.exists():
        raise FileNotFoundError(
            f"Mock data not found: {fname}. "
            f"Check period='{period}' and adjust='{adjust}' are correct per AkShare docs."
        )
    df = pd.read_csv(fname)
    df = df[(df["日期"] >= start_date.replace("-","")[:4]+"-"+start_date.replace("-","")[4:6]+"-"+start_date.replace("-","")[6:]) &
            (df["日期"] <= end_date.replace("-","")[:4]+"-"+end_date.replace("-","")[4:6]+"-"+end_date.replace("-","")[6:])]
    return df.reset_index(drop=True)


def stock_financial_abstract_ths(symbol: str, indicator: str = "按报告期") -> pd.DataFrame:
    """Returns financial abstract data from THS."""
    if indicator != "按报告期":
        raise ValueError(
            f"Invalid indicator='{indicator}'. "
            f"For period-by-period financials, must use indicator=\'按报告期\'"
        )
    fname = _DATA_DIR / f"financial_abstract_{symbol}.csv"
    if not fname.exists():
        raise FileNotFoundError(f"No mock financial data for {symbol}")
    return pd.read_csv(fname)


def stock_board_industry_name_em() -> pd.DataFrame:
    """Returns industry board list."""
    return pd.DataFrame({
        "板块名称": ["半导体", "新能源", "医药生物", "银行", "军工"],
        "板块代码": ["BK0447", "BK0595", "BK0465", "BK0475", "BK0476"],
        "最新价": [1234.5, 987.6, 876.5, 654.3, 543.2],
        "涨跌幅": [1.23, -0.45, 0.67, -0.12, 0.89],
    })
'''

(WORKSPACE / "mock_akshare_data" / "mock_akshare_module.py").write_text(mock_ak_code, encoding="utf-8")

print("Workspace generated successfully.")
print(f"Files created in {WORKSPACE}:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")