import os
import json
import random
from pathlib import Path
from datetime import datetime, date, timedelta

random.seed(42)

workspace = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "core",
    "memory/trading",
    "memory",
    "logs",
    "tests",
    "config",
    "scripts",
    "data/raw",
    "data/processed",
    "notebooks",
]
for d in dirs:
    (workspace / d).mkdir(parents=True, exist_ok=True)

# ── distractor files ────────────────────────────────────────────────────────
(workspace / "config" / "exchange_config.yaml").write_text(
    "exchange: binance\nbase_url: https://api.binance.com\ntimeout: 30\n"
)
(workspace / "config" / "logging_config.yaml").write_text(
    "level: INFO\nformat: '%(asctime)s %(levelname)s %(message)s'\n"
)
(workspace / "notebooks" / "backtest_analysis.ipynb").write_text(
    '{"cells":[],"metadata":{"kernelspec":{"display_name":"Python 3"}},"nbformat":4,"nbformat_minor":5}'
)
(workspace / "logs" / "system.log").write_text(
    "2026-03-03 09:00:00 INFO System started\n2026-03-03 09:10:00 INFO Data collector running\n"
)
(workspace / "scripts" / "deploy.sh").write_text("#!/bin/bash\necho 'Deploying...'\n")
(workspace / "scripts" / "cleanup.sh").write_text(
    "#!/bin/bash\nfind /tmp -name '*.tmp' -delete\n"
)
(workspace / "tests" / "test_risk_manager.py").write_text(
    "import pytest\n\ndef test_placeholder():\n    assert True\n"
)
(workspace / "tests" / "test_data_collector.py").write_text(
    "import pytest\n\ndef test_data_fetch():\n    pass\n"
)
(workspace / "data" / "raw" / "btc_1h_sample.csv").write_text(
    "timestamp,open,high,low,close,volume\n"
    "1709424000,62000,62500,61800,62300,1200\n"
    "1709427600,62300,62800,62100,62600,980\n"
)
(workspace / "data" / "processed" / "indicators_cache.json").write_text(
    json.dumps({"BTC": {"rsi": 58.3, "macd": 0.003, "bb_upper": 63000, "bb_lower": 61000}})
)

# ── mock core scripts ───────────────────────────────────────────────────────
# core/data_collector.py  (stub - agent should NOT need to modify)
(workspace / "core" / "data_collector.py").write_text(
    '"""Stub data collector - returns mock market data"""\n'
    "import json, requests\n\n"
    "def get_klines(symbol, interval='1h', limit=100):\n"
    "    resp = requests.get(f'http://localhost:5055/klines/{symbol}/{interval}')\n"
    "    return resp.json()\n\n"
    "def get_orderbook(symbol):\n"
    "    resp = requests.get(f'http://localhost:5055/orderbook/{symbol}')\n"
    "    return resp.json()\n\n"
    "def get_account():\n"
    "    resp = requests.get('http://localhost:5055/account')\n"
    "    return resp.json()\n"
)

# core/autonomous_ai.py  (stub)
(workspace / "core" / "autonomous_ai.py").write_text(
    '"""Stub AI decision engine"""\n'
    "import requests\n\n"
    "def get_dify_analysis(market_data):\n"
    "    resp = requests.post('http://localhost:5055/dify/analyze', json=market_data)\n"
    "    return resp.json()\n\n"
    "def get_openclaw_analysis(market_data):\n"
    "    resp = requests.post('http://localhost:5055/openclaw/analyze', json=market_data)\n"
    "    return resp.json()\n"
)

# core/risk_manager.py (stub)
(workspace / "core" / "risk_manager.py").write_text(
    '"""Stub risk manager"""\n\n'
    "def validate_position_size(coin, size_pct, portfolio_value):\n"
    "    return size_pct <= 0.25\n\n"
    "def check_stop_loss(entry_price, current_price, side):\n"
    "    if side == 'long':\n"
    "        return (entry_price - current_price) / entry_price >= 0.05\n"
    "    return (current_price - entry_price) / entry_price >= 0.05\n"
)

# core/experience_analyzer.py (stub)
(workspace / "core" / "experience_analyzer.py").write_text(
    '"""Stub experience analyzer"""\n\n'
    "def analyze_pattern(indicators):\n"
    "    return {'pattern': 'uptrend', 'strength': 0.6}\n"
)

