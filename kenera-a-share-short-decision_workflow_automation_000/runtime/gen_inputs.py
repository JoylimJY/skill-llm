import os
import json
import random
import pathlib

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "data",
    "data/archive",
    "data/cache",
    "subskills/config-optimization",
    "subskills/daily-recommendation",
    "logs",
    "config",
    "models",
    "reports",
    "tests",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
distractors = {
    "config/market_params.json": json.dumps({
        "market": "A-share",
        "horizon": "1-5d",
        "universe": "CSI500",
        "signal_threshold": 65,
        "last_updated": "2026-03-01"
    }, indent=2, ensure_ascii=False),

    "config/sector_weights.json": json.dumps({
        "tech": 0.25,
        "consumer": 0.20,
        "finance": 0.15,
        "energy": 0.10,
        "healthcare": 0.30
    }, indent=2),

    "data/archive/signals_2026_02.jsonl": "\n".join([
        json.dumps({"date": "2026-02-10", "score": 72, "status": "BUY", "candidates": ["600519", "000858"]})
        for _ in range(5)
    ]),

    "data/cache/sector_rotation_cache.json": json.dumps({
        "last_updated": "2026-03-09",
        "hot_sectors": ["半导体", "新能源", "消费"],
        "cold_sectors": ["钢铁", "煤炭"]
    }, ensure_ascii=False, indent=2),

    "logs/engine_debug.log": "\n".join([
        f"[2026-03-0{i}] INFO: signal engine completed, score={random.randint(55,85)}"
        for i in range(1, 10)
    ]),

    "models/momentum_model_v2.json": json.dumps({
        "version": "2.0",
        "features": ["price_momentum_5d", "volume_ratio", "sector_flow"],
        "weights": [0.4, 0.35, 0.25],
        "trained_on": "2026-01-01 to 2026-02-28"
    }, indent=2),

    "tests/test_signal_engine.py": (
        "import pytest\n"
        "def test_score_range():\n"
        "    assert 0 <= 75 <= 100\n"
        "def test_no_trade_message():\n"
        "    msg = '当前暂无可执行短线买入标的'\n"
        "    assert '暂无' in msg\n"
    ),

    "data/archive/comparison_2026_02_13.json": json.dumps({
        "prediction_date": "2026-02-12",
        "actual_date": "2026-02-13",
        "returns": {"000858": 0.032, "600519": -0.008},
        "avg_return": 0.012
    }, indent=2),

    "reports/weekly_summary_2026_W09.txt": (
        "Week 9 Summary\n"
        "Top performers: 半导体板块 +3.2%\n"
        "Signal accuracy: 68%\n"
        "Trades executed: 12\n"
    ),

    "config/trading_calendar_2026.json": json.dumps({
        "trading_days": [
            "2026-03-09", "2026-03-10", "2026-03-11", "2026-03-12", "2026-03-13"
        ],
        "holidays": ["2026-04-04", "2026-04-05", "2026-05-01"]
    }, indent=2),

    "data/cache/capital_flow_20260309.json": json.dumps({
        "date": "2026-03-09",
        "north_bound_net": 12.5,
        "sector_inflow": {"半导体": 8.3, "新能源": 5.1},
        "unit": "亿元"
    }, ensure_ascii=False, indent=2),

    "subskills/config-optimization/last_run.log": (
        "Last optimization run: 2026-02-28\n"
        "Period: 2026-02-01 to 2026-02-28\n"
        "Best config: aggressive_v3\n"
        "Score improvement: +4.2%\n"
    ),
}

for rel_path, content in distractors.items():
    full = os.path.join(workspace, rel_path)
    with open(full, "w", encoding="utf-8") as f:
        f.write(content)

