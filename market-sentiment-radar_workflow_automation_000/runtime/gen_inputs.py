import os
import json
import textwrap

workspace = "/workspace"

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "scripts",
    "references",
    "data/raw/2026-03",
    "data/processed",
    "logs",
    "reports/archive",
    "config",
    "tests",
    "docs/api",
    "notebooks",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "config/settings.yaml": "# App configuration\nenv: production\ndebug: false\nlog_level: INFO\n",
    "config/db_config.json": json.dumps({"host": "localhost", "port": 5432, "db": "market_db"}, indent=2),
    "data/raw/2026-03/index_data.csv": "date,close,volume\n2026-03-13,3287.45,820000000000\n2026-03-14,3241.12,710000000000\n",
    "data/processed/summary_20260314.json": json.dumps({"date": "2026-03-14", "status": "processed"}, indent=2),
    "logs/app.log": "[2026-03-14 09:30:00] INFO market open\n[2026-03-14 15:00:00] INFO market close\n",
    "reports/archive/report_20260310.md": "# Archive Report 2026-03-10\nThis is an old report.\n",
    "tests/test_sentiment.py": "import unittest\nclass TestSentiment(unittest.TestCase):\n    pass\n",
    "docs/api/README.md": "# API Documentation\nSee individual script headers.\n",
    "notebooks/exploration.ipynb": '{"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}',
    "data/raw/2026-03/sector_weights.json": json.dumps({"finance": 0.28, "tech": 0.22, "energy": 0.15}, indent=2),
    "references/sentiment-cycles.md": textwrap.dedent("""\
        # Sentiment Cycles Reference
        冰点期: 千股跌停，成交极度萎缩，恐慌蔓延
        混沌期: 板块快速轮动，无主线，资金互相收割
        退潮期: 高位股派发，缩量下跌，跌停扩散
        主升期: 量能爆棚，主线清晰，赚钱效应强
    """),
    "references/sector-rotation.md": textwrap.dedent("""\
        # Sector Rotation Guide
        高切低: 资金从高位撤入低位防御
        强者恒强: 主线持续
        电风扇: 快速轮动，一天换几个热点
    """),
    "references/macro-indicators.md": textwrap.dedent("""\
        # Macro Indicators Guide
        美联储利率影响全球流动性
        CPI/非农影响加息预期
        中国PMI/社融影响国内经济预期
    """),
    "references/position-mapping.md": textwrap.dedent("""\
        # Position Mapping
        冰点期: 0-10% 防守
        退潮/混沌期: 0-20% 极轻仓或空仓
        震荡期: 20-50% 均衡
        主升期: 50-80% 重仓
    """),
}
for path, content in distractors.items():
    full = os.path.join(workspace, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

# ── core mock script: sentiment_analyzer.py ────────────────────────────────
sentiment_script = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    Market Sentiment Analyzer
    Usage: python3 scripts/sentiment_analyzer.py --date YYYY-MM-DD
    \"\"\"
    import argparse
    import json
    import sys

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--date', required=True, help='Analysis date YYYY-MM-DD')
        parser.add_argument('--output', default='json', choices=['json', 'text'])
        args = parser.parse_args()

        if args.date != '2026-03-15':
            print(json.dumps({"error": f"No data available for {args.date}"}))
            sys.exit(1)

        # Deterministic mock data for 2026-03-15
        data = {
            "date": "2026-03-15",
            "market_volume_billion_cny": 7500,
            "volume_vs_yesterday": "缩量",
            "advance_count": 480,
            "decline_count": 3210,
            "flat_count": 312,
            "advance_decline_ratio": "480:3210",
            "limit_up_count": 23,
            "limit_down_count": 87,
            "max_consecutive_limit_up": 2,
            "yesterday_limit_up_avg_premium_pct": -2.3,
            "shanghai_composite_change_pct": -1.85,
            "shenzhen_component_change_pct": -2.41,
            "chinext_change_pct": -2.78,
            "money_effect_score": "极差",
            "notes": "高位股集体大幅低开低走，跌停板蔓延，成交量持续萎缩至7500亿，低于8000亿警戒线，赚钱效应极差，昨日涨停股今日平均亏损2.3%"
        }

        if args.output == 'json':
            print(json.dumps(data, ensure_ascii=False, indent=2))
        else:
            print(f"日期: {data['date']}")
            print(f"成交量: {data['market_volume_billion_cny']} 亿元 ({data['volume_vs_yesterday']})")
            print(f"涨跌家数: 涨 {data['advance_count']} : 跌 {data['decline_count']}")
            print(f"连板高度: {data['max_consecutive_limit_up']} 板")
            print(f"跌停家数: {data['limit_down_count']} 家")
            print(f"昨涨停溢价: {data['yesterday_limit_up_avg_premium_pct']}%")

    if __name__ == '__main__':
        main()
""")

# ── core mock script: sector_flow.py ───────────────────────────────────────
sector_script = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    Sector Money Flow Analyzer
    Usage: python3 scripts/sector_flow.py [--date YYYY-MM-DD]
    \"\"\"
    import argparse
    import json

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--date', default='2026-03-15')
        args = parser.parse_args()

        data = {
            "date": args.date,
            "rotation_pattern": "电风扇",
            "rotation_description": "板块快速轮动，上午炒地产午后资金撤离转向煤炭，午后又切换至银行，全天换了3个热点",
            "top_inflow_sectors": [
                {"name": "银行", "net_inflow_billion": 12.3, "type": "防守板块", "sustainability": "弱"},
                {"name": "煤炭", "net_inflow_billion": 4.1, "type": "过渡板块", "sustainability": "弱"}
            ],
            "top_outflow_sectors": [
                {"name": "AI算力", "net_outflow_billion": -23.5, "note": "高位龙头大幅低开，主力出货迹象明显"},
                {"name": "新能源", "net_outflow_billion": -18.2, "note": "持续调整，资金撤离"},
                {"name": "地产", "net_outflow_billion": -11.0, "note": "昙花一现，上午拉升午后全面撤退"}
            ],
            "main_theme": "无明确主线",
            "smart_money_behavior": "外资北向净流出47亿，游资在微盘股和低价股之间乱跑，整体以防御为主",
            "warning": "AI算力、新能源板块正在退潮，高位股风险极大，避免追高"
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))

    if __name__ == '__main__':
        main()
""")

