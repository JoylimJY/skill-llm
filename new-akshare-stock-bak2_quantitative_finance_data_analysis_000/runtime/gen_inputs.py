import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)
workspace = Path("/workspace")

# ── directory structure ──────────────────────────────────────────────────────
dirs = [
    "data/raw", "data/processed", "data/cache",
    "reports/2023", "reports/2024",
    "scripts/deprecated", "scripts/utils",
    "config", "logs", "tmp/scratch",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ─────────────────────────────────────────────────────────

# 1. Old analysis script (wrong API style, wrong parameters)
(workspace / "scripts/deprecated/old_analysis.py").write_text(textwrap.dedent("""\
    # DEPRECATED - uses tushare, do not use
    import tushare as ts
    pro = ts.pro_api('FAKE_TOKEN')
    df = pro.daily(ts_code='600519.SH', start_date='20240101', end_date='20240331')
    df.to_csv('../data/raw/moutai_old.csv')
"""))

# 2. Distractor config
(workspace / "config/db_config.json").write_text(json.dumps({
    "host": "localhost", "port": 5432,
    "database": "quantdb", "user": "analyst",
    "comment": "PostgreSQL for storing processed data"
}, indent=2))

# 3. Stale CSV that looks like stock data but has wrong columns
import random, csv
stale_rows = [["date","ticker","price","vol"]]
for i in range(30):
    stale_rows.append([f"2023-{(i%12)+1:02d}-01","600519", round(1700+random.uniform(-50,50),2), random.randint(100000,999999)])
with open(workspace / "data/raw/moutai_stale.csv","w",newline="") as f:
    csv.writer(f).writerows(stale_rows)

# 4. Fake financial summary with wrong schema
(workspace / "data/processed/financial_summary_2023.json").write_text(json.dumps({
    "symbol": "600519",
    "note": "manually curated - columns differ from API output",
    "roe": "28.5%", "net_margin": "51.2%",
    "revenue_growth": "18.1%"
}, indent=2))

# 5. Requirements file that lists wrong packages
(workspace / "config/requirements_old.txt").write_text("tushare==1.2.89\npandas==1.3.0\nnumpy==1.21.0\n")

# 6. Deprecated utility helper
(workspace / "scripts/utils/tushare_helper.py").write_text(textwrap.dedent("""\
    \"\"\"Deprecated helper - use akshare instead\"\"\"
    def get_history(code, start, end):
        raise NotImplementedError('tushare helper is deprecated')
"""))

# 7. Old report with placeholder values
(workspace / "reports/2023/q4_report.txt").write_text(
    "Q4 2023 Report\n"
    "Sector: Baijiu\n"
    "Top stock: 贵州茅台\n"
    "WARNING: Data sourced manually, not verified.\n"
)

# 8. Log file with noise
with open(workspace / "logs/fetch_errors.log","w") as f:
    for i in range(20):
        f.write(f"2024-01-{(i%28)+1:02d} ERROR: ConnectionTimeout fetching 60051{i%9}\n")

# 9. Partial script that uses wrong function names
(workspace / "scripts/utils/wrong_api_calls.py").write_text(textwrap.dedent("""\
    import akshare as ak
    # BUG: wrong function names - do not use
    # df = ak.get_stock_history('600519')          # does not exist
    # df = ak.stock_history(code='600519')          # does not exist
    # df = ak.stock_zh_a_hist('600519', adj='qfq')  # wrong param name
    pass
"""))

# 10. A fake sector mapping file
(workspace / "data/raw/sector_map.json").write_text(json.dumps({
    "白酒": ["600519","000858","002304","600809","603369"],
    "半导体": ["688981","002049","603986","002371","688012"],
    "note": "This file is stale - use live API instead"
}, indent=2))

# 11. A competitor analysis stub
(workspace / "reports/2024/competitor_stub.csv").write_text(
    "symbol,name,sector\n600519,贵州茅台,白酒\n000858,五粮液,白酒\n002304,洋河股份,白酒\n"
)

# 12. tmp scratch
(workspace / "tmp/scratch/test_fetch.py").write_text(textwrap.dedent("""\
    # scratch file - never finished
    import akshare as ak
    # TODO: figure out the right period and adjust params
    df = ak.stock_zh_a_hist(symbol='600519')
    print(df.head())
"""))

# ── mock akshare package ──────────────────────────────────────────────────────
mock_pkg_dir = workspace / "mock_packages" / "akshare"
mock_pkg_dir.mkdir(parents=True, exist_ok=True)

# We use a fixed random seed so all values are deterministic
import numpy as np

np.random.seed(7)

# Generate 60 trading days of daily OHLCV data for 600519 (qfq-adjusted)
import pandas as pd

dates = pd.bdate_range("2024-01-02","2024-03-29")[:60]
close_base = 1700.0
closes = [close_base]
for _ in range(59):
    closes.append(round(closes[-1] * (1 + np.random.normal(0, 0.012)), 2))

opens  = [round(c * (1 + np.random.normal(0, 0.005)), 2) for c in closes]
highs  = [round(max(o, c) * (1 + abs(np.random.normal(0, 0.007))), 2) for o, c in zip(opens, closes)]
lows   = [round(min(o, c) * (1 - abs(np.random.normal(0, 0.007))), 2) for o, c in zip(opens, closes)]
volumes = [int(np.random.randint(50000, 200000)) for _ in range(60)]
amounts = [round(v * c / 1000, 2) for v, c in zip(volumes, closes)]

hist_df = pd.DataFrame({
    "日期":    [d.strftime("%Y-%m-%d") for d in dates],
    "开盘":    opens,
    "收盘":    closes,
    "最高":    highs,
    "最低":    lows,
    "成交量":  volumes,
    "成交额":  amounts,
    "振幅":    [round((h-l)/l*100, 2) for h,l in zip(highs,lows)],
    "涨跌幅":  [round((closes[i]-closes[i-1])/closes[i-1]*100, 2) if i>0 else 0.0 for i in range(60)],
    "涨跌额":  [round(closes[i]-closes[i-1], 2) if i>0 else 0.0 for i in range(60)],
    "换手率":  [round(np.random.uniform(0.5, 3.0), 2) for _ in range(60)],
})

# Also generate data for unadjusted (no adjust) - slightly different closes
closes_raw = [round(c * 1.05, 2) for c in closes]  # fake raw price is 5% higher
hist_df_raw = hist_df.copy()
hist_df_raw["收盘"] = closes_raw

# Financial indicator data for 600519
fin_df = pd.DataFrame({
    "日期":      ["2024-03-31","2023-12-31","2023-09-30","2023-06-30"],
    "净利润":    [27.5, 74.7, 51.2, 35.9],
    "净利率":    [54.8, 53.1, 52.7, 52.4],
    "净资产收益率": [10.2, 37.9, 26.1, 17.5],
    "每股收益":  [21.9, 59.49, 40.8, 28.6],
    "总资产":    [2760.1, 2701.5, 2580.3, 2503.2],
    "营业收入":  [50.2, 140.6, 97.2, 68.4],
})

# Industry constituents for 白酒 sector
baijiu_cons_df = pd.DataFrame({
    "代码": ["600519","000858","002304","600809","603369","600779","000596","002216"],
    "名称": ["贵州茅台","五粮液","洋河股份","山西汾酒","今世缘","水井坊","古井贡酒","三元股份"],
    "最新价": [1712.5, 124.3, 92.7, 198.4, 38.6, 47.2, 155.8, 5.3],
    "涨跌幅": [0.55, -0.32, 1.12, -0.87, 0.44, 1.05, -0.21, 0.76],
    "换手率": [0.72, 0.88, 1.43, 0.95, 1.27, 2.1, 1.08, 1.89],
    "市盈率": [28.5, 20.1, 18.7, 35.2, 16.4, 22.8, 24.1, 45.7],
})

# save as pickle for the mock to load (ensures exact dtypes)
hist_df.to_pickle(workspace / "data/cache/hist_qfq_600519.pkl")
hist_df_raw.to_pickle(workspace / "data/cache/hist_raw_600519.pkl")
fin_df.to_pickle(workspace / "data/cache/fin_indicator_600519.pkl")
baijiu_cons_df.to_pickle(workspace / "data/cache/baijiu_cons.pkl")

# Save reference values so eval script can verify
ma20_last = round(float(pd.Series(closes[-20:]).mean()), 4)
latest_close = closes[-1]
latest_net_margin = float(fin_df["净利率"].iloc[0])
sector_count = len(baijiu_cons_df)
median_pe = float(baijiu_cons_df["市盈率"].median())

reference = {
    "ma20_last": ma20_last,
    "latest_close": latest_close,
    "latest_net_margin": latest_net_margin,
    "sector_stock_count": sector_count,
    "sector_median_pe": median_pe,
    "closes": closes,
}
(workspace / "data/cache/reference_values.json").write_text(json.dumps(reference, indent=2))

# ── write the mock akshare __init__.py ────────────────────────────────────────
mock_init = textwrap.dedent(f"""\
    \"\"\"Mock AkShare package for sandbox testing.\"\"\"
    import pandas as pd
    import os

    _CACHE = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'cache')

    def stock_zh_a_hist(symbol, period="daily", start_date=None, end_date=None, adjust=""):
        if symbol != "600519":
            return pd.DataFrame()
        if period != "daily":
            return pd.DataFrame()
        if adjust == "qfq":
            df = pd.read_pickle(os.path.join(_CACHE, "hist_qfq_600519.pkl"))
        else:
            df = pd.read_pickle(os.path.join(_CACHE, "hist_raw_600519.pkl"))
        # filter by date range if provided
        if start_date or end_date:
            df = df.copy()
            df["日期"] = pd.to_datetime(df["日期"])
            if start_date:
                df = df[df["日期"] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df["日期"] <= pd.to_datetime(end_date)]
            df["日期"] = df["日期"].dt.strftime("%Y-%m-%d")
            df = df.reset_index(drop=True)
        return df

    def stock_financial_analysis_indicator(symbol):
        if symbol != "600519":
            return pd.DataFrame()
        return pd.read_pickle(os.path.join(_CACHE, "fin_indicator_600519.pkl"))

    def stock_board_industry_cons_em(symbol):
        if symbol in ("白酒", "白酒行业", "baijiu"):
            return pd.read_pickle(os.path.join(_CACHE, "baijiu_cons.pkl"))
        return pd.DataFrame()

    # stub out other functions so import doesn't fail
    def stock_zh_a_spot_em(*args, **kwargs):
        return pd.DataFrame()

    def stock_board_industry_name_em(*args, **kwargs):
        return pd.DataFrame()

    def stock_board_concept_name_em(*args, **kwargs):
        return pd.DataFrame()

    def stock_individual_fund_flow(*args, **kwargs):
        return pd.DataFrame()

    def stock_lhb_detail_em(*args, **kwargs):
        return pd.DataFrame()

    def stock_new_ipo_em(*args, **kwargs):
        return pd.DataFrame()

    def stock_margin_sse(*args, **kwargs):
        return pd.DataFrame()

    def stock_financial_abstract_ths(*args, **kwargs):
        return pd.DataFrame()
""")

(mock_pkg_dir / "__init__.py").write_text(mock_init)

# write a setup.py so pip install -e works
(workspace / "mock_packages" / "setup.py").write_text(textwrap.dedent("""\
    from setuptools import setup, find_packages
    setup(name='akshare', version='1.99.99', packages=find_packages())
"""))

print("Workspace initialized successfully.")
print(f"Reference MA20(last): {ma20_last}")
print(f"Reference latest close: {latest_close}")
print(f"Reference latest net margin: {latest_net_margin}")
print(f"Reference sector count: {sector_count}")