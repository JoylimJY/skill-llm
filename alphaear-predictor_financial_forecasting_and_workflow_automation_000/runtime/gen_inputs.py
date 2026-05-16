import os
import json
import random
import csv
import textwrap
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")

# ─── Directory skeleton ───────────────────────────────────────────────────────
dirs = [
    "scripts/utils",
    "scripts/legacy",
    "exports/models",
    "exports/reports",
    "references",
    "data/raw",
    "data/processed",
    "config",
    "notebooks",
    "logs",
    "tests",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ─── Distractor files ─────────────────────────────────────────────────────────
(workspace / "config" / "app_config.yaml").write_text(textwrap.dedent("""\
    app:
      name: AlphaEar
      version: 1.0.0
    database:
      host: localhost
      port: 5432
    cache:
      ttl: 300
"""))

(workspace / "config" / "logging.yaml").write_text(textwrap.dedent("""\
    version: 1
    handlers:
      console:
        class: logging.StreamHandler
    root:
      level: DEBUG
"""))

(workspace / "scripts" / "legacy" / "old_predictor.py").write_text(textwrap.dedent("""\
    # Deprecated — do not use
    class OldPredictor:
        def forecast(self, ticker, days):
            raise NotImplementedError('Use KronosPredictorUtility instead')
"""))

(workspace / "scripts" / "legacy" / "data_cleaner.py").write_text(textwrap.dedent("""\
    import pandas as pd
    def clean(df):
        return df.dropna()
"""))

(workspace / "exports" / "reports" / "q1_summary.txt").write_text(
    "Q1 2024 performance summary placeholder.\n")

(workspace / "notebooks" / "exploration.ipynb").write_text(json.dumps({
    "nbformat": 4,
    "cells": [{"cell_type": "code", "source": "# EDA notebook\n", "metadata": {}, "outputs": []}],
    "metadata": {"kernelspec": {"name": "python3"}},
    "nbformat_minor": 5
}))

(workspace / "logs" / "training.log").write_text(
    "2024-01-15 10:23:11 INFO  Training started\n"
    "2024-01-15 14:55:03 INFO  Epoch 50/50 loss=0.0312\n"
    "2024-01-15 14:55:10 INFO  Model saved\n"
)

(workspace / "tests" / "test_utils.py").write_text(textwrap.dedent("""\
    def test_placeholder():
        assert True
"""))

(workspace / "data" / "processed" / "features_v2.parquet.bak").write_text(
    "binary placeholder — not a real parquet\n")

(workspace / "scripts" / "utils" / "__init__.py").write_text("")
(workspace / "scripts" / "__init__.py").write_text("")

(workspace / "config" / "model_registry.json").write_text(json.dumps({
    "models": [
        {"name": "kronos_base", "version": "1.0", "path": "exports/models/"},
        {"name": "kronos_news_v1", "version": "1.0", "path": "exports/models/kronos_news_v1.pt"}
    ]
}, indent=2))

# ─── The REAL skill scripts (stubs that the agent must invoke correctly) ──────

# KronosPredictorUtility — real implementation stub
(workspace / "scripts" / "utils" / "kronos_predictor.py").write_text(textwrap.dedent("""\
    \"\"\"
    KronosPredictorUtility — lightweight stub for sandbox evaluation.
    The real implementation loads Kronos model weights; here we use a
    deterministic synthetic forecast so no GPU/large model is needed.
    \"\"\"
    from __future__ import annotations
    import hashlib, json, math
    from dataclasses import dataclass, asdict
    from typing import List
    import pandas as pd
    import numpy as np

    @dataclass
    class KLinePoint:
        date: str
        open: float
        high: float
        low: float
        close: float
        volume: float
        predicted: bool = True

    class KronosPredictorUtility:
        \"\"\"
        Primary forecasting utility.

        Usage
        -----
        predictor = KronosPredictorUtility()
        forecast  = predictor.get_base_forecast(df, lookback=20, pred_len=5, news_text="...")
        # returns List[KLinePoint]
        \"\"\"

        def __init__(self, model_path: str | None = None):
            self._model_path = model_path

        # ------------------------------------------------------------------
        # Public API
        # ------------------------------------------------------------------
        def get_base_forecast(
            self,
            df: pd.DataFrame,
            lookback: int,
            pred_len: int,
            news_text: str,
        ) -> List[KLinePoint]:
            \"\"\"
            Generate a deterministic base forecast.

            Parameters
            ----------
            df        : DataFrame with columns [date, open, high, low, close, volume]
                        sorted ascending by date.
            lookback  : Number of historical rows to condition on.
            pred_len  : Number of future bars to predict.
            news_text : Raw news string (used for sentiment seed).

            Returns
            -------
            List[KLinePoint]  (length == pred_len)
            \"\"\"
            required = {"date", "open", "high", "low", "close", "volume"}
            missing = required - set(df.columns)
            if missing:
                raise ValueError(f"DataFrame missing columns: {missing}")
            if len(df) < lookback:
                raise ValueError(
                    f"DataFrame has {len(df)} rows but lookback={lookback} requires at least {lookback}."
                )

            seed_int = int(hashlib.md5(news_text.encode()).hexdigest(), 16) % (2**31)
            rng = np.random.RandomState(seed_int)

            window = df.tail(lookback).copy()
            last_close = float(window["close"].iloc[-1])
            last_date  = pd.Timestamp(window["date"].iloc[-1])

            results: List[KLinePoint] = []
            price = last_close
            for i in range(pred_len):
                delta  = rng.normal(0, 0.012) * price
                open_  = round(price + rng.normal(0, 0.003) * price, 2)
                close_ = round(price + delta, 2)
                high_  = round(max(open_, close_) + abs(rng.normal(0, 0.005) * price), 2)
                low_   = round(min(open_, close_) - abs(rng.normal(0, 0.005) * price), 2)
                vol    = round(float(window["volume"].mean()) * rng.uniform(0.85, 1.15), 0)
                next_date = last_date + pd.offsets.BDay(i + 1)
                results.append(KLinePoint(
                    date=next_date.strftime("%Y-%m-%d"),
                    open=open_, high=high_, low=low_, close=close_, volume=vol,
                ))
                price = close_
            return results

        # ------------------------------------------------------------------
        # Convenience wrapper (different signature — do NOT confuse with above)
        # ------------------------------------------------------------------
        def predict(self, ticker: str, horizon: str = "7d") -> dict:
            \"\"\"Convenience wrapper — returns raw dict, NOT List[KLinePoint].\"\"\"""
            return {"ticker": ticker, "horizon": horizon, "status": "use get_base_forecast for full output"}
"""))

# DatabaseManager stub
(workspace / "scripts" / "utils" / "database_manager.py").write_text(textwrap.dedent("""\
    class DatabaseManager:
        def get_ohlcv(self, ticker: str, limit: int = 100):
            raise NotImplementedError('Use the CSV file provided in data/raw/ instead.')
"""))

# ─── PROMPTS.md ───────────────────────────────────────────────────────────────
(workspace / "references" / "PROMPTS.md").write_text(textwrap.dedent("""\
    # AlphaEar Forecast Prompts

    ## Forecast Adjustment Prompt

    Use this prompt (or equivalent logic) when adjusting a base quantitative forecast
    with qualitative news sentiment:

    ```
    You are a senior quantitative analyst. You have been given:
    1. A base forecast: {base_forecast_json}
    2. Recent news headlines: {news_headlines}

    Task:
    - Analyse the sentiment of the news headlines (positive / negative / neutral).
    - For each forecasted day, apply a sentiment multiplier to the 'close' price:
        * Positive sentiment  → multiply close by 1.015
        * Negative sentiment  → multiply close by 0.985
        * Neutral sentiment   → no change (multiply by 1.000)
    - Recalculate 'high' and 'low' proportionally (same ratio change as close).
    - Round all price fields to 2 decimal places.
    - Return ONLY a JSON array of adjusted KLinePoint objects with fields:
      date, open, high, low, close, volume, predicted, sentiment_label, sentiment_multiplier
    ```

    > **Note**: The sentiment_label and sentiment_multiplier fields must be appended
    > to each KLinePoint object in the final adjusted output.
"""))

# ─── Messy raw OHLCV data (the agent's input) ─────────────────────────────────
# Intentionally messy: inconsistent date formats, a duplicate row,
# one row with a missing volume, mixed column casing.
rows = [
    ["Date",    "OPEN",  "HIGH",  "LOW",   "CLOSE", "VOLUME"],
    ["2024-01-02", 1820.5, 1835.0, 1812.3, 1830.2, 8_543_200],
    ["2024-01-03", 1831.0, 1848.5, 1825.6, 1840.7, 9_120_400],
    ["01/04/2024", 1839.5, 1855.2, 1831.0, 1849.3, 7_985_600],   # different date fmt
    ["2024-01-05", 1848.0, 1862.1, 1840.5, 1855.9, 10_234_100],
    ["2024-01-08", 1854.3, 1870.0, 1847.2, 1863.4, 8_876_500],
    ["2024-01-09", 1862.0, 1875.5, 1855.1, 1869.8, 9_445_300],
    ["2024-01-10", 1868.5, 1882.3, 1861.0, 1876.2, 8_123_700],
    ["2024-01-11", 1875.0, 1890.1, 1868.4, 1882.7, 9_678_200],
    ["2024-01-12", 1881.3, 1895.0, 1873.6, 1888.1, 7_543_900],
    ["2024-01-15", 1887.5, 1900.4, 1879.2, 1894.6, 10_987_600],
    ["2024-01-15", 1887.5, 1900.4, 1879.2, 1894.6, 10_987_600],  # duplicate
    ["2024-01-16", 1893.0, 1908.7, 1885.5, 1901.3, ""],           # missing volume
    ["2024-01-17", 1900.2, 1914.5, 1892.1, 1907.8, 8_765_400],
    ["2024-01-18", 1906.5, 1920.0, 1898.4, 1913.2, 9_234_100],
    ["2024-01-19", 1912.0, 1925.3, 1904.6, 1918.7, 8_456_800],
    ["2024-01-22", 1917.4, 1930.8, 1909.3, 1924.1, 10_123_400],
    ["2024-01-23", 1923.0, 1937.2, 1915.1, 1929.6, 9_012_700],
    ["2024-01-24", 1928.5, 1943.0, 1920.4, 1935.0, 8_234_500],
    ["2024-01-25", 1934.2, 1948.5, 1926.3, 1941.8, 9_876_300],
    ["2024-01-26", 1940.7, 1955.0, 1932.5, 1948.3, 10_456_200],
]

raw_csv_path = workspace / "data" / "raw" / "stock_600519_ohlcv_messy.csv"
with open(raw_csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(rows)

# ─── News headlines file ──────────────────────────────────────────────────────
(workspace / "data" / "raw" / "news_headlines_20240127.txt").write_text(textwrap.dedent("""\
    [2024-01-27] Kweichow Moutai posts record-breaking Q4 revenue, beats analyst estimates by 12%.
    [2024-01-27] Chinese consumer spending rebounds strongly; luxury goods sector leads gains.
    [2024-01-27] PBOC signals continued accommodative monetary policy through H1 2024.
    [2024-01-26] Moutai brand ranked #1 in global spirits valuation for third consecutive year.
"""))

# ─── Skill documentation entry point ─────────────────────────────────────────
(workspace / "SKILL.md").write_text(textwrap.dedent("""\
    ---
    name: alphaear-predictor
    slug: alphaear-predictor
    version: 1.0.0
    description: Market prediction skill using Kronos. Use when user needs finance market time-series forecasting or news-aware finance market adjustments.
    ---

    # AlphaEar Predictor Skill

    ## Overview

    This skill utilizes the Kronos model (via `KronosPredictorUtility`) to perform time-series forecasting and adjust predictions based on news sentiment.

    ## Capabilities

    ### 1. Forecast Market Trends

    **Workflow:**
    1.  **Generate Base Forecast**: Use `scripts/kronos_predictor.py` (via `KronosPredictorUtility`) to generate the technical/quantitative forecast.
    2.  **Adjust Forecast (Agentic)**: Use the **Forecast Adjustment Prompt** in `references/PROMPTS.md` to subjectively adjust the numbers based on latest news/logic.

    **Key Tools:**
    -   `KronosPredictorUtility.get_base_forecast(df, lookback, pred_len, news_text)`: Returns `List[KLinePoint]`.

    **Example Usage (Python):**

    ```python
    from scripts.utils.kronos_predictor import KronosPredictorUtility
    from scripts.utils.database_manager import DatabaseManager

    db = DatabaseManager()
    predictor = KronosPredictorUtility()

    # Forecast
    forecast = predictor.predict("600519", horizon="7d")
    print(forecast)
    ```


    ## Configuration

    This skill requires the **Kronos** model and an embedding model.

    1.  **Kronos Model**:
        -   Ensure `exports/models` directory exists in the project root.
        -   Place trained news projector weights (e.g., `kronos_news_v1.pt`) in `exports/models/`.
        -   Or depend on the base model (automatically downloaded).

    > [!CAUTION]
    > **Model Security**: This skill loads model weights from `exports/models`. We use `weights_only=True` and only scan for the `kronos_news_*.pt` pattern. Ensure you only place trusted checkpoints in this directory.

    2.  **Environment Variables**:
        -   `EMBEDDING_MODEL`: Path or name of the embedding model (default: `sentence-transformers/all-MiniLM-L6-v2`).
        -   `KRONOS_MODEL_PATH`: Optional path to override model loading.

    ## Dependencies

    -   `torch`
    -   `transformers`
    -   `sentence-transformers`
    -   `pandas`
    -   `numpy`
    -   `scikit-learn`
"""))

print("Workspace scaffold complete.")
print(f"Files created under {workspace}:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")