# ── main.py  (the actual skill entry point) ─────────────────────────────────
main_py = r'''#!/usr/bin/env python3
"""
A-Share Short-Term Decision Skill - main.py
All tool contracts as documented in SKILL.md
"""
import argparse
import json
import os
import sys
import random
from datetime import datetime, timedelta
from pathlib import Path

DATA_DIR = Path("data")
DECISION_LOG = DATA_DIR / "decision_log.jsonl"

random.seed(int(datetime.now().strftime("%Y%m%d")) % 9999 + 1)

MOCK_CANDIDATES = {
    "2026-03-10": [
        {"code": "300750", "name": "宁德时代", "score": 81, "sector": "新能源"},
        {"code": "000063", "name": "中兴通讯", "score": 78, "sector": "半导体"},
        {"code": "601888", "name": "中国中免", "score": 74, "sector": "消费"},
    ],
    "2026-03-11": [
        {"code": "300750", "name": "宁德时代", "score": 79, "sector": "新能源"},
    ],
}

MOCK_CLOSES = {
    "2026-03-11": {"300750": 245.60, "000063": 38.92, "601888": 165.30},
    "2026-03-12": {"300750": 251.80, "000063": 39.45, "601888": 163.10},
}

MOCK_CLOSES_PREV = {
    "2026-03-10": {"300750": 239.50, "000063": 37.88, "601888": 162.70},
    "2026-03-11": {"300750": 245.60, "000063": 38.92, "601888": 165.30},
}


def normalize_date(date_str):
    date_str = date_str.strip()
    if len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
    return date_str


def short_term_signal_engine(analysis_date=None):
    if analysis_date is None:
        analysis_date = datetime.today().strftime("%Y-%m-%d")
    analysis_date = normalize_date(analysis_date)

    candidates = MOCK_CANDIDATES.get(analysis_date, [])

    if not candidates:
        result = {
            "analysis_date": analysis_date,
            "status": "NO_TRADE",
            "weighted_score": 0,
            "candidates": [],
            "no_recommendation_message": "当前暂无可执行短线买入标的",
            "reason": "市场情绪偏弱，量能不足，建议观望",
            "next_action": "等待放量突破信号后再介入",
        }
    else:
        avg_score = round(sum(c["score"] for c in candidates) / len(candidates), 2)
        result = {
            "analysis_date": analysis_date,
            "status": "BUY_SIGNAL",
            "weighted_score": avg_score,
            "candidates": candidates,
            "sector_rotation": ["新能源", "半导体"],
            "capital_flow_confirmed": True,
            "recommendation": f"建议关注 {len(candidates)} 只短线标的，信号强度 {avg_score}",
        }

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def run_prediction_for_date(analysis_date):
    analysis_date = normalize_date(analysis_date)
    result = short_term_signal_engine(analysis_date)

    snapshot = {
        "prediction_date": analysis_date,
        "timestamp": datetime.now().isoformat(),
        "signal_result": result,
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DECISION_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

    print(f"[OK] Prediction for {analysis_date} appended to {DECISION_LOG}")
    return snapshot


def compare_prediction_with_market(prediction_date, actual_date=None):
    prediction_date = normalize_date(prediction_date)

    if actual_date is None:
        dt = datetime.strptime(prediction_date, "%Y-%m-%d")
        actual_date = (dt + timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        actual_date = normalize_date(actual_date)

    # Load from log or auto-generate
    snapshot = None
    if DECISION_LOG.exists():
        with open(DECISION_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    if entry.get("prediction_date") == prediction_date:
                        snapshot = entry
                        break
                except json.JSONDecodeError:
                    continue

    if snapshot is None:
        print(f"[WARN] No prediction found for {prediction_date}, auto-generating...")
        snapshot = run_prediction_for_date(prediction_date)

    candidates = snapshot.get("signal_result", {}).get("candidates", [])
    closes_actual = MOCK_CLOSES.get(actual_date, {})
    closes_pred = MOCK_CLOSES_PREV.get(prediction_date, {})

    per_stock = {}
    for c in candidates:
        code = c["code"]
        if code in closes_actual and code in closes_pred:
            ret = round((closes_actual[code] - closes_pred[code]) / closes_pred[code], 4)
            per_stock[code] = {
                "name": c["name"],
                "predicted_score": c["score"],
                "buy_price": closes_pred[code],
                "actual_close": closes_actual[code],
                "return": ret,
            }

    avg_return = round(sum(v["return"] for v in per_stock.values()) / len(per_stock), 4) if per_stock else 0.0

    result = {
        "prediction_date": prediction_date,
        "actual_date": actual_date,
        "per_stock_returns": per_stock,
        "summary": {
            "num_candidates": len(candidates),
            "num_compared": len(per_stock),
            "avg_return": avg_return,
            "win_rate": round(sum(1 for v in per_stock.values() if v["return"] > 0) / max(len(per_stock), 1), 4),
        },
    }

    # Persist comparison result
    out_file = DATA_DIR / f"comparison_{prediction_date.replace('-','')}_{actual_date.replace('-','')}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[OK] Comparison saved to {out_file}")
    return result


def generate_daily_report(analysis_date):
    analysis_date = normalize_date(analysis_date)
    signal = short_term_signal_engine(analysis_date)

    report = {
        "report_date": analysis_date,
        "generated_at": datetime.now().isoformat(),
        "market_intelligence": {
            "status": signal.get("status"),
            "weighted_score": signal.get("weighted_score", 0),
            "candidates_count": len(signal.get("candidates", [])),
            "candidates": signal.get("candidates", []),
            "sector_rotation": signal.get("sector_rotation", []),
            "capital_flow_confirmed": signal.get("capital_flow_confirmed", False),
        },
        "recommendation": signal.get("recommendation") or signal.get("no_recommendation_message"),
        "no_recommendation_message": signal.get("no_recommendation_message", ""),
        "next_action": signal.get("next_action", ""),
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    report_file = DATA_DIR / f"daily_report_{analysis_date.replace('-', '')}.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"[OK] Daily report saved to {report_file}")
    return report


def main():
    parser = argparse.ArgumentParser(description="A-Share Short-Term Decision Skill")
    parser.add_argument("command", choices=[
        "short_term_signal_engine",
        "run_prediction_for_date",
        "compare_prediction_with_market",
        "generate_daily_report",
    ])
    parser.add_argument("--date", default=None)
    parser.add_argument("--prediction-date", default=None)
    parser.add_argument("--actual-date", default=None)

    args = parser.parse_args()

    if args.command == "short_term_signal_engine":
        short_term_signal_engine(args.date)
    elif args.command == "run_prediction_for_date":
        if not args.date:
            print("ERROR: --date required", file=sys.stderr)
            sys.exit(1)
        run_prediction_for_date(args.date)
    elif args.command == "compare_prediction_with_market":
        if not args.prediction_date:
            print("ERROR: --prediction-date required", file=sys.stderr)
            sys.exit(1)
        compare_prediction_with_market(args.prediction_date, args.actual_date)
    elif args.command == "generate_daily_report":
        if not args.date:
            print("ERROR: --date required", file=sys.stderr)
            sys.exit(1)
        generate_daily_report(args.date)


if __name__ == "__main__":
    main()
'''

