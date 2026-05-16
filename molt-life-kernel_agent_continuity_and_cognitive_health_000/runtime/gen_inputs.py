import os
import json
import random
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Deep directory structure with distractor files ---
dirs = [
    "trading_bot/config",
    "trading_bot/strategies",
    "trading_bot/logs/raw",
    "trading_bot/logs/processed",
    "trading_bot/data/market_feeds",
    "trading_bot/data/snapshots",
    "trading_bot/audit",
    "trading_bot/infra/monitoring",
    "trading_bot/infra/recovery",
    "trading_bot/src/core",
    "trading_bot/src/signals",
    "trading_bot/tests",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files ---
distractor_files = {
    "trading_bot/config/broker_config.yaml": """
broker: "AlphaConnect"
account_id: "AC-88231"
max_position_size: 50000
risk_limit: 0.02
environments:
  prod: "wss://api.alphaconnect.io/v3"
  staging: "wss://staging.alphaconnect.io/v3"
""",
    "trading_bot/config/strategy_params.json": json.dumps({
        "strategy": "momentum_breakout",
        "lookback_window": 20,
        "entry_threshold": 0.015,
        "exit_threshold": 0.008,
        "max_drawdown": 0.05
    }, indent=2),
    "trading_bot/strategies/momentum.js": """
// Momentum Breakout Strategy
// WARNING: Do not deploy without risk approval
function calculateMomentum(prices, window) {
    return prices.slice(-window).reduce((a, b) => a + b, 0) / window;
}
module.exports = { calculateMomentum };
""",
    "trading_bot/strategies/mean_reversion.py": """
import numpy as np

def z_score(series, window=20):
    mean = np.mean(series[-window:])
    std = np.std(series[-window:])
    return (series[-1] - mean) / std if std > 0 else 0
""",
    "trading_bot/logs/raw/session_001.log": "\n".join([
        f"[2024-01-{i+1:02d}T09:{random.randint(0,59):02d}:00Z] TRADE_SIGNAL ticker=AAPL action={'BUY' if random.random()>0.5 else 'SELL'} qty={random.randint(10,500)} price={150+random.uniform(-5,5):.2f}"
        for i in range(30)
    ]),
    "trading_bot/logs/raw/session_002.log": "\n".join([
        f"[2024-02-{i+1:02d}T14:{random.randint(0,59):02d}:00Z] RISK_CHECK passed={random.choice(['true','false'])} exposure={random.uniform(0,1):.4f}"
        for i in range(20)
    ]),
    "trading_bot/logs/processed/summary.csv": "date,trades,pnl,sharpe\n2024-01-15,42,1823.50,1.34\n2024-01-16,38,992.10,0.87\n2024-01-17,55,-440.22,0.12\n",
    "trading_bot/data/market_feeds/btc_feed.json": json.dumps([
        {"ts": f"2024-01-{i+1:02d}", "open": 40000+random.uniform(-500,500), "close": 40000+random.uniform(-500,500)}
        for i in range(10)
    ], indent=2),
    "trading_bot/infra/monitoring/health_check.sh": """#!/bin/bash
# Stale health check — replaced by new system
echo "Legacy health check — DO NOT USE"
exit 1
""",
    "trading_bot/infra/recovery/old_snapshot.json": json.dumps({
        "version": "0.1.0-legacy",
        "timestamp": "2024-01-01T00:00:00Z",
        "state": {"session_id": "sess-legacy-001", "entries": []},
        "note": "Legacy format — incompatible with current kernel"
    }, indent=2),
    "trading_bot/src/core/engine.js": """
// Core trading engine — stub
class TradingEngine {
    constructor(config) { this.config = config; }
    start() { console.log('Engine started'); }
}
module.exports = TradingEngine;
""",
    "trading_bot/src/signals/detector.py": """
# Signal detection module
def detect_anomaly(prices, threshold=2.0):
    import statistics
    mu = statistics.mean(prices)
    sigma = statistics.stdev(prices) if len(prices) > 1 else 0
    return abs(prices[-1] - mu) > threshold * sigma
""",
    "trading_bot/tests/test_strategy.js": """
const assert = require('assert');
// placeholder tests
assert.ok(true, 'placeholder test');
console.log('Tests passed');
""",
    "trading_bot/audit/.gitkeep": "",
    "trading_bot/data/snapshots/.gitkeep": "",
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.parent.mkdir(parents=True, exist_ok=True)
    fpath.write_text(content)

# --- THE ACTUAL PROBLEM: agent_session_events.json ---
# 70 raw agent session events that the agent must feed through molt-life-kernel
# These simulate a trading bot's cognitive log — varied types to create entropy variety
event_types = [
    "market_scan", "trade_signal", "risk_check", "position_open",
    "position_close", "pnl_update", "model_inference", "strategy_switch",
    "data_fetch", "alert_trigger"
]

random.seed(42)
events = []
for i in range(70):
    event_type = event_types[i % len(event_types)]
    events.append({
        "seq": i + 1,
        "type": event_type,
        "payload": {
            "ticker": random.choice(["AAPL", "MSFT", "BTC", "ETH", "TSLA"]),
            "value": round(random.uniform(0, 1000), 4),
            "confidence": round(random.uniform(0, 1), 4),
            "session": f"sess-2024-{(i // 10) + 1:02d}"
        },
        "timestamp": f"2024-03-{(i % 28) + 1:02d}T{(i % 24):02d}:00:00Z"
    })

# Inject a high-risk event at position 65 (near the end) to trigger witness gate
events[64]["type"] = "execute_liquidation"
events[64]["payload"]["risk_score"] = 0.95
events[64]["payload"]["action"] = "FULL_PORTFOLIO_LIQUIDATION"

session_events_path = WORKSPACE / "trading_bot" / "audit" / "agent_session_events.json"
session_events_path.write_text(json.dumps(events, indent=2))

# --- Task briefing document (business context, NO tool hints) ---
briefing = """# Trading Bot Cognitive Health Audit — Q1 2024

## Background
Our autonomous trading bot (AlphaBot v2) has been running for three months.
We need a full cognitive health audit before Q2 deployment.

## Requirements from Risk Committee
1. All 70 session events in agent_session_events.json must be permanently logged
   to an immutable, append-only agent ledger.
2. The system must demonstrate crash survivability: take a snapshot of the full
   ledger state, simulate a crash (discard in-memory state), then restore from
   the snapshot and verify the ledger is intact.
3. Run a cognitive drift/anomaly check across the last 50 logged entries and
   record whether the agent is coherent or has drifted.
4. The high-risk liquidation event (execute_liquidation) must pass through an
   approval gate — auto-approve it for this audit (return true from the callback).
5. Produce a single audit report file: kernel_audit_report.json

## Expected Report Structure
The report must contain:
- total_entries_after_rehydration: number of entries in the ledger after crash recovery
- coherence_status: the result/status from the drift check (last 50 entries)
- witness_approved: boolean — was the liquidation action approved?
- snapshot_integrity: boolean — did rehydration succeed (ledger length matches pre-crash)?
"""
(WORKSPACE / "trading_bot" / "audit" / "AUDIT_BRIEF.md").write_text(briefing)

print("Workspace generated successfully.")
print(f"Events file: {session_events_path}")