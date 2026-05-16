import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── Create realistic distractor directory structure ──────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/cache",
    "reports/daily",
    "reports/weekly",
    "logs",
    "config",
    "notebooks",
    "archive/2023",
    "archive/2024",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "config/market_config.yaml": textwrap.dedent("""\
        markets:
          - name: HK
            timezone: Asia/Hong_Kong
          - name: US
            timezone: America/New_York
          - name: Crypto
            timezone: UTC
        """),
    "config/strategy_params.json": json.dumps({
        "lookback_days": 90,
        "ma_short": 20,
        "ma_long": 60,
        "rsi_threshold": 30,
        "note": "Legacy MA-RSI strategy parameters"
    }, indent=2),
    "data/raw/tickers.txt": "\n".join(["BTC-USD", "ETH-USD", "0700.HK", "9988.HK", "AAPL", "TSLA", "NVDA"]),
    "data/raw/portfolio.csv": textwrap.dedent("""\
        ticker,shares,cost_basis,currency
        BTC-USD,0.5,58000,USD
        0700.HK,200,320.00,HKD
        AAPL,50,175.00,USD
        """),
    "data/processed/.gitkeep": "",
    "logs/run_20240101.log": textwrap.dedent("""\
        2024-01-01 09:00:01 INFO  Starting daily scan
        2024-01-01 09:00:05 INFO  Fetched 7 tickers
        2024-01-01 09:00:12 WARN  ETH-USD: insufficient data
        2024-01-01 09:00:20 INFO  Scan complete
        """),
    "logs/run_20240102.log": textwrap.dedent("""\
        2024-01-02 09:00:01 INFO  Starting daily scan
        2024-01-02 09:00:18 INFO  Scan complete - 7 tickers processed
        """),
    "reports/daily/.gitkeep": "",
    "reports/weekly/.gitkeep": "",
    "archive/2023/strategy_v1.json": json.dumps({"version": 1, "deprecated": True}, indent=2),
    "archive/2024/strategy_v2.json": json.dumps({"version": 2, "deprecated": True}, indent=2),
    "notebooks/exploratory.py": textwrap.dedent("""\
        # Exploratory analysis notebook (converted to .py)
        # WARNING: Not production code
        import json
        # placeholder
        tickers = ['BTC-USD', '0700.HK']
        for t in tickers:
            print(f'Analyzing {t}...')
        """),
}

for rel_path, content in distractor_files.items():
    fp = workspace / rel_path
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)

