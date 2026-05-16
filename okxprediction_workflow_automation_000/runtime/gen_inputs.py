import os
import json
import csv
import random
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# --- Create realistic directory structure with distractor files ---
dirs = [
    "market_data/candles",
    "market_data/sentiment",
    "market_data/liquidations",
    "reports/archive",
    "reports/drafts",
    "config",
    "risk_management",
    "logs",
    "scripts",
    "analysis/deprecated",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# --- DISTRACTOR FILES ---

# Config files
with open(workspace / "config/trading_params.json", "w") as f:
    json.dump({
        "max_leverage": 10,
        "base_currency": "USDT",
        "pair": "BTC-USDT-SWAP",
        "risk_per_trade": 0.01,
        "cooldown_minutes": 15
    }, f, indent=2)

with open(workspace / "config/exchange_settings.cfg", "w") as f:
    f.write("[okx]\nenv=paper\ntimeout=30\nretry=3\n")

# Old reports
with open(workspace / "reports/archive/signal_2024_01_15.json", "w") as f:
    json.dump({"direction": "long", "score": 75, "signal": "watch", "entry_type": "pullback",
               "stop_loss": "41200", "target": "43500", "reason": "old archived signal"}, f, indent=2)

with open(workspace / "reports/archive/signal_2024_02_03.json", "w") as f:
    json.dump({"direction": "short", "score": 55, "signal": "no_trade", "entry_type": "none",
               "stop_loss": "none", "target": "none", "reason": "structure unclear"}, f, indent=2)

with open(workspace / "reports/drafts/draft_template.txt", "w") as f:
    f.write("Draft signal template - DO NOT USE\nFields: direction, score, signal, entry_type, stop_loss, target, reason\n")

# Risk management
with open(workspace / "risk_management/position_limits.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(["tier", "max_position_btc", "max_loss_usdt"])
    writer.writerows([["A", 2.0, 5000], ["B", 1.0, 2500], ["C", 0.5, 1000]])

with open(workspace / "risk_management/drawdown_log.txt", "w") as f:
    f.write("2024-01-15: -1200 USDT\n2024-02-03: +3400 USDT\n2024-03-21: -800 USDT\n")

# Logs
with open(workspace / "logs/system.log", "w") as f:
    f.write("[INFO] 2024-06-01 08:00:00 - Market feed connected\n")
    f.write("[INFO] 2024-06-01 08:00:05 - Candle stream initialized\n")
    f.write("[WARN] 2024-06-01 08:01:22 - Funding rate feed latency: 250ms\n")
    f.write("[INFO] 2024-06-01 08:05:00 - Snapshot complete\n")

with open(workspace / "logs/trades.log", "w") as f:
    f.write("2024-05-30 14:22:00 | LONG | BTC | Entry: 67800 | Exit: 69100 | PnL: +1300\n")
    f.write("2024-05-31 09:15:00 | SHORT | BTC | Entry: 68500 | Exit: 67200 | PnL: +1300\n")

# Scripts (distractor)
with open(workspace / "scripts/fetch_data.sh", "w") as f:
    f.write("#!/bin/bash\n# Fetches live market data - not needed for offline analysis\necho 'Live fetch not available in offline mode'\n")

with open(workspace / "scripts/backtest_runner.py", "w") as f:
    f.write("# Backtesting runner - not related to current signal generation\nprint('Backtest module placeholder')\n")

with open(workspace / "analysis/deprecated/old_scoring_v1.py", "w") as f:
    f.write("# OLD SCORING SYSTEM - DEPRECATED\n# score = direction*10 + structure*10 + momentum*5\n# DO NOT USE\n")

with open(workspace / "analysis/deprecated/notes.txt", "w") as f:
    f.write("Old v1 scoring used 5 layers. Current system uses 6 layers. See SKILL.md.\n")


# =====================================================================
# ACTUAL MARKET DATA - The agent must analyze these
# =====================================================================

# --- 1D Candles (last 10 days) - Clear UPTREND: higher highs + higher lows ---
# Price consistently rising, above 20-MA
daily_candles = [
    {"ts": "2024-05-22", "open": 64800, "high": 66200, "low": 64500, "close": 65900, "vol": 12500},
    {"ts": "2024-05-23", "open": 65900, "high": 67100, "low": 65600, "close": 66800, "vol": 13200},
    {"ts": "2024-05-24", "open": 66800, "high": 68000, "low": 66400, "close": 67500, "vol": 11800},
    {"ts": "2024-05-25", "open": 67500, "high": 68900, "low": 67200, "close": 68600, "vol": 14100},
    {"ts": "2024-05-26", "open": 68600, "high": 69500, "low": 68100, "close": 68900, "vol": 10900},
    {"ts": "2024-05-27", "open": 68900, "high": 70200, "low": 68700, "close": 69800, "vol": 15600},
    {"ts": "2024-05-28", "open": 69800, "high": 71000, "low": 69500, "close": 70400, "vol": 16200},
    {"ts": "2024-05-29", "open": 70400, "high": 71800, "low": 70100, "close": 71200, "vol": 13800},
    {"ts": "2024-05-30", "open": 71200, "high": 72500, "low": 70900, "close": 72000, "vol": 17100},
    {"ts": "2024-05-31", "open": 72000, "high": 73200, "low": 71800, "close": 72800, "vol": 14700},
]
# 20-day SMA of close would be ~69200; current close 72800 >> above MA
with open(workspace / "market_data/candles/btc_1d.json", "w") as f:
    json.dump(daily_candles, f, indent=2)

# --- 1H Candles (last 24 hours) - UPTREND confirmed: higher highs + higher lows ---
hourly_candles = []
base_price = 72000
for i in range(24):
    # Simulate upward drift with noise
    open_p = base_price + i * 35 + random.randint(-30, 30)
    close_p = open_p + random.randint(10, 60)
    high_p = close_p + random.randint(20, 80)
    low_p = open_p - random.randint(10, 40)
    hourly_candles.append({
        "ts": f"2024-05-31T{i:02d}:00:00Z",
        "open": round(open_p, 0),
        "high": round(high_p, 0),
        "low": round(low_p, 0),
        "close": round(close_p, 0),
        "vol": random.randint(800, 1600)
    })
# Ensure clear higher highs and higher lows pattern
# Override some key candles for clarity
hourly_candles[0] = {"ts": "2024-05-31T00:00:00Z", "open": 72000, "high": 72380, "low": 71850, "close": 72200, "vol": 1100}
hourly_candles[6] = {"ts": "2024-05-31T06:00:00Z", "open": 72400, "high": 72750, "low": 72300, "close": 72600, "vol": 1250}
hourly_candles[12] = {"ts": "2024-05-31T12:00:00Z", "open": 72700, "high": 73100, "low": 72580, "close": 72950, "vol": 1400}
hourly_candles[18] = {"ts": "2024-05-31T18:00:00Z", "open": 73000, "high": 73450, "low": 72880, "close": 73250, "vol": 1350}
hourly_candles[23] = {"ts": "2024-05-31T23:00:00Z", "open": 73300, "high": 73800, "low": 73150, "close": 73600, "vol": 1550}
# EMA20 on 1H is approximately 72600; current close 73600 → price above MA
with open(workspace / "market_data/candles/btc_1h.json", "w") as f:
    json.dump(hourly_candles, f, indent=2)

# --- 4H Candles - TREND: EMA clearly aligned ---
candles_4h = [
    {"ts": "2024-05-29T00:00:00Z", "open": 70400, "high": 71200, "low": 70200, "close": 70900, "ema9": 70200, "ema21": 69800, "ema55": 68900, "vol": 4200},
    {"ts": "2024-05-29T04:00:00Z", "open": 70900, "high": 71600, "low": 70700, "close": 71400, "ema9": 70600, "ema21": 70100, "ema55": 69200, "vol": 3900},
    {"ts": "2024-05-29T08:00:00Z", "open": 71400, "high": 72100, "low": 71200, "close": 71900, "ema9": 71000, "ema21": 70500, "ema55": 69600, "vol": 4600},
    {"ts": "2024-05-29T12:00:00Z", "open": 71900, "high": 72600, "low": 71700, "close": 72300, "ema9": 71500, "ema21": 70900, "ema55": 69900, "vol": 5100},
    {"ts": "2024-05-29T16:00:00Z", "open": 72300, "high": 73000, "low": 72100, "close": 72700, "ema9": 71900, "ema21": 71300, "ema55": 70200, "vol": 4800},
    {"ts": "2024-05-29T20:00:00Z", "open": 72700, "high": 73400, "low": 72500, "close": 73100, "ema9": 72300, "ema21": 71700, "ema55": 70600, "vol": 5300},
    # EMA9 > EMA21 > EMA55 → clear bullish alignment
    {"ts": "2024-05-30T00:00:00Z", "open": 73100, "high": 73800, "low": 72900, "close": 73500, "ema9": 72800, "ema21": 72100, "ema55": 71000, "vol": 5600},
    {"ts": "2024-05-30T04:00:00Z", "open": 73500, "high": 74100, "low": 73300, "close": 73900, "ema9": 73200, "ema21": 72500, "ema55": 71400, "vol": 4900},
]
with open(workspace / "market_data/candles/btc_4h.json", "w") as f:
    json.dump(candles_4h, f, indent=2)

# --- 15M Candles - TREND structure with sustained higher highs ---
candles_15m = []
price_15m = 73200
for i in range(32):  # last 8 hours
    open_p = price_15m + i * 12 + random.randint(-8, 8)
    close_p = open_p + random.randint(5, 25)
    high_p = close_p + random.randint(10, 30)
    low_p = open_p - random.randint(5, 15)
    candles_15m.append({
        "ts": f"2024-05-31T{15 + i // 4:02d}:{(i % 4) * 15:02d}:00Z",
        "open": round(open_p, 0),
        "high": round(high_p, 0),
        "low": round(low_p, 0),
        "close": round(close_p, 0),
        "vol": random.randint(200, 500)
    })
# Ensure EMA9 > EMA21 → trending structure note in metadata
with open(workspace / "market_data/candles/btc_15m.json", "w") as f:
    json.dump(candles_15m, f, indent=2)

# --- 5M Candles - Price at SUPPORT, pullback holding (good position layer) ---
# Support zone around 73100-73200; price just bounced off that zone
candles_5m = [
    {"ts": "2024-05-31T23:00:00Z", "open": 73600, "high": 73750, "low": 73500, "close": 73650, "vol": 180},
    {"ts": "2024-05-31T23:05:00Z", "open": 73650, "high": 73700, "low": 73180, "close": 73220, "vol": 320},  # pullback to support
    {"ts": "2024-05-31T23:10:00Z", "open": 73220, "high": 73350, "low": 73150, "close": 73300, "vol": 280},  # holding support
    {"ts": "2024-05-31T23:15:00Z", "open": 73300, "high": 73420, "low": 73200, "close": 73380, "vol": 240},  # bounce starting
    {"ts": "2024-05-31T23:20:00Z", "open": 73380, "high": 73480, "low": 73320, "close": 73440, "vol": 210},
    {"ts": "2024-05-31T23:25:00Z", "open": 73440, "high": 73520, "low": 73380, "close": 73490, "vol": 195},
    {"ts": "2024-05-31T23:30:00Z", "open": 73490, "high": 73580, "low": 73420, "close": 73550, "vol": 220},
    {"ts": "2024-05-31T23:35:00Z", "open": 73550, "high": 73620, "low": 73480, "close": 73590, "vol": 205},
    {"ts": "2024-05-31T23:40:00Z", "open": 73590, "high": 73680, "low": 73520, "close": 73640, "vol": 215},
    {"ts": "2024-05-31T23:45:00Z", "open": 73640, "high": 73710, "low": 73570, "close": 73680, "vol": 198},
    {"ts": "2024-05-31T23:50:00Z", "open": 73680, "high": 73740, "low": 73610, "close": 73720, "vol": 210},
    {"ts": "2024-05-31T23:55:00Z", "open": 73720, "high": 73800, "low": 73650, "close": 73760, "vol": 225},
]
# Support at ~73150 held; price above support → valid long position
with open(workspace / "market_data/candles/btc_5m.json", "w") as f:
    json.dump(candles_5m, f, indent=2)

# --- 1M Candles - THE TRAP: No higher low formed, NO valid trigger ---
# For a long trigger: need "更高低点形成 + 突破并站稳" (higher low + breakout and hold)
# Here: last few 1M candles show choppy action, low at 73640, previous low at 73650 → LOWER low (not higher)
# No breakout confirmed → trigger layer = NONE → score_trigger = 0
candles_1m = [
    {"ts": "2024-05-31T23:50:00Z", "open": 73720, "high": 73760, "low": 73680, "close": 73750, "vol": 62},
    {"ts": "2024-05-31T23:51:00Z", "open": 73750, "high": 73790, "low": 73700, "close": 73720, "vol": 58},
    {"ts": "2024-05-31T23:52:00Z", "open": 73720, "high": 73740, "low": 73650, "close": 73670, "vol": 71},  # low drops
    {"ts": "2024-05-31T23:53:00Z", "open": 73670, "high": 73720, "low": 73640, "close": 73700, "vol": 65},  # lower low (73640 < 73650)
    {"ts": "2024-05-31T23:54:00Z", "open": 73700, "high": 73740, "low": 73660, "close": 73710, "vol": 59},
    {"ts": "2024-05-31T23:55:00Z", "open": 73710, "high": 73750, "low": 73670, "close": 73720, "vol": 63},
    {"ts": "2024-05-31T23:56:00Z", "open": 73720, "high": 73760, "low": 73680, "close": 73740, "vol": 57},
    {"ts": "2024-05-31T23:57:00Z", "open": 73740, "high": 73770, "low": 73690, "close": 73750, "vol": 61},
    {"ts": "2024-05-31T23:58:00Z", "open": 73750, "high": 73780, "low": 73700, "close": 73730, "vol": 68},
    {"ts": "2024-05-31T23:59:00Z", "open": 73730, "high": 73760, "low": 73700, "close": 73740, "vol": 55},
]
# No clear higher low formed, no confirmed breakout above prior swing high
# Lows sequence: 73680, 73700, 73650, 73640, 73660, 73670 → declining lows = NO higher low pattern
with open(workspace / "market_data/candles/btc_1m.json", "w") as f:
    json.dump(candles_1m, f, indent=2)

# --- Sentiment Data ---
# Funding rate: 0.005 → between -0.01 and 0.01 → NEUTRAL (not over/underheated)
# Long/short ratio: 62% long → below 70% threshold → NEUTRAL
sentiment_data = {
    "timestamp": "2024-05-31T23:59:00Z",
    "pair": "BTC-USDT-SWAP",
    "funding_rate": {
        "current": 0.005,
        "next_settlement": "2024-06-01T00:00:00Z",
        "8h_rate": 0.005,
        "annualized": 0.219
    },
    "long_short_ratio": {
        "long_pct": 62.3,
        "short_pct": 37.7,
        "source": "top_trader_positions",
        "snapshot_time": "2024-05-31T23:55:00Z"
    },
    "open_interest": {
        "value_usd": 8420000000,
        "change_24h_pct": 3.2
    }
}
# Note: funding 0.005 = neutral; long 62.3% = neutral → sentiment layer is NEUTRAL
# For scoring: neither bullish nor bearish sentiment confirmation → partial or 0?
# SKILL.md says sentiment layer max=15. Neutral means neither of the threshold conditions met.
# A careful agent should score sentiment as 0 (no confirmation) or partial.
# We'll document that: funding neutral (0.005 in [-0.01, 0.01]) = no sentiment signal
# long pct 62.3% < 70% threshold = no sentiment signal
# Sentiment score = 0 (no confirmatory signal for either direction)
with open(workspace / "market_data/sentiment/funding_and_ratio.json", "w") as f:
    json.dump(sentiment_data, f, indent=2)

# --- Liquidation Data ---
# Cluster of longs around 74800-75200 (above current price 73760)
# Makes sense as a target for a long trade
liquidation_data = {
    "timestamp": "2024-05-31T23:59:00Z",
    "pair": "BTC-USDT-SWAP",
    "clusters": [
        {
            "type": "short_liquidations",
            "price_zone": "74800-75200",
            "estimated_volume_usd": 185000000,
            "density": "high",
            "notes": "High density of short positions that would liquidate in this zone"
        },
        {
            "type": "long_liquidations",
            "price_zone": "71000-71500",
            "estimated_volume_usd": 142000000,
            "density": "medium",
            "notes": "Long liquidation cluster below current price - acts as downside magnet"
        }
    ],
    "current_price": 73760,
    "analysis_note": "Price likely to target short liquidation zone at 74800-75200 if bullish momentum continues"
}
# Liquidity target identified (74800-75200) → score_liquidity = 15
with open(workspace / "market_data/liquidations/btc_liq_clusters.json", "w") as f:
    json.dump(liquidation_data, f, indent=2)

# --- Market metadata file (distractor with some useful context) ---
with open(workspace / "market_data/metadata.json", "w") as f:
    json.dump({
        "data_source": "OKX Derivatives",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "contract_type": "perpetual_swap",
        "data_snapshot_time": "2024-05-31T23:59:00Z",
        "timeframes_available": ["1m", "5m", "15m", "1h", "4h", "1d"],
        "notes": "All candle data is historical. Use SKILL.md methodology for analysis."
    }, f, indent=2)

# --- Additional distractor: partial analysis notes that are WRONG ---
with open(workspace / "analysis/deprecated/analyst_notes_v1.txt", "w") as f:
    f.write("OUTDATED ANALYSIS (DO NOT USE)\n")
    f.write("Quick score estimate (old method): direction=10, structure=10, momentum=5, sentiment=5 → total=30\n")
    f.write("Old threshold: >25 = execute. THIS IS DEPRECATED.\n")
    f.write("See new SKILL.md for current scoring methodology.\n")

print("Workspace setup complete.")
print(f"Files created in {workspace}")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")