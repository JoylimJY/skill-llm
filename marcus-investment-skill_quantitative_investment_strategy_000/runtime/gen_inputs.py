import os
import json
import random
import sqlite3
import struct
from pathlib import Path

random.seed(42)

BASE = Path("/root/.openclaw/workspace/skills/marcus-investment-analyst")
SCRIPTS = BASE / "scripts"
REFS = BASE / "references"
ASSETS = BASE / "assets"
MEMORY = Path("/root/.openclaw/workspace/memory/stock-analysis")
DATA = Path("/root/data")
WORKSPACE = Path("/workspace")

# ─── Distractor files ──────────────────────────────────────────────────────────
distractor_dir = WORKSPACE / "analysis_drafts" / "2025Q4"
distractor_dir.mkdir(parents=True, exist_ok=True)

(distractor_dir / "rough_notes.txt").write_text(
    "TODO: check 600256 performance\nRSI threshold discussion: some say 30, others 20?\nMeeting at 3pm\n"
)
(distractor_dir / "old_strategy_v3.yaml").write_text(
    "rsi_oversold: 30\nrsi_overbought: 70\nmacd_fast: 10\nmacd_slow: 30\npivot_band: 0.05\ntrailing_stop: 0.10\n"
)
(distractor_dir / "competitor_params.json").write_text(
    json.dumps({"rsi_buy": 25, "rsi_sell": 75, "pivot_pct": 0.06, "trailing": 0.12})
)
(distractor_dir / "watchlist_draft.csv").write_text(
    "code,name,note\n600256,广汇能源,high volatility\n300760,迈瑞医疗,medical device\n002594,比亚迪,EV\n"
)

report_dir = WORKSPACE / "reports" / "historical"
report_dir.mkdir(parents=True, exist_ok=True)
(report_dir / "2024_annual_summary.txt").write_text(
    "Annual returns varied. Core positions outperformed benchmark by ~12%.\n"
    "Trailing stop triggered 3 times on satellite positions.\n"
)
(report_dir / "risk_metrics_q3_2025.json").write_text(
    json.dumps({"sharpe": 0.48, "max_drawdown": -0.18, "win_rate": 0.68})
)
(report_dir / "README_OLD.md").write_text(
    "This is outdated. Do not use for current strategy decisions.\n"
)

misc_dir = WORKSPACE / "misc"
misc_dir.mkdir(parents=True, exist_ok=True)
(misc_dir / "cron_backup.sh").write_text("#!/bin/bash\ncp /root/data/*.db /backup/\n")
(misc_dir / "env_check.py").write_text(
    "import sys\nprint(f'Python {sys.version}')\n"
)
(misc_dir / "dead_code_test.py").write_text(
    "# This file is no longer used\n# Old RSI period was 14\n# pivot_band was 0.05\n"
)
(misc_dir / "deployment_log.txt").write_text(
    "2026-01-10 v5.9 deployed\n2026-02-14 v6.0 hotfix\n2026-03-12 v6.0 stable\n"
)

# ─── market_snapshot.json: raw data for 3 stocks ─────────────────────────────
# Stock A: 兆易创新 603986 (core, satellite-eligible signal)
# Stock B: 四方精创 300468 (satellite)
# Stock C: 广汇能源 600256 (AVOID - must NOT appear in recommendations)
#
# We craft data so that:
#   603986: BUY signal (price in pivot, MACD golden cross, RSI6 = 18 < 20)
#   300468: HOLD (price in pivot, no golden cross yet, RSI6 = 35)
#   600256: would be BUY by raw math but must be excluded (avoid list)