# ── Create the actual analyze.py script in scripts/ ──────────────────────────
# This is the proprietary 缠论 analysis script described in SKILL.md
# It produces the exact output format shown in SKILL.md
analyze_script = textwrap.dedent('''\
    #!/usr/bin/env python3
    """
    缠论技术分析脚本
    基于缠中说禅理论的走势分析工具
    """
    import sys
    import json
    import random
    import hashlib
    import datetime

    def get_deterministic_seed(ticker: str) -> int:
        """Generate deterministic seed from ticker name"""
        h = hashlib.md5(ticker.encode()).hexdigest()
        return int(h[:8], 16)

    def analyze(ticker: str) -> dict:
        seed = get_deterministic_seed(ticker)
        rng = random.Random(seed)

        # 模拟缠论分析结果 - deterministic per ticker
        bi_count = rng.choice([3, 4, 5, 6, 7, 8])
        current_bi_type = rng.choice(["上涨笔", "下跌笔"])
        bi_amplitude = round(rng.uniform(-45.0, 45.0), 2)
        beichi = rng.random() < 0.4  # 40% chance of 背驰

        # 中枢数量决定走势类型
        zhongshu_count = rng.randint(1, 3)
        trend_type = "盘整" if zhongshu_count == 1 else "趋势"

        # 关键位置
        high_price = round(rng.uniform(50000, 80000) if "BTC" in ticker else
                          rng.uniform(200, 400) if ".HK" in ticker else
                          rng.uniform(100, 300), 2)
        low_price = round(high_price * rng.uniform(0.55, 0.85), 2)
        position_pct = rng.randint(10, 95)  # percentage 0-100

        # 井论判断 (for odd bi counts)
        jing_type = None
        if bi_count >= 5:
            wave1 = round(rng.uniform(5, 20), 2)
            wave3 = round(rng.uniform(5, 20), 2)
            wave5 = round(rng.uniform(5, 20), 2)
            if wave5 > wave3 and wave5 > wave1:
                jing_type = "大井"
            elif wave5 > wave1 or wave5 > wave3:
                jing_type = "小井"
            else:
                jing_type = None
        else:
            wave1, wave3, wave5 = None, None, None

        # MACD背驰详情
        macd_area_current = round(rng.uniform(100, 500), 1)
        macd_area_prev = round(rng.uniform(100, 600), 1)
        macd_beichi = macd_area_current < macd_area_prev

        result = {
            "ticker": ticker,
            "analysis_time": datetime.datetime.now().isoformat(),
            "bi_analysis": {
                "count": bi_count,
                "current_type": current_bi_type,
                "amplitude_pct": bi_amplitude,
                "beichi": beichi,
                "macd_area_current": macd_area_current,
                "macd_area_prev": macd_area_prev,
                "macd_beichi": macd_beichi
            },
            "trend": {
                "type": trend_type,
                "zhongshu_count": zhongshu_count
            },
            "jing": {
                "type": jing_type,
                "wave1": wave1,
                "wave3": wave3,
                "wave5": wave5
            },
            "key_levels": {
                "high": high_price,
                "low": low_price,
                "position_pct": position_pct
            }
        }
        return result

    def format_output(result: dict):
        ticker = result["ticker"]
        bi = result["bi_analysis"]
        trend = result["trend"]
        jing = result["jing"]
        levels = result["key_levels"]

        print(f"\\n{'='*50}")
        print(f"🔍 缠论分析: {ticker}")
        print(f"{'='*50}")
        print(f"\\n📈 笔分析:")
        print(f"   有效笔: {bi[\'count\']}笔")
        print(f"   当前笔: {bi[\'current_type\']}")
        print(f"   幅度: {bi[\'amplitude_pct\']:+.2f}%")
        if bi["beichi"] or bi["macd_beichi"]:
            print(f"   ⚠️  背驰迹象: 力度减弱")
        else:
            print(f"   ✅  无背驰信号")

        print(f"\\n🏛️  走势中枢:")
        print(f"   走势类型: {trend[\'type\']}")
        print(f"   中枢数量: {trend[\'zhongshu_count\']}个")

        if jing["type"]:
            print(f"\\n🌀 井论判断:")
            print(f"   井型: {jing[\'type\']}")
            print(f"   波1幅度: {jing[\'wave1\']:.2f}")
            print(f"   波3幅度: {jing[\'wave3\']:.2f}")
            print(f"   波5幅度: {jing[\'wave5\']:.2f}")

        print(f"\\n🎯 关键位置:")
        print(f"   最高: {levels[\'high\']}")
        print(f"   最低: {levels[\'low\']}")
        print(f"   当前位置: {levels[\'position_pct\']}% ", end="")
        pos = levels["position_pct"]
        if pos < 30:
            print("(低位区间)")
        elif pos > 70:
            print("(高位区间)")
        else:
            print("(中性区间)")

        print()

    def get_json(ticker: str) -> dict:
        """Return raw analysis as JSON (used by downstream scripts)"""
        return analyze(ticker)

    if __name__ == "__main__":
        if len(sys.argv) < 2:
            print("Usage: python3 analyze.py <TICKER> [--json]")
            sys.exit(1)

        ticker = sys.argv[1]
        output_json = "--json" in sys.argv

        result = analyze(ticker)

        if output_json:
            print(json.dumps(result, indent=2))
        else:
            format_output(result)
''')

(workspace / "scripts" / "analyze.py").write_text(analyze_script)

# ── Task description / brief for the agent (acts as the prompt context file) ─
task_brief = textwrap.dedent("""\
    PORTFOLIO SCREENING TASK
    ========================
    Assets under review: BTC-USD, 0700.HK, AAPL

    The quantitative research team needs a structured screening report
    for the above three assets. Please run the appropriate analysis tools
    and produce the file: screening_report.json

    See SKILL.md for available tools and output interpretation.
    """)

(workspace / "TASK_BRIEF.txt").write_text(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {list(workspace.rglob('*'))}")