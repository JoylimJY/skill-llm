import os
import json
import random
import stat
from pathlib import Path

random.seed(42)

WORKSPACE = Path("/workspace")

# --- Create the main project structure (fintech risk calculator) ---
dirs = [
    "project/src/risk_engine",
    "project/src/portfolio",
    "project/src/data_feed",
    "project/tests/unit",
    "project/tests/integration",
    "project/docs",
    "project/config",
    "project/scripts/legacy",
    "project/.openclaw/scripts",
    "project/reports",
    "downloads",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# --- Distractor files (realistic, messy, NOT hints) ---
distractor_files = {
    "project/src/risk_engine/var_calculator.py": """\
import numpy as np

class VaRCalculator:
    def __init__(self, confidence=0.95):
        self.confidence = confidence

    def historical_var(self, returns):
        # TODO: fix edge case with empty returns
        sorted_returns = sorted(returns)
        index = int((1 - self.confidence) * len(sorted_returns))
        return abs(sorted_returns[index])
""",
    "project/src/risk_engine/stress_test.py": """\
# Placeholder - stress test module
# FIXME: not thread-safe
class StressTest:
    scenarios = ['2008_crisis', 'covid_crash', 'flash_crash_2010']

    def run(self, portfolio, scenario):
        raise NotImplementedError("scenario runner pending")
""",
    "project/src/portfolio/position_manager.py": """\
class PositionManager:
    def __init__(self):
        self.positions = {}

    def add_position(self, ticker, qty, price):
        self.positions[ticker] = {'qty': qty, 'price': price, 'value': qty * price}

    def total_value(self):
        return sum(p['value'] for p in self.positions.values())
""",
    "project/src/data_feed/market_data.py": """\
import requests

class MarketDataFeed:
    BASE_URL = 'https://api.internal.finco.local'  # internal, not public

    def fetch_quote(self, ticker):
        # Mocked in tests
        raise ConnectionError('production feed unavailable in sandbox')
""",
    "project/tests/unit/test_var.py": """\
import pytest
from src.risk_engine.var_calculator import VaRCalculator

def test_var_basic():
    calc = VaRCalculator()
    returns = [-0.05, -0.03, 0.01, 0.02, -0.08, 0.03]
    var = calc.historical_var(returns)
    assert var > 0

def test_var_empty():
    calc = VaRCalculator()
    with pytest.raises(IndexError):
        calc.historical_var([])
""",
    "project/tests/integration/test_pipeline.py": """\
# Integration test stubs - DO NOT RUN IN CI YET
# These require live feed credentials
def test_end_to_end():
    pass
""",
    "project/docs/architecture.md": """\
# Risk Engine Architecture

## Components
- **VaR Calculator**: Historical and parametric VaR
- **Stress Test**: Scenario-based shock analysis
- **Position Manager**: Real-time P&L tracking

## Known Issues
- Thread-safety not guaranteed in PositionManager v1
- MarketDataFeed hardcoded to internal URL
""",
    "project/config/thresholds.json": json.dumps({
        "var_limit_pct": 0.05,
        "stress_test_threshold": 0.15,
        "max_single_position_pct": 0.20,
        "alert_email": "risk-ops@finco.internal"
    }, indent=2),
    "project/scripts/legacy/migrate_positions.sh": """\
#!/bin/bash
# Legacy migration script - DO NOT USE
echo "Migrating from v1 schema..."
sqlite3 positions_v1.db ".dump" | python3 transform_schema.py > positions_v2.sql
""",
    "project/reports/.gitkeep": "",
    "downloads/design_brief.txt": """\
Risk Engine Refactor - Design Brief
=====================================
Objective: Refactor the VaR calculator to support Monte Carlo simulation.
Priority: Fix thread-safety issues in PositionManager.
Timeline: Sprint 3 (2 weeks)
Owner: quant-dev@finco.internal

Requirements:
- Monte Carlo VaR with configurable iterations (default 10000)
- Thread-safe position updates using RLock
- Unit test coverage > 80%
- No breaking changes to existing VaRCalculator API
""",
}

for rel_path, content in distractor_files.items():
    fpath = WORKSPACE / rel_path
    fpath.write_text(content)

# --- Create the baseDir structure for the orchestration scripts ---
# The scripts live at {baseDir}/scripts/ which maps to /workspace/project/.openclaw/scripts
# We also need to record baseDir so the agent can reference it
basedir_marker = WORKSPACE / "project" / ".openclaw" / "basedir.txt"
basedir_marker.write_text("/workspace/project/.openclaw\n")

# --- Create invocation log directory (mock scripts will write here) ---
(WORKSPACE / "project" / ".openclaw" / "logs").mkdir(parents=True, exist_ok=True)

# Write a session state store directory
(WORKSPACE / "project" / ".openclaw" / "sessions").mkdir(parents=True, exist_ok=True)

print("Workspace generated successfully.")
print(f"Structure created under: {WORKSPACE}")