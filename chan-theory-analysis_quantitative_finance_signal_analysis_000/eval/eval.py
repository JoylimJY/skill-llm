#!/usr/bin/env python3
"""
Evaluation script for the chan-theory screening task.
Checks that the agent:
1. Ran analyze.py on all three tickers (BTC-USD, 0700.HK, AAPL)
2. Produced screening_report.json with correct structure
3. Correctly applied 缠论 买卖点 classification rules
4. Correctly applied 井论 (大井/小井) rules to determine signal type
5. Correctly interpreted 关键位置 percentage zones
6. Correctly identified 背驰 signals
"""

import sys
import json
import hashlib
import random
import math
from pathlib import Path

def get_deterministic_seed(ticker: str) -> int:
    h = hashlib.md5(ticker.encode()).hexdigest()
    return int(h[:8], 16)

def compute_expected(ticker: str) -> dict:
    """Reproduce the exact same deterministic analysis as analyze.py"""
    seed = get_deterministic_seed(ticker)
    rng = random.Random(seed)

    bi_count = rng.choice([3, 4, 5, 6, 7, 8])
    current_bi_type = rng.choice(["上涨笔", "下跌笔"])
    bi_amplitude = round(rng.uniform(-45.0, 45.0), 2)
    beichi = rng.random() < 0.4

    zhongshu_count = rng.randint(1, 3)
    trend_type = "盘整" if zhongshu_count == 1 else "趋势"

    high_price = round(rng.uniform(50000, 80000) if "BTC" in ticker else
                      rng.uniform(200, 400) if ".HK" in ticker else
                      rng.uniform(100, 300), 2)
    low_price = round(high_price * rng.uniform(0.55, 0.85), 2)
    position_pct = rng.randint(10, 95)

    jing_type = None
    wave1 = wave3 = wave5 = None
    if bi_count >= 5:
        wave1 = round(rng.uniform(5, 20), 2)
        wave3 = round(rng.uniform(5, 20), 2)
        wave5 = round(rng.uniform(5, 20), 2)
        if wave5 > wave3 and wave5 > wave1:
            jing_type = "大井"
        elif wave5 > wave1 or wave5 > wave3:
            jing_type = "小井"
        else:
            jing_type = None

    macd_area_current = round(rng.uniform(100, 500), 1)
    macd_area_prev = round(rng.uniform(100, 600), 1)
    macd_beichi = macd_area_current < macd_area_prev

    has_beichi = beichi or macd_beichi

    # Derive buy/sell point type per 缠论 rules
    # 第1类: 趋势背驰点
    # 第2类: 第1类后次级别回抽 / 大井→第1类 / 小井→第2类
    # 第3类: 次级别离开后不回抽

    if jing_type == "大井":
        signal_type = "第1类买卖点"
    elif jing_type == "小井":
        signal_type = "第2类买卖点"
    elif has_beichi and trend_type == "趋势":
        signal_type = "第1类买卖点"
    elif has_beichi and trend_type == "盘整":
        signal_type = "第3类买卖点"
    else:
        signal_type = None

    # Position zone
    if position_pct < 30:
        position_zone = "低位区间"
    elif position_pct > 70:
        position_zone = "高位区间"
    else:
        position_zone = "中性区间"

    return {
        "ticker": ticker,
        "bi_count": bi_count,
        "current_bi": current_bi_type,
        "trend_type": trend_type,
        "zhongshu_count": zhongshu_count,
        "has_beichi": has_beichi,
        "jing_type": jing_type,
        "signal_type": signal_type,
        "position_pct": position_pct,
        "position_zone": position_zone,
    }

