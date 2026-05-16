import os
import json
import random
import datetime

random.seed(42)

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "data",
    "data/history",
    "data/reports",
    "data/backtest",
    "subskills/config-optimization",
    "subskills/daily-recommendation",
    "subskills/sector-rotation",
    "logs",
    "config",
    "tests",
]
for d in dirs:
    os.makedirs(d, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "config/settings.yaml": """\
market: CN_A_SHARE
horizon_days: 5
signal_threshold: 0.65
sector_filter: true
capital_flow_weight: 0.3
momentum_weight: 0.4
sentiment_weight: 0.3
""",
    "config/sector_map.json": json.dumps({
        "002594": "新能源汽车",
        "300750": "锂电池",
        "600519": "白酒",
        "000858": "白酒",
        "601318": "保险",
    }, ensure_ascii=False, indent=2),
    "logs/engine_2026-01-15.log": """\
[INFO] 2026-01-15 09:30:00 Signal engine started
[INFO] 2026-01-15 09:30:01 Loaded 4823 tickers
[INFO] 2026-01-15 09:30:05 Sector rotation detected: 新能源
[INFO] 2026-01-15 09:30:07 Candidates found: 3
[INFO] 2026-01-15 09:30:08 Score: 0.72 -> BUY signal
""",
    "logs/engine_2026-01-16.log": """\
[INFO] 2026-01-16 09:30:00 Signal engine started
[WARN] 2026-01-16 09:30:03 Low market breadth detected
[INFO] 2026-01-16 09:30:06 Candidates found: 0
[INFO] 2026-01-16 09:30:07 NO_TRADE signal issued
""",
    "data/backtest/backtest_2025_Q4.json": json.dumps({
        "period": "2025-10-01 to 2025-12-31",
        "total_signals": 47,
        "win_rate": 0.617,
        "avg_return": 0.034,
        "max_drawdown": -0.081,
    }, indent=2),
    "data/history/market_index_2026-01.csv": """\
date,sh_index,sz_index,vol_billion
2026-01-02,3318.45,2115.67,892.3
2026-01-05,3342.11,2134.22,945.8
2026-01-06,3329.88,2128.55,881.2
2026-01-07,3355.00,2145.90,1023.4
2026-01-08,3361.77,2152.30,988.7
""",
    "subskills/sector-rotation/sector_weights.json": json.dumps({
        "date": "2026-02-10",
        "weights": {
            "新能源": 0.22,
            "半导体": 0.18,
            "消费": 0.15,
            "医药": 0.12,
            "金融": 0.10,
        }
    }, ensure_ascii=False, indent=2),
    "subskills/config-optimization/last_run.json": json.dumps({
        "last_optimization": "2026-02-01",
        "params_used": {"aggressive_mode": True, "lookback_days": 10},
        "sharpe_ratio": 1.43,
    }, indent=2),
    "tests/test_signal_engine.py": """\
import pytest
# Placeholder tests - do not modify
def test_score_range():
    pass

def test_no_trade_message():
    pass
""",
    "data/history/capital_flow_2026-02-10.json": json.dumps({
        "date": "2026-02-10",
        "net_inflow_billion": 23.4,
        "top_sectors": ["半导体", "新能源汽车", "军工"],
        "north_bound_flow": 8.2,
    }, ensure_ascii=False, indent=2),
    "data/history/capital_flow_2026-02-11.json": json.dumps({
        "date": "2026-02-11",
        "net_inflow_billion": -5.1,
        "top_sectors": ["防御", "公用事业"],
        "north_bound_flow": -2.3,
    }, ensure_ascii=False, indent=2),
}

for path, content in distractors.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

