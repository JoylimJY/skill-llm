import os
import json
import random
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# ── Simulate the skill root with scripts and references already present ──

scripts_dir = workspace / "scripts"
scripts_dir.mkdir(exist_ok=True)

references_dir = workspace / "references" / "api"
references_dir.mkdir(parents=True, exist_ok=True)

# ── query_symbol.py ──
(scripts_dir / "query_symbol.py").write_text(textwrap.dedent("""
import argparse
import json
from tvscreener import StockScreener, Market

MARKET_MAP = {
    "HONGKONG": Market.HONGKONG,
    "CHINA": Market.CHINA,
    "AMERICA": Market.AMERICA,
    "AMERICA_ETF": Market.AMERICA_ETF,
}

FIELDS = [
    "NAME", "PRICE", "CHANGE_PERCENT", "VOLUME",
    "RELATIVE_STRENGTH_INDEX_14",
    "MACD_LEVEL_12_26", "MACD_SIGNAL_12_26", "MACD_HIST",
    "SIMPLE_MOVING_AVERAGE_20", "SIMPLE_MOVING_AVERAGE_50", "SIMPLE_MOVING_AVERAGE_200",
    "EXPONENTIAL_MOVING_AVERAGE_20", "EXPONENTIAL_MOVING_AVERAGE_50", "EXPONENTIAL_MOVING_AVERAGE_200",
    "BOLLINGER_UPPER_BAND_20", "BOLLINGER_LOWER_BAND_20",
    "STOCHASTIC_PERCENTK_14_3_3", "STOCHASTIC_PERCENTD_14_3_3",
    "AVERAGE_TRUE_RANGE_14", "MOVING_AVERAGES_RATING",
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--market", required=True)
    args = parser.parse_args()

    market = MARKET_MAP[args.market]
    sc = StockScreener(market)
    sc.set_tickers(args.symbol)
    sc.set_fields(*FIELDS)
    df = sc.get_data()
    result = df.to_dict(orient="records")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
""").strip())

# ── custom_query.py ──
(scripts_dir / "custom_query.py").write_text(textwrap.dedent("""
import argparse
import json
from tvscreener import StockScreener, Market
from tvscreener.field import Field

MARKET_MAP = {
    "HONGKONG": Market.HONGKONG,
    "CHINA": Market.CHINA,
    "AMERICA": Market.AMERICA,
}

def parse_filter(filter_str):
    import re
    ops = ["!=", ">=", "<=", ">", "<", "="]
    for op in ops:
        if op in filter_str:
            k, v = filter_str.split(op, 1)
            return k.strip(), op, v.strip()
    raise ValueError(f"Cannot parse filter: {filter_str}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--market", required=True)
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--fields", required=True)
    parser.add_argument("--filter", default=None, dest="filter_expr")
    args = parser.parse_args()

    market = MARKET_MAP[args.market]
    sc = StockScreener(market)
    if args.symbol:
        sc.set_tickers(args.symbol)
    fields = [f.strip() for f in args.fields.split(",")]
    sc.set_fields(*fields)
    if args.filter_expr:
        fname, op, fval = parse_filter(args.filter_expr)
        sc.filter_by(fname, op, fval)
    df = sc.get_data()
    result = df.to_dict(orient="records")
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    main()
""").strip())

# ── run_query.sh ──
(scripts_dir / "run_query.sh").write_text(textwrap.dedent("""
#!/usr/bin/env bash
set -euo pipefail

MARKET=""
SYMBOL=""
FIELDS=""
FILTER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --market) MARKET="$2"; shift 2;;
    --symbol) SYMBOL="$2"; shift 2;;
    --fields) FIELDS="$2"; shift 2;;
    --filter) FILTER="$2"; shift 2;;
    *) echo "Unknown arg: $1"; exit 1;;
  esac
done

CMD="python3 $(dirname "$0")/custom_query.py --market $MARKET --fields '$FIELDS'"
[[ -n "$SYMBOL" ]] && CMD="$CMD --symbol $SYMBOL"
[[ -n "$FILTER" ]] && CMD="$CMD --filter '$FILTER'"

eval $CMD
""").strip())
os.chmod(scripts_dir / "run_query.sh", 0o755)

# ── discover_fields.py ──
(scripts_dir / "discover_fields.py").write_text(textwrap.dedent("""
import argparse
from tvscreener.field import Field

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keyword", default="")
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    kw = args.keyword.lower()
    count = 0
    for attr in dir(Field):
        if attr.startswith("_"):
            continue
        if kw in attr.lower():
            print(attr)
            count += 1
            if count >= args.limit:
                break

if __name__ == "__main__":
    main()
""").strip())

