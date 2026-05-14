import sys
import json
import math
from pathlib import Path

def find_snapshot(workspace: Path):
    """Search for technical_snapshot.json anywhere under workspace."""
    candidates = list(workspace.rglob("technical_snapshot.json"))
    return candidates[0] if candidates else None

def is_numeric(val):
    if val is None:
        return False
    try:
        f = float(val)
        return not math.isnan(f)
    except (TypeError, ValueError):
        return False

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []
    total_score = 0.0

    # ── CHECK 1: File exists ──
    snap_path = find_snapshot(workspace)
    file_exists = snap_path is not None
    checks.append({
        "name": "technical_snapshot.json exists",
        "passed": file_exists,
        "detail": str(snap_path) if file_exists else "File not found anywhere under workspace"
    })
    if not file_exists:
        return {"passed": False, "score": 0.0, "checks": checks}

    # ── CHECK 2: Valid JSON ──
    try:
        raw = snap_path.read_text()
        data = json.loads(raw)
        valid_json = True
    except Exception as e:
        checks.append({"name": "valid JSON", "passed": False, "detail": str(e)})
        return {"passed": False, "score": 0.0, "checks": checks}

    checks.append({"name": "valid JSON", "passed": True, "detail": f"Parsed OK, type={type(data).__name__}"})

    # Normalize: accept list or dict with single record
    if isinstance(data, list):
        if len(data) == 0:
            checks.append({"name": "non-empty records", "passed": False, "detail": "JSON array is empty"})
            return {"passed": False, "score": 0.1, "checks": checks}
        record = data[0]
    elif isinstance(data, dict):
        record = data
    else:
        checks.append({"name": "JSON structure", "passed": False, "detail": f"Expected list or dict, got {type(data)}"})
        return {"passed": False, "score": 0.1, "checks": checks}

    checks.append({"name": "non-empty records", "passed": True, "detail": f"Record keys: {list(record.keys())[:10]}"})

    # ── CHECK 3: Symbol is Tencent (HKEX:700 or similar) ──
    # Accept symbol field OR ticker field containing 700
    raw_keys = {k.lower(): k for k in record.keys()}
    symbol_val = ""
    for candidate_key in ["ticker", "symbol", "name", "NAME"]:
        if candidate_key in record:
            symbol_val = str(record[candidate_key])
            break
        if candidate_key.lower() in raw_keys:
            symbol_val = str(record[raw_keys[candidate_key.lower()]])
            break

    is_tencent = "700" in symbol_val or "tencent" in symbol_val.lower()
    checks.append({
        "name": "symbol is Tencent (700/HKEX:700)",
        "passed": is_tencent,
        "detail": f"symbol_val='{symbol_val}'"
    })

    # ── CHECK 4: Core price fields present and numeric ──
    # These fields come from the tvscreener proprietary naming
    proprietary_field_map = {
        "PRICE": ["price", "PRICE", "close", "CLOSE"],
        "CHANGE_PERCENT": ["change_percent", "CHANGE_PERCENT", "changepercent"],
        "VOLUME": ["volume", "VOLUME"],
    }

    def find_field(record, candidates):
        for c in candidates:
            if c in record and is_numeric(record[c]):
                return True, record[c]
            # case-insensitive
            for k in record:
                if k.lower() == c.lower() and is_numeric(record[k]):
                    return True, record[k]
        return False, None

    price_ok, price_val = find_field(record, proprietary_field_map["PRICE"])
    change_ok, change_val = find_field(record, proprietary_field_map["CHANGE_PERCENT"])
    volume_ok, volume_val = find_field(record, proprietary_field_map["VOLUME"])

    checks.append({
        "name": "PRICE field present and numeric",
        "passed": price_ok,
        "detail": f"value={price_val}"
    })
    checks.append({
        "name": "CHANGE_PERCENT field present and numeric",
        "passed": change_ok,
        "detail": f"value={change_val}"
    })
    checks.append({
        "name": "VOLUME field present and numeric",
        "passed": volume_ok,
        "detail": f"value={volume_val}"
    })

    # ── CHECK 5: RSI present ──
    rsi_ok, rsi_val = find_field(record, [
        "RELATIVE_STRENGTH_INDEX_14", "relative_strength_index_14",
        "RSI", "rsi", "RSI_14", "rsi14"
    ])
    checks.append({
        "name": "RSI-14 field present and numeric",
        "passed": rsi_ok,
        "detail": f"value={rsi_val}"
    })

    # ── CHECK 6: MACD fields (all 3 components) ──
    macd_line_ok, macd_line_val = find_field(record, [
        "MACD_LEVEL_12_26", "macd_level_12_26", "MACD_LINE", "macd_line", "MACD", "macd"
    ])
    macd_signal_ok, macd_signal_val = find_field(record, [
        "MACD_SIGNAL_12_26", "macd_signal_12_26", "MACD_SIGNAL", "macd_signal"
    ])
    macd_hist_ok, macd_hist_val = find_field(record, [
        "MACD_HIST", "macd_hist", "MACD_HISTOGRAM", "macd_histogram"
    ])

    checks.append({
        "name": "MACD line (MACD_LEVEL_12_26) present and numeric",
        "passed": macd_line_ok,
        "detail": f"value={macd_line_val}"
    })
    checks.append({
        "name": "MACD signal (MACD_SIGNAL_12_26) present and numeric",
        "passed": macd_signal_ok,
        "detail": f"value={macd_signal_val}"
    })
    checks.append({
        "name": "MACD histogram (MACD_HIST) present and numeric",
        "passed": macd_hist_ok,
        "detail": f"value={macd_hist_val}"
    })

    # ── CHECK 7: SMAs (20, 50, 200) ──
    sma20_ok, sma20_val = find_field(record, ["SIMPLE_MOVING_AVERAGE_20", "sma_20", "SMA_20", "sma20"])
    sma50_ok, sma50_val = find_field(record, ["SIMPLE_MOVING_AVERAGE_50", "sma_50", "SMA_50", "sma50"])
    sma200_ok, sma200_val = find_field(record, ["SIMPLE_MOVING_AVERAGE_200", "sma_200", "SMA_200", "sma200"])

    checks.append({"name": "SMA-20 present and numeric", "passed": sma20_ok, "detail": f"{sma20_val}"})
    checks.append({"name": "SMA-50 present and numeric", "passed": sma50_ok, "detail": f"{sma50_val}"})
    checks.append({"name": "SMA-200 present and numeric", "passed": sma200_ok, "detail": f"{sma200_val}"})

    # ── CHECK 8: EMAs (20, 50, 200) ──
    ema20_ok, ema20_val = find_field(record, ["EXPONENTIAL_MOVING_AVERAGE_20", "ema_20", "EMA_20", "ema20"])
    ema50_ok, ema50_val = find_field(record, ["EXPONENTIAL_MOVING_AVERAGE_50", "ema_50", "EMA_50", "ema50"])
    ema200_ok, ema200_val = find_field(record, ["EXPONENTIAL_MOVING_AVERAGE_200", "ema_200", "EMA_200", "ema200"])

    checks.append({"name": "EMA-20 present and numeric", "passed": ema20_ok, "detail": f"{ema20_val}"})
    checks.append({"name": "EMA-50 present and numeric", "passed": ema50_ok, "detail": f"{ema50_val}"})
    checks.append({"name": "EMA-200 present and numeric", "passed": ema200_ok, "detail": f"{ema200_val}"})

    # ── CHECK 9: Bollinger Bands ──
    bb_upper_ok, bb_upper_val = find_field(record, [
        "BOLLINGER_UPPER_BAND_20", "bollinger_upper_band_20", "BB_UPPER", "bb_upper"
    ])
    bb_lower_ok, bb_lower_val = find_field(record, [
        "BOLLINGER_LOWER_BAND_20", "bollinger_lower_band_20", "BB_LOWER", "bb_lower"
    ])

    checks.append({"name": "Bollinger Upper Band (20) present and numeric", "passed": bb_upper_ok, "detail": f"{bb_upper_val}"})
    checks.append({"name": "Bollinger Lower Band (20) present and numeric", "passed": bb_lower_ok, "detail": f"{bb_lower_val}"})

    # ── CHECK 10: Stochastic %K and %D ──
    stoch_k_ok, stoch_k_val = find_field(record, [
        "STOCHASTIC_PERCENTK_14_3_3", "stochastic_percentk_14_3_3",
        "STOCH_K", "stoch_k", "STOCHASTIC_K"
    ])
    stoch_d_ok, stoch_d_val = find_field(record, [
        "STOCHASTIC_PERCENTD_14_3_3", "stochastic_percentd_14_3_3",
        "STOCH_D", "stoch_d", "STOCHASTIC_D"
    ])

    checks.append({"name": "Stochastic %K (14,3,3) present and numeric", "passed": stoch_k_ok, "detail": f"{stoch_k_val}"})
    checks.append({"name": "Stochastic %D (14,3,3) present and numeric", "passed": stoch_d_ok, "detail": f"{stoch_d_val}"})

    # ── CHECK 11: ATR ──
    atr_ok, atr_val = find_field(record, [
        "AVERAGE_TRUE_RANGE_14", "average_true_range_14", "ATR_14", "atr_14", "ATR"
    ])
    checks.append({"name": "ATR-14 present and numeric", "passed": atr_ok, "detail": f"{atr_val}"})

    # ── CHECK 12: Moving Averages Rating ──
    ma_rating_ok, ma_rating_val = find_field(record, [
        "MOVING_AVERAGES_RATING", "moving_averages_rating",
        "MA_RATING", "ma_rating"
    ])
    checks.append({"name": "MOVING_AVERAGES_RATING present and numeric", "passed": ma_rating_ok, "detail": f"{ma_rating_val}"})

    # ── CHECK 13: Price sanity for Tencent HK (should be between 100 and 1000 HKD) ──
    price_sane = False
    if price_ok and price_val is not None:
        try:
            pf = float(price_val)
            price_sane = 50.0 < pf < 2000.0
        except Exception:
            pass
    checks.append({
        "name": "PRICE in plausible HKD range (50–2000)",
        "passed": price_sane,
        "detail": f"price={price_val}"
    })

    # ── SCORING ──
    # Weight distribution:
    # file_exists: 0.05
    # valid_json: 0.05
    # non_empty: 0.03
    # symbol_tencent: 0.05
    # price, change, volume: 0.03 each = 0.09
    # rsi: 0.05
    # macd x3: 0.04 each = 0.12
    # sma x3: 0.03 each = 0.09
    # ema x3: 0.03 each = 0.09
    # bb x2: 0.04 each = 0.08
    # stoch x2: 0.04 each = 0.08
    # atr: 0.04
    # ma_rating: 0.04
    # price_sane: 0.04
    # total = 0.05+0.05+0.03+0.05+0.09+0.05+0.12+0.09+0.09+0.08+0.08+0.04+0.04+0.04 = 0.95 → normalize

    weights = {
        "technical_snapshot.json exists": 0.05,
        "valid JSON": 0.05,
        "non-empty records": 0.03,
        "symbol is Tencent (700/HKEX:700)": 0.05,
        "PRICE field present and numeric": 0.03,
        "CHANGE_PERCENT field present and numeric": 0.03,
        "VOLUME field present and numeric": 0.03,
        "RSI-14 field present and numeric": 0.05,
        "MACD line (MACD_LEVEL_12_26) present and numeric": 0.04,
        "MACD signal (MACD_SIGNAL_12_26) present and numeric": 0.04,
        "MACD histogram (MACD_HIST) present and numeric": 0.04,
        "SMA-20 present and numeric": 0.03,
        "SMA-50 present and numeric": 0.03,
        "SMA-200 present and numeric": 0.03,
        "EMA-20 present and numeric": 0.03,
        "EMA-50 present and numeric": 0.03,
        "EMA-200 present and numeric": 0.03,
        "Bollinger Upper Band (20) present and numeric": 0.04,
        "Bollinger Lower Band (20) present and numeric": 0.04,
        "Stochastic %K (14,3,3) present and numeric": 0.04,
        "Stochastic %D (14,3,3) present and numeric": 0.04,
        "ATR-14 present and numeric": 0.04,
        "MOVING_AVERAGES_RATING present and numeric": 0.04,
        "PRICE in plausible HKD range (50–2000)": 0.04,
    }

    score = 0.0
    for c in checks:
        if c["passed"] and c["name"] in weights:
            score += weights[c["name"]]

    # A "pass" requires: file + valid JSON + symbol + price + at least 16 of remaining checks
    core_passed = (
        file_exists
        and valid_json
        and is_tencent
        and price_ok
        and rsi_ok
        and macd_line_ok
        and macd_signal_ok
        and macd_hist_ok
        and (sma20_ok or sma50_ok or sma200_ok)
        and (ema20_ok or ema50_ok or ema200_ok)
        and bb_upper_ok
        and bb_lower_ok
        and stoch_k_ok
        and atr_ok
    )

    return {
        "passed": bool(core_passed),
        "score": round(min(score, 1.0), 4),
        "checks": checks
    }

if __name__ == "__main__":
    ws = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    result = run_eval(ws)
    print(json.dumps(result, indent=2))