# ── core mock script: cross_market.py ──────────────────────────────────────
cross_script = textwrap.dedent("""\
    #!/usr/bin/env python3
    \"\"\"
    Cross-Market Linkage Analyzer
    Usage: python3 scripts/cross_market.py [--date YYYY-MM-DD]
    \"\"\"
    import argparse
    import json

    def main():
        parser = argparse.ArgumentParser()
        parser.add_argument('--date', default='2026-03-15')
        args = parser.parse_args()

        data = {
            "date": args.date,
            "us_market": {
                "nasdaq_change_pct": -1.95,
                "sp500_change_pct": -1.42,
                "dow_change_pct": -0.98,
                "vix": 28.4,
                "note": "昨夜纳斯达克大幅下跌近2%，科技股领跌，英伟达跌4.2%，恐慌情绪VIX升至28"
            },
            "china_concepts": {
                "change_pct": -3.1,
                "note": "中概股跟随大盘下跌，阿里跌2.8%，京东跌3.5%"
            },
            "currency": {
                "usd_index": 106.8,
                "usd_index_change": "+0.45%",
                "usdcny": 7.298,
                "usdcny_change": "人民币贬值",
                "note": "美元指数上涨至106.8，人民币汇率走弱至7.298，外资流出压力加大"
            },
            "commodities": {
                "gold_change_pct": +0.82,
                "oil_change_pct": -0.55,
                "note": "黄金小幅上涨避险需求上升，原油小幅下跌"
            },
            "macro_events": [
                "本周四将公布美国3月CPI数据，市场预期偏高，加息预期升温",
                "美联储官员近期讲话偏鹰，全球流动性收紧预期增强",
                "中国2月社融数据低于预期，国内经济复苏动能偏弱"
            ],
            "a_share_impact": "美股科技股大跌将拖累A股半导体、AI板块今日低开；美元强势+人民币走弱加大外资流出压力；整体偏空"
        }
        print(json.dumps(data, ensure_ascii=False, indent=2))

    if __name__ == '__main__':
        main()
""")

for fname, content in [
    ("scripts/sentiment_analyzer.py", sentiment_script),
    ("scripts/sector_flow.py", sector_script),
    ("scripts/cross_market.py", cross_script),
]:
    with open(os.path.join(workspace, fname), "w", encoding="utf-8") as f:
        f.write(content)

print("Workspace scaffold created successfully.")
print(f"Files created: {sum(1 for _ in Path('/workspace').rglob('*') if _.is_file()) if False else 'see ls'}")