# ── test_markets.sh ──
(scripts_dir / "test_markets.sh").write_text(textwrap.dedent("""
#!/usr/bin/env bash
set -euo pipefail
echo "=== Testing HKEX:700 (Tencent) ==="
python3 "$(dirname "$0")/query_symbol.py" --symbol HKEX:700 --market HONGKONG

echo "=== Testing SHSE:600519 (Moutai) ==="
python3 "$(dirname "$0")/query_symbol.py" --symbol SHSE:600519 --market CHINA

echo "=== Testing SHSE:510300 (ETF) ==="
python3 "$(dirname "$0")/query_symbol.py" --symbol SHSE:510300 --market CHINA

echo "=== Testing NASDAQ:BIDU ==="
python3 "$(dirname "$0")/query_symbol.py" --symbol NASDAQ:BIDU --market AMERICA
""").strip())
os.chmod(scripts_dir / "test_markets.sh", 0o755)

# ── references ──
(references_dir / "fields.md").write_text(textwrap.dedent("""
# Fields Reference

Available fields (non-exhaustive):
- NAME, PRICE, CHANGE_PERCENT, VOLUME
- RELATIVE_STRENGTH_INDEX_14
- MACD_LEVEL_12_26, MACD_SIGNAL_12_26, MACD_HIST
- SIMPLE_MOVING_AVERAGE_20, SIMPLE_MOVING_AVERAGE_50, SIMPLE_MOVING_AVERAGE_200
- EXPONENTIAL_MOVING_AVERAGE_20, EXPONENTIAL_MOVING_AVERAGE_50, EXPONENTIAL_MOVING_AVERAGE_200
- BOLLINGER_UPPER_BAND_20, BOLLINGER_LOWER_BAND_20
- STOCHASTIC_PERCENTK_14_3_3, STOCHASTIC_PERCENTD_14_3_3
- AVERAGE_TRUE_RANGE_14
- MOVING_AVERAGES_RATING
""").strip())

(references_dir / "enums.md").write_text(textwrap.dedent("""
# Market Enums

- HONGKONG
- CHINA
- AMERICA
- AMERICA_ETF
""").strip())

(references_dir / "filters.md").write_text(textwrap.dedent("""
# Filter Syntax

Filters are specified as FIELD=VALUE, FIELD>VALUE, etc.
Operators: =, !=, >, <, >=, <=
""").strip())

(references_dir / "screeners.md").write_text(textwrap.dedent("""
# Screeners

StockScreener(market) creates a screener for a given market.
Supported markets: HONGKONG, CHINA, AMERICA, AMERICA_ETF
""").strip())

(workspace / "references" / "README_USAGE.md").write_text(textwrap.dedent("""
# Usage Patterns

Use query_symbol.py for stable single-symbol snapshots.
Use run_query.sh for custom multi-field queries with filters.
Use discover_fields.py to find available field names.
""").strip())

# ── SKILL.md ──
(workspace / "SKILL.md").write_text(textwrap.dedent("""
---
name: tvscreener
description: Query TradingView screener data for HK, A-share, A-share ETF, and US symbols with deepentropy/tvscreener.
---

# tvscreener

Use this skill for market queries with simple scripts first, then native Python when needed.

## Install

```bash
python3 -m pip install -U tvscreener
```

Python must be `>=3.10`.

## Quick commands (run from skill root)

```bash
# Preset single-symbol output (recommended)
python3 scripts/query_symbol.py --symbol HKEX:700 --market HONGKONG

# Custom query (fields + filters)
bash scripts/run_query.sh \\
  --market CHINA \\
  --symbol SHSE:600519 \\
  --fields 'NAME,PRICE,CHANGE_PERCENT,VOLUME,RELATIVE_STRENGTH_INDEX_14,MACD_LEVEL_12_26,MACD_SIGNAL_12_26,MACD_HIST,SIMPLE_MOVING_AVERAGE_20,SIMPLE_MOVING_AVERAGE_50,SIMPLE_MOVING_AVERAGE_200,EXPONENTIAL_MOVING_AVERAGE_20,EXPONENTIAL_MOVING_AVERAGE_50,EXPONENTIAL_MOVING_AVERAGE_200,BOLLINGER_UPPER_BAND_20,BOLLINGER_LOWER_BAND_20,STOCHASTIC_PERCENTK_14_3_3,STOCHASTIC_PERCENTD_14_3_3,AVERAGE_TRUE_RANGE_14,MOVING_AVERAGES_RATING' \\
  --filter 'NAME=600519'

# Field discovery
python3 scripts/discover_fields.py --keyword macd --limit 20
```

## Query rules

- Core technical set (recommended): PRICE, CHANGE_PERCENT, VOLUME, RELATIVE_STRENGTH_INDEX_14, MACD_LEVEL_12_26, MACD_SIGNAL_12_26, MACD_HIST, SIMPLE_MOVING_AVERAGE_20/50/200, EXPONENTIAL_MOVING_AVERAGE_20/50/200, BOLLINGER_UPPER_BAND_20, BOLLINGER_LOWER_BAND_20, STOCHASTIC_PERCENTK_14_3_3, STOCHASTIC_PERCENTD_14_3_3, AVERAGE_TRUE_RANGE_14, MOVING_AVERAGES_RATING
- Filters: =, !=, >, <, >=, <=

## References

- references/README_USAGE.md
- references/api/screeners.md
- references/api/fields.md
- references/api/filters.md
- references/api/enums.md
""").strip())

