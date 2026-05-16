import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(exist_ok=True)

# ── directory scaffold ──────────────────────────────────────────────────────
dirs = [
    "data/raw/xauusd",
    "data/raw/eurusd",
    "data/processed",
    "reports/archive",
    "reports/drafts",
    "scripts/indicators",
    "scripts/backtest",
    "configs",
    "logs",
    "notes",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "configs/trading_params.json": json.dumps({
        "instrument": "XAUUSD",
        "lot_size": 0.1,
        "max_drawdown_pct": 5,
        "session": "London",
        "risk_per_trade": 1.5
    }, indent=2),

    "configs/alert_config.yaml": "alerts:\n  - type: price\n    level: 1900\n    direction: above\n  - type: price\n    level: 1850\n    direction: below\n",

    "scripts/indicators/rsi.py": "# Placeholder RSI script\ndef rsi(closes, period=14):\n    pass\n",

    "scripts/indicators/ema.py": "# Placeholder EMA\ndef ema(closes, period=20):\n    pass\n",

    "scripts/backtest/runner.py": "# Backtest runner stub\nimport pandas as pd\n\ndef run_backtest(df, strategy):\n    return {}\n",

    "data/raw/eurusd/eurusd_1h_2024.csv": "datetime,open,high,low,close\n2024-01-02 08:00,1.0950,1.0975,1.0940,1.0965\n2024-01-02 09:00,1.0965,1.0980,1.0955,1.0970\n",

    "data/processed/xauusd_cleaned_old.csv": "datetime,open,high,low,close\n2023-06-01 00:00,1950.0,1962.0,1945.0,1958.0\n",

    "reports/archive/gold_report_q1_2024.txt": "Q1 2024 Gold Report\nOverall uptrend maintained. Key resistance at 2050.\nSupport held at 1980. No structural breaks observed.\n",

    "reports/drafts/template_structure.txt": "DRAFT TEMPLATE\n[Instrument] Analysis\n- Trend:\n- Key Levels:\n- Recommendation:\n",

    "logs/system.log": "2024-03-01 09:00:01 INFO  Feed connected\n2024-03-01 09:00:05 INFO  Subscribed XAUUSD\n2024-03-01 09:15:00 WARN  Latency spike 120ms\n",

    "notes/meeting_notes_2024_03.txt": "Committee meeting:\n- Discussed gold exposure\n- Risk team flagged USD strength\n- Decision: reduce position by 20%\n- Next review: 2024-04-01\n",

    "data/raw/xauusd/xauusd_daily_2023.csv": "datetime,open,high,low,close\n2023-01-02,1824.0,1839.5,1819.0,1835.0\n2023-01-03,1835.0,1855.0,1830.0,1848.0\n",
}

for rel_path, content in distractors.items():
    fpath = workspace / rel_path
    fpath.write_text(content)

# ── MAIN TASK INPUT: Synthetic XAUUSD 4H OHLC data ─────────────────────────
# Carefully engineered candle sequence to embed:
#   1. Bullish structure (HH + HL × 2) with two BOS events
#   2. A bullish Order Block (last bearish candle before impulse up) at candle index 4
#   3. A Fair Value Gap (candles 6-7-8) during the bullish impulse
#   4. Distribution range at the top (EQH forming at candles 13-14)
#   5. CHoCH: price breaks below the most recent HL (set at ~1920) at candle 17
#   6. Continued markdown with a bearish OB (last bullish candle before impulse down) at candle 16
#   7. Current price in DISCOUNT zone (below 50% of the most recent swing high ~1975 to swing low ~1890)
#
# Structure narrative:
#   - Candles 0-4: Initial range, accumulation, EQL building around 1895-1900
#   - Candle 5: BOS ↑ (breaks above swing high at 1910) → bullish impulse begins
#   - Candles 6-8: Strong bullish impulse with FVG between candle 6 high (1920) and candle 8 low (1928)
#     => FVG: C1 high=1920.5, C3 low=1928.0 — wait, FVG = C1 wick top and C3 wick bottom do NOT overlap
#     FVG bullish: gap between candle[i].high and candle[i+2].low  (C1.high < C3.low means gap exists)
#   - Candles 9-12: Markup, new HH at 1975, HL held at 1935
#   - Candles 13-15: Distribution, EQH forming ~1973-1975, bearish CHoCH setup
#   - Candle 16: Last bullish candle before impulse DOWN → Bearish OB body ~ 1960-1970
#   - Candle 17: BOS ↓ (breaks below HL at 1935) → this is actually CHoCH since HL was the Higher Low
#   - Candles 18-23: Markdown, price falling, LL forming at 1890
#   - Current (candle 23): price ~1898 → in discount zone (range 1975 high to 1890 low, 50%=1932.5, current 1898 < 1932.5)