snapshot = {
    "snapshot_date": "2026-03-15",
    "stocks": [
        {
            "code": "603986",
            "name": "兆易创新",
            "industry": "存储芯片",
            "close_price": 118.50,
            "ma60": 114.20,
            "pivot_lower": round(114.20 * 0.92, 4),   # 105.064
            "pivot_upper": round(114.20 * 1.08, 4),   # 123.336
            "macd_dif": 0.85,
            "macd_dea": 0.72,
            "macd_hist": 0.13,
            "rsi6": 18.3,
            "prev_macd_dif": 0.61,
            "prev_macd_dea": 0.68,
            "note": "DIF just crossed above DEA"
        },
        {
            "code": "300468",
            "name": "四方精创",
            "industry": "软件",
            "close_price": 22.10,
            "ma60": 21.30,
            "pivot_lower": round(21.30 * 0.92, 4),   # 19.596
            "pivot_upper": round(21.30 * 1.08, 4),   # 23.004
            "macd_dif": 0.12,
            "macd_dea": 0.18,
            "macd_hist": -0.06,
            "rsi6": 35.2,
            "prev_macd_dif": 0.10,
            "prev_macd_dea": 0.15,
            "note": "No golden cross, RSI not oversold"
        },
        {
            "code": "600256",
            "name": "广汇能源",
            "industry": "能源",
            "close_price": 7.45,
            "ma60": 7.30,
            "pivot_lower": round(7.30 * 0.92, 4),
            "pivot_upper": round(7.30 * 1.08, 4),
            "macd_dif": 0.08,
            "macd_dea": 0.05,
            "macd_hist": 0.03,
            "rsi6": 17.9,
            "prev_macd_dif": 0.03,
            "prev_macd_dea": 0.06,
            "note": "On avoid list - must not be recommended"
        }
    ]
}

(WORKSPACE / "market_snapshot.json").write_text(json.dumps(snapshot, ensure_ascii=False, indent=2))

# ─── The mock scripts ─────────────────────────────────────────────────────────
# marcus_chan_theory.py - produces deterministic clandelion analysis output
chan_theory_script = r'''#!/usr/bin/env python3
"""Marcus Chan Theory Analysis Script v6.0"""
import sys
import json

STOCK_DB = {
    "603986": {
        "name": "兆易创新",
        "ma60": 114.20,
        "pivot_lower": round(114.20 * 0.92, 4),
        "pivot_upper": round(114.20 * 1.08, 4),
        "current_price": 118.50,
        "trend": "上升趋势",
        "zhongshu_level": "三级中枢",
        "beichi": "顶背驰信号待确认",
        "buy_point": "第一类买点已出现",
        "sell_point": "无",
    },
    "301308": {
        "name": "江波龙",
        "ma60": 88.40,
        "pivot_lower": round(88.40 * 0.92, 4),
        "pivot_upper": round(88.40 * 1.08, 4),
        "current_price": 91.20,
        "trend": "震荡趋势",
        "zhongshu_level": "二级中枢",
        "beichi": "底背驰",
        "buy_point": "第二类买点",
        "sell_point": "无",
    },
    "300468": {
        "name": "四方精创",
        "ma60": 21.30,
        "pivot_lower": round(21.30 * 0.92, 4),
        "pivot_upper": round(21.30 * 1.08, 4),
        "current_price": 22.10,
        "trend": "横盘整理",
        "zhongshu_level": "一级中枢",
        "beichi": "无背驰",
        "buy_point": "无",
        "sell_point": "无",
    },
}

def analyze(code):
    info = STOCK_DB.get(code)
    if not info:
        print(f"[ERROR] 未找到股票代码: {code}")
        sys.exit(1)
    print(f"\n{'='*50}")
    print(f"缠论分析报告 - {info['name']} ({code})")
    print(f"{'='*50}")
    print(f"当前价格: {info['current_price']}")
    print(f"60日均线: {info['ma60']}")
    print(f"缠论中枢区间: [{info['pivot_lower']}, {info['pivot_upper']}]")
    print(f"  中枢计算: 60日均线 × 0.92 = {info['pivot_lower']}")
    print(f"            60日均线 × 1.08 = {info['pivot_upper']}")
    print(f"价格在中枢内: {'是' if info['pivot_lower'] <= info['current_price'] <= info['pivot_upper'] else '否'}")
    print(f"趋势判断: {info['trend']}")
    print(f"中枢级别: {info['zhongshu_level']}")
    print(f"背驰情况: {info['beichi']}")
    print(f"买点信号: {info['buy_point']}")
    print(f"卖点信号: {info['sell_point']}")
    print(f"{'='*50}")
    result = {
        "code": code,
        "name": info["name"],
        "ma60": info["ma60"],
        "pivot_lower": info["pivot_lower"],
        "pivot_upper": info["pivot_upper"],
        "current_price": info["current_price"],
        "in_pivot": info["pivot_lower"] <= info["current_price"] <= info["pivot_upper"],
        "trend": info["trend"],
        "zhongshu_level": info["zhongshu_level"],
        "beichi": info["beichi"],
        "buy_point": info["buy_point"],
        "sell_point": info["sell_point"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 marcus_chan_theory.py <股票代码>")
        sys.exit(1)
    analyze(sys.argv[1])
'''

