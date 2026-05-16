import os
import json
import random

random.seed(42)

base = "/workspace"
os.makedirs(base, exist_ok=True)

# Create a deeply nested distractor structure
dirs = [
    "finance/reports/q1_2025",
    "finance/reports/q2_2025",
    "finance/data/raw",
    "finance/data/processed",
    "tools/scripts",
    "tools/configs",
    "archive/2024/gold",
    "archive/2024/stocks",
    "logs/daily",
    "logs/weekly",
]
for d in dirs:
    os.makedirs(os.path.join(base, d), exist_ok=True)

# Distractor files
distractor_files = {
    "finance/reports/q1_2025/silver_report.md": "# Silver Market Report Q1 2025\n\nSilver prices remained stable...\n",
    "finance/reports/q1_2025/copper_analysis.txt": "Copper LME 3M: $9,200/t\nTrend: Sideways\n",
    "finance/reports/q2_2025/equity_summary.txt": "A股市场 Q2总结：上证指数3,200点位附近震荡...\n",
    "finance/data/raw/fx_rates_20250601.csv": "USD/CNY,7.25\nEUR/USD,1.08\nGBP/USD,1.27\n",
    "finance/data/processed/commodity_index.json": json.dumps({"CRB": 280.5, "BCOM": 103.2}),
    "tools/scripts/fetch_data.py": "# Deprecated data fetcher\nimport requests\n# TODO: update endpoint\n",
    "tools/configs/api_config.yaml": "endpoint: http://old-api.example.com\ntimeout: 30\n",
    "archive/2024/gold/annual_gold_review_2024.txt": "2024年黄金全年回顾：XAUUSD全年涨幅约27%，创历史新高...\n",
    "archive/2024/stocks/sp500_returns.csv": "Month,Return\nJan,1.5%\nFeb,-0.8%\nMar,3.2%\n",
    "logs/daily/system_log_20250601.txt": "[INFO] Market data pipeline completed\n[INFO] 1,204 records processed\n",
    "logs/weekly/weekly_summary_week22.txt": "Week 22 Summary: All pipelines nominal. Gold data feed latency: 2ms.\n",
    "archive/2024/gold/gold_etf_flows_2024.csv": "Date,GLD_Flow,IAU_Flow\n2024-01-01,+250M,-50M\n2024-06-01,-180M,+120M\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(base, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# THE CORE PROBLEM: market context data file with specific values
# These values are engineered to trigger 🔴 暂缓买入 (defer buying) based on SKILL.md criteria:
# - DXY > 104 (currently 106.3) -> hawkish signal
# - Gold 1-month surge > 8% (current vs 1 month ago: 3520 vs 3210 = ~9.7%) -> technical overbought
# - Fed hawkish signals
market_context = {
    "data_date": "2025-06-15",
    "international_gold": {
        "xauusd_spot": 3520.45,
        "xauusd_change_pct": 0.82,
        "xauusd_change_usd": 28.70,
        "unit": "USD/oz"
    },
    "domestic_gold": {
        "au9999_price": 808.35,
        "au9999_change_pct": 0.75,
        "au9999_change_cny": 6.05,
        "unit": "CNY/g",
        "exchange": "上海黄金交易所"
    },
    "historical_3month": {
        "start_date": "2025-03-15",
        "start_price": 2985.00,
        "month1_high": 3050.20,
        "month1_low": 2940.10,
        "month2_high": 3210.80,
        "month2_low": 3080.50,
        "month3_high": 3545.00,
        "month3_low": 3380.20,
        "current_price": 3520.45,
        "3month_change_pct": 17.94,
        "support_level": 3380.00,
        "resistance_level": 3550.00
    },
    "macro_factors": {
        "fed_policy": "鹰派立场维持，2025年仅预期降息1次，下次会议2025年7月30日",
        "dxy_index": 106.3,
        "dxy_trend": "走强",
        "geopolitics": "中东局势趋缓，避险情绪边际回落",
        "cpi_latest": "美国5月CPI同比+3.4%，高于预期",
        "real_rate": "美国10年期TIPS实际利率+2.1%，处于高位",
        "etf_flows": "近2周黄金ETF持仓净流出 -45吨",
        "1month_gold_change_pct": 9.7
    },
    "etf_data": {
        "hua_an_518880": {
            "nav": 7.2341,
            "monthly_change_pct": 9.65,
            "aum_billion_cny": 92.3
        },
        "boshi_159937": {
            "nav": 7.1856,
            "monthly_change_pct": 9.58,
            "aum_billion_cny": 45.1
        },
        "yifangda_159934": {
            "nav": 5.8923,
            "monthly_change_pct": 9.71,
            "aum_billion_cny": 28.7
        },
        "guotai_518800": {
            "nav": 7.1102,
            "monthly_change_pct": 9.42,
            "aum_billion_cny": 18.4
        }
    }
}

market_context_path = os.path.join(base, "market_data.json")
with open(market_context_path, "w", encoding="utf-8") as f:
    json.dump(market_context, f, ensure_ascii=False, indent=2)

# Also create a task brief file
task_brief = """CLIENT BRIEF - Gold Investment Analysis Request
================================================
Date: 2025-06-15
Client: Retail Investment Division

The investment team requires a comprehensive gold investment analysis report for 
client-facing distribution. The report must be current as of today's date and 
cover all standard analysis modules our gold analyst framework provides.

Please generate the complete analysis report and save it as: gold_analysis_report.md

All relevant market data has been collected and is available in market_data.json 
in the workspace root directory.
"""

with open(os.path.join(base, "task_brief.txt"), "w", encoding="utf-8") as f:
    f.write(task_brief)

print("Workspace generated successfully.")
print(f"Files created: {len(distractor_files) + 2} files")
print("market_data.json contains: XAUUSD=3520.45, DXY=106.3, 1M-change=9.7% -> should trigger 🔴 暂缓买入")