def run_eval(workspace: str):
    workspace_path = Path(workspace)
    checks = []
    total_score = 0.0
    score_weights = {
        "file_exists": 0.10,
        "all_tickers_present": 0.10,
        "bi_count_BTC-USD": 0.06,
        "bi_count_0700.HK": 0.06,
        "bi_count_AAPL": 0.06,
        "trend_type_BTC-USD": 0.05,
        "trend_type_0700.HK": 0.05,
        "trend_type_AAPL": 0.05,
        "jing_type_BTC-USD": 0.06,
        "jing_type_0700.HK": 0.06,
        "jing_type_AAPL": 0.06,
        "signal_type_BTC-USD": 0.07,
        "signal_type_0700.HK": 0.07,
        "signal_type_AAPL": 0.07,
        "position_zone_BTC-USD": 0.04,
        "position_zone_0700.HK": 0.04,
        "position_zone_AAPL": 0.04,
    }

    # 1. Find screening_report.json
    report_files = list(workspace_path.rglob("screening_report.json"))
    if not report_files:
        checks.append({"name": "file_exists", "passed": False,
                       "detail": "screening_report.json not found anywhere in workspace"})
        return {"passed": False, "score": 0.0, "checks": checks}

    report_path = report_files[0]
    checks.append({"name": "file_exists", "passed": True,
                   "detail": f"Found at {report_path}"})
    total_score += score_weights["file_exists"]

    # 2. Load and parse JSON
    try:
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
    except Exception as e:
        checks.append({"name": "parse_json", "passed": False,
                       "detail": f"Failed to parse JSON: {e}"})
        return {"passed": False, "score": total_score, "checks": checks}

    # Normalize: accept list of dicts or dict keyed by ticker
    tickers = ["BTC-USD", "0700.HK", "AAPL"]
    ticker_data = {}

    if isinstance(report, list):
        for item in report:
            if isinstance(item, dict):
                t = item.get("ticker") or item.get("symbol") or item.get("asset")
                if t in tickers:
                    ticker_data[t] = item
    elif isinstance(report, dict):
        for t in tickers:
            if t in report:
                ticker_data[t] = report[t]
            else:
                # Try searching nested
                for k, v in report.items():
                    if isinstance(v, dict) and (v.get("ticker") == t or v.get("symbol") == t):
                        ticker_data[t] = v

    all_present = all(t in ticker_data for t in tickers)
    checks.append({"name": "all_tickers_present", "passed": all_present,
                   "detail": f"Found tickers: {list(ticker_data.keys())}"})
    if all_present:
        total_score += score_weights["all_tickers_present"]

    # 3. Per-ticker checks
    for ticker in tickers:
        expected = compute_expected(ticker)
        safe_t = ticker.replace("-", "_").replace(".", "_")

        if ticker not in ticker_data:
            for check_key in ["bi_count", "trend_type", "jing_type", "signal_type", "position_zone"]:
                checks.append({
                    "name": f"{check_key}_{ticker}",
                    "passed": False,
                    "detail": f"Ticker {ticker} missing from report"
                })
            continue

        data = ticker_data[ticker]

        def get_field(d, *keys):
            """Try multiple possible key names"""
            for k in keys:
                if k in d:
                    return d[k]
                # nested search
                for v in d.values():
                    if isinstance(v, dict) and k in v:
                        return v[k]
            return None

        # Check bi_count
        bi_val = get_field(data, "bi_count", "笔数", "stroke_count", "bi_analysis")
        if isinstance(bi_val, dict):
            bi_val = bi_val.get("count", bi_val.get("bi_count"))
        bi_ok = False
        try:
            bi_ok = int(bi_val) == expected["bi_count"]
        except Exception:
            pass
        checks.append({
            "name": f"bi_count_{ticker}",
            "passed": bi_ok,
            "detail": f"Expected bi_count={expected['bi_count']}, got={bi_val}"
        })
        if bi_ok:
            total_score += score_weights[f"bi_count_{ticker}"]

        # Check trend_type
        trend_val = get_field(data, "trend_type", "走势类型", "trend", "trend_classification")
        if isinstance(trend_val, dict):
            trend_val = trend_val.get("type", trend_val.get("trend_type"))
        trend_ok = False
        if trend_val:
            trend_ok = str(trend_val).strip() == expected["trend_type"]
        checks.append({
            "name": f"trend_type_{ticker}",
            "passed": trend_ok,
            "detail": f"Expected trend_type={expected['trend_type']}, got={trend_val}"
        })
        if trend_ok:
            total_score += score_weights[f"trend_type_{ticker}"]

        # Check jing_type
        jing_val = get_field(data, "jing_type", "井型", "jing", "well_type")
        if isinstance(jing_val, dict):
            jing_val = jing_val.get("type", jing_val.get("jing_type"))
        jing_ok = False
        if expected["jing_type"] is None:
            jing_ok = jing_val is None or str(jing_val).strip().lower() in ["null", "none", "无", "n/a", "", "不适用"]
        else:
            jing_ok = jing_val is not None and str(jing_val).strip() == expected["jing_type"]
        checks.append({
            "name": f"jing_type_{ticker}",
            "passed": jing_ok,
            "detail": f"Expected jing_type={expected['jing_type']}, got={jing_val}"
        })
        if jing_ok:
            total_score += score_weights[f"jing_type_{ticker}"]

        # Check signal_type (most critical proprietary logic)
        signal_val = get_field(data, "signal_type", "买卖点", "buy_sell_point",
                               "signal_classification", "点位类型", "trade_signal")
        if isinstance(signal_val, dict):
            signal_val = signal_val.get("type", signal_val.get("signal_type"))
        signal_ok = False
        if expected["signal_type"] is None:
            signal_ok = signal_val is None or str(signal_val).strip().lower() in [
                "null", "none", "无", "n/a", "", "不适用", "无信号", "no signal"
            ]
        else:
            if signal_val is not None:
                normalized = str(signal_val).strip()
                signal_ok = normalized == expected["signal_type"]
        checks.append({
            "name": f"signal_type_{ticker}",
            "passed": signal_ok,
            "detail": f"Expected signal_type='{expected['signal_type']}', got='{signal_val}'"
        })
        if signal_ok:
            total_score += score_weights[f"signal_type_{ticker}"]

        # Check position_zone
        zone_val = get_field(data, "position_zone", "位置区间", "zone", "price_zone",
                             "position_classification", "区间")
        if isinstance(zone_val, dict):
            zone_val = zone_val.get("zone", zone_val.get("position_zone"))
        zone_ok = False
        if zone_val:
            zone_ok = str(zone_val).strip() == expected["position_zone"]
        checks.append({
            "name": f"position_zone_{ticker}",
            "passed": zone_ok,
            "detail": f"Expected position_zone={expected['position_zone']}, got={zone_val}"
        })
        if zone_ok:
            total_score += score_weights[f"position_zone_{ticker}"]

    total_score = round(min(total_score, 1.0), 4)
    passed = total_score >= 0.70 and all(c["passed"] for c in checks if c["name"] in [
        "file_exists", "all_tickers_present"
    ])

    return {
        "passed": passed,
        "score": total_score,
        "checks": checks
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"passed": False, "score": 0.0,
                          "checks": [{"name": "invocation", "passed": False,
                                      "detail": "No workspace path provided"}]}))
        sys.exit(1)

    result = run_eval(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))