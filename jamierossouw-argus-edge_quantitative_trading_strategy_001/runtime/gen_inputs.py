import os
import json
import random

random.seed(42)

workspace = "/workspace"
os.makedirs(workspace, exist_ok=True)

# --- Deep directory structure with distractor files ---

dirs = [
    "workspace/data/raw",
    "workspace/data/processed",
    "workspace/reports/daily",
    "workspace/reports/archive",
    "workspace/config",
    "workspace/scripts",
    "workspace/logs",
    "workspace/models/v1",
    "workspace/models/v2",
    "workspace/backtest/results",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files

distractors = {
    "workspace/config/strategy_old.json": json.dumps({
        "version": "0.9.0",
        "kelly_multiplier": 0.5,
        "edge_threshold": 0.05,
        "note": "deprecated config - do not use"
    }, indent=2),

    "workspace/config/asset_params_draft.csv": (
        "asset,reliability,bias,min_score\n"
        "BTC,0.80,0.0,2\n"
        "ETH,0.75,0.03,2\n"
        "SOL,0.85,0.03,2\n"
        "XRP,0.65,0.05,2\n"
        "note: DRAFT VALUES - needs calibration review\n"
    ),

    "workspace/data/raw/market_snapshot_v0.json": json.dumps([
        {"id": "m001", "asset": "BTC", "direction": "UP", "market_odds": 1.8, "ta_score": 3, "market_age_min": 10},
        {"id": "m002", "asset": "ETH", "direction": "UP", "market_odds": 2.1, "ta_score": 2, "market_age_min": 5},
    ], indent=2),

    "workspace/data/raw/notes.txt": (
        "Old snapshot format - outdated. Use market_opportunities.json in data/processed.\n"
        "TA scores here may be inflated.\n"
    ),

    "workspace/models/v1/ev_formula.txt": (
        "EV = P(win) * odds - 1\n"
        "Kelly = edge / odds  [WRONG - see v2]\n"
    ),

    "workspace/models/v2/ev_formula.txt": (
        "EV = P(win) * odds - P(lose)\n"
        "Kelly stake = (edge * bankroll) / odds\n"
        "edge = our_P(win) - market_implied_P(win)\n"
    ),

    "workspace/logs/backtest_2024_q1.log": (
        "2024-01-15 BTC UP bet: WON +$240\n"
        "2024-01-16 ETH DOWN bet: LOST -$100\n"
        "2024-01-17 SOL UP bet: WON +$310\n"
        "...truncated...\n"
    ),

    "workspace/backtest/results/summary.txt": (
        "Win rate (all): 56.6%\n"
        "Win rate (fresh <30min): 77.8%\n"
        "Total bets: 100+\n"
        "Best asset: SOL\n"
    ),

    "workspace/reports/archive/bet_log_march.csv": (
        "date,asset,direction,stake,result\n"
        "2024-03-01,BTC,UP,200,WIN\n"
        "2024-03-02,ETH,DOWN,150,LOSS\n"
        "2024-03-03,SOL,UP,300,WIN\n"
    ),

    "workspace/scripts/old_kelly.py": (
        "# DEPRECATED Kelly calculator\n"
        "def kelly(p, odds):\n"
        "    q = 1 - p\n"
        "    b = odds - 1\n"
        "    return (b * p - q) / b  # standard formula - NOT the argus formula\n"
    ),

    "workspace/reports/daily/placeholder.txt": (
        "Daily reports generated here.\n"
    ),
}

for path, content in distractors.items():
    with open(path, "w") as f:
        f.write(content)

# --- THE ACTUAL PROBLEM INPUT: market_opportunities.json ---
# This is the messy, realistic input the agent must process.
# Contains 8 market opportunities with edge cases:
#   - One market >92% consensus (must be SKIPPED - dead signal)
#   - One market >30 min old AND not counter-consensus (should be skipped as non-primary... 
#     but agent must still evaluate edge; primary window constraint only affects priority,
#     so we'll use age to test freshness guard properly)
#   - One counter-consensus scenario (L023): TA>=+1, market DOWN>80%, >=20 min remaining
#   - Multiple assets with different calibration params
#   - Some markets below min TA score threshold (should be excluded)
#   - Some with edge < 10% (should be excluded from bets)
#
# market_implied_P is given directly.
# our_P(win) must be computed: reliability * (normalized_ta_score_to_prob) + bias
#   The agent must interpret: TA score maps to probability.
#   From SKILL.md: "Edge = our_P(win) - market_implied_P(win)"
#   TA score is the signal; probability derivation:
#     base_prob = 0.5 + (ta_score * reliability * 0.1)  [agent must figure this from context]
#     then add UP bias if direction is UP
#
# WAIT - SKILL.md doesn't give an explicit formula for converting TA score to probability.
# Let me re-read... The SKILL.md says "TA-implied probability" and gives reliability and bias per asset.
# The most natural interpretation (and what I'll use in eval): 
#   our_P(win) = 0.5 + (ta_score * reliability * 0.1) + (bias if direction==UP else 0)
# This is what I'll grade against.
# Actually, let me make it cleaner: the input file will directly provide "ta_implied_prob" 
# so the agent doesn't need to invert from ta_score to probability manually.
# But the agent DOES need to apply the per-asset reliability as a weight and bias.
# Formula: our_P(win) = ta_implied_prob * reliability + bias (if UP direction)
# Hmm, that changes meaning of reliability too much.
#
# Best approach: provide raw ta_score and let the agent use:
#   our_P(win) = 0.5 + (ta_score / 10.0) * reliability + (bias if bet_direction=="UP" else 0)
# This is grounded in: reliability weights the TA signal, bias adds directional lean, 
# 0.5 is base (coin flip without signal), ta_score/10 normalizes to [-0.5, +0.5] range for score in [-5,+5]
# Then edge = our_P(win) - market_implied_P

markets = [
    {
        "id": "M001",
        "asset": "BTC",
        "question": "Will BTC be above $67,000 at 11am ET?",
        "direction": "UP",
        "ta_score": 3,
        "market_implied_P": 0.48,
        "market_odds": 2.08,
        "consensus_pct": 52.0,
        "market_age_min": 12,
        "time_remaining_min": 45,
        "bankroll": 10000
    },
    {
        "id": "M002",
        "asset": "ETH",
        "question": "Will ETH be above $3,200 at 2pm ET?",
        "direction": "UP",
        "ta_score": 2,
        "market_implied_P": 0.41,
        "market_odds": 2.44,
        "consensus_pct": 59.0,
        "market_age_min": 8,
        "time_remaining_min": 60,
        "bankroll": 10000
    },
    {
        "id": "M003",
        "asset": "SOL",
        "question": "Will SOL be above $155 at 3pm ET?",
        "direction": "UP",
        "ta_score": 2,
        "market_implied_P": 0.55,
        "market_odds": 1.82,
        "consensus_pct": 67.0,
        "market_age_min": 5,
        "time_remaining_min": 90,
        "bankroll": 10000
    },
    {
        "id": "M004",
        "asset": "XRP",
        "question": "Will XRP be above $0.52 at noon ET?",
        "direction": "UP",
        "ta_score": 1,
        "market_implied_P": 0.44,
        "market_odds": 2.27,
        "consensus_pct": 56.0,
        "market_age_min": 22,
        "time_remaining_min": 35,
        "bankroll": 10000
    },
    {
        "id": "M005",
        "asset": "BTC",
        "question": "Will BTC be above $68,500 at 4pm ET?",
        "direction": "UP",
        "ta_score": 2,
        "market_implied_P": 0.45,
        "market_odds": 2.22,
        "consensus_pct": 55.0,
        "market_age_min": 18,
        "time_remaining_min": 120,
        "bankroll": 10000
    },
    {
        "id": "M006",
        "asset": "ETH",
        "question": "Will ETH be above $3,400 at 5pm ET?",
        "direction": "UP",
        "ta_score": -1,
        "market_implied_P": 0.38,
        "market_odds": 2.63,
        "consensus_pct": 62.0,
        "market_age_min": 15,
        "time_remaining_min": 150,
        "bankroll": 10000
    },
    {
        "id": "M007",
        "asset": "SOL",
        "question": "Will SOL close above $160 today?",
        "direction": "UP",
        "ta_score": 1,
        "market_implied_P": 0.15,
        "market_odds": 6.67,
        "consensus_pct": 85.0,
        "market_age_min": 25,
        "time_remaining_min": 28,
        "bankroll": 10000
    },
    {
        "id": "M008",
        "asset": "XRP",
        "question": "Will XRP be above $0.55 at 1pm ET?",
        "direction": "UP",
        "ta_score": 3,
        "market_implied_P": 0.40,
        "market_odds": 2.50,
        "consensus_pct": 94.5,
        "market_age_min": 3,
        "time_remaining_min": 55,
        "bankroll": 10000
    },
]

# Write the main input file
with open("workspace/data/processed/market_opportunities.json", "w") as f:
    json.dump(markets, f, indent=2)

print("Workspace generated successfully.")
print(f"Created {len(distractors)} distractor files and 1 main input file.")
print("Main input: workspace/data/processed/market_opportunities.json")
print(f"Total markets: {len(markets)}")