# marcus_ultimate_optimized_strategy.py - main backtest
ultimate_script = r'''#!/usr/bin/env python3
"""Marcus Ultimate Optimized Strategy v6.0 - Backtest Runner"""
import json
import random
random.seed(42)

STOCKS = [
    ("301308", "江波龙", "存储芯片", 0.2850),
    ("603986", "兆易创新", "存储芯片", 0.3120),
    ("002384", "东山精密", "消费电子", 0.1540),
    ("002202", "金风科技", "风电", 0.1890),
    ("300468", "四方精创", "软件", 0.0980),
    ("600096", "云天化", "化工", 0.1230),
    ("600989", "宝丰能源", "化工", 0.1580),
    ("000559", "万向钱潮", "汽配", 0.2210),
    ("601600", "中国铝业", "有色", 0.1760),
]

print("Marcus Ultimate Optimized Strategy v6.0")
print("策略参数: MACD(12,26,9) RSI6 超卖=20 中枢±8% 止损5% 止盈15% 追踪止损8%")
print("="*60)
total = 0
for code, name, industry, ret in STOCKS:
    sharpe = round(ret / 0.12 + random.uniform(-0.1, 0.1), 2)
    win = round(0.70 + random.uniform(-0.05, 0.10), 2)
    print(f"{name}({code}) | 年化:{ret*100:.1f}% | 夏普:{sharpe:.2f} | 胜率:{win*100:.0f}%")
    total += ret

avg = total / len(STOCKS)
print("="*60)
print(f"平均年化收益: {avg*100:.2f}%")
print(f"策略夏普比率: 0.56")
print(f"整体胜率: 75.0%")
'''

# marcus_backtest_chan.py
backtest_chan_script = r'''#!/usr/bin/env python3
"""Marcus Chan Theory Backtest v6.0"""
import sys
import random
random.seed(99)

STOCK_RETURNS = {
    "301308": (0.285, 0.73, 0.58),
    "603986": (0.312, 0.76, 0.61),
    "300468": (0.098, 0.62, 0.44),
    "002384": (0.154, 0.68, 0.52),
}

def backtest(code):
    if code not in STOCK_RETURNS:
        print(f"[WARN] 暂无{code}的缠论回测数据，使用默认参数")
        ret, sharpe, win = 0.18, 0.50, 0.60
    else:
        ret, sharpe, win = STOCK_RETURNS[code]
    print(f"\n缠论回测结果 - {code}")
    print(f"回测区间: 2023-01-01 ~ 2026-03-12")
    print(f"年化收益: {ret*100:.1f}%")
    print(f"夏普比率: {sharpe:.2f}")
    print(f"胜率: {win*100:.0f}%")
    print(f"中枢参数: 60日均线 ± 8%")
    print(f"买入: MACD金叉 + RSI6<20 + 价格在中枢内")
    print(f"卖出: 止盈15% / 止损5% / 追踪止损8% / MACD死叉 / 跌破中枢下沿")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 marcus_backtest_chan.py <股票代码>")
        sys.exit(1)
    backtest(sys.argv[1])
'''

# data_indicator_fetcher.py
fetcher_script = r'''#!/usr/bin/env python3
"""Data Indicator Fetcher v6.0"""
print("正在更新指标数据...")
print("MACD(12,26,9) 数据已更新")
print("RSI6 数据已更新")
print("KDJ(9,3,3) 数据已更新")
print("数据库更新完成: /root/data/astock_indicators.db")
'''

SCRIPTS.mkdir(parents=True, exist_ok=True)
(SCRIPTS / "marcus_chan_theory.py").write_text(chan_theory_script)
(SCRIPTS / "marcus_ultimate_optimized_strategy.py").write_text(ultimate_script)
(SCRIPTS / "marcus_backtest_chan.py").write_text(backtest_chan_script)
(SCRIPTS / "data_indicator_fetcher.py").write_text(fetcher_script)

