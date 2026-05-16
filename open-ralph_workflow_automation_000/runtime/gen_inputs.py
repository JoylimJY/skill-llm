#!/usr/bin/env python3
import os
import random
import subprocess

random.seed(42)

BASE = "/workspace/trading-backtester"
os.makedirs(BASE, exist_ok=True)

# Initialize git repo
subprocess.run(["git", "init", BASE], check=True)

# ---- Core source files ----
os.makedirs(f"{BASE}/src/backtester", exist_ok=True)
os.makedirs(f"{BASE}/src/indicators", exist_ok=True)
os.makedirs(f"{BASE}/src/risk", exist_ok=True)
os.makedirs(f"{BASE}/tests/unit", exist_ok=True)
os.makedirs(f"{BASE}/tests/integration", exist_ok=True)
os.makedirs(f"{BASE}/config", exist_ok=True)
os.makedirs(f"{BASE}/scripts", exist_ok=True)
os.makedirs(f"{BASE}/docs", exist_ok=True)
os.makedirs(f"{BASE}/data/sample", exist_ok=True)

# Main backtester module
with open(f"{BASE}/src/backtester/__init__.py", "w") as f:
    f.write("")

with open(f"{BASE}/src/backtester/engine.py", "w") as f:
    f.write('''"""Core backtesting engine for trading strategies."""

class BacktestEngine:
    def __init__(self, initial_capital: float = 100000.0):
        self.capital = initial_capital
        self.positions = {}
        self.trade_history = []

    def run(self, strategy, data):
        for timestamp, row in data.iterrows():
            signal = strategy.generate_signal(row)
            if signal == "BUY":
                self._open_position(timestamp, row["close"])
            elif signal == "SELL":
                self._close_position(timestamp, row["close"])
        return self._compute_results()

    def _open_position(self, ts, price):
        self.positions[ts] = price

    def _close_position(self, ts, price):
        if self.positions:
            entry_ts = list(self.positions.keys())[0]
            entry_price = self.positions.pop(entry_ts)
            pnl = price - entry_price
            self.trade_history.append({"entry": entry_ts, "exit": ts, "pnl": pnl})

    def _compute_results(self):
        total_pnl = sum(t["pnl"] for t in self.trade_history)
        return {"total_pnl": total_pnl, "trades": len(self.trade_history)}
''')

with open(f"{BASE}/src/indicators/__init__.py", "w") as f:
    f.write("")

with open(f"{BASE}/src/indicators/moving_average.py", "w") as f:
    f.write('''"""Moving average indicators."""

def simple_moving_average(prices: list, window: int) -> list:
    if window <= 0:
        raise ValueError("Window must be positive")
    result = []
    for i in range(len(prices)):
        if i < window - 1:
            result.append(None)
        else:
            result.append(sum(prices[i - window + 1:i + 1]) / window)
    return result

def exponential_moving_average(prices: list, alpha: float) -> list:
    if not (0 < alpha <= 1):
        raise ValueError("Alpha must be in (0, 1]")
    result = [prices[0]]
    for p in prices[1:]:
        result.append(alpha * p + (1 - alpha) * result[-1])
    return result
''')

with open(f"{BASE}/src/risk/__init__.py", "w") as f:
    f.write("")

with open(f"{BASE}/src/risk/position_sizer.py", "w") as f:
    f.write('''"""Position sizing utilities."""

def fixed_fractional(capital: float, risk_pct: float, stop_distance: float) -> float:
    if stop_distance <= 0:
        raise ValueError("Stop distance must be positive")
    risk_amount = capital * (risk_pct / 100.0)
    return risk_amount / stop_distance

def kelly_criterion(win_rate: float, win_loss_ratio: float) -> float:
    if not (0 < win_rate < 1):
        raise ValueError("Win rate must be between 0 and 1")
    return win_rate - (1 - win_rate) / win_loss_ratio
''')

# Tests with failing assertions (intentionally broken)
with open(f"{BASE}/tests/__init__.py", "w") as f:
    f.write("")

with open(f"{BASE}/tests/unit/__init__.py", "w") as f:
    f.write("")