# ── Distractor files to simulate a messy real workspace ──

distractor_dirs = [
    workspace / "archive" / "old_queries",
    workspace / "archive" / "legacy_configs",
    workspace / "data" / "raw" / "2023",
    workspace / "data" / "raw" / "2024",
    workspace / "data" / "processed",
    workspace / "notebooks",
    workspace / "config",
    workspace / "logs",
]
for d in distractor_dirs:
    d.mkdir(parents=True, exist_ok=True)

distractors = {
    workspace / "archive" / "old_queries" / "hk_query_v1.py": "# Deprecated HK query using old API\nimport requests\nprint('deprecated')",
    workspace / "archive" / "old_queries" / "us_query_v2.py": "# Old US screener\nprint('old us')",
    workspace / "archive" / "legacy_configs" / "screener_config.yaml": "market: HK\nsymbol: 700\nfields: RSI,MACD\n",
    workspace / "archive" / "legacy_configs" / "filter_rules.json": json.dumps({"rules": [{"field": "RSI", "op": ">", "val": 50}]}),
    workspace / "data" / "raw" / "2023" / "tencent_daily.csv": "date,close\n2023-01-03,340.2\n2023-01-04,338.8\n",
    workspace / "data" / "raw" / "2024" / "tencent_daily.csv": "date,close\n2024-01-02,355.0\n2024-01-03,358.2\n",
    workspace / "data" / "processed" / "tencent_indicators_WRONG.json": json.dumps({
        "symbol": "700.HK",
        "RSI": 58.3,
        "MACD": 1.24,
        "Bollinger_Upper": 382.5,
        "note": "OUTDATED FORMAT - DO NOT USE"
    }, indent=2),
    workspace / "notebooks" / "exploration.ipynb": json.dumps({"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}),
    workspace / "config" / "markets.yaml": "hk:\n  exchange: HKEX\n  currency: HKD\nus:\n  exchange: NASDAQ\n  currency: USD\n",
    workspace / "config" / "wrong_fields.txt": "RSI_14\nMACD_LINE\nBB_UPPER\nBB_LOWER\nSTOCH_K\nSTOCH_D\n",
    workspace / "logs" / "query_errors.log": "[ERROR] Unknown field: RSI_14\n[ERROR] Unknown field: MACD_LINE\n[WARN]  Symbol format invalid: 700.HK\n",
}

for path, content in distractors.items():
    path.write_text(content)

# ── Task brief (the "request" from the manager) ──
# This file is the prompt context, NOT instructions
task_brief = {
    "request": "Pull a full technical snapshot for Tencent (HK-listed) and save it to technical_snapshot.json",
    "symbol_hint": "Tencent Holdings - listed on the Hong Kong Stock Exchange, ticker 700",
    "required_indicators": [
        "current price", "percent change",
        "RSI (14-period)",
        "MACD line, signal line, and histogram",
        "20/50/200-day simple moving averages",
        "20/50/200-day exponential moving averages",
        "Bollinger Band upper and lower (20-period)",
        "Stochastic %K and %D (14,3,3)",
        "Average True Range (14)",
        "Moving averages consensus rating"
    ],
    "output_file": "technical_snapshot.json",
    "note": "Data must reflect live market values. The output file must be machine-readable JSON with one record per symbol."
}
(workspace / "task_brief.json").write_text(json.dumps(task_brief, indent=2))

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in workspace.rglob('*') if _.is_file())}")