candles = [
    # idx, datetime,          open,    high,    low,     close
    # Accumulation / initial range
    ( 0, "2024-03-01 00:00", 1900.0,  1910.5,  1892.0,  1895.0),   # Initial candle, low at 1892 (SSL)
    ( 1, "2024-03-01 04:00", 1895.0,  1908.0,  1890.0,  1905.0),   # LL formed at 1890 (EQL zone)
    ( 2, "2024-03-01 08:00", 1905.0,  1912.0,  1898.0,  1908.0),   # Minor bounce
    ( 3, "2024-03-01 12:00", 1908.0,  1915.0,  1902.0,  1906.0),   # Swing high at 1915, rejects
    ( 4, "2024-03-01 16:00", 1906.0,  1909.0,  1897.0,  1900.5),   # *** BULLISH OB: last bearish candle before impulse UP ***
                                                                      #   body: 1906 open, 1900.5 close (bearish body)
    # BOS ↑: impulse breaks above swing high at 1915
    ( 5, "2024-03-01 20:00", 1901.0,  1928.0,  1899.5,  1925.0),   # Strong bullish impulse, BOS ↑ above 1915
                                                                      # C1 of FVG: high=1928 → wait, let's build FVG in next 3
    # FVG setup: candles 5,6,7
    # FVG = C[5].high < C[7].low → gap exists (bullish FVG)
    # C[5].high = 1928.0, C[7].low must be > 1928.0
    ( 6, "2024-03-02 00:00", 1925.0,  1942.0,  1923.0,  1940.0),   # Middle candle of FVG (strong body)
    ( 7, "2024-03-02 04:00", 1940.0,  1952.0,  1930.5,  1948.0),   # C3 of FVG: low=1930.5 > C[5].high=1928.0 → FVG zone: 1928.0–1930.5
    # Continued markup
    ( 8, "2024-03-02 08:00", 1948.0,  1958.0,  1942.0,  1955.0),   # HL formed at 1942 (first HL)
    ( 9, "2024-03-02 12:00", 1955.0,  1965.0,  1950.0,  1962.0),   # BOS ↑ continuation above 1952
    (10, "2024-03-02 16:00", 1962.0,  1975.5,  1955.0,  1970.0),   # *** HH at 1975.5 ***
    (11, "2024-03-02 20:00", 1970.0,  1972.0,  1958.0,  1960.0),   # Pullback
    (12, "2024-03-03 00:00", 1960.0,  1968.0,  1935.0,  1963.0),   # HL at 1935 (second HL — most recent HL for CHoCH)
    # Distribution / EQH forming
    (13, "2024-03-03 04:00", 1963.0,  1975.0,  1958.0,  1971.0),   # EQH approaching 1975 → near HH
    (14, "2024-03-03 08:00", 1971.0,  1974.5,  1962.0,  1965.0),   # EQH confirmed (1975-1974.5 range = equal highs)
    (15, "2024-03-03 12:00", 1965.0,  1969.0,  1957.0,  1962.0),   # Consolidation
    # Bearish OB setup
    (16, "2024-03-03 16:00", 1962.0,  1971.0,  1958.0,  1968.5),   # *** BEARISH OB: last bullish candle before impulse DOWN ***
                                                                      #   body: 1962 open, 1968.5 close (bullish body)
    # CHoCH: breaks BELOW the most recent HL at 1935
    (17, "2024-03-03 20:00", 1968.5,  1970.0,  1925.0,  1928.0),   # *** CHoCH: breaks below HL at 1935 → shift to bearish ***
    # Markdown
    (18, "2024-03-04 00:00", 1928.0,  1933.5,  1910.0,  1912.0),   # BOS ↓ below 1928 area, continuation
    (19, "2024-03-04 04:00", 1912.0,  1920.0,  1902.0,  1905.0),   # LH forming at 1920
    (20, "2024-03-04 08:00", 1905.0,  1908.0,  1892.0,  1895.5),   # LL forming, approaching SSL
    (21, "2024-03-04 12:00", 1895.5,  1905.5,  1888.0,  1900.0),   # Sweep of SSL at 1888 (liquidity sweep below EQL 1890)
    (22, "2024-03-04 16:00", 1900.0,  1910.0,  1895.0,  1897.0),   # LH at 1910, stays below structure
    (23, "2024-03-04 20:00", 1897.0,  1903.5,  1890.5,  1898.0),   # Current candle: price 1898 — DISCOUNT zone
]

import csv

ohlc_path = workspace / "data/raw/xauusd/xauusd_4h_march2024.csv"
with open(ohlc_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["index", "datetime", "open", "high", "low", "close"])
    for row in candles:
        writer.writerow(row)

print(f"[✓] Generated OHLC data: {ohlc_path} ({len(candles)} candles)")
print(f"[✓] Generated {len(distractors)} distractor files")
print(f"[✓] Workspace structure ready at {workspace}")

# Print key structural facts for reference (not stored in workspace)
print("\n=== STRUCTURAL GROUND TRUTH (for test design only) ===")
print("Bullish OB: candle 4, body range open=1906.0 close=1900.5 (bearish body, last before impulse up)")
print("FVG bullish: candle[5].high=1928.0 to candle[7].low=1930.5 → zone 1928.0–1930.5")
print("BOS ↑: candle 5 (breaks above swing high 1915)")
print("BOS ↑: candle 9 (continuation)")
print("HH: candle 10 at 1975.5")
print("Most recent HL (before CHoCH): candle 12 at 1935.0")
print("EQH: candles 10 and 13 (~1975)")
print("Bearish OB: candle 16, body range open=1962.0 close=1968.5 (bullish body, last before impulse down)")
print("CHoCH: candle 17 breaks below HL at 1935")
print("Range for Premium/Discount: HH=1975.5 (candle 10), recent swing low=1890.5 (candle 23)")
print("  OR swing high=1975.5 to pre-CHoCH swing low=1890.0 (candle 1/21)")
print("Equilibrium: (1975.5 + 1888.0) / 2 = 1931.75")
print("Current price 1898 < 1931.75 → DISCOUNT")
print("Phase: Markdown (after CHoCH + BOS ↓)")
print("SSL: below 1888–1890 (EQL from candles 1,21)")
print("BSL: above 1975.5 (HH) or EQH ~1975")