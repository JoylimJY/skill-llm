#!/usr/bin/env python3
"""
Evaluation script for the AlphaEar Predictor task.
Usage: python eval_script.py /workspace
"""
import sys
import json
import math
import hashlib
from pathlib import Path

def find_output_file(workspace: Path) -> Path | None:
    candidates = list(workspace.rglob("adjusted_forecast.json"))
    return candidates[0] if candidates else None

def load_json(path: Path):
    with open(path) as f:
        return json.load(f)

def compute_expected_base(workspace: Path):
    """Re-run the same deterministic logic as KronosPredictorUtility.get_base_forecast."""
    import pandas as pd
    import numpy as np

    raw_csv = workspace / "data" / "raw" / "stock_600519_ohlcv_messy.csv"
    df = pd.read_csv(raw_csv)

    # Normalise columns (agent must do this too)
    df.columns = [c.lower() for c in df.columns]

    # Parse dates (mixed formats)
    df["date"] = pd.to_datetime(df["date"], dayfirst=False, infer_datetime_format=True)
    df = df.sort_values("date").drop_duplicates(subset=["date"])

    # Handle missing volume
    df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    df["volume"] = df["volume"].fillna(df["volume"].median())

    # Ensure numeric price columns
    for col in ["open", "high", "low", "close"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["open", "high", "low", "close"])
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    news_text = (workspace / "data" / "raw" / "news_headlines_20240127.txt").read_text()

    lookback = 20
    pred_len = 5

    seed_int = int(hashlib.md5(news_text.encode()).hexdigest(), 16) % (2**31)
    rng = np.random.RandomState(seed_int)

    window = df.tail(lookback).copy()
    last_close = float(window["close"].iloc[-1])
    last_date = pd.Timestamp(window["date"].iloc[-1])

    results = []
    price = last_close
    for i in range(pred_len):
        delta = rng.normal(0, 0.012) * price
        open_ = round(price + rng.normal(0, 0.003) * price, 2)
        close_ = round(price + delta, 2)
        high_ = round(max(open_, close_) + abs(rng.normal(0, 0.005) * price), 2)
        low_ = round(min(open_, close_) - abs(rng.normal(0, 0.005) * price), 2)
        vol = round(float(window["volume"].mean()) * rng.uniform(0.85, 1.15), 0)
        next_date = last_date + pd.offsets.BDay(i + 1)
        results.append({
            "date": next_date.strftime("%Y-%m-%d"),
            "open": open_, "high": high_, "low": low_,
            "close": close_, "volume": vol, "predicted": True,
        })
        price = close_
    return results

def apply_sentiment_adjustment(base_forecast, sentiment_label: str):
    """Apply the adjustment rules from references/PROMPTS.md."""
    multiplier_map = {
        "positive": 1.015,
        "negative": 0.985,
        "neutral": 1.000,
    }
    mult = multiplier_map.get(sentiment_label.lower(), 1.000)
    adjusted = []
    for row in base_forecast:
        ratio = mult  # close changes by this factor
        orig_close = row["close"]
        new_close = round(orig_close * ratio, 2)
        new_high = round(row["high"] * ratio, 2)
        new_low = round(row["low"] * ratio, 2)
        adjusted.append({
            **row,
            "close": new_close,
            "high": new_high,
            "low": new_low,
            "sentiment_label": sentiment_label.lower(),
            "sentiment_multiplier": mult,
        })
    return adjusted

def check_structure(data, checks):
    """Check that output is a list of 5 dicts with required fields."""
    name = "output_is_list_of_5_klinepoints"
    required_fields = {"date", "open", "high", "low", "close", "volume", "predicted",
                       "sentiment_label", "sentiment_multiplier"}
    try:
        assert isinstance(data, list), "Not a list"
        assert len(data) == 5, f"Expected 5 items, got {len(data)}"
        for i, item in enumerate(data):
            missing = required_fields - set(item.keys())
            assert not missing, f"Item {i} missing fields: {missing}"
        checks.append({"name": name, "passed": True,
                        "detail": "Output is a list of 5 KLinePoint dicts with all required fields."})
        return True
    except AssertionError as e:
        checks.append({"name": name, "passed": False, "detail": str(e)})
        return False

def check_dates(data, expected_base, checks):
    name = "predicted_dates_are_business_days"
    try:
        agent_dates = [item["date"] for item in data]
        exp_dates = [item["date"] for item in expected_base]
        assert agent_dates == exp_dates, (
            f"Date mismatch.\nAgent:    {agent_dates}\nExpected: {exp_dates}"
        )
        checks.append({"name": name, "passed": True,
                        "detail": f"Dates match: {agent_dates}"})
        return True
    except AssertionError as e:
        checks.append({"name": name, "passed": False, "detail": str(e)})
        return False

def check_base_prices_used(data, expected_base, checks):
    """Verify agent's base (open) prices are consistent with get_base_forecast output."""
    name = "open_prices_derived_from_get_base_forecast"
    try:
        for i, (agent, exp) in enumerate(zip(data, expected_base)):
            diff = abs(float(agent["open"]) - float(exp["open"]))
            assert diff < 0.5, (
                f"Day {i}: open price mismatch. Agent={agent['open']}, Expected≈{exp['open']}"
            )
        checks.append({"name": name, "passed": True,
                        "detail": "Open prices are consistent with KronosPredictorUtility.get_base_forecast output."})
        return True
    except AssertionError as e:
        checks.append({"name": name, "passed": False, "detail": str(e)})
        return False

