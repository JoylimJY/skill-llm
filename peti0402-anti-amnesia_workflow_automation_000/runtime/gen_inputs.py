import os
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Create distractor directory structure ---

dirs = [
    WORKSPACE / "trading" / "strategies",
    WORKSPACE / "trading" / "logs",
    WORKSPACE / "trading" / "backtests",
    WORKSPACE / "crons" / "scripts",
    WORKSPACE / "crons" / "logs",
    WORKSPACE / "reports" / "daily",
    WORKSPACE / "reports" / "weekly",
    WORKSPACE / "config" / "exchanges",
    WORKSPACE / "templates",          # The skill's template folder
    Path.home() / ".openclaw",        # Partial OpenClaw config dir
]

for d in dirs:
    d.mkdir(parents=True, exist_ok=True)

# --- Distractor files ---

(WORKSPACE / "trading" / "strategies" / "momentum.py").write_text(
    "# Momentum strategy\nTHRESHOLD = 0.02\nLOOKBACK = 14\n"
)
(WORKSPACE / "trading" / "strategies" / "mean_revert.py").write_text(
    "# Mean reversion strategy\nWINDOW = 20\nSTD_MULT = 1.5\n"
)
(WORKSPACE / "trading" / "logs" / "trades_2024-12-01.csv").write_text(
    "timestamp,pair,side,qty,price\n"
    "2024-12-01T00:01:23,BTC/USDT,BUY,0.1,97500.00\n"
    "2024-12-01T00:45:11,BTC/USDT,SELL,0.1,98100.00\n"
)
(WORKSPACE / "trading" / "logs" / "trades_2024-12-02.csv").write_text(
    "timestamp,pair,side,qty,price\n"
    "2024-12-02T03:12:05,ETH/USDT,BUY,1.5,3400.00\n"
)
(WORKSPACE / "trading" / "backtests" / "momentum_backtest_results.json").write_text(
    json.dumps({"sharpe": 1.42, "max_drawdown": -0.087, "total_return": 0.31}, indent=2)
)
(WORKSPACE / "crons" / "scripts" / "fetch_prices.sh").write_text(
    "#!/bin/bash\ncurl -s https://api.example.com/prices >> /workspace/trading/logs/prices.log\n"
)
(WORKSPACE / "crons" / "scripts" / "rebalance.sh").write_text(
    "#!/bin/bash\npython3 /workspace/trading/strategies/mean_revert.py\n"
)
(WORKSPACE / "crons" / "logs" / "cron_errors.log").write_text(
    "[2024-12-01 04:00:01] fetch_prices: OK\n"
    "[2024-12-01 04:05:01] rebalance: ERROR - connection timeout\n"
    "[2024-12-01 04:10:01] fetch_prices: OK\n"
)
(WORKSPACE / "config" / "exchanges" / "binance.json").write_text(
    json.dumps({"exchange": "binance", "sandbox": True, "rateLimit": 1200}, indent=2)
)
(WORKSPACE / "config" / "exchanges" / "kraken.json").write_text(
    json.dumps({"exchange": "kraken", "sandbox": False, "rateLimit": 3000}, indent=2)
)
(WORKSPACE / "reports" / "daily" / "pnl_2024-12-01.md").write_text(
    "# PnL Report 2024-12-01\n\n- BTC/USDT: +$60\n- ETH/USDT: -$20\n- Net: +$40\n"
)
(WORKSPACE / "reports" / "weekly" / "week_48_summary.md").write_text(
    "# Week 48 Summary\n\nTotal trades: 142\nWin rate: 54%\nNet PnL: +$820\n"
)

# --- Broken / incomplete OpenClaw config (the agent must fix this) ---
# This has wrong structure — no hooks key, wrong messages value, missing path

broken_openclaw_config = {
    "agent": "trading-bot-v2",
    "version": "1.0",
    "settings": {
        "verbose": True,
        "timeout": 30
    }
    # Note: NO "hooks" key at all — the agent must add it
}

openclaw_config_path = Path.home() / ".openclaw" / "openclaw.json"
openclaw_config_path.write_text(json.dumps(broken_openclaw_config, indent=2))

# --- Template files (the skill says to copy FROM templates/) ---
# These are the canonical templates the agent must use

(WORKSPACE / "templates" / "STATE.md").write_text(
    "# STATE.md — Current World State\n\n"
    "## Active Projects\n"
    "- [ ] PROJECT_NAME: STATUS\n\n"
    "## Iron Decisions\n"
    "- DECISION: RATIONALE\n\n"
    "## Open Issues\n"
    "- ISSUE: PRIORITY\n\n"
    "## Cron Health\n"
    "| Job | Last Run | Status | consecutiveErrors |\n"
    "|-----|----------|--------|-------------------|\n"
    "| example_job | YYYY-MM-DD HH:MM | OK | 0 |\n\n"
    "## Critical Processes\n"
    "- [ ] process_name: RUNNING/STOPPED\n\n"
    "_Last updated: YYYY-MM-DD HH:MM_\n"
)

(WORKSPACE / "templates" / "HEARTBEAT.md").write_text(
    "# HEARTBEAT.md — Wake-Up Protocol\n\n"
    "## Every Heartbeat Checklist\n"
    "1. Read STATE.md\n"
    "2. Check cron health (consecutiveErrors > 0 → alert)\n"
    "3. Check critical processes (are they running?)\n"
    "4. Read income-tracker.md (if night shift)\n"
    "5. Write everything to memory/today.md\n\n"
    "## Alert Thresholds\n"
    "- consecutiveErrors > 0 → ALERT\n"
    "- Process down > 5 min → ALERT\n"
    "- No heartbeat > 10 min → ESCALATE\n\n"
    "## Recovery Actions\n"
    "- Cron error: check logs, restart if safe\n"
    "- Process down: attempt restart, log outcome\n"
)

# --- Existing AGENTS.md (partial — agent must add the protocol section) ---

(WORKSPACE / "AGENTS.md").write_text(
    "# AGENTS.md — Trading Bot Agent Rules\n\n"
    "## Identity\n"
    "You are a 24/7 autonomous crypto trading agent.\n"
    "You manage BTC/USDT and ETH/USDT positions.\n\n"
    "## Capabilities\n"
    "- Execute limit and market orders\n"
    "- Monitor open positions\n"
    "- Run scheduled rebalancing\n"
    "- Generate daily PnL reports\n\n"
    "## Risk Limits\n"
    "- Max position size: 10% of portfolio\n"
    "- Max daily loss: 2% of portfolio\n"
    "- Never trade during high-volatility news events\n\n"
    "## Communication\n"
    "- Log all decisions to file immediately\n"
    "- Alert on errors > threshold\n"
)

# --- income-tracker.md distractor (referenced in HEARTBEAT) ---
(WORKSPACE / "income-tracker.md").write_text(
    "# Income Tracker\n\n"
    "## December 2024\n"
    "| Date | Strategy | PnL |\n"
    "|------|----------|-----|\n"
    "| 2024-12-01 | momentum | +$60 |\n"
    "| 2024-12-02 | mean_revert | -$20 |\n"
)

print("Workspace generated successfully.")
print(f"Workspace root: {WORKSPACE}")
print(f"OpenClaw config: {openclaw_config_path}")