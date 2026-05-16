import os
import json
import random

random.seed(42)

# --- Create deeply nested directory structure with distractor files ---

dirs = [
    "workspace/src/strategies/quant",
    "workspace/src/strategies/ml",
    "workspace/src/data/feeds",
    "workspace/src/data/cache",
    "workspace/src/models/v1",
    "workspace/src/models/v2",
    "workspace/logs/runtime",
    "workspace/logs/audit",
    "workspace/config/envs",
    "workspace/config/schemas",
    "workspace/assets/gep",
    "workspace/docs",
    "workspace/tests/unit",
    "workspace/tests/integration",
    "workspace/scripts",
]

for d in dirs:
    os.makedirs(d, exist_ok=True)

# Distractor files
distractor_files = {
    "workspace/src/strategies/quant/mean_reversion.py": """# Mean reversion strategy
import numpy as np

def signal(prices):
    mean = np.mean(prices[-20:])
    return 1 if prices[-1] < mean * 0.97 else -1
""",
    "workspace/src/strategies/ml/lstm_predictor.py": """# LSTM price predictor stub
class LSTMPredictor:
    def __init__(self, lookback=60):
        self.lookback = lookback
    def predict(self, X):
        raise NotImplementedError
""",
    "workspace/src/data/feeds/market_feed.json": json.dumps({
        "feeds": ["binance", "coinbase", "kraken"],
        "interval": "1m",
        "symbols": ["BTC/USDT", "ETH/USDT"]
    }, indent=2),
    "workspace/src/data/cache/cache_config.yaml": """ttl: 300
max_size: 10000
eviction: lru
""",
    "workspace/src/models/v1/checkpoint.json": json.dumps({"epoch": 42, "loss": 0.0312, "val_loss": 0.0401}),
    "workspace/src/models/v2/checkpoint.json": json.dumps({"epoch": 100, "loss": 0.0201, "val_loss": 0.0299}),
    "workspace/logs/runtime/app.log": """2024-01-15 08:00:01 INFO  Starting quant engine
2024-01-15 08:00:05 ERROR StrategyLoader: failed to load module 'alpha_v3' - ModuleNotFoundError
2024-01-15 08:01:22 WARN  Latency spike detected: 450ms (threshold: 200ms)
2024-01-15 08:05:00 ERROR BacktestRunner: division by zero in sharpe calculation
2024-01-15 08:10:11 INFO  Checkpoint saved
""",
    "workspace/logs/audit/decisions.jsonl": json.dumps({"ts": "2024-01-15T08:00:01Z", "action": "BUY", "asset": "BTC", "qty": 0.5}) + "\n" +
        json.dumps({"ts": "2024-01-15T08:05:00Z", "action": "SELL", "asset": "ETH", "qty": 2.0}) + "\n",
    "workspace/config/envs/staging.env": """DATABASE_URL=postgres://localhost:5432/quant_staging
REDIS_URL=redis://localhost:6379
LOG_LEVEL=DEBUG
""",
    "workspace/config/schemas/strategy_schema.json": json.dumps({
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "version": {"type": "string"},
            "parameters": {"type": "object"}
        }
    }, indent=2),
    "workspace/tests/unit/test_signals.py": """import pytest

def test_buy_signal():
    assert True  # placeholder

def test_sell_signal():
    assert True  # placeholder
""",
    "workspace/tests/integration/test_pipeline.py": """import pytest

def test_full_pipeline():
    # TODO: implement
    pass
""",
    "workspace/scripts/backtest_runner.sh": """#!/bin/bash
echo "Running backtest..."
python3 src/strategies/quant/mean_reversion.py
""",
    "workspace/docs/architecture_overview.md": """# 🏗️ Quant Bot Architecture

## Overview 🚀
This document describes the overall system architecture.

## Components
- 📊 Data Layer: Market feeds and caching
- 🤖 Strategy Layer: Signal generation
- ⚡ Execution Layer: Order management

## Self-Improvement Pipeline 🔧
The agent improvement system needs proper configuration. ✅
Contact the team lead for setup instructions. 🎯
""",
}

for filepath, content in distractor_files.items():
    with open(filepath, "w") as f:
        f.write(content)

# --- Create the BROKEN / INCOMPLETE GEP asset store ---

# genes.json: exists but is malformed (empty array, needs real gene definitions)
with open("workspace/assets/gep/genes.json", "w") as f:
    f.write("[]")

# capsules.json: missing entirely — don't create it

# events.jsonl: exists but has a corrupt/incomplete entry
with open("workspace/assets/gep/events.jsonl", "w") as f:
    # Write a partial/bad event without required fields
    f.write(json.dumps({"timestamp": "2024-01-01T00:00:00Z", "note": "initial placeholder - incomplete"}) + "\n")

# --- Create a broken .env stub (missing required evolve vars, wrong values) ---
with open("workspace/.env", "w") as f:
    f.write("""# Environment config - INCOMPLETE
DATABASE_URL=postgres://localhost:5432/quant_staging
LOG_LEVEL=DEBUG
EVOLVE_STRATEGY=aggressive
EVOLVE_LOAD_MAX=9.9
""")

# --- Create a draft ops note with bad emojis (agent must fix) ---
with open("workspace/docs/evolution_ops_note_DRAFT.md", "w") as f:
    f.write("""# 🚀 Evolution System Ops Note

## Configuration Summary 📋
This document summarizes the self-improvement system setup for the staging environment.

## Strategy Notes 🎯
- Running in hardened mode for safety ✅
- Load limits applied ⚡
- Self-modification is disabled 🔒

## Event Log 📊
Initial events will be recorded with parent-child lineage.

## Status: DRAFT - Needs Cleanup ❌
""")

# package.json for the evolver (so node index.js works as a reference)
with open("workspace/package.json", "w") as f:
    json.dump({
        "name": "capability-evolver",
        "version": "1.2.0",
        "description": "Self-evolution engine",
        "main": "index.js",
        "scripts": {"start": "node index.js"}
    }, f, indent=2)

print("Workspace generated successfully.")
print("Issues introduced:")
print("  - assets/gep/genes.json: empty array (needs gene definitions)")
print("  - assets/gep/capsules.json: MISSING (needs to be created)")
print("  - assets/gep/events.jsonl: corrupt single entry (needs valid append-only tree events)")
print("  - .env: missing EVOLVE_ALLOW_SELF_MODIFY, wrong EVOLVE_STRATEGY ('aggressive' is invalid), wrong EVOLVE_LOAD_MAX")
print("  - docs/evolution_ops_note_DRAFT.md: contains forbidden emojis")