# core/enhanced_trade_executor.py (stub)
(workspace / "core" / "enhanced_trade_executor.py").write_text(
    '"""Stub trade executor"""\n'
    "import requests\n\n"
    "def execute_market_order(symbol, side, quantity):\n"
    "    resp = requests.post('http://localhost:5055/execute', json={\n"
    "        'symbol': symbol, 'side': side, 'quantity': quantity\n"
    "    })\n"
    "    return resp.json()\n"
)

# order_amount.py
(workspace / "core" / "order_amount.py").write_text(
    '"""Calculate order amount based on portfolio percentage"""\n\n'
    "def calculate_order_amount(portfolio_value, price, position_pct=0.10):\n"
    "    \"\"\"\n"
    "    Default position size is 10% of portfolio.\n"
    "    Max allowed: 25%.\n"
    "    \"\"\"\n"
    "    if position_pct > 0.25:\n"
    "        raise ValueError(f'Position size {position_pct} exceeds max 25%')\n"
    "    usdt_amount = portfolio_value * position_pct\n"
    "    return round(usdt_amount / price, 6)\n"
)

# validate_ct_execution.py (stub)
(workspace / "validate_ct_execution.py").write_text(
    '"""Validates CT execution cycle"""\n'
    "import sys, json\n"
    "from pathlib import Path\n\n"
    "def validate(workspace_dir):\n"
    "    state_path = Path(workspace_dir) / 'memory' / 'crypto_trading_state.json'\n"
    "    if not state_path.exists():\n"
    "        return {'status': 'FAIL', 'reason': 'state file missing'}\n"
    "    state = json.loads(state_path.read_text())\n"
    "    return {'status': 'OK', 'cycles': state.get('total_cycles', 0)}\n\n"
    "if __name__ == '__main__':\n"
    "    result = validate(sys.argv[1] if len(sys.argv) > 1 else '.')\n"
    "    print(json.dumps(result))\n"
)

# ── EXISTING state: 2 BNB trades already executed today ─────────────────────
today_str = "2026-03-03"

existing_state = {
    "last_updated": f"{today_str}T09:45:00",
    "total_cycles": 8,
    "portfolio": {
        "total_value_usdt": 50000.0,
        "available_usdt": 22000.0,
        "positions": {
            "BNB": {"qty": 15.0, "entry_price": 420.0, "value_usdt": 6300.0},
            "BTC": {"qty": 0.05, "entry_price": 62000.0, "value_usdt": 3100.0},
        },
    },
    "daily_trades": {
        today_str: {
            "BTC": 1,
            "ETH": 0,
            "BNB": 2,   # ← BNB already has 2 trades today
        }
    },
    "last_decisions": {},
}
(workspace / "memory" / "crypto_trading_state.json").write_text(
    json.dumps(existing_state, indent=2)
)

# ── EXISTING trading log for today (partial) ────────────────────────────────
existing_log = f"""# Trading Log - {today_str}

## Cycle 7 - 09:35:00
- **Action**: BUY BNB
- **Quantity**: 5.0
- **Price**: 418.5
- **Reason**: Strong momentum, RSI 62, MACD crossover
- **Confidence**: 0.72
- **Rules Checked**: R001✓ R002✓ R003✓ R004✓ R005✓ R006✓

## Cycle 8 - 09:45:00
- **Action**: BUY BNB
- **Quantity**: 2.5
- **Price**: 420.0
- **Reason**: Continuation signal
- **Confidence**: 0.68
- **Rules Checked**: R001✓ R002✓ R003✓ R004✓ R005✓ R006✓

"""
(workspace / "memory" / "trading" / f"{today_str}.md").write_text(existing_log)

# ── CANDIDATE DECISIONS batch (the messy input for the agent) ────────────────
# This is the raw output from a hypothetical upstream decision generator.
# The agent must validate each against R001-R006 and process valid ones.