# ── pre-existing decision_log.jsonl (missing the target date 2026-02-12) ────
old_entries = [
    {
        "prediction_date": "2026-02-10",
        "analysis_date": "2026-02-10",
        "signal": "BUY",
        "score": 0.74,
        "candidates": [
            {"ticker": "300750", "name": "宁德时代", "sector": "锂电池", "entry_price": 245.60},
            {"ticker": "002594", "name": "比亚迪", "sector": "新能源汽车", "entry_price": 312.40},
        ],
        "recommendation": "建议关注锂电板块短线机会",
        "created_at": "2026-02-10T09:45:00",
    },
    {
        "prediction_date": "2026-02-11",
        "analysis_date": "2026-02-11",
        "signal": "NO_TRADE",
        "score": 0.41,
        "candidates": [],
        "no_recommendation_message": "当前暂无可执行短线买入标的",
        "reason": "市场情绪低迷，资金净流出，建议观望",
        "next_action": "等待市场企稳后重新评估",
        "created_at": "2026-02-11T09:45:00",
    },
]

with open("data/decision_log.jsonl", "w", encoding="utf-8") as f:
    for entry in old_entries:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

# ── market close data for 2026-02-12 and 2026-02-13 ─────────────────────────
market_close_0212 = {
    "date": "2026-02-12",
    "closes": {
        "300750": 251.30,
        "002594": 318.80,
        "600519": 1723.50,
        "000858": 156.20,
        "601318": 45.88,
        "600036": 33.45,
        "000001": 12.34,
        "002415": 28.90,
    }
}
market_close_0213 = {
    "date": "2026-02-13",
    "closes": {
        "300750": 258.70,
        "002594": 325.60,
        "600519": 1698.20,
        "000858": 161.80,
        "601318": 46.22,
        "600036": 34.10,
        "000001": 12.55,
        "002415": 29.45,
    }
}

for data_obj in [market_close_0212, market_close_0213]:
    fname = f"data/history/market_close_{data_obj['date']}.json"
    with open(fname, "w", encoding="utf-8") as f:
        json.dump(data_obj, f, ensure_ascii=False, indent=2)