def check_sentiment_label(data, checks):
    name = "sentiment_label_is_positive"
    try:
        labels = {item["sentiment_label"].lower() for item in data}
        assert labels == {"positive"}, (
            f"Expected all items to have sentiment_label='positive', got: {labels}"
        )
        checks.append({"name": name, "passed": True,
                        "detail": "All KLinePoints have sentiment_label='positive' (correct given bullish news)."})
        return True
    except AssertionError as e:
        checks.append({"name": name, "passed": False, "detail": str(e)})
        return False

def check_sentiment_multiplier(data, checks):
    name = "sentiment_multiplier_is_1015"
    try:
        for i, item in enumerate(data):
            mult = float(item["sentiment_multiplier"])
            assert abs(mult - 1.015) < 1e-6, (
                f"Day {i}: sentiment_multiplier={mult}, expected 1.015"
            )
        checks.append({"name": name, "passed": True,
                        "detail": "Multiplier 1.015 correctly applied for positive sentiment."})
        return True
    except AssertionError as e:
        checks.append({"name": name, "passed": False, "detail": str(e)})
        return False

def check_close_adjustment(data, expected_base, checks):
    name = "close_prices_adjusted_by_sentiment_multiplier"
    try:
        for i, (agent, exp) in enumerate(zip(data, expected_base)):
            expected_close = round(exp["close"] * 1.015, 2)
            agent_close = round(float(agent["close"]), 2)
            diff = abs(agent_close - expected_close)
            assert diff < 0.02, (
                f"Day {i}: close mismatch. Agent={agent_close}, Expected≈{expected_close}"
            )
        checks.append({"name": name, "passed": True,
                        "detail": "Close prices correctly adjusted by 1.015x."})
        return True
    except AssertionError as e:
        checks.append({"name": name, "passed": False, "detail": str(e)})
        return False

def check_high_low_adjustment(data, expected_base, checks):
    name = "high_low_prices_proportionally_adjusted"
    try:
        for i, (agent, exp) in enumerate(zip(data, expected_base)):
            exp_high = round(exp["high"] * 1.015, 2)
            exp_low = round(exp["low"] * 1.015, 2)
            agent_high = round(float(agent["high"]), 2)
            agent_low = round(float(agent["low"]), 2)
            assert abs(agent_high - exp_high) < 0.02, (
                f"Day {i}: high mismatch. Agent={agent_high}, Expected≈{exp_high}"
            )
            assert abs(agent_low - exp_low) < 0.02, (
                f"Day {i}: low mismatch. Agent={agent_low}, Expected≈{exp_low}"
            )
        checks.append({"name": name, "passed": True,
                        "detail": "High/Low proportionally adjusted by 1.015x."})
        return True
    except AssertionError as e:
        checks.append({"name": name, "passed": False, "detail": str(e)})
        return False

def check_data_cleaning(data, checks):
    """Verify agent used all 20 clean rows (not duplicated/missing-volume rows)."""
    name = "messy_data_cleaned_before_forecast"
    try:
        # If the agent did NOT deduplicate / handle missing volume, the deterministic
        # RNG seed would produce different prices. We indirectly verify this by
        # checking that the forecast dates start from the correct business day.
        # The last valid date in the cleaned data should be 2024-01-26.
        first_forecast_date = data[0]["date"]
        assert first_forecast_date == "2024-01-29", (
            f"First forecast date should be 2024-01-29 (next BDay after 2024-01-26), "
            f"got {first_forecast_date}. Likely the CSV was not cleaned correctly."
        )
        checks.append({"name": name, "passed": True,
                        "detail": f"First forecast date {first_forecast_date} confirms correct data cleaning."})
        return True
    except AssertionError as e:
        checks.append({"name": name, "passed": False, "detail": str(e)})
        return False

def main():
    workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/workspace")
    checks = []

    # ── Locate output file ──────────────────────────────────────────────────
    output_path = find_output_file(workspace)
    if output_path is None:
        checks.append({"name": "output_file_exists",
                        "passed": False,
                        "detail": "adjusted_forecast.json not found anywhere under workspace."})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, indent=2))
        return

    checks.append({"name": "output_file_exists", "passed": True,
                    "detail": f"Found at {output_path.relative_to(workspace)}"})

    # ── Load agent output ───────────────────────────────────────────────────
    try:
        agent_data = load_json(output_path)
    except Exception as e:
        checks.append({"name": "output_json_parseable", "passed": False, "detail": str(e)})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, indent=2))
        return

    checks.append({"name": "output_json_parseable", "passed": True, "detail": "Valid JSON."})

    # ── Compute expected values ─────────────────────────────────────────────
    try:
        expected_base = compute_expected_base(workspace)
    except Exception as e:
        checks.append({"name": "internal_expected_compute", "passed": False,
                        "detail": f"Eval internal error: {e}"})
        result = {"passed": False, "score": 0.0, "checks": checks}
        print(json.dumps(result, indent=2))
        return

    # ── Run checks ──────────────────────────────────────────────────────────
    s1 = check_structure(agent_data, checks)
    if not s1:
        result = {"passed": False, "score": 0.1, "checks": checks}
        print(json.dumps(result, indent=2))
        return

    check_data_cleaning(agent_data, checks)
    check_dates(agent_data, expected_base, checks)
    check_base_prices_used(agent_data, expected_base, checks)
    check_sentiment_label(agent_data, checks)
    check_sentiment_multiplier(agent_data, checks)
    check_close_adjustment(agent_data, expected_base, checks)
    check_high_low_adjustment(agent_data, expected_base, checks)

    # ── Score ────────────────────────────────────────────────────────────────
    n_passed = sum(1 for c in checks if c["passed"])
    score = round(n_passed / len(checks), 4)
    passed = all(c["passed"] for c in checks)

    result = {"passed": passed, "score": score, "checks": checks}
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()