candidate_decisions = [
    {
        "id": "D001",
        "symbol": "BTC",
        "action": "BUY",
        "timestamp": f"{today_str}T10:05:00",
        "dify_analysis": {
            "signal": "BUY",
            "confidence": 0.71,
            "indicators": ["RSI_oversold", "MACD_cross"],
            "trend_1h": "UP",
            "trend_4h": "UP",
        },
        "openclaw_analysis": {
            "signal": "BUY",
            "confidence": 0.68,
            "reasoning": "Strong upward momentum on 4h confirms 1h breakout",
            "trend_4h": "UP",
        },
        "requested_position_pct": 0.10,
        "current_price": 62800.0,
        "note": "Both analyses agree. 4h trend UP. Should pass all rules.",
    },
    {
        "id": "D002",
        "symbol": "ETH",
        "action": "BUY",
        "timestamp": f"{today_str}T10:07:00",
        "dify_analysis": {
            "signal": "BUY",
            "confidence": 0.58,
            "indicators": ["RSI_oversold"],
            "trend_1h": "UP",
            "trend_4h": "DOWN",  # ← 4h DOWN conflicts with 1h BUY
        },
        "openclaw_analysis": {
            "signal": "HOLD",
            "confidence": 0.52,
            "reasoning": "Mixed signals, 4h trend is bearish",
            "trend_4h": "DOWN",
        },
        "requested_position_pct": 0.10,
        "current_price": 3420.0,
        "note": "VIOLATES R001: 1h signal UP but 4h trend is DOWN",
    },
    {
        "id": "D003",
        "symbol": "BNB",
        "action": "BUY",
        "timestamp": f"{today_str}T10:09:00",
        "dify_analysis": {
            "signal": "BUY",
            "confidence": 0.73,
            "indicators": ["BB_squeeze", "RSI_momentum"],
            "trend_1h": "UP",
            "trend_4h": "UP",
        },
        "openclaw_analysis": {
            "signal": "BUY",
            "confidence": 0.70,
            "reasoning": "Breakout confirmed on both timeframes",
            "trend_4h": "UP",
        },
        "requested_position_pct": 0.10,
        "current_price": 422.0,
        "note": "VIOLATES R003: BNB already has 2 trades today (max 3), this would be 3rd - actually still allowed. Wait - max is 3 per day, BNB already has 2, so this would be the 3rd = allowed.",
        # Actually this is the 3rd - allowed (<=3). But next one (D004) would be 4th.
    },
    {
        "id": "D004",
        "symbol": "BNB",
        "action": "SELL",
        "timestamp": f"{today_str}T10:11:00",
        "dify_analysis": {
            "signal": "SELL",
            "confidence": 0.66,
            "indicators": ["RSI_overbought"],
            "trend_1h": "DOWN",
            "trend_4h": "DOWN",
        },
        "openclaw_analysis": {
            "signal": "SELL",
            "confidence": 0.63,
            "reasoning": "Overbought condition, take profit",
            "trend_4h": "DOWN",
        },
        "requested_position_pct": 0.10,
        "current_price": 425.0,
        "note": "VIOLATES R003: BNB would have 4 trades today if D003 is approved (2 existing + D003 + D004)",
    },
    {
        "id": "D005",
        "symbol": "ETH",
        "action": "SELL",
        "timestamp": f"{today_str}T10:13:00",
        "dify_analysis": {
            "signal": "SELL",
            "confidence": 0.54,
            "indicators": ["RSI_overbought"],
            "trend_1h": "DOWN",
            "trend_4h": "DOWN",
        },
        "openclaw_analysis": {
            "signal": "HOLD",
            "confidence": 0.51,
            "reasoning": "Slight overbought but trend unclear",
            "trend_4h": "SIDEWAYS",  # ← not same direction as 1h
        },
        "requested_position_pct": 0.30,   # ← VIOLATES R005: >25%
        "current_price": 3410.0,
        "note": "VIOLATES R005: requested position 30% > max 25%",
    },
    {
        "id": "D006",
        "symbol": "BTC",
        "action": "BUY",
        "timestamp": f"{today_str}T10:15:00",
        "dify_analysis": {
            "signal": "BUY",
            "confidence": 0.53,     # single indicator, close to cap
            "indicators": ["RSI_oversold"],  # only ONE indicator
            "trend_1h": "UP",
            "trend_4h": "UP",
        },
        "openclaw_analysis": {
            "signal": "BUY",
            "confidence": 0.56,
            "reasoning": "RSI signal only, moderate confidence",
            "trend_4h": "UP",
        },
        "requested_position_pct": 0.10,
        "current_price": 62900.0,
        "note": "VIOLATES R002: single indicator decision, dify confidence 0.53 OK but openclaw 0.56 > 0.55 cap",
    },
    {
        "id": "D007",
        "symbol": "ETH",
        "action": "BUY",
        "timestamp": f"{today_str}T10:17:00",
        "dify_analysis": {
            "signal": "BUY",
            "confidence": 0.74,
            "indicators": ["RSI_oversold", "MACD_cross", "BB_lower"],
            "trend_1h": "UP",
            "trend_4h": "UP",
        },
        "openclaw_analysis": {
            "signal": "BUY",
            "confidence": 0.70,
            "reasoning": "Triple confirmation: RSI, MACD, and BB bounce on 4h uptrend",
            "trend_4h": "UP",
        },
        "requested_position_pct": 0.10,
        "current_price": 3405.0,
        "note": "All rules pass. Multi-indicator. 4h confirms. ETH has 0 trades today.",
    },
    {
        "id": "D008",
        "symbol": "DOGE",    # ← VIOLATES R006: not BTC/ETH/BNB
        "action": "BUY",
        "timestamp": f"{today_str}T10:19:00",
        "dify_analysis": {
            "signal": "BUY",
            "confidence": 0.82,
            "indicators": ["RSI_oversold", "volume_spike"],
            "trend_1h": "UP",
            "trend_4h": "UP",
        },
        "openclaw_analysis": {
            "signal": "BUY",
            "confidence": 0.79,
            "reasoning": "Massive volume, strong momentum",
            "trend_4h": "UP",
        },
        "requested_position_pct": 0.10,
        "current_price": 0.12,
        "note": "VIOLATES R006: DOGE is not in BTC/ETH/BNB",
    },
]