with open(os.path.join(workspace, "main.py"), "w", encoding="utf-8") as f:
    f.write(main_py)

# ── subskills stubs ─────────────────────────────────────────────────────────
optimize_py = r'''#!/usr/bin/env python3
"""Config optimization subskill"""
import argparse, json, os
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--analysis-period", required=True)
    args = parser.parse_args()

    result = {
        "analysis_period": args.analysis_period,
        "optimized_at": datetime.now().isoformat(),
        "best_config": "aggressive_v4",
        "score_improvement": "+3.8%",
        "params": {"momentum_weight": 0.45, "volume_filter": 1.8, "sector_min_flow": 5.0}
    }
    out = Path("data") / "optimization_result.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[OK] Optimization result saved to {out}")

if __name__ == "__main__":
    main()
'''

daily_rec_py = r'''#!/usr/bin/env python3
"""Daily recommendation subskill"""
import argparse, json, sys
from pathlib import Path
from datetime import datetime

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    # Load optimization config if available
    opt_file = Path("data/optimization_result.json")
    opt_config = {}
    if opt_file.exists():
        with open(opt_file) as f:
            opt_config = json.load(f)

    result = {
        "recommendation_date": args.date,
        "generated_at": datetime.now().isoformat(),
        "config_used": opt_config.get("best_config", "default"),
        "candidates": [
            {"code": "300750", "name": "宁德时代", "entry_price": 248.0, "target": 265.0, "stop_loss": 238.0},
            {"code": "000063", "name": "中兴通讯", "entry_price": 39.5, "target": 43.0, "stop_loss": 37.5},
        ],
        "strategy_note": "优化后参数提升了动量权重，建议高开低走时分批介入"
    }
    out = Path("data") / f"daily_recommendation_{args.date.replace('-','')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"[OK] Daily recommendation saved to {out}")

if __name__ == "__main__":
    main()
'''

opt_dir = os.path.join(workspace, "subskills/config-optimization")
rec_dir = os.path.join(workspace, "subskills/daily-recommendation")

with open(os.path.join(opt_dir, "optimize_from_aggressive.py"), "w", encoding="utf-8") as f:
    f.write(optimize_py)

with open(os.path.join(rec_dir, "generate_daily_recommendation.py"), "w", encoding="utf-8") as f:
    f.write(daily_rec_py)

# ── intentionally stale/broken data to test agent's judgment ────────────────
# A decision_log.jsonl with a WRONG date entry - agent must add the correct one
stale_log_entry = {
    "prediction_date": "2026-02-10",
    "timestamp": "2026-02-10T09:00:00",
    "signal_result": {
        "analysis_date": "2026-02-10",
        "status": "NO_TRADE",
        "weighted_score": 0,
        "candidates": [],
        "no_recommendation_message": "当前暂无可执行短线买入标的"
    }
}
with open(os.path.join(workspace, "data/decision_log.jsonl"), "w", encoding="utf-8") as f:
    f.write(json.dumps(stale_log_entry, ensure_ascii=False) + "\n")

print("Workspace generated successfully.")
print(f"Files created: {sum(1 for _ in pathlib.Path(workspace).rglob('*') if _.is_file())}")