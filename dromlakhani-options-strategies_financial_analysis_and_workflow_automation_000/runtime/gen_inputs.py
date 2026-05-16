import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep distractor directory structure ──────────────────────────────────────
dirs = [
    "trade_desk/archived/2022/Q4",
    "trade_desk/archived/2023/Q1",
    "trade_desk/archived/2023/Q2",
    "trade_desk/current/pending_review",
    "trade_desk/current/approved",
    "trade_desk/current/rejected",
    "risk_committee/minutes",
    "risk_committee/memos/draft",
    "risk_committee/memos/final",
    "research/macro",
    "research/earnings_calendar",
    "quant_models/vol_surface",
    "quant_models/backtests",
    "compliance/pre_trade",
    "compliance/post_trade",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# ── Distractor files ──────────────────────────────────────────────────────────
distractors = {
    "trade_desk/archived/2022/Q4/old_trades.csv": (
        "ticker,strategy,pnl\nAAPL,covered_call,420\nMSFT,iron_condor,-110\n"
    ),
    "trade_desk/archived/2023/Q1/q1_summary.txt": (
        "Q1 2023 summary: 14 trades closed, net P&L +$6,200. "
        "Best performer: TSLA bull call spread (+$1,800).\n"
    ),
    "trade_desk/archived/2023/Q2/expired_positions.json": json.dumps(
        [{"ticker": "SPY", "strategy": "long_straddle", "result": "expired_worthless"}]
    ),
    "trade_desk/current/approved/approved_trades.txt": (
        "NVDA long call approved 2024-01-15\nAMD bull put spread approved 2024-01-16\n"
    ),
    "trade_desk/current/rejected/rejected_trades.txt": (
        "GS short straddle REJECTED — insufficient margin\n"
    ),
    "risk_committee/minutes/jan_meeting.txt": (
        "Risk committee meeting Jan 2024:\n"
        "- Reviewed IV rank thresholds for premium selling\n"
        "- Approved max single-position delta of 0.30\n"
        "- Noted upcoming earnings for AAPL, MSFT, GOOGL\n"
    ),
    "risk_committee/memos/draft/draft_memo_template.txt": (
        "DRAFT — DO NOT USE\n"
        "Strategy Name: [TBD]\nSetup: [TBD]\nCost/Credit: [TBD]\n"
        "Max Profit: [TBD]\nMax Loss: [TBD]\nBreakeven: [TBD]\n"
    ),
    "research/macro/rate_outlook.txt": (
        "Fed expected to hold rates. Volatility indices elevated across sectors.\n"
        "Energy sector IV rank averaging 55. Tech IV rank averaging 38.\n"
    ),
    "research/earnings_calendar/upcoming_earnings.csv": (
        "ticker,earnings_date,expected_move\n"
        "AAPL,2024-02-01,3.5%\nMSFT,2024-01-30,4.2%\nGOOGL,2024-01-23,5.1%\n"
        "XOM,2024-02-02,2.8%\n"
    ),
    "quant_models/vol_surface/iv_rank_data.csv": (
        "ticker,current_iv,iv_52w_low,iv_52w_high,iv_rank\n"
        "AAPL,28,18,65,21.5\n"
        "SPY,14,10,42,12.5\n"
        "XOM,52,30,78,46.0\n"
        "TSLA,71,35,120,42.4\n"
    ),
    "quant_models/backtests/condor_backtest.json": json.dumps(
        {"strategy": "iron_condor", "ticker": "SPY", "win_rate": 0.68, "avg_profit": 145}
    ),
    "quant_models/backtests/straddle_backtest.json": json.dumps(
        {"strategy": "long_straddle", "ticker": "TSLA", "win_rate": 0.42, "avg_profit": 310}
    ),
    "compliance/pre_trade/position_limits.txt": (
        "Max notional per trade: $50,000\n"
        "Max single-leg delta: 0.50\n"
        "Prohibited: naked short calls on individual equities\n"
    ),
    "compliance/post_trade/audit_log.csv": (
        "date,trader,ticker,strategy,status\n"
        "2024-01-10,jsmith,AAPL,bull_call_spread,FILED\n"
        "2024-01-12,mlee,SPY,iron_condor,FILED\n"
    ),
}

for rel_path, content in distractors.items():
    full_path = os.path.join(workspace, rel_path)
    with open(full_path, "w") as f:
        f.write(content)

# ── THE ACTUAL PROBLEM INPUT ──────────────────────────────────────────────────
# Three trade candidates with messy, realistic data the agent must interpret
trade_candidates = {
    "memo_title": "Q1 2024 Pre-Trade Analysis — Pending Risk Committee Approval",
    "analyst": "J. Rivera",
    "date": "2024-01-22",
    "candidates": [
        {
            "id": "TRADE-001",
            "ticker": "XOM",
            "underlying_price": 105.50,
            "market_outlook": "moderately bullish, income focus",
            "iv_rank": 46.0,
            "proposed_strategy_type": "credit spread — bullish",
            "legs": [
                {"action": "SELL", "type": "PUT", "strike": 100.0, "expiry_dte": 38, "premium": 2.85},
                {"action": "BUY",  "type": "PUT", "strike": 95.0,  "expiry_dte": 38, "premium": 1.10}
            ],
            "notes": "Analyst prefers defined risk. Stock has strong support at 98."
        },
        {
            "id": "TRADE-002",
            "ticker": "SPY",
            "underlying_price": 472.00,
            "market_outlook": "neutral, range-bound for next 30 days",
            "iv_rank": 12.5,
            "proposed_strategy_type": "iron condor",
            "legs": [
                {"action": "SELL", "type": "CALL", "strike": 490.0, "expiry_dte": 35, "premium": 1.20},
                {"action": "BUY",  "type": "CALL", "strike": 495.0, "expiry_dte": 35, "premium": 0.55},
                {"action": "SELL", "type": "PUT",  "strike": 455.0, "expiry_dte": 35, "premium": 1.35},
                {"action": "BUY",  "type": "PUT",  "strike": 450.0, "expiry_dte": 35, "premium": 0.70}
            ],
            "notes": "IV rank is low — committee flagged this as possibly misaligned with vol environment."
        },
        {
            "id": "TRADE-003",
            "ticker": "TSLA",
            "underlying_price": 215.00,
            "market_outlook": "large move expected, direction uncertain — earnings in 5 days",
            "iv_rank": 42.4,
            "proposed_strategy_type": "volatility long",
            "legs": [
                {"action": "BUY", "type": "CALL", "strike": 215.0, "expiry_dte": 7, "premium": 6.80},
                {"action": "BUY", "type": "PUT",  "strike": 215.0, "expiry_dte": 7, "premium": 6.40}
            ],
            "notes": "Earnings play. ATM strike for both legs. Same expiry."
        }
    ]
}

input_path = os.path.join(workspace, "trade_desk/current/pending_review/q1_trade_candidates.json")
with open(input_path, "w") as f:
    json.dump(trade_candidates, f, indent=2)

print("Workspace generated successfully.")
print(f"Input file: {input_path}")