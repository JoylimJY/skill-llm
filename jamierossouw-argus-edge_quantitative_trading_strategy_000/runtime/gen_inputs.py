import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# ── Deep directory structure with distractor files ──────────────────────────
dirs = [
    "market_data/raw",
    "market_data/processed",
    "market_data/archive",
    "strategy/configs",
    "strategy/backtests",
    "reports/daily",
    "reports/weekly",
    "logs",
    "scripts",
    "notebooks",
]
for d in dirs:
    os.makedirs(os.path.join(workspace, d), exist_ok=True)

# Distractor files
distractors = {
    "market_data/raw/btc_ohlcv_2024.csv": "timestamp,open,high,low,close,volume\n1700000000,42000,43000,41500,42500,1500\n",
    "market_data/raw/eth_ohlcv_2024.csv": "timestamp,open,high,low,close,volume\n1700000000,2200,2300,2100,2250,8000\n",
    "market_data/processed/normalized_scores.csv": "asset,score\nBTC,0.55\nETH,0.72\n",
    "market_data/archive/old_signals_2023.json": json.dumps({"signals": [], "note": "deprecated format"}),
    "strategy/configs/legacy_kelly.json": json.dumps({"formula": "classic", "fraction": 0.5, "note": "old formula, not current"}),
    "strategy/configs/risk_params.yaml": "max_exposure: 0.20\nmin_edge: 0.08\nnote: draft only\n",
    "strategy/backtests/backtest_results_q1.txt": "Total bets: 45\nWin rate: 62%\nROI: 18%\nNote: pre-calibration run\n",
    "strategy/backtests/backtest_results_q2.txt": "Total bets: 52\nWin rate: 71%\nROI: 24%\n",
    "reports/daily/summary_2024_01_15.txt": "Markets scanned: 30\nBets placed: 7\nP&L: +$320\n",
    "reports/weekly/week3_report.txt": "Weekly P&L: +$1,200\nTop asset: SOL\n",
    "logs/system.log": "2024-01-15 09:00:00 INFO Scanner started\n2024-01-15 09:00:05 INFO 30 markets loaded\n",
    "logs/errors.log": "2024-01-14 08:55:00 ERROR Timeout on market fetch\n",
    "scripts/fetch_markets.sh": "#!/bin/bash\necho 'Fetching markets...'\n",
    "notebooks/exploratory_analysis.txt": "EDA notebook placeholder - not executable\n",
    "market_data/processed/consensus_tracker.csv": "market_id,consensus_pct\nM001,85\nM002,94\nM003,72\n",
}
for path, content in distractors.items():
    with open(os.path.join(workspace, path), "w") as f:
        f.write(content)

# ── The actual problem input: a batch of market opportunities ────────────────
# The agent must read this and produce betting_recommendations.json
#
# Fields per market:
#   id, asset, direction (UP/DOWN our TA says),
#   ta_score (raw TA signal integer),
#   market_age_minutes (how old the market is),
#   market_implied_prob_up (decimal, market's implied prob of UP),
#   market_consensus_pct (% of market money on the dominant side),
#   bankroll (available capital for this market),
#   decimal_odds (payout multiplier for the bet)
#
# Some markets are traps (should be skipped), some trigger counter-consensus rule.