with open(f"{BASE}/tests/unit/test_moving_average.py", "w") as f:
    f.write('''"""Unit tests for moving average indicators."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
from indicators.moving_average import simple_moving_average, exponential_moving_average

def test_sma_basic():
    prices = [1, 2, 3, 4, 5]
    result = simple_moving_average(prices, 3)
    # BUG: wrong expected value intentionally
    assert result[2] == 3.0, f"Expected 3.0, got {result[2]}"
    assert result[4] == 4.0, f"Expected 4.0, got {result[4]}"

def test_sma_window_too_large():
    prices = [10, 20]
    result = simple_moving_average(prices, 5)
    assert all(r is None for r in result)

def test_ema_basic():
    prices = [10.0, 11.0, 12.0, 11.0]
    result = exponential_moving_average(prices, 0.5)
    # BUG: wrong rounding
    assert round(result[-1], 1) == 11.4, f"Got {result[-1]}"
''')

with open(f"{BASE}/tests/unit/test_risk.py", "w") as f:
    f.write('''"""Unit tests for risk management."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
from risk.position_sizer import fixed_fractional, kelly_criterion

def test_fixed_fractional():
    result = fixed_fractional(100000, 2.0, 50.0)
    assert result == 40.0, f"Expected 40.0, got {result}"

def test_kelly_basic():
    result = kelly_criterion(0.6, 1.5)
    # BUG: imprecise assertion
    assert round(result, 2) == 0.34, f"Expected 0.34, got {round(result, 2)}"
''')

with open(f"{BASE}/tests/integration/__init__.py", "w") as f:
    f.write("")

with open(f"{BASE}/tests/integration/test_engine.py", "w") as f:
    f.write('''"""Integration test for backtesting engine."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))
from backtester.engine import BacktestEngine

class FakeData:
    def iterrows(self):
        yield (0, {"close": 100.0})
        yield (1, {"close": 105.0})
        yield (2, {"close": 110.0})

class MockStrategy:
    def generate_signal(self, row):
        if row["close"] == 100.0:
            return "BUY"
        elif row["close"] == 110.0:
            return "SELL"
        return "HOLD"

def test_engine_pnl():
    engine = BacktestEngine(initial_capital=50000)
    result = engine.run(MockStrategy(), FakeData())
    assert result["trades"] == 1
    assert result["total_pnl"] == 10.0
''')

# Config files
with open(f"{BASE}/config/backtest.yaml", "w") as f:
    f.write('''# Backtest configuration
initial_capital: 100000
commission: 0.001
slippage: 0.0005
data_source: sample
start_date: "2023-01-01"
end_date: "2024-01-01"
''')

with open(f"{BASE}/config/logging.yaml", "w") as f:
    f.write('''version: 1
handlers:
  console:
    class: logging.StreamHandler
    level: INFO
loggers:
  backtester:
    level: DEBUG
    handlers: [console]
''')

# Distractor files
with open(f"{BASE}/scripts/data_download.sh", "w") as f:
    f.write('#!/bin/bash\necho "Downloading sample data..."\ncurl -s https://example.com/data.csv -o data/sample/prices.csv\n')

with open(f"{BASE}/scripts/deploy.sh", "w") as f:
    f.write('#!/bin/bash\necho "Deploying backtester service..."\npython3 -m pytest tests/ && echo "Deploy OK"\n')

with open(f"{BASE}/docs/architecture.md", "w") as f:
    f.write('# Architecture\n\nThe backtester uses an event-driven engine.\n\n## Components\n- Engine: core loop\n- Indicators: technical signals\n- Risk: position management\n')

with open(f"{BASE}/data/sample/prices_stub.csv", "w") as f:
    f.write('timestamp,open,high,low,close,volume\n2023-01-02,100.0,102.5,99.1,101.3,1500000\n2023-01-03,101.3,103.0,100.2,102.7,1800000\n')

with open(f"{BASE}/.gitignore", "w") as f:
    f.write('__pycache__/\n*.pyc\n.pytest_cache/\ndist/\nbuild/\n*.egg-info/\n')

with open(f"{BASE}/pyproject.toml", "w") as f:
    f.write('''[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "trading-backtester"
version = "0.1.0"
''')

# The agent must create this script
# (intentionally NOT creating it - agent must create fix_loop.sh)
print("Workspace generated: intentional test failures exist in tests/")
print("Agent must create fix_loop.sh implementing the full autonomous fix loop with fallback.")

# Commit initial state
subprocess.run(["git", "-C", BASE, "add", "-A"], check=True)
subprocess.run(["git", "-C", BASE, "commit", "-m", "Initial commit: trading backtester with failing tests"], check=True)

print("Done. Git repo initialized with initial commit.")