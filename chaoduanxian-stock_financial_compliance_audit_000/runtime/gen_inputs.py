import os
import json
import random
import csv

random.seed(42)

WORKSPACE = "/workspace"

# Create directory structure with distractors
dirs = [
    "trading_desk/reports/2024",
    "trading_desk/raw_data/ticks",
    "trading_desk/raw_data/daily",
    "trading_desk/strategy/params",
    "trading_desk/logs/system",
    "trading_desk/logs/orders",
    "archive/2023/q4",
    "archive/2023/q3",
    "config/backtest",
    "config/live",
    "docs/internal",
]
for d in dirs:
    os.makedirs(os.path.join(WORKSPACE, d), exist_ok=True)

# Distractor files
distractor_files = [
    ("trading_desk/strategy/params/macd_params.json", json.dumps({"fast": 12, "slow": 26, "signal": 9})),
    ("trading_desk/strategy/params/kdj_params.json", json.dumps({"period": 9, "m1": 3, "m2": 3})),
    ("trading_desk/logs/system/system_2024_05_01.log", "INFO: System started\nINFO: Market connected\nINFO: Feed alive"),
    ("trading_desk/logs/system/system_2024_05_02.log", "INFO: System started\nWARN: Latency spike detected\nINFO: Feed alive"),
    ("config/backtest/settings.json", json.dumps({"start": "2024-01-01", "end": "2024-03-31", "capital": 1000000})),
    ("config/live/settings.json", json.dumps({"broker": "mock", "account": "SIM001", "capital": 500000})),
    ("archive/2023/q4/summary.txt", "Q4 2023: Total trades 382, Win rate 54.2%, Net PnL: +8.3%"),
    ("archive/2023/q3/summary.txt", "Q3 2023: Total trades 291, Win rate 49.8%, Net PnL: -2.1%"),
    ("docs/internal/risk_memo.txt", "Risk memo: All traders must adhere to position limits. See compliance handbook."),
    ("trading_desk/raw_data/ticks/tick_sample.csv", "time,price,volume\n09:30:00,12.50,10000\n09:30:01,12.52,500"),
    ("trading_desk/reports/2024/monthly_summary.txt", "May 2024: 12 trading days, average daily turnover 3.2M"),
]
for rel_path, content in distractor_files:
    with open(os.path.join(WORKSPACE, rel_path), "w", encoding="utf-8") as f:
        f.write(content)

# === MAIN TASK INPUT ===
# Trading log: a week of trades with messy data
# Total capital: 500,000 CNY
# Fields: date, stock_code, stock_name, buy_price, current_price, position_value, turnover_rate, consecutive_limit_up, board_type, day_limit_up_count, day_board_break_count

TOTAL_CAPITAL = 500000

# We will create a messy CSV trading log
# Some entries will violate rules, some won't
# board_type: 首板, 连板, 反包, 跟风
# consecutive_limit_up: number of consecutive limit-up days (龙头 needs >=3)
# turnover_rate: % (龙头 needs 5-15%)
# position_value: CNY value held in this stock
# pnl_pct: current profit/loss percentage on the position

