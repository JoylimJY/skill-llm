#!/bin/bash
set -e

# Start a local mock "gold data API" server that serves the market_data.json
# This simulates web search results the agent can query

cat > /workspace/tools/scripts/mock_gold_server.py << 'PYEOF'
from flask import Flask, jsonify, request
import json
import os

app = Flask(__name__)

with open('/workspace/market_data.json', 'r', encoding='utf-8') as f:
    MARKET_DATA = json.load(f)

@app.route('/gold/international', methods=['GET'])
def international_gold():
    return jsonify(MARKET_DATA['international_gold'])

@app.route('/gold/domestic', methods=['GET'])
def domestic_gold():
    return jsonify(MARKET_DATA['domestic_gold'])

@app.route('/gold/history', methods=['GET'])
def gold_history():
    return jsonify(MARKET_DATA['historical_3month'])

@app.route('/gold/macro', methods=['GET'])
def macro_factors():
    return jsonify(MARKET_DATA['macro_factors'])

@app.route('/gold/etf', methods=['GET'])
def etf_data():
    return jsonify(MARKET_DATA['etf_data'])

@app.route('/gold/all', methods=['GET'])
def all_data():
    return jsonify(MARKET_DATA)

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').lower()
    if 'xauusd' in query or 'gold price' in query or '金价' in query or 'au9999' in query:
        return jsonify(MARKET_DATA)
    return jsonify({"result": "no data", "query": query})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7474, debug=False)
PYEOF

# Start mock server in background
python /workspace/tools/scripts/mock_gold_server.py &
MOCK_SERVER_PID=$!
echo "Mock gold data server started with PID $MOCK_SERVER_PID on port 7474"
sleep 2

# Verify server is running
if curl -s http://localhost:7474/gold/all > /dev/null 2>&1; then
    echo "Mock server is responding correctly."
else
    echo "WARNING: Mock server may not be ready yet."
fi

# Make the mock server PID available
echo $MOCK_SERVER_PID > /workspace/.mock_server_pid

echo "Setup complete. Market data API available at http://localhost:7474"
echo "Endpoints: /gold/all, /gold/international, /gold/domestic, /gold/history, /gold/macro, /gold/etf"