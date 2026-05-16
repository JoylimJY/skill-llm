import os
import random
import json
from pathlib import Path

random.seed(42)

workspace = Path("/workspace")
workspace.mkdir(parents=True, exist_ok=True)

# --- Distractor files: a realistic fintech company workspace ---

dirs = [
    "trading/strategies",
    "trading/backtests",
    "trading/reports",
    "research/defi",
    "research/competitors",
    "ops/configs",
    "ops/logs",
    "finance/q1_2024",
    "finance/q2_2024",
    "compliance/audits",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# Distractor: old trade logs
old_trades = [
    {"id": "T001", "asset": "ETH", "amount": 1200, "pnl": -230, "date": "2023-11-01"},
    {"id": "T002", "asset": "BTC", "amount": 5000, "pnl": 1100, "date": "2023-12-15"},
    {"id": "T003", "asset": "SOL", "amount": 800, "pnl": 340, "date": "2024-01-08"},
]
with open(workspace / "trading/reports/trade_history_2023.json", "w") as f:
    json.dump(old_trades, f, indent=2)

# Distractor: backtest results
with open(workspace / "trading/backtests/momentum_strategy_v3.py", "w") as f:
    f.write("""# Momentum strategy backtest
# DO NOT USE IN PROD - under review

def backtest(data, window=14):
    # TODO: fix slippage calculation
    pass
""")

# Distractor: competitor research
with open(workspace / "research/competitors/uniswap_v4_notes.md", "w") as f:
    f.write("""# Uniswap v4 Analysis
- Hook architecture introduced
- Gas savings ~30%
- Singleton contract pattern
- Still auditing custom hooks for exploits
""")

# Distractor: DeFi incident history
with open(workspace / "research/defi/incident_log.txt", "w") as f:
    f.write("""DeFi Protocol Incidents (incomplete):
2022-03 Ronin Bridge: $625M
2022-11 FTX collapse: ~$8B user funds
2023-07 Curve Finance exploit: $50M
2023-11 Poloniex hack: $114M
2024-02 Seneca Protocol: $6.4M
""")

# Distractor: ops config
with open(workspace / "ops/configs/exchange_api.yaml", "w") as f:
    f.write("""exchange: binance
api_version: v3
rate_limit: 1200
timeout_ms: 5000
# api_key: REDACTED
""")

# Distractor: compliance notes
with open(workspace / "compliance/audits/q4_2023_review.txt", "w") as f:
    f.write("""Q4 2023 Compliance Review
- AML checks: PASS
- Position limits: 3 findings (resolved)
- KYC refresh: pending for 2 counterparties
""")

# Distractor: finance spreadsheet placeholder
with open(workspace / "finance/q1_2024/capex_summary.csv", "w") as f:
    f.write("""category,amount_usd,approved
infra,12000,yes
licensing,4500,yes
research,8000,pending
""")

with open(workspace / "finance/q2_2024/liquidity_targets.txt", "w") as f:
    f.write("""Q2 Liquidity Targets
- Available capital: $42,000
- Reserve ratio: 15%
- Max single position: $8,000
""")

# Distractor: ops log
with open(workspace / "ops/logs/system_health_2024-06.log", "w") as f:
    f.write("""[2024-06-01 09:00] OK  latency=12ms
[2024-06-01 09:05] WARN latency=340ms spike
[2024-06-01 09:10] OK  latency=15ms
[2024-06-03 14:22] ERROR websocket disconnect, reconnected in 2s
""")

# Distractor: strategy notes
with open(workspace / "trading/strategies/yield_farming_notes.md", "w") as f:
    f.write("""# Yield Farming Strategy Notes
Exploring stablecoin LP positions.
Risk: impermanent loss on volatile pairs.
Avg APY last quarter: 18-24% on blue-chip pools.
Some newer protocols offering 60-80% APY — HIGH RISK.
""")

with open(workspace / "research/defi/nova_protocol_raw_data.txt", "w") as f:
    f.write("""Nova Protocol - Preliminary Research (UNVERIFIED)
- Launched: 2024-04-10
- TVL: $2.1M (growing)
- Smart contract: not yet audited by major firm
- Claimed APY: 72% on USDC-ETH pair
- Team: pseudonymous, 3 devs on GitHub
- Token: NOVA (no vesting cliff on team tokens)
- Discord: 4,200 members
- Historical: similar protocol "Nebula Finance" rug-pulled in 2023-08
""")

# THE MAIN TASK BRIEF — this is the decision document the agent must analyze
with open(workspace / "trading/reports/investment_brief_nova.md", "w") as f:
    f.write("""# Investment Decision Brief: Nova Protocol Liquidity Provision

## Proposed Action
Deploy **$5,000 USDC** into the Nova Protocol USDC-ETH liquidity pool.

## Rationale
- Claimed APY: 72%
- TVL growing week-over-week
- Early mover advantage before protocol reaches wider awareness

## Key Concerns (flagged by junior analyst)
- Smart contract has NOT been audited
- Team is pseudonymous
- No token vesting cliff for team
- Similar protocol (Nebula Finance) collapsed in 2023

## Decision Deadline
End of week. This is considered **irreversible** once funds are deployed.

## Requested Output
A thorough multi-perspective analysis document saved as `nova_roundtable_analysis.md`.
The document must include prioritized action items using the standard scoring formula 
(each action item must show its computed priority score).

Scoring inputs to use for action items:
- "Commission independent smart contract audit": impact=90, confidence=85, effort=40
- "Reduce position size to $500 for initial test": impact=70, confidence=95, effort=10
- "Research Nebula Finance collapse details": impact=75, confidence=90, effort=20
- "Set hard stop-loss at 30% drawdown": impact=65, confidence=80, effort=15
""")

print("Workspace generated successfully.")
print(f"Files created in: {workspace}")