# ── main.py: the core CLI dispatcher ────────────────────────────────────────
main_py = '''\
#!/usr/bin/env python3
"""A-Share Short-Term Decision CLI"""
import sys
import json
import os
import datetime
import argparse
import random
import pathlib

DATA_DIR = pathlib.Path("data")
LOG_FILE = DATA_DIR / "decision_log.jsonl"
REPORTS_DIR = DATA_DIR / "reports"
DATA_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)

random.seed(0)

MOCK_TICKERS = {
    "300750": {"name": "宁德时代", "sector": "锂电池"},
    "002594": {"name": "比亚迪", "sector": "新能源汽车"},
    "600519": {"name": "贵州茅台", "sector": "白酒"},
    "002415": {"name": "海康威视", "sector": "安防"},
    "000001": {"name": "平安银行", "sector": "银行"},
}


def _parse_date(d):
    d = str(d).strip()
    if len(d) == 8:
        return datetime.datetime.strptime(d, "%Y%m%d").date()
    return datetime.datetime.strptime(d, "%Y-%m-%d").date()


def _load_market_close(date_str):
    p = DATA_DIR / "history" / f"market_close_{date_str}.json"
    if p.exists():
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return None


def short_term_signal_engine(analysis_date=None):
    if analysis_date is None:
        analysis_date = datetime.date.today().isoformat()
    dt = _parse_date(analysis_date)
    date_str = dt.isoformat()

    # Deterministic seed based on date
    seed = sum(ord(c) for c in date_str)
    rng = random.Random(seed)

    score = round(rng.uniform(0.38, 0.89), 3)
    has_candidates = score >= 0.55

    result = {
        "analysis_date": date_str,
        "score": score,
    }

    if has_candidates:
        candidates = []
        close_data = _load_market_close(date_str)
        ticker_list = list(MOCK_TICKERS.items())
        rng.shuffle(ticker_list)
        for ticker, info in ticker_list[:2]:
            entry_price = round(rng.uniform(20, 350), 2)
            if close_data and ticker in close_data.get("closes", {}):
                entry_price = close_data["closes"][ticker]
            candidates.append({
                "ticker": ticker,
                "name": info["name"],
                "sector": info["sector"],
                "entry_price": entry_price,
                "signal_strength": round(rng.uniform(0.6, 0.95), 3),
            })
        result["signal"] = "BUY"
        result["candidates"] = candidates
        result["recommendation"] = f"建议关注{candidates[0][\'sector\']}板块短线机会"
    else:
        result["signal"] = "NO_TRADE"
        result["candidates"] = []
        result["no_recommendation_message"] = "当前暂无可执行短线买入标的"
        result["reason"] = "综合评分未达到入场阈值，市场信号偏弱"
        result["next_action"] = "建议观望，等待市场方向明确后重新评估"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def run_prediction_for_date(analysis_date):
    dt = _parse_date(analysis_date)
    date_str = dt.isoformat()
    result = short_term_signal_engine(date_str)
    entry = dict(result)
    entry["prediction_date"] = date_str
    entry["created_at"] = datetime.datetime.now().isoformat()

    # Append to decision log
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\\n")

    print(f"[OK] Prediction for {date_str} appended to {LOG_FILE}")
    return entry


def compare_prediction_with_market(prediction_date, actual_date=None):
    pred_dt = _parse_date(prediction_date)
    pred_str = pred_dt.isoformat()

    if actual_date is None:
        actual_dt = pred_dt + datetime.timedelta(days=1)
    else:
        actual_dt = _parse_date(actual_date)
    actual_str = actual_dt.isoformat()

    # Load prediction from log
    prediction = None
    if LOG_FILE.exists():
        with open(LOG_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if obj.get("prediction_date") == pred_str or obj.get("analysis_date") == pred_str:
                        prediction = obj
                except Exception:
                    pass

    if prediction is None:
        print(f"[WARN] No prediction found for {pred_str}, auto-generating...")
        prediction = short_term_signal_engine(pred_str)

    candidates = prediction.get("candidates", [])
    if not candidates:
        result = {
            "prediction_date": pred_str,
            "actual_date": actual_str,
            "signal": prediction.get("signal", "NO_TRADE"),
            "no_recommendation_message": prediction.get("no_recommendation_message", "当前暂无可执行短线买入标的"),
            "per_stock_returns": [],
            "summary": {"num_candidates": 0, "avg_return": None, "win_rate": None},
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    close_data = _load_market_close(actual_str)
    per_stock = []
    for c in candidates:
        ticker = c["ticker"]
        entry_price = c.get("entry_price", 0)
        actual_close = None
        if close_data and ticker in close_data.get("closes", {}):
            actual_close = close_data["closes"][ticker]
        if actual_close and entry_price:
            ret = round((actual_close - entry_price) / entry_price, 4)
        else:
            ret = None
        per_stock.append({
            "ticker": ticker,
            "name": c.get("name"),
            "entry_price": entry_price,
            "actual_close": actual_close,
            "return": ret,
        })

    valid_returns = [s["return"] for s in per_stock if s["return"] is not None]
    avg_ret = round(sum(valid_returns) / len(valid_returns), 4) if valid_returns else None
    win_rate = round(sum(1 for r in valid_returns if r > 0) / len(valid_returns), 4) if valid_returns else None

    result = {
        "prediction_date": pred_str,
        "actual_date": actual_str,
        "signal": prediction.get("signal"),
        "per_stock_returns": per_stock,
        "summary": {
            "num_candidates": len(candidates),
            "avg_return": avg_ret,
            "win_rate": win_rate,
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def generate_daily_report(analysis_date):
    dt = _parse_date(analysis_date)
    date_str = dt.isoformat()
    signal_result = short_term_signal_engine(date_str)

    report = {
        "report_date": date_str,
        "generated_at": datetime.datetime.now().isoformat(),
        "signal_summary": {
            "date": date_str,
            "score": signal_result.get("score"),
            "signal": signal_result.get("signal"),
            "candidates_count": len(signal_result.get("candidates", [])),
        },
        "candidates": signal_result.get("candidates", []),
        "recommendation": signal_result.get("recommendation",
                          signal_result.get("no_recommendation_message", "当前暂无可执行短线买入标的")),
        "risk_note": "短线交易具有较高风险，以上仅供参考，请结合个人风险承受能力决策。",
    }

    out_path = REPORTS_DIR / f"daily_report_{date_str}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"[OK] Daily report saved to {out_path}")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 main.py <command> [options]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "short_term_signal_engine":
        parser = argparse.ArgumentParser()
        parser.add_argument("--date", default=None)
        args, _ = parser.parse_known_args(sys.argv[2:])
        short_term_signal_engine(args.date)

    elif command == "run_prediction_for_date":
        parser = argparse.ArgumentParser()
        parser.add_argument("--date", required=True)
        args, _ = parser.parse_known_args(sys.argv[2:])
        run_prediction_for_date(args.date)

    elif command == "compare_prediction_with_market":
        parser = argparse.ArgumentParser()
        parser.add_argument("--prediction-date", required=True)
        parser.add_argument("--actual-date", default=None)
        args, _ = parser.parse_known_args(sys.argv[2:])
        compare_prediction_with_market(args.prediction_date, args.actual_date)

    elif command == "generate_daily_report":
        parser = argparse.ArgumentParser()
        parser.add_argument("--date", required=True)
        args, _ = parser.parse_known_args(sys.argv[2:])
        generate_daily_report(args.date)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

with open("main.py", "w", encoding="utf-8") as f:
    f.write(main_py)

# ── subskills stubs (already exist per SKILL.md) ────────────────────────────
optimize_script = '''\
#!/usr/bin/env python3
"""Config optimization subskill - stub"""
import argparse, json, datetime, pathlib

