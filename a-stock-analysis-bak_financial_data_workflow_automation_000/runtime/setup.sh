#!/bin/bash
set -e

# Start the mock Sina Finance API server
cat > /tmp/mock_sina_server.py << 'MOCK_EOF'
#!/usr/bin/env python3
"""Mock server for Sina Finance APIs to ensure deterministic test results."""
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

MOCK_STOCKS = {
    "600789": {
        "code": "600789", "name": "鲁抗医药",
        "open": 10.20, "prev_close": 10.23,
        "price": 10.32, "high": 10.77, "low": 9.82,
        "volume": 21818380, "amount": 2251053000.0,
        "change_pct": 0.88
    },
    "002446": {
        "code": "002446", "name": "盛路通信",
        "open": 8.35, "prev_close": 8.32,
        "price": 8.48, "high": 8.62, "low": 8.28,
        "volume": 9800000, "amount": 830580000.0,
        "change_pct": 1.92
    },
    "002342": {
        "code": "002342", "name": "巨星科技",
        "open": 14.80, "prev_close": 14.75,
        "price": 15.10, "high": 15.35, "low": 14.65,
        "volume": 5640000, "amount": 851400000.0,
        "change_pct": 2.37
    },
    "300750": {
        "code": "300750", "name": "宁德时代",
        "open": 186.00, "prev_close": 185.60,
        "price": 187.50, "high": 189.20, "low": 184.80,
        "volume": 12350000, "amount": 23153250000.0,
        "change_pct": 1.02
    },
    "000858": {
        "code": "000858", "name": "五粮液",
        "open": 143.50, "prev_close": 143.20,
        "price": 144.80, "high": 145.60, "low": 142.90,
        "volume": 4230000, "amount": 6122040000.0,
        "change_pct": 1.12
    },
}

MOCK_MINUTE_DATA = {
    "600789": [
        {"d": "2024-01-15 09:31:00", "c": "10.03", "v": "216545", "turnover": "21965.3"},
        {"d": "2024-01-15 09:32:00", "c": "10.10", "v": "189234", "turnover": "19113.1"},
        {"d": "2024-01-15 09:33:00", "c": "10.15", "v": "203411", "turnover": "20646.2"},
        {"d": "2024-01-15 09:45:00", "c": "10.20", "v": "98234", "turnover": "10019.9"},
        {"d": "2024-01-15 09:55:00", "c": "10.25", "v": "87654", "turnover": "8984.5"},
        {"d": "2024-01-15 10:05:00", "c": "10.30", "v": "65432", "turnover": "6739.5"},
        {"d": "2024-01-15 10:30:00", "c": "10.35", "v": "54321", "turnover": "5622.2"},
        {"d": "2024-01-15 11:00:00", "c": "10.28", "v": "43210", "turnover": "4441.6"},
        {"d": "2024-01-15 13:05:00", "c": "10.32", "v": "32100", "turnover": "3313.5"},
        {"d": "2024-01-15 14:35:00", "c": "10.45", "v": "76543", "turnover": "7998.7"},
        {"d": "2024-01-15 14:45:00", "c": "10.50", "v": "54321", "turnover": "5703.7"},
        {"d": "2024-01-15 14:55:00", "c": "10.52", "v": "45678", "turnover": "4805.3"},
    ],
}

@app.route('/hq')
def hq():
    codes_param = request.args.get('codes', '')
    codes = [c.strip() for c in codes_param.split(',') if c.strip()]
    result = {}
    for code in codes:
        if code in MOCK_STOCKS:
            result[code] = MOCK_STOCKS[code]
        else:
            result[code] = {"code": code, "name": code, "price": 0, "change_pct": 0,
                           "open": 0, "high": 0, "low": 0, "prev_close": 0,
                           "volume": 0, "amount": 0}
    return jsonify(result)

@app.route('/minute')
def minute():
    code = request.args.get('code', '')
    data = MOCK_MINUTE_DATA.get(code, [
        {"d": "2024-01-15 09:31:00", "c": "10.00", "v": "10000", "turnover": "1000.0"},
        {"d": "2024-01-15 10:05:00", "c": "10.05", "v": "8000", "turnover": "804.0"},
        {"d": "2024-01-15 13:05:00", "c": "10.08", "v": "5000", "turnover": "504.0"},
        {"d": "2024-01-15 14:35:00", "c": "10.10", "v": "3000", "turnover": "303.0"},
    ])
    return jsonify(data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8766, debug=False)
MOCK_EOF

python3 /tmp/mock_sina_server.py &
MOCK_PID=$!
echo "Mock server started with PID $MOCK_PID"

# Wait for mock server to start
sleep 2

# Verify server is running
curl -s "http://localhost:8766/hq?codes=600789" > /dev/null && echo "Mock server is responding" || echo "WARNING: Mock server may not be ready"

# Export environment variable so scripts use the mock server
export MOCK_SERVER_BASE="http://localhost:8766"

# Also persist it for the agent's shell sessions
echo 'export MOCK_SERVER_BASE="http://localhost:8766"' >> /root/.bashrc
echo 'export MOCK_SERVER_BASE="http://localhost:8766"' >> /root/.profile

# Set up uv environment for the skill
cd /opt/a-stock-analysis
uv sync --quiet 2>/dev/null || uv pip install requests --quiet 2>/dev/null || true

# Verify the scripts are executable and accessible
ls -la /opt/a-stock-analysis/scripts/

# Test that the analyze script works via uv
cd /opt/a-stock-analysis
MOCK_SERVER_BASE="http://localhost:8766" uv run scripts/analyze.py 600789 --json 2>/dev/null | head -5 || true

echo "Setup complete. Skill base directory: /opt/a-stock-analysis"
echo "Usage: uv run /opt/a-stock-analysis/scripts/analyze.py <code> [--minute] [--json]"
echo "Usage: uv run /opt/a-stock-analysis/scripts/portfolio.py <cmd> [args]"