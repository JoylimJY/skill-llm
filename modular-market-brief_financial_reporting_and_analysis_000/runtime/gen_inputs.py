import os
import random
import json
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")
WORKSPACE.mkdir(exist_ok=True)

# ── 1. Directory structure with distractor files ──────────────────────────────
dirs = [
    "scripts",
    "data/raw",
    "data/processed",
    "data/cache",
    "config",
    "reports/archive",
    "reports/drafts",
    "logs",
    "notebooks",
    "tools/helpers",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# Distractor files
distractor_files = {
    "config/regions.json": json.dumps({"regions": ["US", "EU", "Asia"], "default": "US"}, indent=2),
    "config/tickers_legacy.csv": "ticker,name\nAAPL,Apple\nGOOGL,Alphabet\nMSFT,Microsoft",
    "config/risk_profile.yaml": "risk_appetite: conservative\nmax_drawdown: 0.05\nvolatility_budget: 0.12",
    "data/raw/prices_stale.csv": "date,open,high,low,close\n2023-01-01,100,105,99,103\n2023-01-02,103,107,101,106",
    "data/raw/fx_snapshot.json": json.dumps({"EURUSD": 1.0821, "GBPUSD": 1.2745, "USDJPY": 149.32}),
    "data/processed/macro_indicators.csv": "indicator,value,date\nCPI,3.2,2024-01\nPPI,2.1,2024-01\nUnemployment,3.7,2024-01",
    "data/cache/yf_cache_old.pkl": "BINARY_STUB_DO_NOT_USE",
    "logs/run_2024_01_15.log": "[INFO] price_tape.py executed\n[WARN] Timeout on ticker XYZ\n[INFO] Done",
    "logs/errors.log": "[ERROR] movers_yahoo.py: HTTP 429 rate limit\n[ERROR] tmx_movers.py: Connection refused",
    "notebooks/exploratory.ipynb": json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    "tools/helpers/format_utils.py": "def fmt_pct(x):\n    return f'{x:.2f}%'\n\ndef fmt_price(x):\n    return f'${x:,.2f}'\n",
    "reports/archive/morning_brief_2024_01_15.md": "# AM Brief 2024-01-15\n\nMarkets opened mixed...\n",
    "reports/drafts/template_draft.txt": "DRAFT ONLY - NOT FOR DISTRIBUTION\n[TBD sections here]",
}
for path, content in distractor_files.items():
    (WORKSPACE / path).write_text(content)

# ── 2. The bundled scripts (as described in SKILL.md) ─────────────────────────
# price_tape.py: pulls prices/returns/MA/RSI for a ticker list
price_tape_content = '''#!/usr/bin/env python3
"""
scripts/price_tape.py
Pull prices + returns + MA20/MA50/RSI(14) for a ticker list.
Usage: python price_tape.py --tickers TICKER1 TICKER2 ... [--period 60d]
Outputs JSON to stdout.
"""
import argparse
import json
import sys

def compute_rsi(prices, period=14):
    import numpy as np
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def get_tape(tickers, period="60d"):
    try:
        import yfinance as yf
        import pandas as pd
        import numpy as np
    except ImportError:
        return {"error": "yfinance not available"}

    results = {}
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period=period)
            if hist.empty or len(hist) < 51:
                results[ticker] = {"error": f"insufficient data (rows={len(hist)})"}
                continue
            closes = hist["Close"].values
            close = float(closes[-1])
            prev_close = float(closes[-2])
            ret_1d = round((close - prev_close) / prev_close * 100, 2)
            ma20 = float(np.mean(closes[-20:]))
            ma50 = float(np.mean(closes[-50:]))
            rsi = compute_rsi(closes[-29:])  # last 29 for 14-period RSI with buffer
            # Trend label
            if close > ma20 > ma50 and rsi >= 50:
                trend = "BUY"
            elif close < ma20 < ma50 and rsi <= 50:
                trend = "SELL"
            else:
                trend = "WAIT"
            results[ticker] = {
                "close": round(close, 4),
                "prev_close": round(prev_close, 4),
                "return_1d_pct": ret_1d,
                "ma20": round(ma20, 4),
                "ma50": round(ma50, 4),
                "rsi14": rsi,
                "trend": trend
            }
        except Exception as e:
            results[ticker] = {"error": str(e)}
    return results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tickers", nargs="+", required=True)
    parser.add_argument("--period", default="60d")
    args = parser.parse_args()
    results = get_tape(args.tickers, args.period)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
'''

# movers_yahoo.py: Yahoo Finance screeners for top gainers/losers
movers_yahoo_content = '''#!/usr/bin/env python3
"""
scripts/movers_yahoo.py
Fetch top gainers/losers/actives from Yahoo Finance screeners (best-effort, free tier).
Usage: python movers_yahoo.py --type gainers|losers|actives [--count 5]
Outputs JSON to stdout.
"""
import argparse
import json
import sys

SCREENER_MAP = {
    "gainers": "day_gainers",
    "losers":  "day_losers",
    "actives": "most_actives",
}

def fetch_movers(screen_type="gainers", count=5):
    try:
        import yfinance as yf
    except ImportError:
        return {"error": "yfinance not available"}

    key = SCREENER_MAP.get(screen_type, "day_gainers")
    try:
        screener = yf.screen(key)
        quotes = screener.get("quotes", [])[:count]
        movers = []
        for q in quotes:
            movers.append({
                "symbol": q.get("symbol", "N/A"),
                "name":   q.get("shortName", q.get("longName", "N/A")),
                "price":  round(q.get("regularMarketPrice", 0), 2),
                "change_pct": round(q.get("regularMarketChangePercent", 0), 2),
            })
        return {"type": screen_type, "movers": movers}
    except Exception as e:
        # Fallback: try pandas_datareader style
        return {"type": screen_type, "movers": [], "warning": str(e)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default="gainers", choices=["gainers","losers","actives"])
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()
    result = fetch_movers(args.type, args.count)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
'''

# tmx_movers.py: TMX movers scraper stub
tmx_movers_content = '''#!/usr/bin/env python3
"""
scripts/tmx_movers.py
Example TMX Money movers scraper (Canada). Adapt or swap as needed.
Usage: python tmx_movers.py [--count 5]
"""
import argparse
import json

def fetch_tmx_movers(count=5):
    # Stub: In production, scrape https://money.tmx.com/en/market-data
    return {
        "exchange": "TSX",
        "movers": [],
        "note": "Stub implementation. Replace with live scraper logic."
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()
    print(json.dumps(fetch_tmx_movers(args.count), indent=2))

if __name__ == "__main__":
    main()
'''

# render_example.md: template
render_example_content = '''# [TIME] Market Brief — [DATE]

## TL;DR
- Bullet 1
- Bullet 2
- Bullet 3

## Equities
| Region | Index | Price | 1D Chg | Trend |
|--------|-------|-------|--------|-------|
| US     | SPY   | ...   | ...    | BUY/SELL/WAIT |

## Rates
| Tenor | Yield | Chg (bps) |
|-------|-------|-----------|
| US 2Y | ...   | ...       |

## FX
| Pair  | Rate  | 1D Chg |
|-------|-------|--------|
| DXY   | ...   | ...    |

## Commodities
| Asset | Price | 1D Chg |
|-------|-------|--------|
| WTI   | ...   | ...    |

## Crypto
| Asset | Price | 1D Chg |
|-------|-------|--------|
| BTC   | ...   | ...    |

## Top Movers
**Gainers:** ...
**Losers:** ...

## Patterns / Trend Box
| Ticker | Trend | Rationale |
|--------|-------|-----------|
| SPY    | BUY   | Close > MA20 > MA50 & RSI >= 50 |

## One Best Idea
**Thesis:** ...
**Invalidation:** ...
'''

scripts = {
    "scripts/price_tape.py": price_tape_content,
    "scripts/movers_yahoo.py": movers_yahoo_content,
    "scripts/tmx_movers.py": tmx_movers_content,
    "scripts/render_example.md": render_example_content,
}
for path, content in scripts.items():
    (WORKSPACE / path).write_text(content)

# ── 3. The task brief (investment committee request) ──────────────────────────
# This is the "messy input" — an internal memo with partial info
ict_memo = """INTERNAL MEMO — INVESTMENT COMMITTEE
Date: Today (PM Session)
From: Portfolio Strategy Desk
To: Market Intelligence Team

We need a PM (afternoon) market wrap-up brief for the IC meeting at 05:00 PM today.

REQUIRED COVERAGE:
- Equities: SPY, QQQ, IWM (US), EWZ (Brazil), FXI (China)
- Rates: ^TNX (10Y Treasury), ^IRX (3M Bill)
- FX: DX-Y.NYB (DXY), EURUSD=X, USDJPY=X
- Commodities: CL=F (WTI crude), GC=F (Gold), HG=F (Copper)
- Crypto: BTC-USD, ETH-USD
- Top 3 gainers and top 3 losers from US equity screener
- Trend signals (BUY/SELL/WAIT pattern labels) for ALL equities and crypto listed above
- A single "best idea" wrap-up with a clear invalidation scenario

Risk framing: AGGRESSIVE

OUTPUT FILE: pm_brief.md
Location: reports/ folder
"""
(WORKSPACE / "investment_committee_request.txt").write_text(ict_memo)

# ── 4. Additional messy context files ─────────────────────────────────────────
# Stale ticker alias mapping (distractor / trap)
alias_map = {
    "DXY": "DX-Y.NYB",
    "WTI": "CL=F",
    "GOLD": "GC=F",
    "COPPER": "HG=F",
    "BTC": "BTC-USD",
    "ETH": "ETH-USD",
    "NOTE": "Tickers above are yfinance-compatible aliases. Use the right-hand side."
}
(WORKSPACE / "config/ticker_aliases.json").write_text(json.dumps(alias_map, indent=2))

# Incomplete prior AM brief (distractor)
am_brief_stub = """# AM Brief — [Today]

## TL;DR
- US futures slightly lower overnight
- DXY holding 104 handle
- BTC tested 67k resistance

## Equities
(incomplete — not published)
"""
(WORKSPACE / "reports/drafts/am_brief_today_INCOMPLETE.md").write_text(am_brief_stub)

print("Workspace generated successfully.")
print(f"Files created: {len(list(WORKSPACE.rglob('*')))}")