parser = argparse.ArgumentParser()
parser.add_argument("--analysis-period", required=True)
args = parser.parse_args()

out = pathlib.Path("data/backtest/optimization_result.json")
result = {
    "analysis_period": args.analysis_period,
    "optimized_at": datetime.datetime.now().isoformat(),
    "best_params": {"signal_threshold": 0.58, "momentum_weight": 0.42, "capital_flow_weight": 0.31},
    "sharpe_ratio": 1.51,
}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(f"[OK] Optimization result saved to {out}")
'''

recommend_script = '''\
#!/usr/bin/env python3
"""Daily recommendation subskill - stub"""
import argparse, json, datetime, pathlib, subprocess, sys

parser = argparse.ArgumentParser()
parser.add_argument("--date", required=True)
args = parser.parse_args()

result = subprocess.run(
    [sys.executable, "main.py", "generate_daily_report", "--date", args.date],
    capture_output=True, text=True
)
print(result.stdout)
if result.returncode != 0:
    print(result.stderr)
    sys.exit(result.returncode)
'''

with open("subskills/config-optimization/optimize_from_aggressive.py", "w", encoding="utf-8") as f:
    f.write(optimize_script)

with open("subskills/daily-recommendation/generate_daily_recommendation.py", "w", encoding="utf-8") as f:
    f.write(recommend_script)

# ── old stale report to act as distractor ────────────────────────────────────
stale_report = {
    "report_date": "2026-02-05",
    "generated_at": "2026-02-05T10:00:00",
    "signal_summary": {"date": "2026-02-05", "score": 0.81, "signal": "BUY", "candidates_count": 2},
    "recommendation": "建议关注半导体板块",
}
with open("data/reports/daily_report_2026-02-05.json", "w", encoding="utf-8") as f:
    json.dump(stale_report, f, ensure_ascii=False, indent=2)

print("Workspace initialized successfully.")
print("Files created:")
for root, dirs_, files in os.walk("."):
    for fname in files:
        fpath = os.path.join(root, fname)
        print(f"  {fpath}")