import os
import json
import random
import numpy as np
import pandas as pd
from pathlib import Path

random.seed(42)
np.random.seed(42)

WORKSPACE = Path("/workspace")

# ── directory scaffold (distractor files) ──────────────────────────────────
dirs = [
    "data/raw/candles",
    "data/raw/orderbook",
    "data/processed",
    "models/backtest",
    "models/live",
    "config",
    "logs",
    "reports/daily",
    "reports/weekly",
    "scripts/utils",
    "scripts/ingest",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# distractor files
distractor_files = {
    "config/exchange_config.yaml": "exchange: binance\napi_key: PLACEHOLDER\nsecret: PLACEHOLDER\n",
    "config/risk_params.yaml": "max_drawdown: 0.15\nposition_size_pct: 0.02\n",
    "config/watchlist.txt": "BTC\nETH\nSOL\nXRP\nADA\n",
    "logs/system.log": "[INFO] 2024-06-01 12:00:00 - System started\n[WARN] 2024-06-01 12:01:00 - High latency\n",
    "logs/errors.log": "[ERROR] 2024-05-30 - Failed to fetch candle data for ATOM\n",
    "models/backtest/btc_backtest_2024.csv": "date,pnl\n2024-01-01,120.5\n2024-01-02,-34.2\n",
    "models/live/model_v2.txt": "model_type: gradient_boosting\nfeatures: [rsi, macd, obv]\n",
    "scripts/utils/helpers.py": "# utility helpers\ndef clamp(x, lo, hi): return max(lo, min(hi, x))\n",
    "scripts/ingest/fetch_candles.py": "# fetch candles from exchange\nimport requests\ndef fetch(symbol, interval): pass\n",
    "reports/daily/report_2024_05_31.txt": "Daily PnL: +$340\nOpen positions: 2\n",
    "reports/weekly/week22_summary.txt": "Week 22 net: +$1,200\nWin rate: 62%\n",
    "data/raw/orderbook/btc_ob_snapshot.json": json.dumps({"bids": [[30000, 1.2]], "asks": [[30010, 0.8]]}),
}
for rel_path, content in distractor_files.items():
    (WORKSPACE / rel_path).write_text(content)


# ── helper: generate synthetic OHLCV candles ──────────────────────────────
def make_candles(n=220, start_price=100.0, trend="up", noise=0.015, seed=0):
    """Generate n hourly OHLCV candles with a controlled trend."""
    rng = np.random.default_rng(seed)
    prices = [start_price]
    for _ in range(n - 1):
        drift = 0.003 if trend == "up" else -0.003 if trend == "down" else 0.0
        r = drift + rng.normal(0, noise)
        prices.append(max(prices[-1] * (1 + r), 0.01))
    prices = np.array(prices)
    opens = prices
    closes = prices * (1 + rng.normal(0, 0.005, n))
    highs = np.maximum(opens, closes) * (1 + rng.uniform(0.001, 0.008, n))
    lows = np.minimum(opens, closes) * (1 - rng.uniform(0.001, 0.008, n))
    volume = rng.uniform(500, 2000, n)
    # Spike volume on last candle to signal "high volume on move"
    volume[-1] = volume[-1] * 3.5

    df = pd.DataFrame({
        "open": np.round(opens, 4),
        "high": np.round(highs, 4),
        "low": np.round(lows, 4),
        "close": np.round(closes, 4),
        "volume": np.round(volume, 2),
    })
    return df


# ── Asset definitions ───────────────────────────────────────────────────────
# We create 3 assets with carefully crafted candle data so that
# the final momentum score is deterministic and verifiable.
#
# ASSET 1: SOL  — strong bullish momentum, counter-consensus opportunity
#   Trend: clearly upward for 220 candles → RSI will be >50 (neutral, not oversold)
#   We engineer: EMA20>EMA50, price>EMA200, OBV rising, volume spike, MACD bullish
#   Polymarket: DOWN 80%  → counter-consensus BET UP
#
# ASSET 2: XRP  — moderate bearish momentum
#   Trend: clearly downward → bearish signals
#   Polymarket: UP 65%  → edge check but NOT counter-consensus (UP not >70%)
#
# ASSET 3: ATOM — near-neutral, no trade signal
#   Mixed signals → abs(score) < 3
#   Polymarket: UP 55%

assets = {
    "SOL":  {"trend": "up",   "start": 150.0,  "seed": 7,  "market_up": 0.20},
    "XRP":  {"trend": "down", "start": 0.60,   "seed": 13, "market_up": 0.65},
    "ATOM": {"trend": "flat", "start": 8.50,   "seed": 99, "market_up": 0.55},
}

candle_dir = WORKSPACE / "data" / "raw" / "candles"
for symbol, cfg in assets.items():
    df = make_candles(n=220, start_price=cfg["start"], trend=cfg["trend"],
                      noise=0.012, seed=cfg["seed"])
    df.to_csv(candle_dir / f"{symbol}_1h_candles.csv", index=False)
    print(f"  Written {symbol} candles: {len(df)} rows, close[-1]={df['close'].iloc[-1]:.4f}")

# ── Polymarket odds file ────────────────────────────────────────────────────
polymarket_odds = {
    "SOL":  {"market_up": 0.20, "market_down": 0.80, "market_id": "sol_4pm_et", "age_minutes": 12},
    "XRP":  {"market_up": 0.65, "market_down": 0.35, "market_id": "xrp_4pm_et", "age_minutes": 25},
    "ATOM": {"market_up": 0.55, "market_down": 0.45, "market_id": "atom_4pm_et", "age_minutes": 8},
}
(WORKSPACE / "data" / "raw" / "polymarket_odds.json").write_text(
    json.dumps(polymarket_odds, indent=2)
)

# ── Task description ────────────────────────────────────────────────────────
task_brief = (
    "Analyze the hourly candle data in data/raw/candles/ and the Polymarket odds "
    "in data/raw/polymarket_odds.json.  "
    "For each asset produce a full momentum signal report and save the combined "
    "output to reports/momentum_signals.json.\n"
    "Each asset entry must include: asset, score, rsi, rsi_status, macd_hist, "
    "macd_direction, obv_trend, bb_pct, ema_cross, bias, confidence_pct, and a "
    "polymarket_edge sub-object that shows market_up, our_p, edge, and direction. "
    "Also include a top-level 'bets' list that contains only the assets where a "
    "valid bet exists AND the setup is counter-consensus (L023)."
)
(WORKSPACE / "TASK.txt").write_text(task_brief)

print("\nWorkspace ready.")
print("Assets:", list(assets.keys()))
print("Polymarket odds file:", WORKSPACE / "data" / "raw" / "polymarket_odds.json")