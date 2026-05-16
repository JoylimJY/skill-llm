import os
import random
import csv

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Directory structure with distractor files ──────────────────────────────
dirs = [
    "market_data/raw",
    "market_data/processed",
    "watchlist",
    "logs/old",
    "logs/archive",
    "reports/weekly",
    "reports/monthly",
    "config",
    "notes",
    "templates",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "market_data/raw/yesterday_close.txt": "代码,收盘\n000001,14.32\n600519,1820.00\n",
    "market_data/raw/index_data.csv": "指数,涨跌幅\n上证,0.45%\n深证,0.82%\n创业板,1.23%\n",
    "market_data/processed/sector_flow_old.csv": "板块,净流入(亿)\n新能源,3.2\n半导体,1.8\n",
    "watchlist/longterm_holds.txt": "600036 招商银行\n601318 中国平安\n",
    "watchlist/blacklist.txt": "300999 金龙鱼 (ST)\n002415 海康威视\n",
    "logs/old/trade_2025_01.txt": "1月份已归档",
    "logs/archive/2024_summary.txt": "全年盈利12%",
    "reports/weekly/week_20_summary.txt": "本周主线：机器人板块",
    "reports/monthly/may_review.txt": "五月回顾：连亏3次后强制停手",
    "config/broker_settings.txt": "券商：华泰证券\n账户：****1234\n",
    "notes/mindset.txt": "短线交易的核心不是选股，是纪律。",
    "templates/blank_log.txt": "日期：\n标的：\n买入价：\n卖出价：\n盈亏：\n买卖理由：\n复盘总结：\n",
}
for relpath, content in distractors.items():
    with open(os.path.join(workspace, relpath), "w", encoding="utf-8") as f:
        f.write(content)

# ── Main problem input: messy candidate stock CSV ─────────────────────────
# Fields: 代码, 名称, 流通市值(亿), 换手率(%), 今日涨停, 板块, 板块涨停数, 买点类型, 买入价, 信号强度
# Intentionally messy: mixed types, extra whitespace, some invalid/edge-case rows

candidates_raw = """\
代码,名称,流通市值(亿),换手率(%),今日涨停,板块,板块涨停数,买点类型,买入价,信号强度
300123 , 华立科技 , 85.3 , 8.7 , 是 , 卫星互联网 , 5 , 首板打板 , 22.50 , 强
 002456,天齐锂业, 420.0 ,12.1, 是 ,锂电池,4,二板确认,45.80,一般
300677,英科医疗,198.6,6.3,是,医疗器械,3,分歧转一致,31.20,强
688111,金山办公,950.0,3.2,否,国产软件,2,首板打板,280.00,弱
300859,三维天地,42.0,18.5,是,数字经济,4,首板打板,15.60,弱
000725,京东方A,750.0,4.8,是,半导体,5,二板确认,6.30,一般
300015,爱尔眼科,310.5,7.9,是,医疗服务,3,分歧转一致,18.90,一般
301088,戎美股份,55.2,11.3,是,卫星互联网,5,二板确认,38.40,强
300124,汇川技术,180.0,9.1,是,工业机器人,6,首板打板,55.70,强
002594,比亚迪,6800.0,2.1,否,新能源车,1,首板打板,220.00,弱
300450,先导智能,95.8,5.5,是,工业机器人,6,分歧转一致,28.30,强
 ,缺失代码,88.0,9.0,是,卫星互联网,5,首板打板,30.00,强
300999,金龙鱼,260.0,13.2,是,食品饮料,2,二板确认,55.00,强
"""

with open(os.path.join(workspace, "market_data/raw/candidates_today.csv"), "w", encoding="utf-8") as f:
    f.write(candidates_raw)

# ── Sector summary for context ────────────────────────────────────────────
sector_summary = """\
板块,今日涨停数,主力净流入(亿),板块描述
卫星互联网,5,12.3,国家低轨卫星政策加持，资金持续涌入
工业机器人,6,18.7,工信部发布机器人三年规划，题材爆发第二天
医疗器械,3,4.2,集采政策边际改善
锂电池,4,3.8,原材料价格反弹
医疗服务,3,2.1,消费复苏预期
国产软件,2,0.8,题材偏弱
半导体,5,9.1,美国芯片出口限制边际放松预期
新能源车,1,1.2,题材退潮
食品饮料,2,0.5,防御属性，非主流
数字经济,4,3.5,政策驱动但板块涨停数刚刚达标
"""
with open(os.path.join(workspace, "market_data/processed/sector_summary.csv"), "w", encoding="utf-8") as f:
    f.write(sector_summary)

# ── Today's date context file ─────────────────────────────────────────────
with open(os.path.join(workspace, "config/trading_date.txt"), "w", encoding="utf-8") as f:
    f.write("交易日期：2026-07-15\n账户总资产：500000\n")

print("Workspace generated successfully.")
print("Files created:")
for root, dirs_, files in os.walk(workspace):
    for fn in files:
        print(" ", os.path.join(root, fn).replace(workspace, ""))