trades = [
    # date, stock_code, stock_name, buy_price, current_price, position_value, turnover_rate, consecutive_limit_up, board_type, day_limit_up_count, day_board_break_count, notes
    # Day 1: 2024-05-06 - Market warming up (启动期): few limit-ups, few breaks
    ("2024-05-06", "600001", "华东科技", 10.00, 10.70,  45000, 7.2,  1, "首板",  5,  1, "normal"),
    ("2024-05-06", "600002", "北方材料", 8.00,  7.44,   55000, 3.1,  1, "首板",  5,  1, "stop_loss_needed"),  # -7% exactly
    ("2024-05-06", "600003", "南方能源", 15.00, 13.80,  80000, 2.5,  0, "跟风",  5,  1, "overweight"),  # position too large >10% of 500k=50k, 80k is violation
    # Day 2: 2024-05-07 - High tide (高潮期): many limit-ups, few breaks
    ("2024-05-07", "600004", "东海芯片", 20.00, 23.00,  48000, 8.5,  3, "连板",  18, 2, "normal"),   # consecutive>=3, turnover 5-15% -> 龙头
    ("2024-05-07", "600005", "西部钢铁", 12.00, 13.80,  50000, 6.3,  4, "连板",  18, 2, "normal"),   # 龙头 candidate
    ("2024-05-07", "600006", "中原化工", 9.00,  9.63,   30000, 9.1,  1, "首板",  18, 2, "normal"),
    ("2024-05-07", "600007", "泰达物流", 6.00,  6.90,   90000, 4.2,  2, "连板",  18, 2, "overweight"),  # 90k > 50k limit violation
    # Day 3: 2024-05-08 - Tide retreating (退潮期): board breaks increasing
    ("2024-05-08", "600008", "赤峰黄金", 30.00, 28.20,  52000, 11.2, 3, "连板",  8,  9, "stop_loss_needed"),  # -6% close to but not at -7%
    ("2024-05-08", "600009", "蓝天传媒", 5.00,  4.65,   25000, 2.3,  0, "跟风",  8,  9, "stop_loss_needed"),  # -7% exactly, must stop
    ("2024-05-08", "600010", "紫光半导", 22.00, 22.00,  44000, 13.5, 5, "连板",  8,  9, "normal"),   # 龙头 (>=3 consec, 5-15% turnover)
    ("2024-05-08", "600011", "鸿运地产", 18.00, 20.70,  50000, 1.2,  1, "首板",  8,  9, "take_profit_partial"),  # +15% -> sell remaining half
    # Day 4: 2024-05-09 - Ice point (冰点期): almost no limit-ups, many breaks
    ("2024-05-09", "600012", "银河科技", 11.00, 10.23,  35000, 5.5,  0, "跟风",  2,  14, "stop_loss_needed"),  # -7%
    ("2024-05-09", "600013", "海通机械", 7.50,  8.025,  40000, 16.3, 1, "首板",  2,  14, "normal"),   # turnover >15%, not 龙头 range
    ("2024-05-09", "600014", "锦州港口", 25.00, 26.75,  50000, 7.8,  3, "反包",  2,  14, "take_profit_partial"),  # +7% sell half
    # Day 5: 2024-05-10 - Back to warming (启动期): moderate
    ("2024-05-10", "600015", "渤海钻探", 14.00, 16.10,  45000, 6.1,  2, "连板",  6,  3, "take_profit_full"),  # +15% -> second half out
    ("2024-05-10", "600016", "天山水泥", 9.00,  8.28,   28000, 4.5,  0, "跟风",  6,  3, "stop_loss_needed"),  # -8%, beyond -7%, violation if not stopped
    ("2024-05-10", "600017", "国电电力", 33.00, 33.99,  49500, 12.1, 4, "连板",  6,  3, "normal"),   # 龙头
]

# Also: daily cumulative position check
# On 2024-05-07: positions 48000+50000+30000+90000 = 218000 > 30% of 500k (150k) — daily overweight

# Write the main trading log
fieldnames = [
    "date", "stock_code", "stock_name", "buy_price", "current_price",
    "position_value", "turnover_rate_pct", "consecutive_limit_up",
    "board_type", "day_limit_up_count", "day_board_break_count", "internal_note"
]

log_path = os.path.join(WORKSPACE, "trading_desk/raw_data/daily/weekly_trading_log.csv")
with open(log_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for row in trades:
        writer.writerow({
            "date": row[0],
            "stock_code": row[1],
            "stock_name": row[2],
            "buy_price": row[3],
            "current_price": row[4],
            "position_value": row[5],
            "turnover_rate_pct": row[6],
            "consecutive_limit_up": row[7],
            "board_type": row[8],
            "day_limit_up_count": row[9],
            "day_board_break_count": row[10],
            "internal_note": row[11],
        })

# Write total capital config
capital_path = os.path.join(WORKSPACE, "trading_desk/raw_data/daily/account_capital.json")
with open(capital_path, "w", encoding="utf-8") as f:
    json.dump({"total_capital": TOTAL_CAPITAL, "currency": "CNY"}, f, indent=2)

print("Workspace generated successfully.")
print(f"Total capital: {TOTAL_CAPITAL}")
print(f"Trading log: {log_path}")