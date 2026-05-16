import os
import json
import random
import csv
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Directory Structure ---
dirs = [
    "data/news",
    "data/market",
    "data/fund",
    "archive/2024Q3",
    "archive/2024Q4",
    "tools/templates",
    "tools/scripts",
    "reports/drafts",
    "config",
    "logs",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_configs = {
    "config/db_config.yaml": "host: localhost\nport: 5432\ndbname: funddb\nuser: analyst\n",
    "config/logging.conf": "[loggers]\nkeys=root\n[handlers]\nkeys=consoleHandler\n",
    "tools/scripts/fetch_nav.py": "# TODO: fetch NAV from API\ndef fetch_nav(code): pass\n",
    "tools/scripts/data_cleaner.py": "# Clean raw market data\nimport pandas as pd\ndef clean(df): return df.dropna()\n",
    "tools/templates/basic_report.txt": "FUND REPORT\n===========\nName: {name}\nCode: {code}\n",
    "archive/2024Q3/report_Q3.txt": "Q3 Report archived. Performance: +12.3%. No action needed.\n",
    "archive/2024Q4/report_Q4.txt": "Q4 Report archived. Performance: -3.1%. Market correction.\n",
    "logs/fetch_log_20250101.txt": "2025-01-01 08:00:01 INFO: News fetch started\n2025-01-01 08:00:15 INFO: 47 articles retrieved\n",
    "logs/error_log.txt": "2025-01-02 ERROR: Connection timeout for source Reuters\n",
    "reports/drafts/draft_note.txt": "Draft notes: consider adding technical analysis section later.\n",
}
for path, content in distractor_configs.items():
    (workspace / path).write_text(content, encoding="utf-8")

# --- Core Input File 1: Fund Basic Information ---
fund_info = {
    "fund_name": "华夏新兴产业股票",
    "fund_code": "003984",
    "fund_type": "股票型",
    "latest_nav": 2.8341,
    "nav_date": "2025-06-10",
    "manager": "张磊",
    "manager_years": 7,
    "fund_size_billion": 85.3,
    "benchmark": "中证新兴产业指数",
    "performance": {
        "1week": -1.82,
        "1month": -4.51,
        "3month": 6.73,
        "6month": 11.20,
        "1year": 18.45
    },
    "max_drawdown": -23.4,
    "sharpe_ratio": 0.87,
    "top10_holdings": [
        {"name": "宁德时代", "industry": "新能源/电池", "weight": 9.8},
        {"name": "比亚迪", "industry": "新能源/汽车", "weight": 8.4},
        {"name": "阳光电源", "industry": "新能源/逆变器", "weight": 7.2},
        {"name": "迈瑞医疗", "industry": "医疗器械", "weight": 5.6},
        {"name": "汇川技术", "industry": "工业自动化", "weight": 4.9},
        {"name": "东方财富", "industry": "金融科技", "weight": 4.3},
        {"name": "智飞生物", "industry": "生物医药", "weight": 3.8},
        {"name": "北方华创", "industry": "半导体设备", "weight": 3.5},
        {"name": "赛力斯", "industry": "新能源/汽车", "weight": 3.1},
        {"name": "天合光能", "industry": "新能源/光伏", "weight": 2.9},
    ],
    "top10_weight_total": 53.5,
    "industry_distribution": {
        "新能源": 42.3,
        "医疗健康": 12.7,
        "半导体": 9.8,
        "工业自动化": 8.6,
        "金融科技": 6.4,
        "其他": 20.2
    }
}
with open(workspace / "data/fund/fund_info.json", "w", encoding="utf-8") as f:
    json.dump(fund_info, f, ensure_ascii=False, indent=2)

# --- Core Input File 2: Market Data ---
market_data = {
    "date": "2025-06-10",
    "indices": {
        "上证指数": {"value": 3312.45, "change_pct": -0.73, "trend": "震荡偏弱"},
        "深证成指": {"value": 9876.23, "change_pct": -1.12, "trend": "下跌"},
        "创业板指": {"value": 1923.67, "change_pct": -1.45, "trend": "下跌"},
        "科创50": {"value": 856.34, "change_pct": -0.92, "trend": "震荡偏弱"}
    },
    "northbound_flow_billion": -15.3,
    "total_volume_billion": 872.4,
    "fear_greed_index": 32,
    "fear_greed_label": "恐慌",
    "market_trend_score_raw": 35,
    "capital_flow_score_raw": 25,
    "sentiment_score_raw": 30,
    "sector_match_score_raw": 40,
    "main_capital_flow": {
        "新能源": -8.4,
        "半导体": -3.2,
        "医疗": -1.8
    }
}
with open(workspace / "data/market/market_data.json", "w", encoding="utf-8") as f:
    json.dump(market_data, f, ensure_ascii=False, indent=2)

# --- Core Input File 3: News Articles ---
news_articles = [
    {
        "id": "N001",
        "title": "国家能源局：2025年新能源装机目标上调至300GW，超预期",
        "date": "2025-06-09",
        "source": "证券时报",
        "category": "行业政策",
        "industry": "新能源",
        "content": "国家能源局发布2025年能源工作指导意见，将新能源装机目标从250GW上调至300GW，并提出加大光伏、储能补贴力度，出台配套消纳政策。分析人士认为这对新能源产业链上下游均构成重大利好。",
        "impact_direction": "利好",
        "affected_sectors": ["光伏", "储能", "新能源汽车"]
    },
    {
        "id": "N002",
        "title": "美联储6月议息会议：维持利率不变，暗示年内降息次数减至1次",
        "date": "2025-06-10",
        "source": "新华社",
        "category": "宏观",
        "industry": "国际",
        "content": "美联储在最新议息会议上维持联邦基金利率目标区间5.25%-5.50%不变，但点阵图显示年内降息次数预期从3次下调至1次，美元指数走强，全球风险资产承压。外资短期回流趋势可能延续。",
        "impact_direction": "利空",
        "affected_sectors": ["成长股", "科技股", "新兴市场"]
    },
    {
        "id": "N003",
        "title": "中国5月CPI同比+0.3%，PPI同比-2.1%，通缩压力持续",
        "date": "2025-06-10",
        "source": "国家统计局",
        "category": "宏观",
        "industry": "经济数据",
        "content": "5月CPI同比上涨0.3%，低于预期0.5%；PPI同比下降2.1%，连续第30个月为负。分析人士认为当前通缩压力持续，央行有进一步宽松空间，但短期内市场信心受到抑制。",
        "impact_direction": "中性偏空",
        "affected_sectors": ["周期股", "制造业"]
    },
    {
        "id": "N004",
        "title": "工信部拟出台半导体设备国产化支持政策，北方华创等受益",
        "date": "2025-06-08",
        "source": "中国证券报",
        "category": "行业政策",
        "industry": "半导体",
        "content": "工信部就《半导体设备国产化推进方案（征求意见稿）》公开征求意见，拟对国产半导体设备采购给予15%财政补贴，并要求大型晶圆厂在3年内将国产设备使用比例提升至40%以上。",
        "impact_direction": "利好",
        "affected_sectors": ["半导体设备", "芯片制造"]
    },
    {
        "id": "N005",
        "title": "宁德时代：二季度电池出货量创历史新高，海外订单占比达35%",
        "date": "2025-06-09",
        "source": "公司公告",
        "category": "个股",
        "industry": "新能源",
        "content": "宁德时代公告显示，二季度动力电池及储能电池合计出货量达87GWh，同比增长43%，创历史新高。海外订单占比提升至35%，特斯拉、宝马、Stellantis等主要客户采购量均有增加。",
        "impact_direction": "利好",
        "affected_sectors": ["储能", "新能源汽车", "电池"]
    },
    {
        "id": "N006",
        "title": "医保局：对部分创新医疗器械开展价格谈判，迈瑞医疗核心产品纳入范围",
        "date": "2025-06-07",
        "source": "财联社",
        "category": "行业政策",
        "industry": "医疗器械",
        "content": "国家医保局宣布启动2025年医疗器械价格谈判，迈瑞医疗的监护仪、呼吸机等核心产品被纳入谈判范围，市场预期相关产品价格将平均下降15-20%，短期内对公司盈利构成压力。",
        "impact_direction": "利空",
        "affected_sectors": ["医疗器械"]
    }
]
with open(workspace / "data/news/news_articles.json", "w", encoding="utf-8") as f:
    json.dump(news_articles, f, ensure_ascii=False, indent=2)

# --- Core Input File 4: User Investment Profile ---
user_profile = {
    "holder_name": "投资者A",
    "current_position_pct": 30,
    "investment_horizon": "中期",
    "risk_preference": "稳健型",
    "max_acceptable_drawdown_pct": "10-20%",
    "query": "当前市场环境下，华夏新兴产业股票(003984)是否应该继续持有还是减仓？"
}
with open(workspace / "data/fund/user_profile.json", "w", encoding="utf-8") as f:
    json.dump(user_profile, f, ensure_ascii=False, indent=2)

# --- Additional Distractor: old partial report (intentionally incomplete/wrong format) ---
old_report = """基金分析报告
=============
基金: 华夏新兴产业股票
日期: 2025-05-01
简评: 近期表现一般，新能源板块有压力。
建议: 持有观望。
"""
(workspace / "reports/drafts/old_partial_report.txt").write_text(old_report, encoding="utf-8")

# --- Distractor: a separate unrelated fund data file ---
other_fund = {"fund_name": "富国天惠成长混合", "fund_code": "161005", "fund_type": "混合型", "note": "archive only"}
with open(workspace / "archive/2024Q4/other_fund_archive.json", "w", encoding="utf-8") as f:
    json.dump(other_fund, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print(f"Files created: {len(list(workspace.rglob('*.*')))}")