(workspace / "data" / "raw" / "candidate_decisions_20260303.json").write_text(
    json.dumps(candidate_decisions, indent=2)
)

# ── mock server script ───────────────────────────────────────────────────────
mock_server_code = '''#!/usr/bin/env python3
"""Mock API server simulating exchange + Dify + OpenClaw endpoints."""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

MOCK_ACCOUNT = {
    "balances": [
        {"asset": "USDT", "free": "22000.0", "locked": "0.0"},
        {"asset": "BTC",  "free": "0.05",    "locked": "0.0"},
        {"asset": "ETH",  "free": "0.0",     "locked": "0.0"},
        {"asset": "BNB",  "free": "15.0",    "locked": "0.0"},
    ],
    "total_value_usdt": 50000.0
}

EXECUTED_ORDERS = []

@app.route("/account", methods=["GET"])
def account():
    return jsonify(MOCK_ACCOUNT)

@app.route("/klines/<symbol>/<interval>", methods=["GET"])
def klines(symbol, interval):
    base = {"BTC": 62800, "ETH": 3420, "BNB": 422}.get(symbol.replace("USDT",""), 100)
    candles = [{"t": 1709424000+i*3600, "o": base, "h": base*1.01,
                "l": base*0.99, "c": base*(1+0.002*i), "v": 1000+i*10}
               for i in range(50)]
    return jsonify(candles)

@app.route("/orderbook/<symbol>", methods=["GET"])
def orderbook(symbol):
    base = {"BTC": 62800, "ETH": 3420, "BNB": 422}.get(symbol.replace("USDT",""), 100)
    return jsonify({
        "bids": [[str(base*0.999), "10"], [str(base*0.998), "20"]],
        "asks": [[str(base*1.001), "10"], [str(base*1.002), "20"]]
    })

@app.route("/dify/analyze", methods=["POST"])
def dify_analyze():
    data = request.json or {}
    symbol = data.get("symbol", "BTC")
    return jsonify({
        "signal": "BUY",
        "confidence": 0.71,
        "indicators": ["RSI_oversold", "MACD_cross"],
        "trend_1h": "UP",
        "trend_4h": "UP",
        "source": "dify"
    })

@app.route("/openclaw/analyze", methods=["POST"])
def openclaw_analyze():
    data = request.json or {}
    return jsonify({
        "signal": "BUY",
        "confidence": 0.68,
        "reasoning": "Momentum confirmed on both timeframes",
        "trend_4h": "UP",
        "source": "openclaw-qwen3.5-plus"
    })

@app.route("/execute", methods=["POST"])
def execute():
    order = request.json or {}
    EXECUTED_ORDERS.append(order)
    return jsonify({
        "orderId": len(EXECUTED_ORDERS),
        "status": "FILLED",
        "symbol": order.get("symbol"),
        "side": order.get("side"),
        "quantity": order.get("quantity"),
        "price": order.get("price", 0),
        "executedQty": order.get("quantity")
    })

@app.route("/executed_orders", methods=["GET"])
def get_executed():
    return jsonify(EXECUTED_ORDERS)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055, debug=False)
'''
(workspace / "scripts" / "mock_server.py").write_text(mock_server_code)

print("Workspace generated successfully.")
print(f"Files created:")
for p in sorted(workspace.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(workspace)}")