markets = [
    {
        "id": "MKT-001",
        "asset": "BTC",
        "ta_direction": "UP",
        "ta_score": 3,
        "market_age_minutes": 22,
        "market_implied_prob_up": 0.52,
        "market_consensus_pct": 88,
        "bankroll": 1000.0,
        "decimal_odds": 1.92,
        "notes": "Fresh BTC market, ta_score meets BTC min (>=3), edge should be positive"
    },
    {
        "id": "MKT-002",
        "asset": "ETH",
        "ta_direction": "UP",
        "ta_score": 2,
        "market_age_minutes": 15,
        "market_implied_prob_up": 0.60,
        "market_consensus_pct": 75,
        "bankroll": 1000.0,
        "decimal_odds": 1.67,
        "notes": "ETH UP bet: ta_score meets ETH min (>=2), needs ETH UP bias +0.05 applied"
    },
    {
        "id": "MKT-003",
        "asset": "BTC",
        "ta_direction": "UP",
        "ta_score": 2,
        "market_age_minutes": 20,
        "market_implied_prob_up": 0.50,
        "market_consensus_pct": 80,
        "bankroll": 1000.0,
        "decimal_odds": 2.00,
        "notes": "BTC ta_score=2, below BTC min of 3 → SKIP"
    },
    {
        "id": "MKT-004",
        "asset": "SOL",
        "ta_direction": "UP",
        "ta_score": 1,
        "market_age_minutes": 10,
        "market_implied_prob_up": 0.55,
        "market_consensus_pct": 70,
        "bankroll": 1000.0,
        "decimal_odds": 1.82,
        "notes": "SOL ta_score=1, meets SOL min (>=1), apply SOL UP bias +0.05"
    },
    {
        "id": "MKT-005",
        "asset": "XRP",
        "ta_direction": "UP",
        "ta_score": 2,
        "market_age_minutes": 25,
        "market_implied_prob_up": 0.58,
        "market_consensus_pct": 93,
        "bankroll": 1000.0,
        "decimal_odds": 1.72,
        "notes": "Consensus 93% > 92% → SKIP dead signal"
    },
    {
        "id": "MKT-006",
        "asset": "ETH",
        "ta_direction": "UP",
        "ta_score": 2,
        "market_age_minutes": 45,
        "market_implied_prob_up": 0.55,
        "market_consensus_pct": 78,
        "bankroll": 1000.0,
        "decimal_odds": 1.82,
        "notes": "Market age 45 min > 30 → not fresh, skip primary window"
    },
    {
        "id": "MKT-007",
        "asset": "SOL",
        "ta_direction": "UP",
        "ta_score": 2,
        "market_age_minutes": 18,
        "market_implied_prob_up": 0.15,
        "market_consensus_pct": 85,
        "bankroll": 1000.0,
        "decimal_odds": 6.67,
        "notes": "Counter-consensus: ta>=1 (SOL min), market DOWN>80%, >=20min remaining (assuming 60min total market, 42min left). Bet UP per L023."
    },
    {
        "id": "MKT-008",
        "asset": "XRP",
        "ta_direction": "UP",
        "ta_score": 2,
        "market_age_minutes": 28,
        "market_implied_prob_up": 0.45,
        "market_consensus_pct": 76,
        "bankroll": 1000.0,
        "decimal_odds": 2.22,
        "notes": "XRP UP bet: apply XRP bias +0.08, ta_score meets XRP min (>=2)"
    },
    {
        "id": "MKT-009",
        "asset": "BTC",
        "ta_direction": "UP",
        "ta_score": 4,
        "market_age_minutes": 5,
        "market_implied_prob_up": 0.80,
        "market_consensus_pct": 80,
        "bankroll": 1000.0,
        "decimal_odds": 1.25,
        "notes": "BTC: ta_score=4>=3, fresh, but edge may be too small after calculation"
    },
    {
        "id": "MKT-010",
        "asset": "SOL",
        "ta_direction": "DOWN",
        "ta_score": -2,
        "market_age_minutes": 8,
        "market_implied_prob_up": 0.65,
        "market_consensus_pct": 65,
        "bankroll": 1000.0,
        "decimal_odds": 1.54,
        "notes": "SOL DOWN: ta_score abs=-2 >= SOL min abs=1. We are betting DOWN so our_P(down) matters. No UP bias for DOWN bets."
    }
]

with open(os.path.join(workspace, "market_data/raw/opportunity_batch.json"), "w") as f:
    json.dump({"batch_id": "BATCH-2024-001", "markets": markets}, f, indent=2)

# Also write a bankroll summary as additional context
bankroll_summary = {
    "total_bankroll": 10000.0,
    "available_per_market": 1000.0,
    "currency": "USDC",
    "session_id": "SESSION-042"
}
with open(os.path.join(workspace, "strategy/configs/bankroll.json"), "w") as f:
    json.dump(bankroll_summary, f, indent=2)

print("Workspace generated successfully.")
print(f"Input file: {workspace}/market_data/raw/opportunity_batch.json")