# ─── references/strategy.md ──────────────────────────────────────────────────
strategy_md = """# Marcus 策略文档 v6.0

## 股票池

### 核心配置 (55-60%)
| 股票 | 代码 | 行业 | 仓位范围 |
|------|------|------|----------|
| 江波龙 | 301308 | 存储芯片 | 25-30% |
| 兆易创新 | 603986 | 存储芯片 | 20-25% |

### 卫星配置 (25-30%)
| 股票 | 代码 | 行业 | 仓位范围 |
|------|------|------|----------|
| 东山精密 | 002384 | 消费电子 | 10-15% |
| 金风科技 | 002202 | 风电 | 10% |
| 四方精创 | 300468 | 软件 | 10% |
| 云天化 | 600096 | 化工 | 8% |
| 宝丰能源 | 600989 | 化工 | 8% |
| 万向钱潮 | 000559 | 汽配 | 5% |
| 中国铝业 | 601600 | 有色 | 5% |

### 回避列表
- 广汇能源 (600256)
- 创新医疗板块

## 买入信号 (全部满足)
1. 价格在缠论中枢内 (60日均线 × 0.92 ~ 60日均线 × 1.08)
2. MACD金叉 (DIF上穿DEA): 前日DIF < 前日DEA, 当日DIF > 当日DEA
3. RSI6 < 20

## 卖出信号 (任一满足)
1. 盈利 ≥ 15%
2. 亏损 ≥ 5%
3. 从持仓最高点回撤 ≥ 8%
4. MACD死叉
5. 价格跌破中枢下沿
"""
(REFS / "strategy.md").write_text(strategy_md)

# references/optimization_report.md
opt_report = """# 优化报告 v6.0

## 关键优化点
- RSI超卖阈值从30调整为20，减少假信号
- 缠论中枢区间从±5%扩大至±8%，适应存储芯片波动
- 追踪止损从10%收紧至8%

## 行业配置建议
- 存储芯片核心仓位55-60%
- 卫星仓位分散至多行业
- 严格回避广汇能源(600256)及创新医疗板块

## 风险控制
- 单笔止损5%
- 止盈15%
- 追踪止损8%（从最高点计算）
"""
(REFS / "optimization_report.md").write_text(opt_report)

# ─── assets/backtest_data.json ────────────────────────────────────────────────
backtest_data = {
    "strategy": "优化版5-存储芯片专用",
    "version": "6.0",
    "backtest_period": "2023-01-01 to 2026-03-12",
    "parameters": {
        "macd": {"fast": 12, "slow": 26, "signal": 9},
        "rsi_period": 6,
        "rsi_oversold": 20,
        "rsi_overbought": 80,
        "pivot_period": 60,
        "pivot_band_pct": 0.08,
        "stop_loss_pct": 0.05,
        "take_profit_pct": 0.15,
        "trailing_stop_pct": 0.08
    },
    "results": {
        "avg_annual_return": 0.2196,
        "sharpe_ratio": 0.56,
        "win_rate": 0.75
    }
}
(ASSETS / "backtest_data.json").write_text(json.dumps(backtest_data, ensure_ascii=False, indent=2))

# ─── memory/stock-analysis JSON ──────────────────────────────────────────────
mem_json = {
    "strategy": "终极优化策略",
    "generated": "2026-03-12T16:29:00",
    "summary": "603986年化31.2%，301308年化28.5%，整体胜率75%",
    "avoid": ["600256", "创新医疗"]
}
(MEMORY / "终极优化策略回测_20260312_1629.json").write_text(
    json.dumps(mem_json, ensure_ascii=False, indent=2)
)

# ─── Fake SQLite DBs (empty stubs) ───────────────────────────────────────────
for db_name in ["astock_history.db", "astock_indicators.db"]:
    conn = sqlite3.connect(str(DATA / db_name))
    conn.execute("CREATE TABLE IF NOT EXISTS meta (key TEXT, value TEXT)")
    conn.execute("INSERT INTO meta VALUES ('version','6.0')")
    conn.commit()
    conn.close()

print("Workspace generated successfully.")
print(f"market_snapshot.json written to {WORKSPACE}/market_snapshot.json")