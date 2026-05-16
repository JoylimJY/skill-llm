import os
import json
import csv
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# Create deeply nested directory structure with distractor files
dirs = [
    "references",
    "scripts",
    "data/raw",
    "data/processed",
    "data/archive",
    "logs",
    "config",
    "reports/daily",
    "reports/weekly",
    "analysis/sectors",
    "analysis/technical",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractor_files = {
    "references/screening_criteria.md": "# Screening Criteria\n\nThis document is outdated. See SKILL.md for current criteria.\n\nOld criteria: price > 3 yuan, market cap > 10B.\n",
    "references/risk_management.md": "# Risk Management\n\nAlways manage your risk.\nMax drawdown: 5%\n\nOld rule: max position 30% of capital.\n",
    "references/case_studies.md": "# Case Studies\n\n## 2023-01-15\nStock 600519 selected. Result: +2.3%\n\n## 2023-02-20\nStock 000858 selected. Result: -1.1%\n",
    "scripts/quick_check.py": "# Quick check script - requires data source configuration\n# Usage: python quick_check.py --code 600030\nprint('Data source not configured.')\n",
    "scripts/position_calculator.py": "# Position calculator\n# total_capital * 0.20 = max_position\ncapital = float(input('Enter capital: '))\nprint(f'Max position: {capital * 0.20:.2f}')\n",
    "logs/trading_log_20240301.txt": "2024-03-01 14:49:22 BUY 600030 @ 23.45 qty=1000\n2024-03-02 09:30:01 SELL 600030 @ 23.78 qty=1000 PnL=+330\n",
    "logs/trading_log_20240302.txt": "2024-03-02 14:49:55 BUY 000776 @ 18.20 qty=2000\n2024-03-03 09:30:02 SELL 000776 @ 17.95 qty=2000 PnL=-500\n",
    "config/data_source.json": json.dumps({"source": "eastmoney", "api_key": "NOT_CONFIGURED", "timeout": 30}, indent=2),
    "config/strategy_params.json": json.dumps({"strategy": "overnight_v1", "version": "2023.1", "deprecated": True}, indent=2),
    "data/archive/stocks_20240101.csv": "code,name,price\n600519,贵州茅台,1800.00\n000858,五粮液,160.00\n",
    "data/processed/summary_20240101.txt": "Total stocks screened: 45\nPassed filters: 3\nSelected: 600030\n",
    "analysis/sectors/sector_map.json": json.dumps({
        "银行": ["601398", "601288", "000001"],
        "白酒": ["600519", "000858", "600809"],
        "券商": ["600030", "000776", "601688"],
        "科技": ["600584", "002049", "000725"],
    }, indent=2, ensure_ascii=False),
    "analysis/technical/ma_config.txt": "MA5: 5-day moving average\nMA10: 10-day moving average\nMACD settings: 12,26,9\n",
    "reports/weekly/week_summary.txt": "Week 2024-W10\nTotal trades: 4\nWin rate: 75%\nAverage return: +0.8%\n",
    "reports/daily/template.txt": "Date: {date}\nSelected stock: {code}\nReasoning: {reason}\nBuy price: {price}\nExpected exit: next open\n",
}

for filepath, content in distractor_files.items():
    full_path = os.path.join(workspace, filepath)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

# Generate the main input: candidate stocks CSV
# This is the messy, realistic input the agent must process
# Fields: code, name, sector, sector_category, gain_pct, volume_cny, float_mktcap_cny, turnover_rate_pct, price, volume_ratio, is_st, macd_dif_positive, above_ma5_ma10, notes

stocks = [
    # Code, Name, sector, sector_category, gain_pct, volume_cny(亿), float_mktcap(亿), turnover_rate, price, volume_ratio, is_st, macd_dif_pos, above_ma, notes
    
    # === VALID candidates in priority sectors ===
    # 券商/金融 - HIGH PRIORITY - multiple valid
    ("600030", "中信证券", "券商", "券商/金融", 2.5, 3.2, 250, 4.5, 23.45, 1.2, False, True, True, "尾盘温和放量"),
    ("000776", "广发证券", "券商", "券商/金融", 1.8, 1.5, 180, 3.8, 18.20, 0.95, False, True, True, "稳步上涨"),
    
    # 科技/半导体 - SECOND PRIORITY - valid
    ("600584", "长电科技", "半导体", "科技/半导体", 3.1, 2.1, 120, 5.2, 32.10, 1.5, False, True, True, "跟随海外半导体走强"),
    ("002049", "紫光国微", "半导体", "科技/半导体", 4.2, 1.8, 350, 7.1, 85.30, 1.8, False, False, True, "MACD待突破"),
    
    # 新能源 - THIRD PRIORITY - valid
    ("601012", "隆基绿能", "新能源", "新能源", 2.2, 5.6, 480, 3.5, 28.50, 1.1, False, True, True, "光伏政策利好预期"),
    
    # 医药 - FOURTH PRIORITY - valid
    ("600276", "恒瑞医药", "医药", "医药", 1.5, 2.3, 320, 4.1, 38.20, 1.0, False, True, True, "新药研发进展"),
    
    # === SHOULD BE EXCLUDED: Wrong code prefix (ChiNext 30xxx) ===
    ("300750", "宁德时代", "新能源", "新能源", 2.8, 12.5, 6500, 5.5, 210.50, 1.3, False, True, True, "创业板股票"),
    ("300059", "东方财富", "金融科技", "科技/半导体", 1.9, 8.2, 2200, 4.2, 18.75, 1.1, False, True, True, "创业板"),
    
    # === SHOULD BE EXCLUDED: STAR Market (68xxx) ===
    ("688981", "中芯国际", "半导体", "科技/半导体", 3.5, 6.1, 1200, 6.2, 55.30, 1.6, False, True, True, "科创板"),
    ("688599", "天合光能", "新能源", "新能源", 2.0, 1.2, 280, 3.9, 32.50, 0.9, False, True, True, "科创板"),
    
    # === SHOULD BE EXCLUDED: ST stocks ===
    ("600013", "ST国中水务", "公用事业", "其他", 2.1, 0.5, 80, 5.5, 6.20, 1.4, True, False, False, "ST股"),
    ("000609", "*ST中迪", "房地产", "房地产", 1.3, 0.3, 30, 4.2, 3.80, 1.2, True, False, False, "ST股且价格低"),
    
    # === SHOULD BE EXCLUDED: Gain too high (>5%) ===
    ("600036", "招商银行", "银行", "券商/金融", 5.8, 8.9, 1200, 2.8, 42.30, 2.3, False, True, True, "涨幅过高"),
    ("000333", "美的集团", "家电", "其他", 6.2, 4.5, 900, 3.1, 58.90, 1.7, False, True, True, "涨幅超5%"),
    
    # === SHOULD BE EXCLUDED: Gain too low (<1%) ===
    ("600000", "浦发银行", "银行", "券商/金融", 0.5, 2.1, 380, 1.8, 8.90, 0.7, False, False, False, "涨幅不足"),
    ("601166", "兴业银行", "银行", "券商/金融", 0.3, 1.9, 420, 1.5, 22.50, 0.6, False, False, False, "涨幅过低"),
    
    # === SHOULD BE EXCLUDED: Volume too low (<1亿) ===
    ("600072", "中船科技", "军工", "其他", 2.3, 0.6, 75, 4.8, 12.30, 1.1, False, True, True, "成交额不足"),
    ("000927", "中国铝业", "有色金属", "其他", 1.7, 0.8, 220, 3.2, 7.80, 0.9, False, False, True, "成交额不足1亿"),
    
    # === SHOULD BE EXCLUDED: Market cap too small (<50亿) ===
    ("600123", "兰花科创", "能源", "其他", 3.0, 1.2, 35, 8.5, 9.50, 1.6, False, True, True, "市值过小"),
    
    # === SHOULD BE EXCLUDED: Market cap too large (>500亿) ===
    ("600519", "贵州茅台", "白酒", "其他", 1.2, 15.3, 2200, 0.8, 1780.00, 0.6, False, True, True, "市值过大超500亿"),
    ("000858", "五粮液", "白酒", "其他", 2.1, 6.8, 650, 1.2, 156.80, 0.7, False, True, True, "市值超500亿"),
    
    # === SHOULD BE EXCLUDED: Turnover rate too low (<3%) ===
    ("601398", "工商银行", "银行", "券商/金融", 1.5, 3.2, 450, 1.5, 5.80, 0.7, False, False, False, "换手率过低"),
    
    # === SHOULD BE EXCLUDED: Turnover rate too high (>10%) ===
    ("002223", "鱼跃医疗", "医药", "医药", 2.8, 1.1, 65, 12.5, 28.60, 1.9, False, True, True, "换手率过高且市值过小"),
    
    # === SHOULD BE EXCLUDED: Price too low (<=5元) ===
    ("000001", "平安银行", "银行", "券商/金融", 1.8, 4.5, 350, 3.5, 4.80, 1.0, False, True, True, "股价低于5元"),
    
    # === SHOULD BE EXCLUDED: Volume ratio too low (<0.8) ===
    ("601601", "中国太保", "保险", "券商/金融", 1.9, 1.8, 280, 3.2, 32.50, 0.5, False, True, True, "量比不足0.8"),
    
    # === SHOULD BE EXCLUDED: Volume ratio too high (>2.0) ===
    ("002594", "比亚迪", "新能源", "新能源", 3.5, 9.8, 480, 6.5, 255.30, 2.5, False, True, True, "量比过高超2.0"),
    
    # === SHOULD BE EXCLUDED: Excluded sector (房地产) - even if metrics ok ===
    ("000002", "万科A", "房地产", "房地产", 2.0, 2.5, 200, 4.5, 10.20, 1.1, False, False, True, "房地产板块排除"),
    ("600048", "保利发展", "房地产", "房地产", 1.5, 1.8, 180, 3.8, 15.60, 0.95, False, True, True, "房地产板块"),
    
    # === EDGE CASES: exactly at boundary ===
    # Gain exactly 5% - should be INCLUDED (boundary is +1% ~ +5%, ambiguous - test will treat <=5 as valid per "避免追高，留出次日空间")
    ("600690", "海尔智家", "家电", "其他", 5.0, 2.1, 350, 5.5, 28.50, 1.3, False, True, True, "涨幅恰好5%,家电其他板块"),
    # Gain exactly 1% - should be INCLUDED
    ("601688", "华泰证券", "券商", "券商/金融", 1.0, 1.5, 200, 4.2, 16.80, 1.1, False, True, True, "涨幅恰好1%,券商板块有效"),
    # Volume ratio exactly 2.0 - should be INCLUDED
    ("000538", "云南白药", "医药", "医药", 2.5, 1.3, 180, 4.8, 58.30, 2.0, False, True, True, "量比恰好2.0"),
    # Volume ratio exactly 0.8 - should be INCLUDED
    ("600887", "伊利股份", "食品", "其他", 1.6, 1.1, 260, 3.1, 33.50, 0.8, False, True, False, "量比恰好0.8,均线不佳"),
]

# Write CSV
csv_path = os.path.join(workspace, "data/raw/candidate_stocks_today.csv")
fieldnames = [
    "code", "name", "sector", "sector_category",
    "gain_pct", "volume_cny_100m", "float_mktcap_cny_100m",
    "turnover_rate_pct", "price", "volume_ratio",
    "is_st", "macd_dif_positive", "above_ma5_ma10", "notes"
]

with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for s in stocks:
        writer.writerow({
            "code": s[0],
            "name": s[1],
            "sector": s[2],
            "sector_category": s[3],
            "gain_pct": s[4],
            "volume_cny_100m": s[5],
            "float_mktcap_cny_100m": s[6],
            "turnover_rate_pct": s[7],
            "price": s[8],
            "volume_ratio": s[9],
            "is_st": s[10],
            "macd_dif_positive": s[11],
            "above_ma5_ma10": s[12],
            "notes": s[13],
        })

print(f"Generated {len(stocks)} candidate stocks in {csv_path}")
print("Workspace structure created with distractor files.")

# Create a misleading "old criteria" file to test if agent uses correct source
old_criteria_path = os.path.join(workspace, "config/old_screening_rules.txt")
with open(old_criteria_path, "w", encoding="utf-8") as f:
    f.write("""OLD SCREENING RULES (DEPRECATED - DO NOT USE)
=====================================================
These rules are from 2022 and are NO LONGER VALID.

Old quantitative criteria:
- Gain: 0.5% ~ 8%          <- WRONG, outdated
- Volume: > 5000万          <- WRONG, outdated  
- Market cap: 20亿 ~ 1000亿 <- WRONG, outdated
- Turnover rate: 2% ~ 15%   <- WRONG, outdated
- Price: > 3元              <- WRONG, outdated
- Volume ratio: 0.5 ~ 3.0   <- WRONG, outdated

Sector exclusions: None     <- WRONG, outdated

DO NOT USE THESE RULES.
""")

print("Also created misleading old_screening_rules.txt as distractor.")